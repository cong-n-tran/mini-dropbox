"""
Database models for Mini Dropbox
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, BigInteger
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash
from app import db


class User(db.Model):
    """User model for authentication and authorization"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    storage_quota = Column(BigInteger, default=5368709120)  # 5GB default
    storage_used = Column(BigInteger, default=0)
    
    # Relationships
    files = relationship('File', backref='owner', lazy='dynamic', cascade='all, delete-orphan')
    devices = relationship('Device', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if provided password matches hash"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'storage_quota': self.storage_quota,
            'storage_used': self.storage_used
        }


class Device(db.Model):
    """Device model for tracking user devices"""
    __tablename__ = 'devices'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    device_name = Column(String(100), nullable=False)
    device_type = Column(String(50))  # desktop, mobile, web
    device_id = Column(String(255), unique=True, nullable=False, index=True)
    last_sync = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'device_name': self.device_name,
            'device_type': self.device_type,
            'device_id': self.device_id,
            'last_sync': self.last_sync.isoformat() if self.last_sync else None,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class File(db.Model):
    """File model for storing file metadata"""
    __tablename__ = 'files'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)  # Path in storage system
    file_hash = Column(String(64), nullable=False, index=True)  # SHA256 hash
    file_size = Column(BigInteger, nullable=False)
    mime_type = Column(String(100))
    version = Column(Integer, default=1)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    versions = relationship('FileVersion', backref='file', lazy='dynamic', cascade='all, delete-orphan')
    shares = relationship('FileShare', backref='file', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_size': self.file_size,
            'mime_type': self.mime_type,
            'version': self.version,
            'is_deleted': self.is_deleted,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'file_hash': self.file_hash
        }


class FileVersion(db.Model):
    """File version model for versioning support"""
    __tablename__ = 'file_versions'
    
    id = Column(Integer, primary_key=True)
    file_id = Column(Integer, ForeignKey('files.id'), nullable=False)
    version_number = Column(Integer, nullable=False)
    file_path = Column(String(500), nullable=False)
    file_hash = Column(String(64), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'version_number': self.version_number,
            'file_size': self.file_size,
            'file_hash': self.file_hash,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class FileShare(db.Model):
    """File sharing model"""
    __tablename__ = 'file_shares'
    
    id = Column(Integer, primary_key=True)
    file_id = Column(Integer, ForeignKey('files.id'), nullable=False)
    shared_with_user_id = Column(Integer, ForeignKey('users.id'), nullable=True)  # None for public links
    share_token = Column(String(255), unique=True, nullable=False, index=True)
    permission = Column(String(20), default='read')  # read, write, admin
    expires_at = Column(DateTime)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    shared_with_user = relationship('User', foreign_keys=[shared_with_user_id])
    
    def to_dict(self):
        return {
            'id': self.id,
            'share_token': self.share_token,
            'permission': self.permission,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'shared_with_user': self.shared_with_user.username if self.shared_with_user else None
        }


class SyncEvent(db.Model):
    """Sync event model for tracking file changes"""
    __tablename__ = 'sync_events'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    file_id = Column(Integer, ForeignKey('files.id'), nullable=True)  # None for folder events
    event_type = Column(String(50), nullable=False)  # upload, update, delete, rename
    event_data = Column(Text)  # JSON data for the event
    device_id = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    processed = Column(Boolean, default=False)
    
    # Relationships
    user = relationship('User')
    file = relationship('File')
    
    def to_dict(self):
        return {
            'id': self.id,
            'event_type': self.event_type,
            'event_data': self.event_data,
            'device_id': self.device_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'processed': self.processed,
            'file': self.file.to_dict() if self.file else None
        }