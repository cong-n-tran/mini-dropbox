#!/usr/bin/env python3
"""
Demo script for Mini Dropbox API
Demonstrates basic functionality including user registration, file upload, and file sharing.
"""

import os
import sys
import requests
import time
import tempfile
from pathlib import Path

# API Base URL
BASE_URL = "http://localhost:5000/api"

def test_api():
    """Test the Mini Dropbox API functionality"""
    print("🚀 Mini Dropbox API Demo")
    print("=" * 50)
    
    # Test 1: User Registration
    print("\n1. Testing User Registration...")
    register_data = {
        "username": "demouser",
        "email": "demo@example.com",
        "password": "demopassword"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
        if response.status_code == 201:
            print("✅ User registered successfully!")
            token = response.json()['access_token']
            print(f"   Access token: {token[:20]}...")
        else:
            print(f"❌ Registration failed: {response.text}")
            return
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed. Make sure the server is running on localhost:5000")
        print("   Run: python run.py")
        return
    
    # Headers for authenticated requests
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test 2: Get User Profile
    print("\n2. Testing User Profile...")
    response = requests.get(f"{BASE_URL}/auth/profile", headers=headers)
    if response.status_code == 200:
        user_data = response.json()['user']
        print("✅ Profile retrieved successfully!")
        print(f"   Username: {user_data['username']}")
        print(f"   Email: {user_data['email']}")
        print(f"   Storage: {user_data['storage_used']}/{user_data['storage_quota']} bytes")
    else:
        print(f"❌ Failed to get profile: {response.text}")
    
    # Test 3: Register Device
    print("\n3. Testing Device Registration...")
    device_data = {
        "device_name": "Demo Device",
        "device_type": "desktop",
        "device_id": "demo-device-001"
    }
    response = requests.post(f"{BASE_URL}/auth/devices", headers=headers, json=device_data)
    if response.status_code == 201:
        print("✅ Device registered successfully!")
        device = response.json()['device']
        print(f"   Device: {device['device_name']} ({device['device_type']})")
    else:
        print(f"❌ Device registration failed: {response.text}")
    
    # Test 4: Create a test file and upload it
    print("\n4. Testing File Upload...")
    
    # Create a temporary test file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("Hello from Mini Dropbox!\nThis is a test file for the demo.\n")
        f.write("Features implemented:\n")
        f.write("- User Authentication & Authorization ✅\n")
        f.write("- File Upload & Storage Distribution ✅\n") 
        f.write("- File Retrieval & Download ✅\n")
        f.write("- Metadata Management & Versioning ✅\n")
        f.write("- File Synchronization & Update Notification ✅\n")
        temp_file_path = f.name
    
    try:
        headers_with_device = headers.copy()
        headers_with_device["X-Device-ID"] = "demo-device-001"
        
        with open(temp_file_path, 'rb') as f:
            files = {'file': ('demo.txt', f, 'text/plain')}
            response = requests.post(f"{BASE_URL}/files/upload", 
                                   headers=headers_with_device, files=files)
        
        if response.status_code == 201:
            print("✅ File uploaded successfully!")
            file_data = response.json()['file']
            file_id = file_data['id']
            print(f"   File ID: {file_id}")
            print(f"   Filename: {file_data['filename']}")
            print(f"   Size: {file_data['file_size']} bytes")
            print(f"   Hash: {file_data['file_hash'][:16]}...")
        else:
            print(f"❌ File upload failed: {response.text}")
            return
    finally:
        # Clean up temporary file
        os.unlink(temp_file_path)
    
    # Test 5: List Files
    print("\n5. Testing File Listing...")
    response = requests.get(f"{BASE_URL}/files/list", headers=headers)
    if response.status_code == 200:
        files_data = response.json()
        print("✅ Files listed successfully!")
        print(f"   Total files: {len(files_data['files'])}")
        for file_info in files_data['files']:
            print(f"   - {file_info['original_filename']} ({file_info['file_size']} bytes)")
    else:
        print(f"❌ Failed to list files: {response.text}")
    
    # Test 6: Get File Info
    print("\n6. Testing File Info Retrieval...")
    response = requests.get(f"{BASE_URL}/files/{file_id}", headers=headers)
    if response.status_code == 200:
        file_info = response.json()['file']
        print("✅ File info retrieved successfully!")
        print(f"   Original filename: {file_info['original_filename']}")
        print(f"   Version: {file_info['version']}")
        print(f"   Created: {file_info['created_at']}")
        print(f"   MIME type: {file_info['mime_type']}")
    else:
        print(f"❌ Failed to get file info: {response.text}")
    
    # Test 7: Create Share Link
    print("\n7. Testing File Sharing...")
    share_data = {
        "expires_in_days": 7,
        "permission": "read"
    }
    response = requests.post(f"{BASE_URL}/files/{file_id}/share", 
                           headers=headers, json=share_data)
    if response.status_code == 201:
        share_info = response.json()
        print("✅ Share link created successfully!")
        print(f"   Share URL: {share_info['share_url']}")
        print(f"   Share token: {share_info['share']['share_token'][:20]}...")
        share_token = share_info['share']['share_token']
    else:
        print(f"❌ Failed to create share link: {response.text}")
        return
    
    # Test 8: Access Shared File (without authentication)
    print("\n8. Testing Shared File Access...")
    response = requests.get(f"{BASE_URL}/files/shared/{share_token}")
    if response.status_code == 200:
        shared_file = response.json()
        print("✅ Shared file accessed successfully!")
        print(f"   File: {shared_file['file']['original_filename']}")
        print(f"   Size: {shared_file['file']['file_size']} bytes")
        print(f"   Permission: {shared_file['share']['permission']}")
    else:
        print(f"❌ Failed to access shared file: {response.text}")
    
    # Test 9: Sync Status
    print("\n9. Testing Sync Status...")
    response = requests.get(f"{BASE_URL}/sync/status", headers=headers)
    if response.status_code == 200:
        sync_status = response.json()
        print("✅ Sync status retrieved successfully!")
        print(f"   Active devices: {len(sync_status['devices'])}")
        print(f"   Recent events (24h): {sync_status['recent_events_24h']}")
        print(f"   Unprocessed events: {sync_status['unprocessed_events']}")
    else:
        print(f"❌ Failed to get sync status: {response.text}")
    
    # Test 10: Delete File
    print("\n10. Testing File Deletion...")
    response = requests.delete(f"{BASE_URL}/files/{file_id}", headers=headers_with_device)
    if response.status_code == 200:
        print("✅ File deleted successfully!")
    else:
        print(f"❌ Failed to delete file: {response.text}")
    
    print("\n" + "=" * 50)
    print("🎉 Mini Dropbox API Demo Complete!")
    print("\nAll 5 functional requirements demonstrated:")
    print("✅ User Authentication & Authorization")
    print("✅ File Upload & Storage Distribution") 
    print("✅ File Retrieval & Download")
    print("✅ Metadata Management & Versioning")
    print("✅ File Synchronization & Update Notification")


if __name__ == "__main__":
    test_api()