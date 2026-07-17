# MediaSort Toolkit

A suite of professional, highly robust Python utility scripts designed to automate, flatten, deduplicate, and organize large media libraries (specifically on network storage shares like TrueNAS).

## Features
- **Intelligent Sorting (`sort_media.py`):** Organizes loose media files/folders into a destination directory based on existing performer folders (prefixed with `#--`) or studio/category folders. Optionally creates folders for recurring items.
- **Recursive Flattening & Cleanup (`flatten_cleanup.py`):** Removes all non-video files recursively, flattens subdirectories under performer and studio folders, preserves source context for generically named files, and cleans up empty folders.
- **Strict Deduplication (`deduplicate_exact.py`):** Finds duplicate files of identical byte size, ranks copies (keeping performer folders over studio, and studio over `zzMisc`), and safely deletes duplicates.
- **Quality-Based Deduplication (`deduplicate_qualities.py`):** Finds duplicate scenes of different qualities (e.g. 1080p vs 2160p), prioritizes keeping `1080p` copies, and cleans up the rest.

## Requirements
- Python 3.x
- Supported on Windows / Win32 (includes automatic `\\?\UNC\` long-path support to bypass the 260-character `MAX_PATH` limit).
