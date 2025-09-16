"""
File service for handling file operations
"""

import os
import shutil
from datetime import datetime
from app import db
from app.models import File, FileVersion, User, SyncEvent
from app.utils.file_utils import (
    calculate_file_hash, generate_storage_path, save_file_to_storage,
    delete_file_from_storage, get_full_storage_path
)


class FileService:
    """Service class for file operations"""
    
    @staticmethod
    def create_file_version(file_record, file_data, device_id=None):
        """Create a new version of an existing file"""
        try:
            # Calculate new hash
            new_hash = calculate_file_hash(file_data)
            
            # Check if this version already exists
            existing_version = FileVersion.query.filter_by(
                file_id=file_record.id,
                file_hash=new_hash
            ).first()
            
            if existing_version:
                return existing_version, False  # Version already exists
            
            # Generate new storage path
            storage_path = generate_storage_path(new_hash, file_record.original_filename)
            
            # Save file to storage
            save_file_to_storage(file_data, storage_path)
            
            # Get file size
            from app.utils.file_utils import get_file_size
            file_size = get_file_size(file_data)
            
            # Create new version record
            new_version = FileVersion(
                file_id=file_record.id,
                version_number=file_record.version + 1,
                file_path=storage_path,
                file_hash=new_hash,
                file_size=file_size
            )
            
            # Update main file record
            old_size = file_record.file_size
            file_record.file_path = storage_path
            file_record.file_hash = new_hash
            file_record.file_size = file_size
            file_record.version = new_version.version_number
            file_record.updated_at = datetime.utcnow()
            
            # Update user storage usage
            user = User.query.get(file_record.user_id)
            if user:
                user.storage_used = user.storage_used - old_size + file_size
            
            # Create sync event
            sync_event = SyncEvent(
                user_id=file_record.user_id,
                file_id=file_record.id,
                event_type='update',
                device_id=device_id,
                event_data=f'{{"filename": "{file_record.original_filename}", "version": {new_version.version_number}}}'
            )
            
            db.session.add(new_version)
            db.session.add(sync_event)
            db.session.commit()
            
            return new_version, True  # New version created
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    @staticmethod
    def restore_file_version(file_record, version_number, device_id=None):
        """Restore a file to a specific version"""
        try:
            # Find the version
            version = FileVersion.query.filter_by(
                file_id=file_record.id,
                version_number=version_number
            ).first()
            
            if not version:
                raise ValueError("Version not found")
            
            # Check if version file exists
            version_path = get_full_storage_path(version.file_path)
            if not os.path.exists(version_path):
                raise ValueError("Version file not found in storage")
            
            # Create new storage path for current version
            current_storage_path = generate_storage_path(
                file_record.file_hash, 
                file_record.original_filename
            )
            
            # Copy version file to new location
            current_full_path = get_full_storage_path(current_storage_path)
            os.makedirs(os.path.dirname(current_full_path), exist_ok=True)
            shutil.copy2(version_path, current_full_path)
            
            # Update file record
            old_size = file_record.file_size
            file_record.file_path = current_storage_path
            file_record.file_hash = version.file_hash
            file_record.file_size = version.file_size
            file_record.version += 1  # Increment version
            file_record.updated_at = datetime.utcnow()
            
            # Update user storage usage
            user = User.query.get(file_record.user_id)
            if user:
                user.storage_used = user.storage_used - old_size + version.file_size
            
            # Create new version record for the restored version
            new_version = FileVersion(
                file_id=file_record.id,
                version_number=file_record.version,
                file_path=current_storage_path,
                file_hash=version.file_hash,
                file_size=version.file_size
            )
            
            # Create sync event
            sync_event = SyncEvent(
                user_id=file_record.user_id,
                file_id=file_record.id,
                event_type='restore',
                device_id=device_id,
                event_data=f'{{"filename": "{file_record.original_filename}", "restored_to_version": {version_number}, "new_version": {file_record.version}}}'
            )
            
            db.session.add(new_version)
            db.session.add(sync_event)
            db.session.commit()
            
            return new_version
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    @staticmethod
    def cleanup_old_versions(file_record, keep_versions=10):
        """Clean up old versions, keeping only the latest N versions"""
        try:
            versions = FileVersion.query.filter_by(
                file_id=file_record.id
            ).order_by(FileVersion.version_number.desc()).all()
            
            if len(versions) <= keep_versions:
                return 0  # Nothing to clean up
            
            # Delete old versions
            versions_to_delete = versions[keep_versions:]
            deleted_count = 0
            
            for version in versions_to_delete:
                # Delete file from storage
                if delete_file_from_storage(version.file_path):
                    db.session.delete(version)
                    deleted_count += 1
            
            db.session.commit()
            return deleted_count
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    @staticmethod
    def get_file_statistics(user_id):
        """Get file statistics for a user"""
        try:
            user = User.query.get(user_id)
            if not user:
                return None
            
            # Get file counts by type
            from sqlalchemy import func
            file_stats = db.session.query(
                func.count(File.id).label('total_files'),
                func.sum(File.file_size).label('total_size'),
                func.count(func.distinct(File.mime_type)).label('file_types')
            ).filter_by(user_id=user_id, is_deleted=False).first()
            
            # Get top file types
            top_types = db.session.query(
                File.mime_type,
                func.count(File.id).label('count'),
                func.sum(File.file_size).label('size')
            ).filter_by(
                user_id=user_id, is_deleted=False
            ).group_by(File.mime_type).order_by(
                func.count(File.id).desc()
            ).limit(5).all()
            
            return {
                'total_files': file_stats.total_files or 0,
                'total_size': file_stats.total_size or 0,
                'file_types': file_stats.file_types or 0,
                'storage_used': user.storage_used,
                'storage_quota': user.storage_quota,
                'storage_percentage': (user.storage_used / user.storage_quota * 100) if user.storage_quota > 0 else 0,
                'top_file_types': [
                    {
                        'mime_type': t.mime_type,
                        'count': t.count,
                        'size': t.size
                    } for t in top_types
                ]
            }
            
        except Exception as e:
            raise e
    
    @staticmethod
    def bulk_delete_files(file_ids, user_id, device_id=None):
        """Delete multiple files at once"""
        try:
            files = File.query.filter(
                File.id.in_(file_ids),
                File.user_id == user_id,
                File.is_deleted == False
            ).all()
            
            if not files:
                return 0, "No files found"
            
            deleted_count = 0
            total_size_freed = 0
            
            for file_record in files:
                file_record.is_deleted = True
                file_record.updated_at = datetime.utcnow()
                total_size_freed += file_record.file_size
                deleted_count += 1
                
                # Create sync event
                sync_event = SyncEvent(
                    user_id=user_id,
                    file_id=file_record.id,
                    event_type='delete',
                    device_id=device_id,
                    event_data=f'{{"filename": "{file_record.original_filename}"}}'
                )
                db.session.add(sync_event)
            
            # Update user storage usage
            user = User.query.get(user_id)
            if user:
                user.storage_used -= total_size_freed
                if user.storage_used < 0:
                    user.storage_used = 0
            
            db.session.commit()
            
            return deleted_count, f"Deleted {deleted_count} files, freed {total_size_freed} bytes"
            
        except Exception as e:
            db.session.rollback()
            raise e