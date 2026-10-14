# Photo Explorer

## Software Requirements Specification (SRS)

**Version:** 0.1 — Draft for Review
**Date:** October 14, 2026
**Status:** Proposed; not yet approved for implementation
**Development approach:** OpenCode-assisted, incremental development
**Primary language:** Python

---

# 1. Project Overview

## 1.1 Purpose

Photo Explorer is a self-hosted photo cataloging and browsing application designed to organize, explore, and discover photographs accumulated over many years and stored across multiple hard drives.

Its primary distinguishing feature is locally executed face recognition, which identifies faces in photographs and groups visually similar faces so that the user can associate them with named individuals.

The application will provide a unified photo library accessible through a web browser from computers on the home network, with the possibility of a dedicated Smart TV interface.

The system will run on an existing Proxmox home server. Photographs will remain in their original locations unless the user explicitly authorizes a future file-management operation.

The application will not depend on cloud-based image recognition services.

## 1.2 Primary Objectives

The system shall:

1. Catalog photographs across multiple directories and drives.
2. Detect faces in photographs using compact, locally executed AI models.
3. Group similar faces for human review and identification.
4. Allow the user to assign names to people and correct incorrect groupings.
5. Provide thumbnail browsing, searching, and chronological navigation.
6. Identify exact duplicate files and suggest visually similar photographs.
7. Preserve the original photographs without modifying them.
8. Maintain a persistent database so photographs do not need to be processed repeatedly.
9. Provide browser-based access from Linux Mint, Windows, and other compatible devices.
10. Support a future television-oriented interface for browsing and displaying family photographs.

## 1.3 Design Philosophy

The project will follow five principles.

**Local first:** Photographs, face embeddings, and catalog data remain on the user's infrastructure.

**Non-destructive:** The application must not modify, move, rename, or delete original photographs without explicit authorization.

**Incremental:** Development will proceed in small, testable stages.

**Resource-conscious:** Prefer compact models and CPU execution before introducing GPU dependencies or larger models.

**Human-supervised:** AI-generated face groupings are suggestions, not unquestionable identifications.

---

# 2. Intended Environment

## 2.1 Server

The application will run on the existing Proxmox server.

The proposed deployment environment is a Debian 13 LXC container, subject to verification of storage access, security, and resource availability.

An appropriately isolated virtual machine is an alternative if container restrictions complicate deployment.

Initial resource allocation targets are:

| Resource         | Initial target    |
| ---------------- | ----------------- |
| Virtual CPUs     | 2–4               |
| RAM              | 2–4 GB            |
| Virtual disk     | 16–32 GB          |
| GPU              | Not required      |
| Network          | Existing home LAN |
| Operating system | Debian 13         |

These figures are preliminary planning estimates. Actual requirements will be determined through testing.

The virtual disk must not be treated as the intended storage location for the entire photo archive. Original photographs will remain on existing storage devices.

The database, application code, model files, and thumbnail cache will reside in designated application storage.

## 2.2 Development Environment

OpenCode will be used to assist with application development, testing, and maintenance.

The preferred initial workflow is:

* Develop and test using the existing Linux Mint development environment.
* Use OpenCode to implement small, explicitly defined tasks.
* Store source code in a version-controlled Git repository.
* Deploy tested versions to Proxmox.
* Run the deployed application independently of OpenCode.

The existing local Ollama setup may provide coding assistance through OpenCode, subject to verification of model availability, connectivity, and compatibility.

The finished application must not depend on Ollama or OpenCode to operate.

## 2.3 Client Devices

The initial supported clients will be:

* Linux Mint computers.
* Windows 11 computers.
* Other devices with a compatible modern web browser.

Smart TV compatibility will be investigated separately because browser capabilities and remote-control behavior differ between manufacturers and operating systems.

---

# 3. Proposed Technology Stack

The following technologies are proposed for the initial implementation.

| Function                  | Proposed technology                                      |
| ------------------------- | -------------------------------------------------------- |
| Programming language      | Python                                                   |
| Web backend               | FastAPI                                                  |
| Web interface             | HTML, CSS, JavaScript                                    |
| Face detection            | OpenCV YuNet                                             |
| Face recognition          | OpenCV SFace                                             |
| Image processing          | Pillow and OpenCV                                        |
| Face clustering           | scikit-learn or an equivalent lightweight implementation |
| Database                  | SQLite                                                   |
| Image metadata            | ExifTool                                                 |
| Exact duplicate detection | Cryptographic file hashes                                |
| Visual similarity         | Perceptual image hashes                                  |
| Background processing     | Separate Python worker                                   |
| Version control           | Git                                                      |
| Development assistant     | OpenCode                                                 |
| Deployment                | Proxmox-hosted Debian environment                        |

