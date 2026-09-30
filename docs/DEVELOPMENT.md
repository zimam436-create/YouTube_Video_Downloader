# Development Guide

## Local setup

1. Install Python 3.11+.
2. Run `setup.ps1` to install the external tools.
3. Run `python -m py_compile ytd.py`.
4. Run the test script:

```powershell
python tests/test_syntax.py
```

## Architecture

`ytd.py` is intentionally a thin orchestration layer around `yt-dlp` and FFmpeg.

Keep these responsibilities separate:

- UI/input handling
- metadata/format discovery
- download command construction
- retry/fallback handling
- playlist bookkeeping
- report generation

## Important invariants

- A selected playlist index must never silently disappear.
- A failed download must never be reported as successful.
- A partial media file must never be treated as a completed final file.
- Playlist indexes must remain stable when using parallel downloads.
- Third-party executables must not be committed to Git.
- Downloaded files should go to the user's normal Downloads directory.
