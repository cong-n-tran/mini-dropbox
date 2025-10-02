import os
import jwt
import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, request, jsonify, Response
import requests, os

app = Flask(__name__)

# URLs for other services (use Docker Compose service names)
STORAGE_API = "http://storage:5002"
METADATA_API = "http://metadata:5001/files"


# # --- Configuration ---
# SECRET_KEY = os.environ.get("SECRET_KEY", "supersecretkey")
# UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "../storage/files")
# DATABASE = os.environ.get("DATABASE", "../metadata/metadata.db")
# os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# URLs for other services (use Docker Compose service names)
# STORAGE_API = "http://storage:5002"
# METADATA_API = "http://metadata:5001/files"

# --- JWT Helpers ---
# def encode_token(user_id):
#     payload = {
#         "exp": datetime.datetime.utcnow() + datetime.timedelta(days=1),
#         "iat": datetime.datetime.utcnow(),
#         "sub": user_id
#     }
#     return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

# def decode_token(token):
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
#         return payload["sub"]
#     except Exception:
#         return None


# # --- Routes ---
# @app.route("/auth/signup", methods=["POST"])
# def signup():
#     data = request.json
#     username = data.get("username")
#     password = data.get("password")
#     if not username or not password:
#         return jsonify({"error": "Missing username or password"}), 400
#     conn = get_db()
#     c = conn.cursor()
#     try:
#         c.execute("INSERT INTO users (username, password) VALUES (?, ?)",
#                   (username, generate_password_hash(password)))
#         conn.commit()
#         return jsonify({"message": "Signup successful!"})
#     except sqlite3.IntegrityError:
#         return jsonify({"error": "Username already exists"}), 409

# @app.route("/auth/login", methods=["POST"])
# def login():
#     data = request.json
#     username = data.get("username")
#     password = data.get("password")
#     conn = get_db()
#     c = conn.cursor()
#     c.execute("SELECT * FROM users WHERE username=?", (username,))
#     user = c.fetchone()
#     if user and check_password_hash(user["password"], password):
#         token = encode_token(user["id"])
#         return jsonify({"token": token})
#     else:
#         return jsonify({"error": "Invalid credentials"}), 401

# def require_auth(f):
#     def wrapper(*args, **kwargs):
#         auth_header = request.headers.get("Authorization")
#         if not auth_header or not auth_header.startswith("Bearer "):
#             return jsonify({"error": "Missing or invalid token"}), 401
#         token = auth_header.split(" ", 1)[1]
#         user_id = decode_token(token)
#         if not user_id:
#             return jsonify({"error": "Invalid or expired token"}), 401
#         request.user_id = user_id
#         return f(*args, **kwargs)
#     wrapper.__name__ = f.__name__
#     return wrapper


def require_auth(f):
    # ... your auth decorator as before ...
    pass

@app.route("/files/upload", methods=["POST"])
# @require_auth
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

# not implemented yet in theory
@app.route("/files/download/<filename>", methods=["GET"])
# @require_auth
def download(filename):
    # Forward request to storage service
    resp = requests.get(f"{STORAGE_API}/download/{filename}", stream=True)
    if resp.status_code == 200:
        # Stream file response directly
        return Response(resp.iter_content(chunk_size=8192), content_type=resp.headers.get('Content-Type'), headers={"Content-Disposition": f"attachment; filename={filename}"})
    else:
        return jsonify({"error": "File not found"}), 404

# not implemented yet in theory
@app.route("/files/list", methods=["GET"])
# @require_auth
def list_files():
    # Get user's file list from metadata service
    user = request.form.get("user", "unknown")
    params = {"user": user}
    resp = requests.get(f"{METADATA_API}", params=params)
    if resp.status_code == 200:
        return resp.json()
    else:
        return jsonify({"error": "Metadata error"}), 500

# not implemented yet in theory
@app.route("/files/delete/<filename>", methods=["DELETE"])
# @require_auth
def delete_file(filename):
    # Forward delete request to storage service (which will also notify metadata)
    resp = requests.delete(f"{STORAGE_API}/delete/{filename}")
    return resp.json(), resp.status_code

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)