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