This stack is provisional.

Before implementation, the selected face models must be checked for availability, licensing, compatibility, and acceptable recognition accuracy.

If YuNet and SFace do not perform adequately on older photographs, alternative compact models may be evaluated.

No model change should require redesigning the entire application.

---

# 4. Functional Requirements

## 4.1 Photo Discovery and Cataloging

The application shall discover photographs within administrator-configured directories.

Supported formats should initially include:

* JPEG and JPG.
* PNG.
* WebP.
* TIFF.
* BMP.

Additional formats, including HEIC and RAW camera formats, may be added after the initial implementation.

The application shall:

1. Recursively discover supported image files.
2. Record each photograph's storage location.
3. Extract available image metadata.
4. Record image dimensions.
5. Calculate a cryptographic hash for exact duplicate detection.
6. Generate and cache a thumbnail.
7. Record processing status.
8. Avoid processing unchanged photographs repeatedly.

The initial implementation will use read-only access to the source directories.

Unsupported, corrupted, or unreadable files shall be recorded as errors without stopping the entire scan.

The user shall be able to initiate a scan manually.

Scheduled or automatic incremental scans may be introduced in a later release.

## 4.2 Multiple Drives

The catalog shall support photographs distributed across multiple directories and storage devices.

Each photograph shall have a persistent database identifier independent of its current path.

The application shall associate each photograph with its source location.

If a drive becomes unavailable, the catalog shall retain its records while indicating that the original photograph cannot currently be accessed.

When the drive returns, the application shall be able to reconcile its records with the available files.

File hashes may help identify files that have moved, although identical files and modified copies must be handled separately.

The application shall not assume that every unavailable file has been deleted.

## 4.3 Face Detection

The application shall analyze photographs and identify visible human faces.

For each detected face, it shall record:

* The photograph containing the face.
* The face's bounding coordinates.
* The generated face embedding, when successfully calculated.
* Processing and quality information.
* The assigned person or unassigned status.

The application should avoid creating misleading person groups from faces that are too small, blurred, obscured, or otherwise unsuitable for reliable comparison.

Where possible, processing shall occur in batches to limit memory consumption.

Face detection shall run in the background rather than blocking normal browsing.

## 4.4 Face Recognition and Grouping

The application shall generate numerical embeddings representing detected faces.

A clustering process shall group embeddings that appear sufficiently similar.

Initially, the system shall use a configurable clustering algorithm, with DBSCAN or a similar density-based approach as the leading candidate.

The grouping system shall support:

* Automatically suggested face groups.
* Unassigned faces.
* Groups containing uncertain matches.
* Manual group merging.
* Manual group separation.
* Removal of incorrectly assigned faces.
* Assignment of individual faces to an existing person.
* Creation of a new person from a selected face or group.

Automatic group assignments shall remain distinguishable from user-confirmed assignments.

The system shall not assume that similar-looking relatives are the same person.

It shall also account for the possibility that one person's appearance changes substantially over several decades.

## 4.5 People Management

The application shall provide a People view showing representative thumbnails for discovered face groups.

The user shall be able to:

1. Open a group to see its associated photographs.
2. Assign a name to the group.
3. Rename a person.
4. Merge two groups.
5. Separate a group containing multiple individuals.
6. Remove incorrect face assignments.
7. View all photographs associated with a named person.
8. View unassigned faces.
9. Review uncertain groupings.

Names shall be assigned by the user rather than inferred automatically.

A person's name and confirmed assignments shall persist between sessions.

The system shall retain a record of manual corrections so that a rescan does not silently undo them.

## 4.6 Photo Browsing

The application shall provide a thumbnail-based photo browser.

The user shall be able to:

* Browse photographs by directory.
* Browse the unified catalog.
* Open a photograph at a larger size.
* View available metadata.
* Filter by capture date.
* Filter by person.
* Search or filter by filename.
* See the photograph's source location.
* View other photographs containing the same person.

