import argparse
import os
import requests

# When running in Docker Compose, use the service name as host
API_URL = os.environ.get("API_URL", "http://services:5000")

def signup(args):
    print("Signup not implemented yet.")
    # Uncomment and implement when ready
    # username = args.username
    # password = args.password
    # resp = requests.post(f"{API_URL}/auth/signup", json={"username": username, "password": password})
    # print(resp.json())

def login(args):
    print("Login not implemented yet.")
    # Uncomment and implement when ready
    # username = args.username
    # password = args.password
    # resp = requests.post(f"{API_URL}/auth/login", json={"username": username, "password": password})
    # data = resp.json()
    # if "token" in data:
    #     save_token(data["token"])
    #     print("Login successful!")
    # else:
    #     print("Login failed:", data)

# for debugging purposes
def print_response(resp):
    try:
        print(resp.json())
    except Exception:
        print("Raw response:", resp.text)
        print("Status code:", resp.status_code)

def upload(args):
    file_name = args.file
    files = {'file': open(file_name, 'rb')}
    data = {}
    resp = requests.post(f"{API_URL}/files/upload", files=files, data=data)
    print_response(resp)
    
# not implemented yet in theory
def download(args):
    file_name = args.file
    resp = requests.get(f"{API_URL}/files/download/{file_name}", stream=True)
    if resp.status_code == 200:
        outname = args.output if args.output else file_name
        with open(outname, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Downloaded to {outname}")
    else:
        print("Download failed:", resp.text)  # or use print_response(resp)

# not implemented yet in theory
def list_files(args):
    params = {}
    resp = requests.get(f"{API_URL}/files/list", params=params)
    print_response(resp)

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

