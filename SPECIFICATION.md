# Photo Explorer — Software Specification

**Document version:** 0.3  
**Status:** Working specification for the first release  
**Current priority:** Portable Windows Edition  
**Development platform:** Windows  
**Future deployment:** Proxmox Server Edition, deferred until the Windows Edition is stable

---

## 1. Project Overview

Photo Explorer is a local-first photo catalog application designed to help people organize and explore large collections of digital photographs, including older scanned prints.

The application will scan selected folders, catalog photographs and their metadata, identify exact and visually similar images, detect faces, group likely photographs of the same person, and provide browsing tools for people and dates.

The first deliverable is a **portable Windows application**. It must be practical to extract into a writable folder and run without requiring the user to separately install Python, application libraries, or AI models.

The project is intended to be developed incrementally with human review and testing. ChatGPT may assist with architecture, specifications, planning, and troubleshooting. OpenCode or another coding assistant may help implement and test small, reviewable tasks. The project owner remains responsible for decisions and acceptance of the results.

## 2. Scope and Priorities

### 2.1 First priority: Portable Windows Edition

The first release will be developed, tested, and packaged on the existing Windows computer. Its available GPUs may be used where compatible and beneficial, but the application must retain a CPU-compatible baseline.

The first release should focus on reliable core cataloging and browsing, followed by face detection and grouping. Work will proceed in small milestones with tests and review after each milestone.

### 2.2 Explicitly deferred: Proxmox Server Edition

A browser-based server edition deployed to Proxmox is a future phase. It is **not part of the initial implementation or acceptance criteria**.

The code should be organized so that reusable cataloging and AI logic can potentially support a future server edition, but we will not build or maintain two user interfaces during the initial Windows development phase.

### 2.3 Initial exclusions

The first release will not:
- Upload photographs, face images, embeddings, or catalog data to cloud services.
- Require an account, subscription, or internet connection for normal local operation.
- Modify, move, rename, or delete original photographs.
- Automatically delete duplicate photographs.
- Synchronize catalogs between computers or between Windows and a future server.
- Require a GPU to function.
- Attempt to edit photographs or replace a full photo-editing application.
- Deploy to Proxmox.

## 3. Target Environment

### 3.1 Development and testing

- **Primary development, testing, and packaging:** Windows.
- **Linux Mint:** Optional client/test machine; it is not the primary development environment.
- **Proxmox:** Deferred until the portable Windows application is stable and useful.

The application should be tested on Windows without relying on software that happens to be installed on the development machine.

### 3.2 Runtime requirements

- Support a currently supported Windows version, with the exact minimum version confirmed during implementation.
- Provide a CPU-only execution path.
- Use compatible GPU acceleration only when it is detected and supported.
- Report errors clearly when a GPU or optional acceleration backend is unavailable.
- Avoid making a particular GPU, CUDA version, or vendor-specific runtime mandatory.

## 4. Portable Packaging Requirements

The Windows Edition must be distributed as a portable folder or ZIP package. A directory-based package is preferred over a single-file executable because it is easier to inspect, troubleshoot, and update.

The package should include all required runtime components, application libraries, and AI model files, subject to their licenses.

The user should be able to:
1. Extract the package into a writable folder.
2. Launch the application using a clearly identified executable or launcher.
3. Use the application without separately installing Python, libraries, or models.
4. Operate the application offline for normal cataloging and browsing.
5. Move the application folder to another writable location and launch it again.

### 4.1 Application-local data

By default, the application should store its own data inside its application folder, using clearly named subdirectories such as:
- `data/` — SQLite catalog and application state.
- `thumbnails/` — generated thumbnails.
- `cache/` — rebuildable caches and face-processing intermediates.
- `models/` — required model files, if not stored elsewhere in the package.
- `logs/` — diagnostic logs.
- `config/` — user settings.

The final directory layout may change during implementation, but data locations must be documented and predictable. The application should not silently write project data to unrelated system directories.

The application must detect when its data directory is not writable and explain the problem clearly. It must not silently lose data or fall back to an unexpected location.

### 4.2 Relocation

The application folder should be relocatable. Internal paths for its own database, configuration, logs, and caches should be resolved relative to the application/data directory rather than hard-coded to a development-machine path.

