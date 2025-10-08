import os
import sqlite3
import hashlib
import jwt
import json
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['DATABASE'] = 'dropbox.db'

# Create upload directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def init_db():
    """Initialize the SQLite database with required tables."""
    conn = sqlite3.connect(app.config['DATABASE'])
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create files table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            original_filename TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            file_size INTEGER NOT NULL,
            file_path TEXT NOT NULL,
            upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def get_db_connection():
    """Get a database connection."""
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password):
    """Hash a password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

def generate_token(user_id):
    """Generate a JWT token for the user."""
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(days=1)
    }
    return jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')

def token_required(f):
    """Decorator to require JWT token for protected routes."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        try:
            if token.startswith('Bearer '):
                token = token[7:]
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user_id = data['user_id']
        except:
            return jsonify({'error': 'Token is invalid'}), 401
        
        return f(current_user_id, *args, **kwargs)
    
    return decorated

@app.route('/signup', methods=['POST'])
def signup():
    """User signup endpoint."""
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password are required'}), 400
    
    username = data['username']
    password = data['password']
    
    # Hash the password
    password_hash = hash_password(password)
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', 
                      (username, password_hash))
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        
        # Generate token for the new user
        token = generate_token(user_id)
        
        return jsonify({
            'message': 'User created successfully',
            'token': token,
            'user_id': user_id
        }), 201
        
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Username already exists'}), 409
    except Exception as e:
        return jsonify({'error': 'Registration failed'}), 500

@app.route('/login', methods=['POST'])
def login():
    """User login endpoint."""
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password are required'}), 400
    
    username = data['username']
    password = data['password']
    password_hash = hash_password(password)
    
    conn = get_db_connection()
    user = conn.execute('SELECT id FROM users WHERE username = ? AND password_hash = ?',
                       (username, password_hash)).fetchone()
    conn.close()
    
    if user:
        token = generate_token(user['id'])
        return jsonify({
            'message': 'Login successful',
            'token': token,
            'user_id': user['id']
        }), 200
    else:
        return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/upload', methods=['POST'])
@token_required
def upload_file(current_user_id):
    """File upload endpoint."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file:
        original_filename = secure_filename(file.filename)
        # Create unique filename to avoid conflicts
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{current_user_id}_{timestamp}_{original_filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Save the file
        file.save(file_path)
        file_size = os.path.getsize(file_path)
        
        # Save file metadata to database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO files (filename, original_filename, user_id, file_size, file_path)
            VALUES (?, ?, ?, ?, ?)
        ''', (filename, original_filename, current_user_id, file_size, file_path))
        conn.commit()
        file_id = cursor.lastrowid
        conn.close()
        
        return jsonify({
            'message': 'File uploaded successfully',
            'file_id': file_id,
            'filename': original_filename,
            'size': file_size
        }), 201

@app.route('/download/<int:file_id>', methods=['GET'])
@token_required
def download_file(current_user_id, file_id):
    """File download endpoint."""
    conn = get_db_connection()
    file_record = conn.execute('''
        SELECT * FROM files WHERE id = ? AND user_id = ?
    ''', (file_id, current_user_id)).fetchone()
    conn.close()
    
    if not file_record:
        return jsonify({'error': 'File not found'}), 404
    
    file_path = file_record['file_path']
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found on disk'}), 404
    
    return send_file(file_path, as_attachment=True, 
                    download_name=file_record['original_filename'])

@app.route('/files', methods=['GET'])
@token_required
def list_files(current_user_id):
    """List user's files endpoint."""
    conn = get_db_connection()
    files = conn.execute('''
        SELECT id, original_filename, file_size, upload_time 
        FROM files WHERE user_id = ? 
        ORDER BY upload_time DESC
    ''', (current_user_id,)).fetchall()
    conn.close()
    
    files_list = []
    for file in files:
        files_list.append({
            'id': file['id'],
            'filename': file['original_filename'],
            'size': file['file_size'],
            'upload_time': file['upload_time']
        })
    
    return jsonify({'files': files_list}), 200

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'message': 'Mini Dropbox API is running'}), 200

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)