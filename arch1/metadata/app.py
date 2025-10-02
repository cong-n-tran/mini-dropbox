from flask import Flask, request, jsonify
import sqlite3, os, time

app = Flask(__name__)
DB_PATH = "/data/metadata.db"
os.makedirs("/data", exist_ok=True)

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT,
                    path TEXT,
                    size INTEGER,
                    version INTEGER,
                    timestamp TEXT,
                    user TEXT
                )''')
    conn.commit()
    conn.close()

@app.route("/files", methods=["POST"])
def add_file():
    data = request.json
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO files (filename, path, size, version, timestamp, user) VALUES (?,?,?,?,?,?)",
              (data["filename"], data["path"], data["size"], data.get("version",1), time.ctime(), data.get("user","unknown")))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"}), 201

@app.route("/files", methods=["GET"])
def list_files():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM files")
    rows = c.fetchall()
    conn.close()
    return jsonify(rows)

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5001)


@app.route("/files/<filename>", methods=["DELETE"])
def delete_file_metadata(filename):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM files WHERE filename = ?", (filename,))
    conn.commit()
    conn.close()
    return jsonify({"status": "metadata deleted"}), 200
