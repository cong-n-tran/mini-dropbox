"""
Mini Dropbox - Distributed File Storage System
Main application factory and configuration
"""

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize extensions
db = SQLAlchemy()
jwt = JWTManager()
socketio = SocketIO(cors_allowed_origins="*")

def create_app():
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///mini_dropbox.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['STORAGE_PATH'] = os.getenv('STORAGE_PATH', './storage')
    app.config['MAX_FILE_SIZE'] = int(os.getenv('MAX_FILE_SIZE', 104857600))  # 100MB
    app.config['ALLOWED_EXTENSIONS'] = os.getenv('ALLOWED_EXTENSIONS', 'txt,pdf,png,jpg,jpeg,gif,doc,docx,xls,xlsx,ppt,pptx,zip,rar').split(',')
    
    # Initialize extensions with app
    db.init_app(app)
    jwt.init_app(app)
    socketio.init_app(app)
    
    # Create storage directory
    os.makedirs(app.config['STORAGE_PATH'], exist_ok=True)
    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.files import files_bp
    from app.routes.sync import sync_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(files_bp, url_prefix='/api/files')
    app.register_blueprint(sync_bp, url_prefix='/api/sync')
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app

if __name__ == '__main__':
    app = create_app()
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)