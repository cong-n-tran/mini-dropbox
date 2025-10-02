#!/usr/bin/env python3
import os
import sys
import json
import argparse
import requests
from pathlib import Path

# Configuration
API_BASE_URL = 'http://localhost:5000'
TOKEN_FILE = os.path.expanduser('~/.mini_dropbox_token')

class DropboxClient:
    def __init__(self):
        self.base_url = API_BASE_URL
        self.token = self.load_token()
    
    def load_token(self):
        """Load JWT token from local file."""
        try:
            if os.path.exists(TOKEN_FILE):
                with open(TOKEN_FILE, 'r') as f:
                    data = json.load(f)
                    return data.get('token')
        except Exception as e:
            print(f"Warning: Could not load token: {e}")
        return None
    
    def save_token(self, token):
        """Save JWT token to local file."""
        try:
            with open(TOKEN_FILE, 'w') as f:
                json.dump({'token': token}, f)
            print("Login successful! Token saved.")
        except Exception as e:
            print(f"Warning: Could not save token: {e}")
    
    def get_headers(self):
        """Get headers with authorization token."""
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        return headers
    
    def signup(self, username, password):
        """Sign up a new user."""
        try:
            data = {'username': username, 'password': password}
            response = requests.post(f'{self.base_url}/signup', json=data)
            
            if response.status_code == 201:
                result = response.json()
                self.token = result['token']
                self.save_token(self.token)
                print(f"Signup successful! Welcome {username}!")
                return True
            else:
                error = response.json().get('error', 'Signup failed')
                print(f"Signup failed: {error}")
                return False
        except requests.exceptions.ConnectionError:
            print("Error: Cannot connect to the server. Make sure the backend is running.")
            return False
        except Exception as e:
            print(f"Error during signup: {e}")
            return False
    
    def login(self, username, password):
        """Log in an existing user."""
        try:
            data = {'username': username, 'password': password}
            response = requests.post(f'{self.base_url}/login', json=data)
            
            if response.status_code == 200:
                result = response.json()
                self.token = result['token']
                self.save_token(self.token)
                print(f"Login successful! Welcome back {username}!")
                return True
            else:
                error = response.json().get('error', 'Login failed')
                print(f"Login failed: {error}")
                return False
        except requests.exceptions.ConnectionError:
            print("Error: Cannot connect to the server. Make sure the backend is running.")
            return False
        except Exception as e:
            print(f"Error during login: {e}")
            return False
    
    def upload(self, file_path):
        """Upload a file to the server."""
        if not self.token:
            print("Error: You must login first. Use 'login' command.")
            return False
        
        if not os.path.exists(file_path):
            print(f"Error: File '{file_path}' not found.")
            return False
        
        try:
            with open(file_path, 'rb') as f:
                files = {'file': f}
                headers = {'Authorization': f'Bearer {self.token}'}
                response = requests.post(f'{self.base_url}/upload', 
                                       files=files, headers=headers)
            
            if response.status_code == 201:
                result = response.json()
                print(f"Upload successful!")
                print(f"File: {result['filename']}")
                print(f"Size: {result['size']} bytes")
                print(f"File ID: {result['file_id']}")
                return True
            else:
                error = response.json().get('error', 'Upload failed')
                print(f"Upload failed: {error}")
                return False
        except requests.exceptions.ConnectionError:
            print("Error: Cannot connect to the server. Make sure the backend is running.")
            return False
        except Exception as e:
            print(f"Error during upload: {e}")
            return False
    
    def download(self, file_id, output_path=None):
        """Download a file from the server."""
        if not self.token:
            print("Error: You must login first. Use 'login' command.")
            return False
        
        try:
            headers = {'Authorization': f'Bearer {self.token}'}
            response = requests.get(f'{self.base_url}/download/{file_id}', 
                                  headers=headers)
            
            if response.status_code == 200:
                # Get filename from response headers or use default
                filename = 'downloaded_file'
                if 'Content-Disposition' in response.headers:
                    content_disposition = response.headers['Content-Disposition']
                    if 'filename=' in content_disposition:
                        filename = content_disposition.split('filename=')[-1].strip('"')
                
                # Use provided output path or default filename
                if output_path:
                    save_path = output_path
                else:
                    save_path = filename
                
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                
                print(f"Download successful! File saved as: {save_path}")
                return True
            else:
                error = response.json().get('error', 'Download failed')
                print(f"Download failed: {error}")
                return False
        except requests.exceptions.ConnectionError:
            print("Error: Cannot connect to the server. Make sure the backend is running.")
            return False
        except Exception as e:
            print(f"Error during download: {e}")
            return False
    
    def list_files(self):
        """List all user's files."""
        if not self.token:
            print("Error: You must login first. Use 'login' command.")
            return False
        
        try:
            headers = {'Authorization': f'Bearer {self.token}'}
            response = requests.get(f'{self.base_url}/files', headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                files = result['files']
                
                if not files:
                    print("No files found.")
                    return True
                
                print("\nYour files:")
                print(f"{'ID':<4} {'Filename':<30} {'Size':<12} {'Upload Time'}")
                print("-" * 70)
                
                for file in files:
                    size_str = f"{file['size']} bytes"
                    upload_time = file['upload_time'][:19]  # Remove microseconds
                    print(f"{file['id']:<4} {file['filename']:<30} {size_str:<12} {upload_time}")
                
                return True
            else:
                error = response.json().get('error', 'Failed to list files')
                print(f"Error: {error}")
                return False
        except requests.exceptions.ConnectionError:
            print("Error: Cannot connect to the server. Make sure the backend is running.")
            return False
        except Exception as e:
            print(f"Error listing files: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(description='Mini Dropbox CLI Client')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Signup command
    signup_parser = subparsers.add_parser('signup', help='Create a new account')
    signup_parser.add_argument('username', help='Username')
    signup_parser.add_argument('password', help='Password')
    
    # Login command  
    login_parser = subparsers.add_parser('login', help='Login to your account')
    login_parser.add_argument('username', help='Username')
    login_parser.add_argument('password', help='Password')
    
    # Upload command
    upload_parser = subparsers.add_parser('upload', help='Upload a file')
    upload_parser.add_argument('file_path', help='Path to file to upload')
    
    # Download command
    download_parser = subparsers.add_parser('download', help='Download a file')
    download_parser.add_argument('file_id', type=int, help='ID of file to download')
    download_parser.add_argument('-o', '--output', help='Output file path')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List your files')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    client = DropboxClient()
    
    if args.command == 'signup':
        client.signup(args.username, args.password)
    elif args.command == 'login':
        client.login(args.username, args.password)
    elif args.command == 'upload':
        client.upload(args.file_path)
    elif args.command == 'download':
        client.download(args.file_id, args.output)
    elif args.command == 'list':
        client.list_files()

if __name__ == '__main__':
    main()