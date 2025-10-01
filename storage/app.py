from flask import Flask, request, send_file
import os, requests

app = Flask(__name__)
STORAGE_PATH = "/storage"
os.makedirs(STORAGE_PATH, exist_ok=True)

# Metadata API URL (use service name from docker-compose)
METADATA_API = "http://metadata:5000/files"

@app.route("/upload", methods=["POST"])
def upload_file():
    f = request.files["file"]
    save_path = os.path.join(STORAGE_PATH, f.filename)
    f.save(save_path)

    # Gather metadata info
    size = os.path.getsize(save_path)
    metadata = {
        "filename": f.filename,
        "path": save_path,
        "size": size,
        "version": 1,
        "user": request.form.get("user", "unknown")
    }

    # Notify metadata container
    try:
        r = requests.post(METADATA_API, json=metadata)
        r.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"[!] Failed to update metadata: {e}")

    return {"status": "saved", "path": save_path}

@app.route("/download/<filename>", methods=["GET"])
def download_file(filename):
    return send_file(os.path.join(STORAGE_PATH, filename), as_attachment=True)

@app.route("/delete/<filename>", methods=["DELETE"])
def delete_file(filename):
    path = os.path.join(STORAGE_PATH, filename)
    if os.path.exists(path):
        os.remove(path)

        # Remove metadata entry
        try:
            r = requests.delete(f"{METADATA_API}/{filename}")
            r.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"[!] Failed to delete metadata: {e}")

        return {"status": "deleted"}
    return {"status": "not found"}, 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
