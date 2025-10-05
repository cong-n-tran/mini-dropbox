from flask import Flask, request, jsonify

app = Flask(__name__)

# In-memory metadata store
FILES = {}

# ---------------- Add / Upload Metadata ----------------
@app.route("/files", methods=["POST"])
def add_file():
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON body required"}), 400

    filename = data.get("filename")
    if not filename:
        return jsonify({"error": "Filename is required"}), 400

    # Store metadata including password
    FILES[filename] = {
        "filename": filename,
        "path": data.get("path"),
        "size": data.get("size"),
        "version": data.get("version", 1),
        "user": data.get("user"),
        "password": data.get("password", "")
    }

    return jsonify(FILES[filename]), 201


# ---------------- Get Metadata ----------------
@app.route("/files/<filename>", methods=["GET"])
def get_file(filename):
    if filename not in FILES:
        return jsonify({"error": "File not found"}), 404
    return jsonify(FILES[filename])


# ---------------- Delete Metadata ----------------
@app.route("/files/<filename>", methods=["DELETE"])
def delete_file(filename):
    if filename not in FILES:
        return jsonify({"error": "File not found"}), 404

    del FILES[filename]
    return jsonify({"status": "deleted"}), 200


# ---------------- List All Files (Optional) ----------------
@app.route("/files", methods=["GET"])
def list_files():
    return jsonify(list(FILES.values())), 200


# ---------------- Main ----------------
if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(line_buffering=True)  # flush prints immediately
    app.run(host="0.0.0.0", port=5000, debug=True)