The interface shall clearly distinguish between a thumbnail and the original image.

The original image shall be accessed from its existing storage location when needed.

## 4.7 Chronological Browsing

The application shall support chronological browsing based on available capture-date metadata.

Date extraction shall consider:

1. EXIF DateTimeOriginal, when available.
2. Other relevant embedded capture-date fields.
3. Digitization dates or other metadata where appropriate.
4. Filesystem timestamps as a fallback.

The system shall distinguish between a known capture date and an estimated or fallback date.

It shall not silently treat a file-copy date as the original photograph date.

The user shall be able to browse by year and progressively narrower date ranges.

## 4.8 Duplicate Detection

The application shall support two distinct forms of duplicate detection.

### Exact duplicates

Calculate a cryptographic hash of each file's contents.

Files with identical hashes shall be identified as exact duplicates, regardless of filename or directory.

### Visually similar photographs

Calculate perceptual hashes or use another suitable image-similarity technique.

This process should identify candidates such as:

* Resized copies.
* Recompressed copies.
* Slightly edited versions.
* Similar frames taken in quick succession.

Visually similar images shall be presented as candidates rather than automatically declared duplicates.

The application shall not delete files automatically.

Any future deletion, movement, or consolidation feature must require explicit user approval and should include safeguards against data loss.

## 4.9 Search

The initial application shall support searching by:

* Person.
* Filename.
* Directory or source location.
* Capture date or date range.
* Exact duplicate status.
* Face-processing status.

More advanced searches may be introduced later.

Examples include finding photographs containing two selected people or locating similar images within a selected time range.

## 4.10 Slideshow

The application shall provide a slideshow mode.

The user shall be able to:

* Start a slideshow from the complete catalog.
* Start a slideshow for a selected person.
* Start a slideshow for a selected date range.
* Adjust the interval between photographs.
* Pause and resume playback.
* Move to the previous or next photograph.
* Exit the slideshow.

The initial slideshow shall display photographs in chronological order when reliable dates are available.

Random ordering may be added as an option.

## 4.11 Smart TV Interface

A television-oriented interface is a planned extension, not a requirement for the first working release.

The preferred approach is to reuse the existing backend and database.

The TV interface should provide:

* Large, readable navigation controls.
* A thumbnail gallery suitable for television viewing.
* People browsing.
* Year-based browsing.
* Full-screen photographs.
* Slideshow controls.
* Navigation using directional remote-control buttons where supported.

The interface should minimize text entry.

The specific implementation will depend on the television's operating system and browser capabilities.

A dedicated Android TV or Google TV application may be considered if the television cannot provide a satisfactory experience through the web interface.

The TV client shall not need its own face-recognition engine or separate photo catalog.

---

# 5. Database Design

SQLite is the proposed database for the initial implementation.

The database shall be stored on persistent application storage and included in the backup plan.

The initial logical data model will include the following entities.

## 5.1 Photos

Suggested fields:

* photo_id
* file_path
* source_id
* file_hash
* perceptual_hash
* capture_date
* capture_date_source
* width
* height
* file_size
* thumbnail_path
* scan_status
* last_scanned

## 5.2 Faces

Suggested fields:

* face_id
* photo_id
* bounding_box
* embedding
* quality_score
* detection_model_version
* processing_status

## 5.3 People

Suggested fields:

* person_id
* display_name
* notes
* representative_face_id
* created_at
* updated_at

## 5.4 Face Assignments

Suggested fields:

* face_id
* person_id
* assignment_source
* confidence_or_review_status
* confirmed_at

## 5.5 Sources

Suggested fields:

* source_id
* source_path
* source_type
* availability_status
* last_scanned

## 5.6 Processing Jobs

Suggested fields:

* job_id
* job_type
* status
* progress
* started_at
* completed_at
* error_summary

The database schema shall support future additions without requiring a complete rewrite.

Database access shall be isolated behind a repository or data-access layer so that PostgreSQL remains a possible future migration target.

The initial application shall not require PostgreSQL.

If future scale or concurrent-write requirements justify a migration, the decision shall be based on measured performance rather than assumed necessity.

---

# 6. System Architecture

## 6.1 Application Components

The system shall consist of the following logical components.

### Web application

Responsible for browser requests, user interface delivery, and application navigation.

### Catalog service

