"""
Test configuration and fixtures
"""

import os
import tempfile
import pytest
from app import create_app, db


@pytest.fixture
def app():
    """Create and configure a test app"""
    # Create a temporary database file
    db_fd, db_path = tempfile.mkstemp()
    
    # Create temporary storage directory
    storage_dir = tempfile.mkdtemp()
    
    app = create_app()
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'STORAGE_PATH': storage_dir,
        'SECRET_KEY': 'test-secret-key',
        'JWT_SECRET_KEY': 'test-jwt-secret-key',
        'WTF_CSRF_ENABLED': False
    })
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()
    
    # Clean up
    os.close(db_fd)
    os.unlink(db_path)
    import shutil
    shutil.rmtree(storage_dir)


@pytest.fixture
def client(app):
    """Create a test client"""
    return app.test_client()


@pytest.fixture
def test_user(app):
    """Create a test user"""
    from app.models import User
    
    with app.app_context():
        user = User(
            username='testuser',
            email='test@example.com'
        )
        user.set_password('testpassword')
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def auth_headers(client, test_user):
    """Get authentication headers for test user"""
    response = client.post('/api/auth/login', json={
        'username': 'testuser',
        'password': 'testpassword'
    })
    
    data = response.get_json()
    token = data['access_token']
    
    return {'Authorization': f'Bearer {token}'}