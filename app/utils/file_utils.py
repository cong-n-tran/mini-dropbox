"""
Utility functions for file handling and storage
"""

import os
import hashlib
import uuid
from werkzeug.utils import secure_filename
from flask import current_app


def allowed_file(filename):
    """Check if file extension is allowed"""
    if not filename or '.' not in filename:
        return False
    
    extension = filename.rsplit('.', 1)[1].lower()
    return extension in current_app.config['ALLOWED_EXTENSIONS']


def calculate_file_hash(file_data):
    """Calculate SHA256 hash of file data"""
    hasher = hashlib.sha256()
    
    if hasattr(file_data, 'read'):
        # File-like object
        file_data.seek(0)
        for chunk in iter(lambda: file_data.read(4096), b""):
            hasher.update(chunk)
        file_data.seek(0)
    else:
        # Bytes data
        hasher.update(file_data)
    
    return hasher.hexdigest()


def generate_storage_path(file_hash, original_filename):
    """Generate distributed storage path based on file hash"""
    # Use first 2 characters of hash for directory structure
    dir1 = file_hash[:2]
    dir2 = file_hash[2:4]
    
    # Generate unique filename to avoid collisions
    unique_filename = f"{file_hash}_{uuid.uuid4().hex[:8]}_{secure_filename(original_filename)}"
    
    return os.path.join(dir1, dir2, unique_filename)


def ensure_storage_directory(storage_path):
    """Ensure storage directory exists"""
    full_path = os.path.join(current_app.config['STORAGE_PATH'], os.path.dirname(storage_path))
    os.makedirs(full_path, exist_ok=True)
    return full_path


def get_full_storage_path(storage_path):
    """Get full filesystem path for stored file"""
    return os.path.join(current_app.config['STORAGE_PATH'], storage_path)


def save_file_to_storage(file_data, storage_path):
    """Save file data to storage location"""
    full_path = get_full_storage_path(storage_path)
    ensure_storage_directory(storage_path)
    
    if hasattr(file_data, 'save'):
        # Flask file object
        file_data.save(full_path)
    else:
        # Raw bytes
        with open(full_path, 'wb') as f:
            f.write(file_data)
    
    return full_path


def delete_file_from_storage(storage_path):
    """Delete file from storage"""
    try:
        full_path = get_full_storage_path(storage_path)
        if os.path.exists(full_path):
            os.remove(full_path)
            return True
    except OSError:
        pass
    return False


def get_file_size(file_obj):
    """Get size of file object"""
    if hasattr(file_obj, 'seek') and hasattr(file_obj, 'tell'):
        # File-like object
        file_obj.seek(0, 2)  # Seek to end
        size = file_obj.tell()
        file_obj.seek(0)  # Reset to beginning
        return size
    else:
        # Bytes data
        return len(file_obj)


def format_file_size(size_bytes):
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"


def validate_file_size(file_obj):
    """Validate if file size is within limits"""
    size = get_file_size(file_obj)
    max_size = current_app.config['MAX_FILE_SIZE']
    return size <= max_size, size


def generate_share_token():
    """Generate a secure share token"""
    return uuid.uuid4().hex + uuid.uuid4().hex[:16]  # 48 characters