Responsible for photo records, metadata, source tracking, and database operations.

### Face-processing service

Responsible for face detection, embedding generation, and grouping.

### Background worker

Responsible for long-running scans, thumbnail generation, and face processing.

### Database

Responsible for persistent catalog information and face assignments.

### Thumbnail cache

Responsible for storing generated preview images separately from the originals.

### Storage interface

Responsible for locating photographs and checking whether their source drives are available.

## 6.2 Processing Workflow

A typical initial scan shall proceed as follows:

1. Discover supported image files.
2. Check whether each file is already cataloged.
3. Record or update file information.
4. Extract metadata.
5. Calculate the file hash.
6. Generate a thumbnail.
7. Detect faces.
8. Generate embeddings for usable faces.
9. Store face records.
10. Make the resulting faces available for grouping.
11. Update processing status.

A file that fails at one stage should not prevent unrelated files from being processed.

The worker shall support progress reporting and useful error messages.

## 6.3 Incremental Processing

The system shall avoid repeating expensive work unnecessarily.

Unchanged photographs shall reuse existing metadata, thumbnails, and face-processing results.

When a file changes, the application shall determine which derived information needs to be regenerated.

Changes to face-recognition models shall be tracked so that the system can identify records produced by older model versions.

A full rescan shall be available when necessary, but shall not be the default behavior.

---

# 7. Performance and Resource Requirements

The initial design target is to operate without a dedicated GPU.

The system should be capable of running within approximately 2–4 GB of allocated RAM, subject to testing.

The application shall:

* Process photographs incrementally.
* Limit concurrent image-processing tasks.
* Avoid loading an entire archive into memory.
* Cache thumbnails.
* Reuse existing embeddings.
* Run expensive operations in the background.
* Allow ordinary browsing while scanning continues.
* Report processing progress.

No fixed scan-time guarantee is specified until a representative test collection has been processed.

A benchmark shall be performed before the system is approved for processing the complete archive.

The benchmark shall record:

* Number of photographs processed.
* Number of faces detected.
* Processing time.
* Peak memory consumption.
* CPU utilization.
* Recognition-grouping accuracy on a manually reviewed sample.

The target is a compact, maintainable application rather than maximum processing speed at any cost.

---

# 8. Security and Privacy

Because the application contains personal photographs and biometric-derived information, privacy is an important design requirement.

The application shall:

1. Operate entirely within the home network during normal use.
2. Require no cloud-based face recognition.
3. Avoid transmitting photographs or face embeddings to external services.
4. Restrict access to configured photo directories.
5. Use read-only source mounts during initial deployment.
6. Avoid exposing the service directly to the public internet.
7. Support authentication if required for access control.
8. Protect the database and its backups from unauthorized access.
9. Avoid logging unnecessary personal information.
10. Make it possible to delete the catalog and derived face data without deleting original photographs.

The application shall not expose arbitrary filesystem browsing or file access through its web interface.

File paths supplied through browser requests must be validated against configured source directories.

If the application is eventually accessed outside the home network, additional authentication and secure remote-access arrangements will be required.

---

# 9. Reliability and Backup

The application shall tolerate interrupted scans and recover gracefully after restarts.

A processing job interrupted by a server restart shall be marked appropriately and resumed or safely retried.

The database shall use appropriate transactional safeguards.

The backup plan shall cover:

* SQLite database.
* Application configuration.
* User-defined person names and assignments.
* Required model files or instructions for obtaining them.
* Important application metadata.

The thumbnail cache may be regenerated if necessary.

Original photographs shall remain under the protection of the existing storage and backup arrangements.

The application database shall be backed up using a SQLite-aware procedure rather than by blindly copying an actively changing database file.

Restoration shall be tested before the application is considered production-ready.

---

# 10. User Interface Requirements

The desktop interface shall prioritize clear navigation and practical use over visual complexity.

The initial interface shall include:

**Home**

* Catalog statistics.
* Recently added photographs.
* Processing status.
* Navigation to major sections.

**Photos**

* Thumbnail gallery.
* Folder browsing.
* Search and filtering.
* Photograph details.

**People**

* Suggested face groups.
* Named individuals.
* Unassigned faces.
* Group-review controls.

**Timeline**

* Chronological navigation.
* Year and date-range filters.

**Duplicates**

