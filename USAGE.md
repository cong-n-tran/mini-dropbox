# Mini Dropbox CLI Usage

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Start the backend server:
   ```bash
   cd services
   python app.py
   ```

3. Use the CLI client (in a new terminal):
   ```bash
   cd client
   python cli.py --help
   ```

## CLI Commands

### Sign up a new user
```bash
python cli.py signup <username> <password>
```

### Login
```bash
python cli.py login <username> <password>
```

### Upload a file
```bash
python cli.py upload <file_path>
```

### List your files
```bash
python cli.py list
```

### Download a file
```bash
python cli.py download <file_id> [-o output_path]
```

## Docker Usage

To run the backend with Docker:

```bash
cd services
docker build -t mini-dropbox-backend .
docker run -p 5000:5000 -v $(pwd)/uploads:/app/uploads mini-dropbox-backend
```

## Example Usage

```bash
# Start backend
cd services && python app.py &

# Create account and upload file
cd client
python cli.py signup alice password123
python cli.py upload ~/document.pdf
python cli.py list
python cli.py download 1 -o ~/Downloads/document.pdf
```