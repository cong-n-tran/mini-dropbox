# Mini-Dropbox - CSE 5406-004 Project Assignment 2

A Mini Dropbox-like Distributed File Storage System that allows users to securely upload, store, and access files. The system supports multiple architectures—Layered Architecture and Microservices Architecture—demonstrating different approaches to distributed storage, metadata management, and backup.

---

## Project Architectures

### Architecture 1: Layered Architecture

- **Structure:** A traditional layered system with clear separation between client, services (API backend), metadata, storage, and backup layers.
- **How it works:**
  - The client container provides a CLI for interacting with the system (signup, login, upload, download, delete, list).
  - All operations are routed through a central service layer, which handles authentication and delegates requests to metadata and storage containers.
  - Metadata and file storage are managed in dedicated containers.
  - The backup server periodically backs up both files and metadata.
- **Running Example:**  
  - Signup, login, upload, download, delete, and list commands are executed via the client CLI and routed through the service.

### Architecture 2: Microservices Architecture

- **Structure:** Decomposes functionality into smaller, independently deployable services (upload, download, metadata, storage, backup, client).
- **How it works:**
  - The client interacts with upload/download services directly, which in turn coordinate with metadata and storage services.
  - Each service exposes its own API endpoint and runs as a distinct container.
  - Backup service runs separately to periodically archive both database and storage.
- **Running Example:**  
  - CLI commands mirror those in Architecture 1, but requests are handled by specialized upload/download services.
  - Example responses include successful signup, login, upload/download confirmations, and file listings.

---

## Capabilities

- User account management and JWT-based authentication.
- Secure file upload and download with permission checks.
- File listing, deletion, and version handling.
- Centralized metadata management (filename, size, version, user, timestamps).
- Persistent storage with periodic backup (files and metadata).
- Extensible to multiple storage nodes for sharding or redundancy (see docker-compose setup in each architecture).
- Command-line client for all major operations.

---

## Five Functional Requirements (Updated)

1. **User Authentication & Authorization**
   - Users can create accounts and log in via the CLI, receiving tokens for authenticated operations. All file operations require a valid authenticated session.
2. **File Upload & Storage Distribution**
   - Authenticated users upload files using the CLI; files are stored in a dedicated storage service/container. The architecture supports extension to multiple storage nodes.
3. **File Retrieval & Download**
   - Users can list their files and download any of them, provided they are authenticated. Downloads are performed securely, with results written to the client environment.
4. **Metadata Management & Versioning**
   - Each file operation updates centralized metadata (filename, user, version, path, and size). Users always access the latest version, with basic support for version history in metadata.
5. **Backup and Recovery**
   - The system includes a backup service/container that periodically copies both the metadata database and all stored files to a backup location, supporting recovery in case of data loss.

---

## How to Run

- See `arch1/README.md` and `arch2/README.md` for architecture-specific instructions and example usage.
- Both architectures are Dockerized for easy deployment and testing.
- Example commands:
  ```bash
  python cli.py signup username password
  python cli.py login username password
  python cli.py upload somefile.txt
  python cli.py download somefile.txt
  python cli.py delete somefile.txt
  python cli.py list
  ```

## Assumptions & Notes

- No advanced error handling; minimal for demonstration.
- Service ports and container names are specified in the respective architecture README files and docker-compose files.
- For more details, consult the [arch1/README.md](https://github.com/cong-n-tran/mini-dropbox/blob/main/arch1/README.md) and [arch2/README.md](https://github.com/cong-n-tran/mini-dropbox/blob/main/arch2/README.md).

---

_This project is for educational purposes under CSE 5406-004._