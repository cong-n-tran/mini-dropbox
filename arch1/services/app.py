import os
import jwt
import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, request, jsonify, Response
import requests, os

app = Flask(__name__)

# URLs for other services (use Docker Compose service names)
STORAGE_API = "http://storage:5002"
METADATA_API = "http://metadata:5001"
SECRET_KEY = os.environ.get("SECRET_KEY", "supersecretkey")


# --- JWT Helpers ---
def encode_token(username):
    now = datetime.datetime.now(datetime.timezone.utc)
    payload = {
        "exp": now + datetime.timedelta(days=1),
        "iat": now,
        "sub": username
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def decode_token(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload["sub"]
    except Exception:
        return None


# # --- Routes ---
@app.route("/auth/signup", methods=["POST"])
def signup():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return jsonify({"error": "Missing username or password"}), 400
    # Hash password before sending to metadata service
    hashed_password = generate_password_hash(password)
    try:
        resp = requests.post(f"{METADATA_API}/users", json={
            "username": username,
            "password": hashed_password
        })
        if resp.status_code == 201:
            return jsonify({"message": "Signup successful!"}), 201
        elif resp.status_code == 409:
            return jsonify({"error": "Username already exists"}), 409
        else:
            return jsonify({"error": "Metadata service error"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/auth/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return jsonify({"error": "Missing username or password"}), 400

    try:
        resp = requests.get(f"{METADATA_API}/users/{username}")
        if resp.status_code != 200:
            return jsonify({"error": "Invalid credentials"}), 401
        user = resp.json()
        stored_hash = user.get("password")
        if stored_hash and check_password_hash(stored_hash, password):
            token = encode_token(username)
            return jsonify({"token": token})
        else:
            return jsonify({"error": "Invalid credentials"}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def require_auth(f):
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid token"}), 401
        token = auth_header.split(" ", 1)[1]
        username = decode_token(token)
        if not username:
            return jsonify({"error": "Invalid or expired token"}), 401
        request.username = username
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper


@app.route("/files/upload", methods=["POST"])
@require_auth
def upload():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]
    # user = request.user_id  # from your auth decorator
    user = request.form.get("user", "unknown")

    # Forward file and user info to storage service
    files = {'file': (file.filename, file.stream, file.mimetype)}
    data = {'user': user}
    resp = requests.post(f"{STORAGE_API}/upload", files=files, data=data)
    if resp.status_code != 200:
        return jsonify({"error": "Storage error"}), 500

    # Storage service notifies metadata itself, so you don't need to do it here
    try:
        return resp.json(), resp.status_code
    except Exception:
        return jsonify({"error": "Non-JSON response from storage", "raw": resp.text}), resp.status_code

@app.route("/files/download", methods=["GET"])
@require_auth
def download():
    # Get filename from query parameters
    filename = request.args.get("filename")
    if not filename:
        return jsonify({"error": "No filename provided"}), 400

    # Forward request to storage service as a GET with query param
    storage_url = f"{STORAGE_API}/download"
    params = {"filename": filename}
    resp = requests.get(storage_url, params=params, stream=True)
    if resp.status_code == 200:
        return Response(
            resp.iter_content(chunk_size=8192),
            content_type=resp.headers.get('Content-Type'),
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    else:
        try:
            return jsonify(resp.json()), resp.status_code
        except Exception:
            return jsonify({"error": "File not found"}), 404

# not implemented yet in theory
@app.route("/files", methods=["GET"])
@require_auth
def list_files():
    # Get user's file list from metadata service
    user = request.form.get("user", "unknown")
    params = {"user": user}
    resp = requests.get(f"{METADATA_API}/files", params=params)
    if resp.status_code == 200:
        return resp.json()
    else:
        return jsonify({"error": "Metadata error"}), 500

#
@app.route("/files/delete", methods=["DELETE"])
@require_auth
def delete_file():
    filename = request.args.get("filename")
    if not filename:
        return jsonify({"error": "No filename provided"}), 400
    
    params = {"filename": filename}
    # Forward delete request to storage service (which will also notify metadata)
    resp = requests.delete(f"{STORAGE_API}/delete", params=params)
    return resp.json(), resp.status_code

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)