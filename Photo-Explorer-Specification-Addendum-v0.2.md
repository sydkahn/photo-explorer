---
date: 2026-10-15
status: Proposed changes for review
tags:
- Photo Explorer
- Specification
- Portable Windows
- Proxmox
title: Photo Explorer Specification Addendum --- Dual Edition
  Architecture
version: 0.2
---

# Photo Explorer --- Specification Addendum

**Version:** 0.2\
**Date:** October 15, 2026\
**Purpose:** Extend the original `SPECIFICATION.md` to define two
editions: a Proxmox-hosted web application and a portable Windows
desktop application.

This document supplements the original specification. Incorporate these
changes into the main specification before implementation begins.

## 1. Revised Project Overview

Photo Explorer shall provide two ways to use a shared photo-catalog and
image-processing core:

1.  **Server Edition:** Runs on the Proxmox home server and is accessed
    through a web browser by computers on the home network.
2.  **Portable Windows Edition:** Runs locally on Windows and catalogs
    user-selected photographs available to that computer. It shall be
    distributed as a self-contained portable package that does not
    require the user to install Python or separate application
    libraries.

Both editions shall support the same core capabilities where practical:
photo discovery, metadata extraction, thumbnail generation, exact
duplicate detection, perceptual similarity, face detection, face
embeddings, face grouping, and manual correction of person assignments.

The editions shall use separate databases by default. The Windows
edition must operate without the Proxmox server or a network connection.

## 2. Revised Architecture

The application shall be separated into three layers.

### 2.1 Shared Core

The shared Python core shall contain platform-independent logic for
photo discovery and cataloging, metadata extraction, thumbnail
generation, cryptographic file hashing, perceptual image hashing, face
detection and embedding generation, face grouping, people and
face-assignment management, database operations, and incremental
scanning.

The core shall not depend on a specific user interface.
Platform-specific file access and application-path handling shall be
isolated behind appropriate interfaces.

### 2.2 Server Edition

The Server Edition shall run on the Proxmox host environment, preferably
in a dedicated Debian 13 LXC container if storage access and security
requirements permit.

Proposed components: - Python runtime installed in the server
environment. - FastAPI backend. - Browser-based interface. - SQLite
database for the initial release. - Background processing worker. -
Local face-recognition models. - Persistent application data and logs.

The server shall make the interface available to authorized clients on
the home LAN. It shall not require cloud-based image processing.

### 2.3 Portable Windows Edition

The Portable Windows Edition shall provide a desktop interface and run
locally on a Windows computer.

Proposed components: - Shared Photo Explorer Core. - Desktop user
interface, with PySide6 as the leading candidate. - Bundled Python
runtime and required application libraries. - Bundled face-recognition
model files. - Local SQLite database. - Local configuration, logs,
thumbnails, and processing cache.

The leading packaging candidate is PyInstaller. The preferred initial
distribution is a ZIP containing an executable and any required bundled
resources. A single-file executable is optional and is not required if a
portable directory is more reliable.

The Windows edition shall not require a separately installed Python
interpreter, OpenCV, or other Python libraries.

The Windows edition shall not require a connection to the Proxmox
server, Ollama, OpenCode, or the internet for normal local cataloging
and face-recognition functions.

### 2.4 Shared Logic, Separate Interfaces

The two editions shall share the core processing code but shall not
share a live database by default.

-   The Server Edition shall maintain its own catalog.
-   The Portable Windows Edition shall maintain its own catalog.
-   A future catalog export/import or synchronization feature may be
    considered separately.
-   Synchronization is outside the initial release scope.

The Smart TV interface, if developed, shall connect to the Server
Edition rather than the Portable Windows Edition.

## 3. Portable Windows Requirements

### 3.1 Portable Distribution

The Windows edition shall be distributed as a self-contained portable
package.

The normal user workflow shall be: 1. Download the ZIP package. 2.
Extract it to a writable directory chosen by the user. 3. Run
`PhotoExplorer.exe`. 4. Select one or more photo directories. 5. Begin
cataloging.

