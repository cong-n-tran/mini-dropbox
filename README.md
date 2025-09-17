# Mini Dropbox - Distributed File Storage System

A distributed file storage system that allows users to securely upload, store, sync, and access files across multiple devices. The system distributes files across storage nodes, manages metadata centrally, and ensures redundancy for reliability.

## Features

### ✅ Five Functional Requirements Implemented:

1. **User Authentication & Authorization**
   - User registration and login with JWT tokens
   - Device registration and management
   - Secure password hashing with bcrypt
   - Profile management

2. **File Upload & Storage Distribution**
   - File upload with validation and size limits
   - Hash-based storage distribution for deduplication
   - Support for multiple file types
   - Storage quota management

3. **File Retrieval & Download**
   - Secure file download with access control
   - File sharing with public links
   - File metadata retrieval
   - Version history access

4. **Metadata Management & Versioning**
   - Complete file metadata tracking
   - File versioning system
   - Version restoration capabilities
   - File statistics and analytics

5. **File Synchronization & Update Notification**
   - Real-time sync events using WebSocket
   - Cross-device synchronization
   - Device-specific sync tracking
   - Event-based notification system

## Technology Stack

- **Backend**: Python Flask with SQLAlchemy ORM
- **Database**: SQLite (easily upgradeable to PostgreSQL)
- **Storage**: Hash-based distributed file system
- **Authentication**: JWT tokens with bcrypt password hashing
- **Real-time**: WebSocket using Flask-SocketIO
- **Testing**: pytest with Flask test client

## Quick Start

### Prerequisites

- Python 3.8+
- pip package manager

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd mini-dropbox
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env file with your configuration
```

5. Run the application:
```bash
python run.py
```

The application will be available at `http://localhost:5000`

### Running Tests

```bash
pytest tests/
```

## API Documentation

### Authentication Endpoints

#### Register User
```http
POST /api/auth/register
Content-Type: application/json

{
  "username": "string",
  "email": "string",
  "password": "string"
}
```

#### Login
```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "string",  // or email
  "password": "string"
}
```

#### Get Profile
```http
GET /api/auth/profile
Authorization: Bearer <token>
```

#### Register Device
```http
POST /api/auth/devices
Authorization: Bearer <token>
Content-Type: application/json

{
  "device_name": "string",
  "device_type": "string",
  "device_id": "string"  // optional
}
```

### File Management Endpoints

#### Upload File
```http
POST /api/files/upload
Authorization: Bearer <token>
X-Device-ID: <device-id>  // optional
Content-Type: multipart/form-data

file: <file-data>
```

#### List Files
```http
GET /api/files/list?page=1&per_page=50&search=filename
Authorization: Bearer <token>
```

#### Get File Info
```http
GET /api/files/<file_id>
Authorization: Bearer <token>
```

#### Download File
```http
GET /api/files/<file_id>/download
Authorization: Bearer <token>
```

#### Delete File
```http
DELETE /api/files/<file_id>
Authorization: Bearer <token>
X-Device-ID: <device-id>  // optional
```

#### Share File
```http
POST /api/files/<file_id>/share
Authorization: Bearer <token>
Content-Type: application/json

{
  "expires_in_days": 7,  // optional
  "permission": "read"   // read, write, admin
}
```

#### Access Shared File
```http
GET /api/files/shared/<share_token>
```

#### Download Shared File
```http
GET /api/files/shared/<share_token>/download
```

### Synchronization Endpoints

#### Get Sync Events
```http
GET /api/sync/events?since=2023-01-01T00:00:00Z&device_id=device123&limit=100
Authorization: Bearer <token>
```

#### Mark Event as Processed
```http
PUT /api/sync/events/<event_id>/processed
Authorization: Bearer <token>
```

#### Get Sync Status
```http
GET /api/sync/status
Authorization: Bearer <token>
```

#### Sync Ping
```http
POST /api/sync/ping
Authorization: Bearer <token>
X-Device-ID: <device-id>
```

### WebSocket Events

Connect to `/socket.io` with JWT token for real-time synchronization:

#### Client Events
- `connect` - Connect to sync channel
- `join_sync_room` - Join user's sync room
- `leave_sync_room` - Leave sync room
- `request_sync` - Request sync events

#### Server Events
- `connected` - Connection confirmation
- `file_uploaded` - File upload notification
- `file_deleted` - File deletion notification
- `sync_event` - General sync event
- `sync_events` - Batch sync events

## Architecture

### Storage Distribution

Files are stored using a hash-based distribution system:
- SHA256 hash calculated for each file
- First 4 characters create directory structure (aa/bb/)
- Deduplication based on file hash
- Unique filename generation to avoid collisions

### Database Schema

- **users**: User accounts and storage quotas
- **devices**: User devices for sync tracking
- **files**: File metadata and current versions
- **file_versions**: Historical file versions
- **file_shares**: File sharing configurations
- **sync_events**: Synchronization event log

### Security Features

- JWT-based authentication
- bcrypt password hashing
- File access control and validation
- Storage quota enforcement
- CORS protection
- File type restrictions

## Configuration

Key environment variables:

- `SECRET_KEY`: Flask secret key
- `JWT_SECRET_KEY`: JWT signing key
- `DATABASE_URL`: Database connection string
- `STORAGE_PATH`: File storage directory
- `MAX_FILE_SIZE`: Maximum file size (bytes)
- `ALLOWED_EXTENSIONS`: Comma-separated file extensions

## Deployment

### Production Deployment

1. Set environment variables for production
2. Use PostgreSQL instead of SQLite:
   ```
   DATABASE_URL=postgresql://user:pass@localhost/mini_dropbox
   ```

3. Use gunicorn for production server:
   ```bash
   gunicorn -w 4 -b 0.0.0.0:5000 run:app
   ```

4. Set up reverse proxy (nginx) for static files and SSL
5. Configure backup strategy for database and storage

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "run:app"]
```

## License

This project is created for CSE 5406-004 Project Assignment 2.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request
=======
# mini-dropbox - cse 5406-004 project assignment 2

A Mini Dropbox-like Distributed File Storage System that allows users to securely upload, store, sync, and access files across multiple devices. The system will distribute files across storage nodes, manage metadata centrally, and ensure redundancy for reliability.

### Five Functional Requirements

#### User Authentication & Authorization
- Users can create accounts, log in, and receive session tokens.
- Only authenticated users can upload, download, or manage files.

#### File Upload & Storage Distribution
- Files are uploaded via a client API and split or assigned to storage nodes.
- Support for multiple storage nodes for redundancy or sharding.

#### File Retrieval & Download
- Users can browse their files and download them from distributed storage nodes.

#### Metadata Management & Versioning
- System keeps track of filenames, paths, versions, sizes, and modification timestamps.
- Users can access the latest version or rollback to a previous version.

#### File Synchronization & Update Notification
- Detect changes in files and notify clients when a file has been updated.
- Basic sync mechanism to keep client files up to date.