* Exact duplicate groups.
* Visually similar candidates.
* Review status.

**Settings**

* Configured photo sources.
* Scan controls.
* Processing options.
* Database and storage information.

The interface shall communicate uncertainty where the software has not established a reliable match.

The user shall be able to correct mistakes without having to manipulate the database directly.

---

# 11. Development Plan

Development shall proceed through gated milestones.

Each milestone must pass its acceptance tests before the next major stage begins.

## Phase 1 — Environment and Prototype

Tasks:

* Verify the Proxmox environment.
* Confirm available resources.
* Select a test photo directory.
* Verify model licensing and dependencies.
* Install the compact face models.
* Create a command-line face detector.
* Generate face embeddings.
* Produce contact sheets showing suggested groups.

Acceptance criteria:

* The prototype processes a test collection.
* Faces are detected and displayed correctly.
* Similar faces can be compared and grouped.
* Processing time and memory consumption are measured.
* Original photographs remain unchanged.

## Phase 2 — Database and Catalog

Tasks:

* Define the SQLite schema.
* Implement photo discovery.
* Extract metadata.
* Calculate file hashes.
* Store face records.
* Implement incremental scanning.
* Handle unavailable drives and processing errors.

Acceptance criteria:

* Catalog records survive restarts.
* Repeated scans do not unnecessarily repeat processing.
* New photographs can be added.
* Unavailable sources are handled safely.

## Phase 3 — Desktop Browser Interface

Tasks:

* Implement the FastAPI backend.
* Build the thumbnail gallery.
* Add folder navigation.
* Add search and date filters.
* Implement full-size image viewing.
* Display processing status.

Acceptance criteria:

* The interface works from Linux Mint and Windows.
* Users can browse cataloged photographs.
* Scanning does not prevent normal browsing.

## Phase 4 — People Management

Tasks:

* Display face groups.
* Assign person names.
* Merge and separate groups.
* Correct individual face assignments.
* Display all photographs associated with a person.
* Preserve user-confirmed assignments.

Acceptance criteria:

* Users can review and correct automatic groups.
* Corrections survive restarts and rescans.
* The interface distinguishes confirmed and suggested assignments.

## Phase 5 — Duplicate Detection

Tasks:

* Implement exact duplicate detection.
* Add perceptual image hashing.
* Group potential visual duplicates.
* Add a review interface.

Acceptance criteria:

* Exact duplicates are identified by file content rather than filenames.
* Similarity matches are presented as candidates.
* No original files are deleted or modified.

## Phase 6 — Smart TV Interface

Tasks:

* Determine television platform compatibility.
* Implement remote-friendly navigation.
* Add full-screen viewing.
* Add slideshow controls.
* Add people and timeline browsing.

Acceptance criteria:

* The interface can be operated comfortably with the available TV remote.
* Photographs can be browsed without a keyboard.
* The TV uses the existing server and catalog.

## Phase 7 — Deployment and Maintenance

Tasks:

* Configure the service to start automatically.
* Configure persistent application storage.
* Establish database backups.
* Test recovery after restart.
* Document upgrades and troubleshooting.

Acceptance criteria:

* The application operates independently of OpenCode.
* The application survives a normal server restart.
* Database backup and restoration have been tested.

---

# 12. Testing Strategy

Testing shall occur throughout development.

The initial face-recognition test collection should contain approximately 200–500 photographs representing a range of conditions.

The test set should include:

* Recent digital photographs.
* Older scanned photographs.
* Different lighting conditions.
* Different facial expressions.
* Group photographs.
* Multiple photographs of the same person.
* Photographs of different people who resemble one another.

The test collection should be reviewed manually so that recognition results can be evaluated against known identities.

The system shall be evaluated for both false matches and missed matches.

A false match occurs when different people are grouped together.

A missed match occurs when photographs of the same person are placed in separate groups or remain unassigned.

The acceptable balance between these errors shall be established after the first prototype is evaluated.

Other tests shall verify:

* Database consistency.
* Incremental scanning.
* Recovery from interrupted jobs.
* Handling of unavailable drives.
* Browser compatibility.
* Access controls.
* Preservation of original files.
* Backup restoration.

---

# 13. OpenCode Development Rules

OpenCode shall be used as a coding assistant under a controlled development process.

The following rules shall apply:

