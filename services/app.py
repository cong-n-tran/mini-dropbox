import os
import sqlite3
import jwt
import datetime
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# --- Configuration ---
SECRET_KEY = os.environ.get("SECRET_KEY", "supersecretkey")
UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "../storage/files")
DATABASE = os.environ.get("DATABASE", "../metadata/metadata.db")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- JWT Helpers ---
def encode_token(user_id):
    payload = {
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=1),
        "iat": datetime.datetime.utcnow(),
        "sub": user_id
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def decode_token(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload["sub"]
    except Exception:
        return None

# --- DB Helpers ---
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            upload_time TEXT NOT NULL,
            FOREIGN KEY(owner_id) REFERENCES users(id)
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# --- Routes ---
@app.route("/auth/signup", methods=["POST"])
def signup():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return jsonify({"error": "Missing username or password"}), 400
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                  (username, generate_password_hash(password)))
        conn.commit()
        return jsonify({"message": "Signup successful!"})
    except sqlite3.IntegrityError:
        return jsonify({"error": "Username already exists"}), 409

@app.route("/auth/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    user = c.fetchone()
    if user and check_password_hash(user["password"], password):
        token = encode_token(user["id"])
        return jsonify({"token": token})
    else:
        return jsonify({"error": "Invalid credentials"}), 401

def require_auth(f):
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid token"}), 401
        token = auth_header.split(" ", 1)[1]
        user_id = decode_token(token)
        if not user_id:
            return jsonify({"error": "Invalid or expired token"}), 401
        request.user_id = user_id
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

@app.route("/files/upload", methods=["POST"])
@require_auth
def upload():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files["file"]
    filename = file.filename
    save_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(save_path)
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO files (owner_id, filename, upload_time) VALUES (?, ?, ?)",
              (request.user_id, filename, datetime.datetime.utcnow().isoformat()))
    conn.commit()
    return jsonify({"message": f"File '{filename}' uploaded!"})

@app.route("/files/download/<filename>", methods=["GET"])
@require_auth
def download(filename):
    # Check ownership
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM files WHERE owner_id=? AND filename=?", (request.user_id, filename))
    file_row = c.fetchone()
    if not file_row:
        return jsonify({"error": "File not found"}), 404
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)

@app.route("/files/list", methods=["GET"])
@require_auth
def list_files():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT filename, upload_time FROM files WHERE owner_id=?", (request.user_id,))
    files = [{"filename": row["filename"], "upload_time": row["upload_time"]} for row in c.fetchall()]
    return jsonify(files)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)