Photograph paths in the catalog necessarily refer to external source locations. If a photograph drive or folder is moved or assigned a different drive letter, the application should report missing files and, where feasible, provide a way to reconnect the affected root folder. It must not assume that moving the application also moves the photograph archive.

### 4.3 Offline operation and updates

Normal scanning, indexing, face processing, and browsing must not depend on a network connection. The application must not make cloud API calls or transmit image data, metadata, embeddings, or usage information.

Updates may be installed manually by the user. Updating the application must not overwrite the catalog or user data. Any future update process must include a safe migration strategy for database changes.

## 5. Core Functional Requirements

### 5.1 Select and scan photo folders

- Let the user select one or more folders to catalog.
- Support incremental rescanning so the application can discover new or changed files without rebuilding the entire catalog unnecessarily.
- Track scan progress and provide meaningful status information.
- Allow a scan to be cancelled safely.
- Handle inaccessible folders, disconnected drives, unsupported files, and damaged images without crashing the entire application.
- Record errors in a log and summarize them in the interface.
- Avoid repeatedly processing unchanged photographs where existing hashes and metadata are still valid.

Scanning must be read-only with respect to original photographs.

### 5.2 Supported image formats

The initial release should support common formats such as JPEG/JPG and PNG, and should evaluate TIFF and other formats useful for scanned photographs. HEIC/HEIF and RAW formats may be added if dependable local libraries and licensing permit.

Unsupported files should be skipped with a clear indication rather than causing the scan to fail. The exact supported-format list must be documented in the application.

### 5.3 Metadata catalog

For each photograph, store available information including:
- Full source path and filename.
- File size and file type.
- Image width and height.
- File modification time.
- EXIF metadata where available.
- Capture date/time, including `DateTimeOriginal` and other relevant date fields when present.
- Any derived or estimated date, clearly distinguished from an original embedded date.
- Scan/index status and processing errors where relevant.

Dates can be absent, inconsistent, or wrong, particularly for scanned prints. The interface should not present an inferred date as if it were certain. The initial version should preserve source metadata and allow users to identify photographs whose dates need attention. Manual date correction can be considered after the core catalog works.

### 5.4 Exact duplicate detection

- Compute a cryptographic content hash for each supported image to identify byte-for-byte duplicates.
- Identify groups of exact duplicates independently of filename and folder.
- Present duplicate groups for review.
- Never automatically delete, move, or rename duplicates.

### 5.5 Visually similar image candidates

- Use a perceptual hash or comparable local method to find photographs that may be visually similar even if their file bytes differ.
- Treat perceptual matches as candidates, not proof that two files are duplicates.
- Allow the user to review the images side by side or in a comparison view.
- Do not automatically remove or merge files based only on a similarity score.

### 5.6 Thumbnail gallery and photo viewing

- Provide a thumbnail-based gallery.
- Allow users to open or preview a photograph at a larger size.
- Support browsing and sorting by available dates, filename, and folder.
- Show useful metadata for the selected photograph.
- Generate thumbnails locally and cache them for later use.
- Provide a way to rebuild the thumbnail cache if needed.

### 5.7 Chronological browsing

- Provide a timeline or date-based browsing view.
- Use available capture dates when reliable.
- Make photographs with missing or uncertain dates discoverable rather than silently omitting them.
- Distinguish the photograph's embedded capture date from filesystem timestamps.

### 5.8 Face detection and recognition

Face processing must run locally.

The application should:
1. Detect faces in supported photographs.
2. Generate face representations/embeddings using a selected local model.
3. Compare faces to identify likely matches.
4. Group likely images of the same person for human review.
5. Allow the user to name a person or group.
6. Allow the user to move a face to another person, separate incorrectly merged groups, and merge groups when appropriate.
7. Allow corrections without changing original image files.

Face grouping is probabilistic. The application must present suggestions as likely matches, not certainty. It should be possible to review unassigned faces and correct mistakes. A mistaken grouping must not irreversibly corrupt the catalog.

Candidate models such as OpenCV YuNet for detection and SFace for recognition may be evaluated for the initial prototype. These are candidates, not final commitments. Before selection, test detection and matching quality on the intended collection, CPU performance, packaging complexity, model size, hardware compatibility, and license terms.

### 5.9 People gallery

- Provide a gallery of named people.
- Show representative face thumbnails and photographs associated with each person.
- Let the user open a person to browse their associated photographs.
- Support renaming people and correcting group membership.
- Avoid treating a face match as a confirmed identity until the user accepts or names it.

