# GEMINI.md - Instructional Context for MediaSort

This file serves as the foundational instruction context for future interactions with the `MediaSort` codebase. Any AI agent operating in this repository should adhere to the rules, architectures, and conventions documented below.

---

## 1. Project Overview

`MediaSort` is a professional-grade suite of CLI-based Python scripts designed to automate the lifecycle of large-scale media libraries, specifically optimized for high-volume network file systems (e.g., TrueNAS shares accessed via Windows UNC paths).

### Key Architectural Features:
- **Zero External Dependencies:** Built entirely on Python 3 standard library modules (`os`, `re`, `shutil`, `argparse`, `collections`).
- **Windows Long-Path Bypassing:** Employs explicit Win32 namespace formatting (`\\?\UNC\` for network shares and `\\?\` for local drives) to bypass the default 260-character `MAX_PATH` limit.
- **Metadata-Only Efficiency:** Performs moves and renames locally on the same file share, making filesystem manipulations instantaneous.
- **Descriptive Naming Preservation:** Uses an intelligent context-aware naming algorithm to rename generically-named scene files (e.g. `i.mp4`) when flattening subdirectories so their names remain fully descriptive.
- **Data Loss Prevention:** Handles duplicate filename collisions gracefully by comparing exact byte sizes (deleting identical duplicates) and adding numbered suffixes (e.g., `_1`, `_2`) for unique files sharing the same name.

---

## 2. Directory & Component Mapping

- **`sort_media.py`**: Recursively searches a loose source directory and matches files against performer folders (prefixed with `#--`) or studio folders in a destination directory.
- **`flatten_cleanup.py`**: Recursively deletes non-video companion files, flattens subdirectories under categories, preserves filenames, and cleans up empty folders.
- **`deduplicate_exact.py`**: Groups video files by exact byte size and deletes duplicate copies based on folder priority (Performer `#--` > Studio > `zzMisc`).
- **`deduplicate_qualities.py`**: Compares different quality versions of the same scene by stripping quality/release tags (e.g., `2160p`, `1080p`, `4K`, `H265`, `x264`), prioritizes keeping `1080p` copies, and removes others.
- **`deduplicate_folders.py`**: Groups duplicate scene folder directories (using match keys like `site.YY.MM.DD`) under a parent path, ranks folder resolutions (preferring `1080p` over others), and recursively deletes redundant folders.

---

## 3. Usage & Commands

Each utility script is designed as an independent CLI with standard inputs.

### Sorting Media
```powershell
python sort_media.py --source "<source_path>" --dest "<dest_path>" [--create-folders] [--dry-run]
```
- `--create-folders`: Dynamically creates recurring performer & studio folders if they do not yet exist.
- `--dry-run`: Performs a full validation check without modifying any files.

### Flattening & Cleanup
```powershell
python flatten_cleanup.py --dir "<abe_directory_path>" [--dry-run]
```

### Strict Size Deduplication
```powershell
python deduplicate_exact.py --dir "<abe_directory_path>" [--dry-run]
```

### Quality-Based Deduplication
```powershell
python deduplicate_qualities.py --dir "<abe_directory_path>" [--dry-run]
```

### Folder-Level Quality Deduplication
```powershell
python deduplicate_folders.py --dir "<adult_review_directory_path>" [--dry-run]
```

---

## 4. Development & Coding Conventions

### Path Handling (Mandatory)
Every script must wrap file paths with the `ensure_win32_long_path` function before accessing the filesystem. On Windows environments (`nt`), paths must be prefixed with `\\?\UNC\` or `\\?\` to prevent `FileNotFoundError` (WinError 3).

### Python Naming & Structure Conventions
- **Variable/Function names:** Use `snake_case` (e.g. `safe_move_file`, `get_quality_label`).
- **Constants:** Use `UPPER_CASE` (e.g. `VIDEO_EXTENSIONS`, `MIN_SIZE_BYTES`).
- **Classes/Libraries:** Keep code lightweight. Do not import third-party packages (like `pandas` or `requests`) unless explicitly requested.
- **Error Handling:** Always wrap filesystem operations (`os.remove`, `shutil.move`, `os.rename`) in `try-except` blocks and log failures gracefully.

### Collision & Duplicate Prevention
Never overwrite a file during moving/renaming without verifying its size:
- If `size_A == size_B`: Delete the source copy (since the stream is identical).
- If `size_A != size_B`: Append `_1`, `_2`, etc. to the destination file to preserve both versions.
