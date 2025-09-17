"""
File management routes
"""

import os
import mimetypes
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from app import db, socketio
from app.models import User, File, FileVersion, FileShare, SyncEvent
from app.utils.file_utils import (
    allowed_file, calculate_file_hash, generate_storage_path,
    save_file_to_storage, delete_file_from_storage, validate_file_size,
    get_full_storage_path, generate_share_token
)
from app.utils.auth_utils import validate_user_access_to_file, validate_share_token

files_bp = Blueprint('files', __name__)


@files_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_file():
    """Upload a file"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file_obj = request.files['file']
        if file_obj.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Validate file
        if not allowed_file(file_obj.filename):
            return jsonify({'error': 'File type not allowed'}), 400
        
        # Validate file size
        is_valid_size, file_size = validate_file_size(file_obj)
        if not is_valid_size:
            return jsonify({'error': 'File size exceeds limit'}), 400
        
        # Check user storage quota
        if user.storage_used + file_size > user.storage_quota:
            return jsonify({'error': 'Storage quota exceeded'}), 400
        
        # Calculate file hash
        file_hash = calculate_file_hash(file_obj)
        
        # Check if file already exists (deduplication)
        existing_file = File.query.filter_by(
            user_id=current_user_id,
            file_hash=file_hash,
            is_deleted=False
        ).first()
        
        if existing_file:
            return jsonify({
                'message': 'File already exists',
                'file': existing_file.to_dict()
            }), 200
        
        # Generate storage path
        storage_path = generate_storage_path(file_hash, file_obj.filename)
        
        # Save file to storage
        save_file_to_storage(file_obj, storage_path)
        
        # Get MIME type
        mime_type, _ = mimetypes.guess_type(file_obj.filename)
        
        # Create file record
        file_record = File(
            user_id=current_user_id,
            filename=secure_filename(file_obj.filename),
            original_filename=file_obj.filename,
            file_path=storage_path,
            file_hash=file_hash,
            file_size=file_size,
            mime_type=mime_type
        )
        
        db.session.add(file_record)
        
        # Update user storage usage
        user.storage_used += file_size
        
        # Create sync event
        device_id = request.headers.get('X-Device-ID')
        sync_event = SyncEvent(
            user_id=current_user_id,
            file_id=file_record.id,
            event_type='upload',
            device_id=device_id,
            event_data=f'{{"filename": "{file_obj.filename}", "size": {file_size}}}'
        )
        db.session.add(sync_event)
        
        db.session.commit()
        
        # Emit real-time notification
        socketio.emit('file_uploaded', {
            'file': file_record.to_dict(),
            'user_id': current_user_id
        }, room=f'user_{current_user_id}')
        
        return jsonify({
            'message': 'File uploaded successfully',
            'file': file_record.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500


@files_bp.route('/list', methods=['GET'])
@jwt_required()
def list_files():
    """List user's files"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 50, type=int), 100)
        search = request.args.get('search', '')
        
        # Build query
        query = File.query.filter_by(user_id=current_user_id, is_deleted=False)
        
        if search:
            query = query.filter(File.original_filename.contains(search))
        
        # Order by updated_at desc
        query = query.order_by(File.updated_at.desc())
        
        # Paginate
        pagination = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        files = [file.to_dict() for file in pagination.items]
        
        return jsonify({
            'files': files,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to list files'}), 500


@files_bp.route('/<int:file_id>', methods=['GET'])
@jwt_required()
def get_file_info(file_id):
    """Get file information"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        file_record = File.query.get(file_id)
        if not file_record:
            return jsonify({'error': 'File not found'}), 404
        
        if not validate_user_access_to_file(user, file_record):
            return jsonify({'error': 'Access denied'}), 403
        
        # Get file versions
        versions = FileVersion.query.filter_by(
            file_id=file_id
        ).order_by(FileVersion.version_number.desc()).all()
        
        file_data = file_record.to_dict()
        file_data['versions'] = [version.to_dict() for version in versions]
        
        return jsonify({'file': file_data}), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get file info'}), 500


@files_bp.route('/<int:file_id>/download', methods=['GET'])
@jwt_required()
def download_file(file_id):
    """Download a file"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        file_record = File.query.get(file_id)
        if not file_record or file_record.is_deleted:
            return jsonify({'error': 'File not found'}), 404
        
        if not validate_user_access_to_file(user, file_record):
            return jsonify({'error': 'Access denied'}), 403
        
        file_path = get_full_storage_path(file_record.file_path)
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found on storage'}), 404
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name=file_record.original_filename,
            mimetype=file_record.mime_type
        )
        
    except Exception as e:
        return jsonify({'error': f'Download failed: {str(e)}'}), 500


@files_bp.route('/<int:file_id>', methods=['DELETE'])
@jwt_required()
def delete_file(file_id):
    """Delete a file (soft delete)"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        file_record = File.query.get(file_id)
        if not file_record:
            return jsonify({'error': 'File not found'}), 404
        
        if file_record.user_id != current_user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        # Soft delete
        file_record.is_deleted = True
        file_record.updated_at = datetime.utcnow()
        
        # Update user storage usage
        user.storage_used -= file_record.file_size
        if user.storage_used < 0:
            user.storage_used = 0
        
        # Create sync event
        device_id = request.headers.get('X-Device-ID')
        sync_event = SyncEvent(
            user_id=current_user_id,
            file_id=file_id,
            event_type='delete',
            device_id=device_id,
            event_data=f'{{"filename": "{file_record.original_filename}"}}'
        )
        db.session.add(sync_event)
        
        db.session.commit()
        
        # Emit real-time notification
        socketio.emit('file_deleted', {
            'file_id': file_id,
            'user_id': current_user_id
        }, room=f'user_{current_user_id}')
        
        return jsonify({'message': 'File deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete file'}), 500


@files_bp.route('/<int:file_id>/share', methods=['POST'])
@jwt_required()
def share_file(file_id):
    """Create a share link for a file"""
    try:
        current_user_id = get_jwt_identity()
        
        file_record = File.query.get(file_id)
        if not file_record or file_record.is_deleted:
            return jsonify({'error': 'File not found'}), 404
        
        if file_record.user_id != current_user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        data = request.get_json() or {}
        
        # Parse expiration
        expires_at = None
        if data.get('expires_in_days'):
            expires_at = datetime.utcnow() + timedelta(days=int(data['expires_in_days']))
        
        # Create share record
        share = FileShare(
            file_id=file_id,
            share_token=generate_share_token(),
            permission=data.get('permission', 'read'),
            expires_at=expires_at
        )
        
        db.session.add(share)
        db.session.commit()
        
        return jsonify({
            'message': 'Share link created successfully',
            'share': share.to_dict(),
            'share_url': f'/api/files/shared/{share.share_token}'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create share link'}), 500


@files_bp.route('/shared/<share_token>', methods=['GET'])
def get_shared_file(share_token):
    """Access a shared file"""
    try:
        share = validate_share_token(share_token)
        if not share:
            return jsonify({'error': 'Invalid or expired share link'}), 404
        
        file_record = share.file
        if not file_record or file_record.is_deleted:
            return jsonify({'error': 'File not found'}), 404
        
        return jsonify({
            'file': file_record.to_dict(),
            'share': share.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to access shared file'}), 500


@files_bp.route('/shared/<share_token>/download', methods=['GET'])
def download_shared_file(share_token):
    """Download a shared file"""
    try:
        share = validate_share_token(share_token)
        if not share:
            return jsonify({'error': 'Invalid or expired share link'}), 404
        
        file_record = share.file
        if not file_record or file_record.is_deleted:
            return jsonify({'error': 'File not found'}), 404
        
        file_path = get_full_storage_path(file_record.file_path)
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found on storage'}), 404
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name=file_record.original_filename,
            mimetype=file_record.mime_type
        )
        
    except Exception as e:
        return jsonify({'error': f'Download failed: {str(e)}'}), 500