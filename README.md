# Photo Explorer

A self-hosted photo explorer that uses local AI to find faces,
group people, catalog family photographs, and discover duplicates.

## Project Goals

- Catalog photographs across multiple hard drives.
- Detect faces and group visually similar faces.
- Allow users to identify people and correct grouping mistakes.
- Browse photographs by person and date.
- Find exact duplicates and visually similar images.
- Keep original photographs unchanged.
- Run AI processing locally without cloud services.
- Provide a browser interface accessible from computers throughout the house.
- Explore a future Smart TV interface for browsing family photographs.

## Proposed Technology

- Python
- FastAPI
- OpenCV YuNet and SFace
- SQLite
- Proxmox
- OpenCode for AI-assisted development

These are preliminary choices and may change as the project develops.

## Project Status

**Early design — seeking feedback.**

The initial software specification will be published in `SPECIFICATION.md`.

The goal is to develop a practical, privacy-conscious photo catalog that runs on a home server.

## Contributing

Suggestions and constructive criticism are welcome!

I'd particularly appreciate feedback on lightweight face-recognition models,
photo catalog design, duplicate detection, and Smart TV compatibility.
