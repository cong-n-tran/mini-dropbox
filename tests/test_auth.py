"""
Tests for authentication endpoints
"""

import pytest
from app.models import User
from app import db


def test_user_registration(client):
    """Test user registration"""
    response = client.post('/api/auth/register', json={
        'username': 'newuser',
        'email': 'newuser@example.com',
        'password': 'newpassword'
    })
    
    assert response.status_code == 201
    data = response.get_json()
    assert 'access_token' in data
    assert data['user']['username'] == 'newuser'
    assert data['user']['email'] == 'newuser@example.com'


def test_user_registration_duplicate_username(client, test_user):
    """Test registration with duplicate username"""
    response = client.post('/api/auth/register', json={
        'username': 'testuser',  # Already exists
        'email': 'different@example.com',
        'password': 'password'
    })
    
    assert response.status_code == 409
    data = response.get_json()
    assert 'already exists' in data['error']


def test_user_login_success(client, test_user):
    """Test successful login"""
    response = client.post('/api/auth/login', json={
        'username': 'testuser',
        'password': 'testpassword'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'access_token' in data
    assert data['user']['username'] == 'testuser'


def test_user_login_invalid_credentials(client, test_user):
    """Test login with invalid credentials"""
    response = client.post('/api/auth/login', json={
        'username': 'testuser',
        'password': 'wrongpassword'
    })
    
    assert response.status_code == 401
    data = response.get_json()
    assert 'Invalid credentials' in data['error']


def test_get_profile(client, auth_headers):
    """Test getting user profile"""
    response = client.get('/api/auth/profile', headers=auth_headers)
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['user']['username'] == 'testuser'
    assert data['user']['email'] == 'test@example.com'


def test_get_profile_unauthorized(client):
    """Test getting profile without authentication"""
    response = client.get('/api/auth/profile')
    
    assert response.status_code == 401  # Unauthorized (missing JWT)


def test_device_registration(client, auth_headers):
    """Test device registration"""
    response = client.post('/api/auth/devices', 
                          headers=auth_headers,
                          json={
                              'device_name': 'Test Device',
                              'device_type': 'desktop',
                              'device_id': 'test-device-123'
                          })
    
    assert response.status_code == 201
    data = response.get_json()
    assert data['device']['device_name'] == 'Test Device'
    assert data['device']['device_type'] == 'desktop'


def test_list_devices(client, auth_headers):
    """Test listing user devices"""
    # First register a device
    client.post('/api/auth/devices', 
                headers=auth_headers,
                json={
                    'device_name': 'Test Device',
                    'device_type': 'desktop'
                })
    
    # Then list devices
    response = client.get('/api/auth/devices', headers=auth_headers)
    
    assert response.status_code == 200
    data = response.get_json()
    assert len(data['devices']) == 1
    assert data['devices'][0]['device_name'] == 'Test Device'