# Architecture 1 - Layered Architecture

This architecture implements a classic layered design with clear separation between client, service/API backend, metadata, storage, and backup layers. It is part of the Mini-Dropbox project and demonstrates end-to-end file storage, retrieval, and management using a monolithic service API.

## Overview

- **Client Layer:** Provides a CLI interface for user operations: signup, login, upload, download, delete, list.
- **Service Layer:** Handles authentication/authorization, and routes requests to storage and metadata layers.
- **Metadata Layer:** Stores file metadata (filename, size, version, user, timestamps) in a dedicated container.
- **Storage Layer:** Manages file I/O (save, fetch, delete) using a mounted volume/directory.
- **Backup Layer:** Periodically creates backups of metadata and stored files.

## Capabilities

- Secure user authentication and JWT-based authorization.
- Upload/download for any file type, with permissions enforced per user.
- File listing and deletion.
- Centralized metadata management for all files.
- Versioning: metadata tracks file versions and changes.
- Persistent storage and periodic backup to guard against data loss.
- Extensible to multiple storage nodes.

## How to Run

1. Start containers:  
   ```
   docker-compose up
   ```
2. Enter the client server:  
   ```
   docker-compose run client /bin/bash
   ```
3. Use the CLI to run commands:  
   ```
   python cli.py signup username password
   python cli.py login username password
   python cli.py upload somefile.txt
   python cli.py download somefile.txt
   python cli.py delete somefile.txt
   python cli.py list
   ```
4. (Optional) Inspect stored files:  
   ```
   docker exec -it arch1-storage-1 sh
   ls /storage
   ```

## Assumptions & Notes

- Minimal error handling; focus is on architectural demonstration.
- Service ports: 5000 (service), 5001 (metadata), 5002 (storage).
- For details on backup and container structure, refer to the project root and backup documentation.
- For overall project context, see the main [README](../README.md).

---

_This architecture is part of the Mini-Dropbox CSE 5406-004 project._