1. Work on one clearly defined task at a time.
2. Read existing project files before modifying them.
3. Explain proposed architectural changes before implementing major changes.
4. Use Git to record working versions.
5. Add automated tests where practical.
6. Run tests after changes.
7. Avoid unrelated refactoring.
8. Avoid unnecessary model downloads.
9. Do not change Proxmox services or network configuration without explicit approval.
10. Do not modify or delete original photographs.
11. Do not expose secrets or credentials in source control.
12. Document dependencies and installation steps.
13. Preserve a working version before attempting risky changes.

The coding assistant shall not be treated as an authority on whether its own implementation is correct.

Code and test results must be reviewed before deployment.

The application shall remain usable if the coding assistant or local language model is unavailable.

---

# 14. Risks and Mitigations

| Risk                                           | Mitigation                                                |
| ---------------------------------------------- | --------------------------------------------------------- |
| Face models confuse similar-looking people     | Human review, group correction, conservative matching     |
| Recognition quality is poor on old photographs | Test representative images before full deployment         |
| Scanning consumes excessive CPU or RAM         | Batch processing and resource limits                      |
| Photo drives become unavailable                | Retain catalog records and mark sources unavailable       |
| Duplicate detection produces false positives   | Separate exact matches from visual similarity suggestions |
| Application accidentally changes originals     | Read-only source mounts and explicit safeguards           |
| Model licensing prevents intended use          | Verify licenses before selecting final models             |
| TV browser is unsuitable                       | Test early; consider a dedicated TV client                |
| Database corruption or accidental loss         | Consistent backups and restoration tests                  |
| Coding-agent changes introduce regressions     | Git, automated tests, and incremental development         |

---

# 15. Initial Release Scope

The first usable release should remain deliberately small.

It shall include:

* A working local face-detection model.
* A working face-recognition model.
* A small SQLite photo catalog.
* A command-line scanning tool.
* Face-group contact sheets.
* Basic manual grouping corrections.
* A simple browser-based photo gallery.
* Incremental scanning.
* Read-only access to original photographs.

The first release will not require:

* GPU acceleration.
* A dedicated Smart TV application.
* PostgreSQL.
* Automatic deletion of duplicates.
* Cloud integration.
* Facial identification by name without user confirmation.
* Advanced facial search across the entire archive.

These features can be added when the core implementation is reliable.

---

# 16. Decisions Requiring Approval

The following questions should be resolved before the corresponding implementation stages begin.

**1. Hosting environment**

Confirm whether the application will run in a dedicated Debian LXC container or a virtual machine.

**2. Photo storage**

Identify the directories and drives that will initially be cataloged and determine how they can be mounted read-only.

**3. Database**

Use SQLite for the first release, with a migration path to PostgreSQL if future requirements justify it.

**4. Face-recognition models**

Begin by evaluating YuNet and SFace, subject to licensing, compatibility, and accuracy tests.

**5. Smart TV platform**

Identify the TV's manufacturer and model before committing to a browser-only or dedicated application approach.

**6. Development location**

Prefer development on Linux Mint, with tested deployments to Proxmox.

**7. Initial test collection**

Select a representative collection of approximately 200–500 photographs.

**8. Resource limits**

Confirm available Proxmox resources before assigning memory and CPU limits.

**9. Authentication**

Determine whether access will initially be limited to a trusted home LAN or whether multiple household users require separate accounts.

**10. Duplicate management**

Keep duplicate identification read-only in the initial implementation. Any later file-removal capability will require an explicit approval workflow.

---

# 17. Definition of Success

The initial project will be considered successful when:

1. The application catalogs a representative photo collection.
2. Face detection and recognition operate locally.
3. Similar faces can be grouped and reviewed.
4. The user can assign names and correct grouping mistakes.
5. The photo catalog persists between sessions.
6. Subsequent scans avoid unnecessary repeated processing.
7. The application is accessible through a browser on the home network.
8. The application runs without requiring a GPU.
9. Original photographs remain unchanged.
10. The application can be backed up and restored.

A later release will be considered successful when it adds reliable duplicate detection, broader multi-drive browsing, and a usable Smart TV interface.

---

# End of Draft Specification

**Recommended next step:** Review this document and agree on the scope of the first release before asking OpenCode to generate the application.

The first coding task should be a small, independently testable face-recognition prototype rather than the entire application.
