# Photo Explorer — Development Instructions

## Development Platform
- Primary development and testing platform: Windows 11.
- Shell: Windows PowerShell.
- Python: 3.12, using the project virtual environment `.venv`.
- GUI: PySide6.
- Project must run as a portable Windows application first.
- Linux and Proxmox support are future goals.

## Shell Commands
- Use Windows PowerShell syntax for shell commands.
- Do not assume Unix utilities such as `head`, `tail`, `grep`, `sed`,
  or `chmod` are installed.
- Use `Get-Content`, `Select-String`, `Get-ChildItem`, and
  `Select-Object` when appropriate.
- If a command fails because it is unavailable on Windows, use a
  PowerShell alternative.
- Do not introduce WSL, Docker, or Linux dependencies.

## Python and Portability
- Use the project's `.venv` for Python commands and tests.
- Prefer Python APIs over shell commands for application functionality.
- Use `pathlib.Path` for filesystem operations.
- Avoid hard-coded machine-specific paths.
- Keep application code cross-platform where practical, without
  compromising the Windows-first deliverable.

## Photo Safety
- Original photographs must never be modified, renamed, moved, or deleted.
- Store the catalog and application data separately from photo folders.
- Automated tests must use temporary directories and test files.
- Never run tests against the user's real photo archive.

## Development Workflow
- Read `SPECIFICATION.md` and the relevant addendum before substantial changes.
- Make small, focused changes.
- Run relevant tests after each implementation stage.
- Preserve existing working functionality.
- Do not install dependencies without a clear need.
- Do not commit or push changes unless the user explicitly requests it.
- Report changed files, test results, and known limitations.
