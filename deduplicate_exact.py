#!/usr/bin/env python3
"""
deduplicate_exact.py: Group video files by exact byte size and delete redundant copies based on folder priority.
"""

import os
import argparse
from collections import defaultdict

# Supported video formats
VIDEO_EXTENSIONS = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.mpg', '.mpeg', '.av1'}

# Minimum file size to consider (1MB to avoid empty/generic files)
MIN_SIZE_BYTES = 1024 * 1024

def ensure_win32_long_path(path):
    if os.name != 'nt':
        return path
    abs_path = os.path.abspath(path)
    if abs_path.startswith(r"\\?\ "):
        return abs_path
    if abs_path.startswith(r"\\"):
        return r"\\?\UNC" + abs_path[1:]
    return r"\\?\\" + abs_path

def get_path_priority(path, root_dir):
    """
    Rank path priority:
    2: Performer folders starting with #-- (Highest)
    1: Studio/Category folders (Medium)
    0: zzMisc (Lowest)
    """
    rel_path = os.path.relpath(path, root_dir)
    parts = rel_path.split(os.sep)
    if not parts:
        return 0
    root_folder = parts[0]
    if root_folder == "zzMisc":
        return 0
    elif root_folder.startswith("#--"):
        return 2
    else:
        return 1

def main():
    parser = argparse.ArgumentParser(description="Find and delete duplicate video files of exact matching byte size.")
    parser.add_argument("--dir", "-d", required=True, help="Target directory (e.g. your 'abe' root folder)")
    parser.add_argument("--dry-run", action="store_true", help="Show proposed deletions without performing them")
    args = parser.parse_args()

    target_dir = ensure_win32_long_path(args.dir)

    if not os.path.exists(target_dir):
        print(f"Directory does not exist: {target_dir}")
        return

    print("=" * 60)
    print("DEDUPLICATING EXACT DUPLICATES (SAME BYTE SIZE)")
    print(f"Directory: {target_dir}")
    print(f"Dry Run:   {args.dry_run}")
    print("=" * 60)

    size_map = defaultdict(list)

    # Walk all files recursively
    for root, dirs, files in os.walk(target_dir):
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in VIDEO_EXTENSIONS:
                file_path = os.path.join(root, f)
                try:
                    size = os.path.getsize(file_path)
                    if size >= MIN_SIZE_BYTES:
                        size_map[size].append(file_path)
                except Exception as e:
                    print(f"Error reading size of {file_path}: {e}")

    # Filter to matching sizes
    duplicate_groups = {size: paths for size, paths in size_map.items() if len(paths) > 1}

    if not duplicate_groups:
        print("No exact duplicate files found.")
        return

    print(f"Found {len(duplicate_groups)} duplicate groups.")

    deletions_list = []
    total_reclaimed_bytes = 0

    for size, paths in sorted(duplicate_groups.items(), key=lambda x: x[0], reverse=True):
        # Sort by priority (descending), then alphabetically to ensure determinism
        ranked_paths = sorted(paths, key=lambda p: (-get_path_priority(p, target_dir), p))
        
        keep_path = ranked_paths[0]
        delete_paths = ranked_paths[1:]

        print(f"\nGroup (Size: {size / (1024*1024):.2f} MB):")
        print(f"  [KEEP]   {os.path.relpath(keep_path, target_dir)}")
        
        for dp in delete_paths:
            print(f"  [DELETE] {os.path.relpath(dp, target_dir)}")
            deletions_list.append(dp)
            total_reclaimed_bytes += size

    print("\n" + "=" * 60)
    print("DELETION STATISTICS")
    print("=" * 60)
    print(f"Duplicate Groups:    {len(duplicate_groups)}")
    print(f"Suggested Deletions: {len(deletions_list)}")
    print(f"Storage Reclaimed:   {total_reclaimed_bytes / (1024*1024*1024):.2f} GB")
    print("=" * 60)

    if not args.dry_run:
        print("\nExecuting deletions...")
        success_count = 0
        for idx, path in enumerate(deletions_list, 1):
            try:
                os.remove(path)
                print(f"[{idx}/{len(deletions_list)}] Deleted: {os.path.basename(path)}")
                success_count += 1
            except Exception as e:
                print(f"[{idx}] Error deleting {path}: {e}")
        print(f"\nSuccessfully deleted {success_count} files.")
    else:
        print("\nDry run completed. No files were deleted.")

if __name__ == "__main__":
    main()
