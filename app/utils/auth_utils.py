"""
Authentication utilities
"""

import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from app.models import User
from app import db


def generate_device_id():
    """Generate a unique device ID"""
    import uuid
    return str(uuid.uuid4())


def create_access_token(user_id, expires_delta=None):
    """Create JWT access token"""
    if expires_delta is None:
        expires_delta = timedelta(hours=24)
    
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + expires_delta,
        'iat': datetime.utcnow()
    }
    
    return jwt.encode(payload, current_app.config['JWT_SECRET_KEY'], algorithm='HS256')


def decode_token(token):
    """Decode JWT token"""
    try:
        payload = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            verify_jwt_in_request()
            current_user_id = get_jwt_identity()
            current_user = User.query.get(current_user_id)
            
            if not current_user or not current_user.is_active:
                return jsonify({'error': 'Invalid or inactive user'}), 401
            
            # Add current_user to kwargs for easy access
            kwargs['current_user'] = current_user
            return f(*args, **kwargs)
            
        except Exception as e:
            return jsonify({'error': 'Authentication required'}), 401
    
    return decorated_function


def validate_user_access_to_file(user, file_obj):
    """Check if user has access to a file"""
    if file_obj.user_id == user.id:
        return True
    
    # Check if file is shared with user
    from app.models import FileShare
    share = FileShare.query.filter_by(
        file_id=file_obj.id,
        shared_with_user_id=user.id,
        is_active=True
    ).first()
    
    if share:
        if share.expires_at is None or share.expires_at > datetime.utcnow():
            return True
    
    return False


def validate_share_token(token):
    """Validate a file share token"""
    from app.models import FileShare
    share = FileShare.query.filter_by(
        share_token=token,
        is_active=True
    ).first()
    
    if not share:
        return None
    
    if share.expires_at and share.expires_at <= datetime.utcnow():
        return None
    
    return share