### 5.10 Search and filtering

The initial version should support practical filters such as:
- Folder/root location.
- Date or date range where dates are available.
- Named person.
- Exact duplicate groups.
- Visually similar candidates.
- Files with missing metadata or processing errors.

Additional search capabilities can be prioritized after the main catalog and people workflows are working.

## 6. Data Storage and Safety

### 6.1 Initial database

Use SQLite for the initial release. It is suitable for a self-contained portable application and does not require a separate database server.

The schema should separate, where practical:
- Source files and their metadata.
- Hashes and duplicate groups.
- Thumbnails and cache references.
- Detected faces and their image locations.
- Face embeddings or references to locally stored embeddings.
- Person/group assignments.
- User corrections and application settings.
- Scan status and processing errors.

The database schema should be versioned so future releases can migrate it safely.

PostgreSQL or another database may be evaluated later only if measured scale or concurrency requirements justify it. It is not required for the initial Windows Edition.

### 6.2 Original-photo protection

The original photo archive is read-only from Photo Explorer's perspective. The application may read images and metadata, and create its own database, thumbnails, embeddings, and caches. It must not modify EXIF data or otherwise write into the original files.

No destructive duplicate-removal feature is in scope for the initial release.

### 6.3 Interrupted scans and recovery

- A cancelled or interrupted scan should leave the database in a consistent state.
- On restart, the application should be able to resume or safely repeat incomplete work.
- Repeated scans should not create duplicate catalog records for the same source file.
- Errors should be logged with enough detail to help diagnose problems without making normal use unnecessarily difficult.
- The user should be given clear instructions for backing up the application data/catalog. The first version may provide documented manual backup rather than a sophisticated backup manager.

## 7. Privacy and Security

- All cataloging, metadata extraction, hashing, face detection, and face grouping must be local.
- No cloud services or external APIs may be required for normal use.
- No telemetry or analytics should be added by default.
- Logs should avoid unnecessarily copying sensitive image metadata or personal information.
- The application should make clear where the catalog and face data are stored.
- The application must not expose a network service in the Windows Edition unless explicitly required and documented.
- Any third-party library and model license obligations must be reviewed before redistribution.

Face embeddings and named-person associations are sensitive personal data in practice. They should remain local and be protected from accidental exposure.

## 8. Proposed Architecture and Technology

Technology choices remain subject to a small working prototype and license/compatibility checks.

### 8.1 Shared core

Use a modular Python core for reusable functions such as:
- File discovery and incremental scanning.
- Metadata extraction.
- Cryptographic and perceptual hashing.
- Thumbnail generation.
- Face detection and embedding generation.
- Face matching and group management.
- Database access and migrations.
- Logging and error handling.

The core should avoid hard-coded paths and UI-specific assumptions.

### 8.2 Windows user interface

Use a native desktop interface, with PySide6 as the leading candidate. The interface should support a gallery, photo details, scan progress, people/group review, and application settings.

The packaging approach should be validated early. PyInstaller is a candidate for bundling the application and Python runtime into a portable directory, but the final approach must be selected based on a working packaged build and testing on a machine without a development environment.

### 8.3 Local AI and image libraries

Evaluate compact, redistributable local models and libraries. Prioritize:
- Reasonable CPU performance.
- Optional GPU acceleration where supported.
- Manageable package size.
- Reliable Windows packaging.
- No network dependency at runtime.
- Clear license and redistribution terms.

Do not download large collections of models speculatively. Select a small number of candidates and test them against the prototype collection first.

## 9. Development Workflow

- Develop on Windows.
- Use Git for version control and make small, understandable commits.
- Ask coding assistants to work on one bounded task at a time.
- Review generated code before accepting it.
- Add automated tests for core behavior as it is implemented.
- Run the tests after changes and investigate failures before proceeding.
- Keep a clear separation between application code and user photo/catalog data.
- Do not use the full photo archive as the first test dataset.
- Document setup, build, packaging, testing, and known limitations.
- Keep the README and specification aligned with the actual implementation.

## 10. Prototype Dataset and Evaluation

