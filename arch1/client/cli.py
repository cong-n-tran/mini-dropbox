import argparse
import os
import requests

API_URL = os.environ.get("API_URL", "http://localhost:5000")
TOKEN_FILE = os.path.expanduser("~/.mini_dropbox_token")

'''

## Add minimal CLI client and Flask backend for mini-dropbox MVP

This PR sets up a minimal working Dropbox-like app using Python.

**Features:**
- CLI client with signup, login, upload, download, and list commands.
- Flask backend exposing REST endpoints for auth and file management.
- SQLite DB for users and file metadata (auto-initialized).
- Local folder storage for uploaded files.

**Files Added:**
- `client/cli.py`: Python CLI implementation.
- `services/app.py`: Flask backend implementation.
- `services/Dockerfile`: Dockerfile for backend.

**How to test:**
1. Start backend:  
   `cd services && python app.py`
2. Use the CLI:  
   `cd client && python cli.py signup yourusername yourpassword`  
   `python cli.py login yourusername yourpassword`  
   `python cli.py upload path/to/yourfile.txt`  
   `python cli.py list`  
   `python cli.py download yourfile.txt`

**Notes:**  
- No backup or metadata separation yet—just one SQLite DB in the backend and file storage in a local directory.
- Ready for future extension (versioning, sync, redundancy).


'''

def save_token(token):
    with open(TOKEN_FILE, "w") as f:
        f.write(token)

def load_token():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE) as f:
            return f.read().strip()
    return None

def signup(args):
    username = args.username
    password = args.password
    resp = requests.post(f"{API_URL}/auth/signup", json={"username": username, "password": password})
    print(resp.json())

def login(args):
    username = args.username
    password = args.password
    resp = requests.post(f"{API_URL}/auth/login", json={"username": username, "password": password})
    data = resp.json()
    if "token" in data:
        save_token(data["token"])
        print("Login successful!")
    else:
        print("Login failed:", data)

def upload(args):
    token = load_token()
    if not token:
        print("Please login first.")
        return
    fname = args.file
    files = {'file': open(fname, 'rb')}
    headers = {'Authorization': f"Bearer {token}"}
    resp = requests.post(f"{API_URL}/files/upload", files=files, headers=headers)
    print(resp.json())

def download(args):
    token = load_token()
    if not token:
        print("Please login first.")
        return
    fname = args.file
    headers = {'Authorization': f"Bearer {token}"}
    resp = requests.get(f"{API_URL}/files/download/{fname}", headers=headers)
    if resp.status_code == 200:
        outname = args.output if args.output else fname
        with open(outname, 'wb') as f:
            f.write(resp.content)
        print(f"Downloaded to {outname}")
    else:
        print("Download failed:", resp.json())

def list_files(args):
    token = load_token()
    if not token:
        print("Please login first.")
        return
    headers = {'Authorization': f"Bearer {token}"}
    resp = requests.get(f"{API_URL}/files/list", headers=headers)
    print("Files:", resp.json())

def main():
    parser = argparse.ArgumentParser(description="Mini-Dropbox CLI Client")
    subparsers = parser.add_subparsers(dest="command")

    # Signup
    parser_signup = subparsers.add_parser("signup")
    parser_signup.add_argument("username")
    parser_signup.add_argument("password")
    parser_signup.set_defaults(func=signup)

    # Login
    parser_login = subparsers.add_parser("login")
    parser_login.add_argument("username")
    parser_login.add_argument("password")
    parser_login.set_defaults(func=login)

    # Upload
    parser_upload = subparsers.add_parser("upload")
    parser_upload.add_argument("file")
    parser_upload.set_defaults(func=upload)

    # Download
    parser_download = subparsers.add_parser("download")
    parser_download.add_argument("file")
    parser_download.add_argument("--output", help="Output file name")
    parser_download.set_defaults(func=download)

    # List files
    parser_list = subparsers.add_parser("list")
    parser_list.set_defaults(func=list_files)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()