No installation wizard shall be required.

Normal operation shall not require administrator privileges, registry
changes, a system-wide Python installation, or separately installed
application libraries.

Windows permissions still apply. The application must report a clear
error if its chosen directory is not writable.

### 3.2 Application-Relative Data

By default, all application-managed writable data shall be stored within
the Photo Explorer application directory.

The data includes: - SQLite catalog database. - Configuration. - Log
files. - Generated thumbnails. - Face embeddings and related cache
data. - Background-job state and other recoverable application state.

A proposed directory layout is:

``` text
PhotoExplorer/
├── PhotoExplorer.exe
├── models/
│   ├── face_detection.onnx
│   └── face_recognition.onnx
├── data/
│   ├── catalog.db
│   ├── thumbnails/
│   └── face-cache/
├── logs/
├── config/
│   └── settings.json
└── README.txt
```

The actual packaged layout may differ, provided the behavior remains
equivalent. Bundled read-only resources may be stored inside the
executable or in a separate resources directory. Writable data must not
be written into a temporary extraction directory used by the packaging
system.

The application shall determine its location from the executable path
when packaged, not from the process's current working directory.

The application shall not silently place its primary database or logs in
`%APPDATA%`, `%LOCALAPPDATA%`, the Windows registry, or another location
outside its directory. If the user chooses to configure an alternate
data directory in a future version, the choice must be explicit.

### 3.3 Relocation

The complete portable application directory shall be movable to another
writable directory or drive.

After relocation, the application shall use the database, configuration,
logs, and caches within the relocated directory.

The application shall detect missing source-photo paths and provide a
way to reconnect or rescan the relevant source directory.

The application directory can move independently of the photo archive.
Moving the application does not move original photographs.

### 3.4 Deletion and Original-File Safety

Deleting the Photo Explorer application directory may remove the
application's database, logs, configuration, thumbnails, and derived
face data stored inside it.

It must not delete, move, rename, or modify original photographs stored
outside the application directory.

The application shall clearly explain that deleting the portable
directory also deletes the local catalog unless it has been backed up.

### 3.5 Offline Operation

After the portable package and its required models have been obtained,
the Windows edition shall perform local cataloging, face detection, face
recognition, grouping, and browsing without an internet connection.

No photographs, face embeddings, or catalog data shall be transmitted to
external services as part of normal operation.

### 3.6 Local Source Selection

The Windows edition shall process only directories explicitly selected
by the user. It shall not automatically scan the entire computer.

Source directories should be read-only from the application's
perspective in the initial release. The application shall not modify
originals.

The interface shall indicate when a source directory or drive is
unavailable.

## 4. Packaging and Model Requirements

### 4.1 Bundled Dependencies

The Windows release shall include the Python runtime and all required
application libraries. Users shall not need to install Python packages
separately.

Packaging must be tested on a clean or representative Windows
environment that does not have the development environment installed.

### 4.2 AI Models

The selected face-detection and face-recognition model files shall be
included in the portable distribution, unless a later, explicitly
documented distribution option is approved.

Model licensing must permit the intended redistribution and use. License
notices shall be included where required.

The application shall report a clear error if a required model is
missing or cannot be loaded.

### 4.3 Model Versioning

The application shall record which model version produced face
detections and embeddings.

A model upgrade may require some or all embeddings to be regenerated.
The application shall not silently treat embeddings produced by
incompatible models as interchangeable.

### 4.4 Packaging Tool

PyInstaller shall be evaluated as the initial packaging tool. Other
packaging methods may be considered if they provide more reliable
portability or easier maintenance.

The first goal is a reliable portable directory package, not necessarily
a single-file executable.

## 5. Data and Database Requirements

SQLite remains the proposed database for the first release of both
editions.

Each edition shall have its own database file by default. The database
schema and core data-access logic should be shared where practical.

Database records may contain absolute paths to original photographs. The
application must therefore handle unavailable or relocated source
directories without assuming the photographs were deleted.