Before processing a large archive, test with approximately **200–500 representative photographs**, including:
- Modern digital photographs.
- Older scanned prints.
- Different image sizes and orientations.
- Photographs with and without EXIF metadata.
- Several photographs of the same people across different years.
- Group photographs with multiple faces.
- Poor-quality, faded, or blurry images.
- Exact duplicates and visually similar but non-identical images.

The prototype evaluation should record:
- Whether all expected files are discovered.
- Accuracy of extracted metadata and date interpretation.
- Correct identification of exact duplicates.
- Usefulness of perceptual-similarity candidates.
- Face detection misses and false detections.
- Face grouping errors, including false matches and missed matches.
- Scan and face-processing time.
- Memory use and package size.
- Whether the packaged app works offline and without separately installed dependencies.

Do not claim a specific accuracy level before measuring it. Establish practical acceptance thresholds after testing representative images and reviewing the results.

## 11. Milestones

### Milestone 1 — Application foundation
- Repository and project structure.
- Windows launchable development build.
- Logging, configuration, and application-local data paths.
- Initial automated tests.

**Exit criteria:** The application starts, reports its version, writes logs/data to the expected location, and handles a non-writable data location clearly.

### Milestone 2 — Read-only catalog and scanning
- Folder selection.
- File discovery and supported-format handling.
- Metadata extraction.
- SQLite catalog.
- Progress, cancellation, error handling, and incremental rescanning.

**Exit criteria:** The application catalogs the prototype collection without modifying source files and can safely repeat or resume a scan.

### Milestone 3 — Hashes and gallery
- Exact hashes and duplicate grouping.
- Perceptual similarity candidates.
- Thumbnail cache.
- Photo gallery and detail view.
- Basic date/folder browsing.

**Exit criteria:** Users can browse the test collection and review duplicate/similarity candidates without destructive actions.

### Milestone 4 — Face processing
- Evaluate and select a local face detector and recognizer.
- Face detection and embedding storage.
- Suggested face groups.
- Review and correction controls.
- Named-person gallery.

**Exit criteria:** The user can inspect, name, separate, and merge groups; corrections persist across restarts.

### Milestone 5 — Portable packaging
- Bundle the runtime, dependencies, and required model files.
- Establish the final portable directory structure.
- Test extraction and launch on a Windows environment without separately installed Python or development libraries.
- Verify offline operation and relocation.
- Document backup and troubleshooting.

**Exit criteria:** The packaged app works independently of the development environment, retains its catalog after restart, and does not require internet access for normal use.

### Milestone 6 — Stabilization
- Test larger collections incrementally.
- Fix high-impact bugs and data-integrity problems.
- Improve recovery, logging, and performance.
- Document limitations and release instructions.

**Exit criteria:** The Windows Edition is useful and stable enough for regular personal testing. Only after this milestone should the Proxmox Server Edition be reconsidered.

## 12. Acceptance Criteria for the First Useful Release

The first useful release should meet all of the following:
- Runs as a portable Windows package.
- Does not require a separately installed Python environment.
- Works offline for normal operation.
- Scans selected folders without changing original photographs.
- Stores a persistent catalog and local caches.
- Supports incremental rescanning and safe cancellation/restart.
- Extracts available metadata and clearly handles missing dates.
- Identifies exact duplicates and presents them for review.
- Provides a usable thumbnail gallery and chronological browsing.
- Performs local face detection and provides reviewable face groups.
- Allows the user to name people and correct face-group mistakes.
- Keeps catalog, settings, logs, and generated data in documented locations.
- Can be relocated without hard-coded application paths.
- Provides useful errors and diagnostic logs.
- Has been tested on a representative 200–500-photo dataset.
- Has had model/library licenses and redistribution requirements reviewed.

## 13. Future Possibilities — Not Initial Requirements

Potential future work, to be considered only after the Windows Edition is stable:
- Proxmox-hosted browser-based Server Edition for use on the home LAN.
- A shared web interface for other computers.
- TV-friendly browsing and slideshows.
- More advanced search and filtering.
- Improved date correction and organization tools.
- Catalog export/import or synchronization.
- Database alternatives if measured scale or multi-user needs require them.

These possibilities must not delay or complicate the initial portable Windows release.

## 14. Project Principle

**Build a useful Windows application first, test it with real photographs, and fix the problems we discover.** Keep the originals safe, keep processing local, measure before optimizing, and postpone the server edition until the portable application earns its next step.
