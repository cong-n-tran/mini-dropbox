# Mini-Dropbox - CSE 5406-004 Project Assignment 2

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

# Implementation Tasks

### 1. Client Container
Python CLI: Use argparse or click for a command-line interface, or tkinter for a simple GUI.
#### Responsibilities:
- Accept user input (login, upload, download, list files).
 -Send HTTP requests to the Services API.
- Display results and notifications.
### 2. Services Container (API Backend)
Python Web Framework: Use Flask or FastAPI.
#### Responsibilities:
- Expose REST API endpoints for all operations (auth, upload, download, sync, metadata).
- Handle authentication (JWT/session management).
- Call Metadata and Storage containers.
- Trigger sync notifications.
### 3. Metadata Container
Python + SQLite: Use sqlite3 (bundled with Python) for simplicity.
#### Responsibilities:
- Store file metadata (filename, path, size, versions, timestamps, user info).
- CRUD operations exposed via a simple Python API (can be REST or just direct DB access from Services).
### 4. Storage Container
Python File I/O: Save files directly to a mounted volume/directory.
#### Responsibilities:
- Save uploaded files.
- Retrieve files for download.
- Delete files if needed.
### 5. Backup Server Container
Python Script: Use shutil for copying files and sqlite3 for dumping metadata.
#### Responsibilities:
- Periodically back up file storage and metadata DB.
- Can be run as a cron job or a long-running Python service with scheduling.



# To get it working:
as of October 2nd, 2025

### 1. run the client server and enter in via bash
`docker-compose run client /bin/bash`

### 2. run the cli.py and run these commands
`python cli.py upload somefile.txt`
`python cli.py signup username password`
`python cli.py login username password`
`python cli.py upload somefile.txt`
`python cli.py download somefile.txt`
`python cli.py delete somefile.txt`
`python cli.py list`

some responses you should see
- signup: `{'message': 'Signup successful!'}`
- login:  `Login successful!`
- upload: `{'path': '/storage/somefile.txt', 'status': 'saved'}`
- download: `Downloaded to somefile.txt`
- delete: `Deletion successful` 
- list: `[{'filename': 'somefile.txt', 'password': '', 'path': '/storage/somefile.txt', 'size': 6, 'user': None, 'version': 1}]` or `[]`

### (optional) 3. open another terminal and enter the storage container
`docker exec -it arch1-storage-1 sh `

list the storage folder `ls /storage`

and you should see the `somefile.txt` there. 


### some assumptions
- no real error handling were made when creating this project. we just hope everything worked as intented lol. 
- current it is: (i updated it in the storage and metadata code already)
    - service - 5000
    - metadata - 5001
    - storage - 5002