The data-access layer should remain sufficiently isolated to allow a
future migration to PostgreSQL if measured concurrency or scale
requirements justify it. PostgreSQL is not required for the initial
release.

Catalog synchronization between the Windows and Server editions is
explicitly outside the initial release scope.

## 6. Revised Development Plan

Development shall proceed in the following order.

### Phase 1 --- Prototype the Shared Core

-   Select and verify compact face models.
-   Process a representative test set of approximately 200--500
    photographs.
-   Produce face contact sheets and suggested groups.
-   Measure recognition quality, CPU time, and memory consumption.
-   Verify that originals remain unchanged.

### Phase 2 --- Catalog and Database

-   Implement SQLite storage.
-   Add metadata extraction, hashes, thumbnails, and face records.
-   Implement incremental scanning and recovery from interrupted jobs.
-   Keep source directories read-only.

### Phase 3 --- Portable Windows Edition

-   Build the desktop interface.
-   Implement application-relative writable paths.
-   Package the runtime, dependencies, and models.
-   Create a ZIP distribution.
-   Test relocation, offline operation, and local data storage.

### Phase 4 --- Proxmox Server Edition

-   Add FastAPI and the browser interface around the shared core.
-   Deploy to a dedicated Debian environment on Proxmox.
-   Configure persistent storage and safe access to photo directories.
-   Test access from Linux Mint and Windows browsers.

### Phase 5 --- Feature Parity and Hardening

-   Ensure both editions support core cataloging, face grouping,
    corrections, and duplicate detection.
-   Test backup and recovery.
-   Test resource usage and error handling.
-   Document differences between the editions.

### Phase 6 --- Smart TV Interface

-   Identify the television platform and test its browser capabilities.
-   Add a remote-friendly interface to the Server Edition or develop a
    dedicated TV client if needed.
-   Do not require the TV to run face-recognition models.

## 7. Portable Edition Acceptance Tests

The Portable Windows Edition shall not be considered ready for release
until the following tests pass.

1.  **No separate Python installation:** The application starts on a
    Windows system without a separately installed Python runtime or
    application-specific Python libraries.
2.  **No installation required:** The application can be extracted to a
    writable directory and launched.
3.  **Relocation:** The application directory can be moved to another
    writable location and continue using its local catalog.
4.  **Application-relative data:** Database, configuration, logs,
    thumbnails, and face cache are stored within the application
    directory by default.
5.  **Offline use:** Face detection, recognition, grouping, and local
    browsing work without network access.
6.  **Independent operation:** The application works when the Proxmox
    server is unavailable.
7.  **Original protection:** Cataloging and recognition do not modify,
    move, rename, or delete source photographs.
8.  **Interrupted processing:** An interrupted scan can be resumed or
    safely retried.
9.  **Missing drive handling:** Unavailable source directories are
    reported without deleting catalog records.
10. **Clean-machine test:** The packaged application is tested outside
    the developer's Python environment.
11. **Model licensing:** The distributed model files and notices comply
    with their licenses.
12. **No unexpected external calls:** Normal local operation does not
    transmit photos, embeddings, or catalog data to external services.

## 8. Revised Definition of Success

The project will have achieved its initial dual-edition goal when:

-   The shared core catalogs photographs and performs local face
    recognition.
-   The Portable Windows Edition runs from a user-selected directory
    without separate Python or library installation.
-   The Windows edition stores its application-managed data within its
    directory by default.
-   The Windows edition works offline and independently of the server.
-   The Server Edition provides browser access from computers on the
    home network.
-   Both editions preserve original photographs and support human
    correction of face groups.
-   The database can be backed up and restored.
-   The two editions use compatible core logic and model versions.
-   A future Smart TV interface can use the Server Edition without
    duplicating the recognition engine.

## Implementation Note

These changes define the intended architecture, not a claim that the
application or packaging has already been tested. Before implementation,
confirm the available Proxmox resources, choose representative
photographs, verify model licensing, and prove the shared
face-recognition core works.

The first coding task should remain the small face-recognition
prototype. The portable packaging and web interface should be built only
after the core processing behavior has been demonstrated.
