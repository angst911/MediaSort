#!/usr/bin/env python3
"""
flatten_cleanup.py: Delete non-video files recursively, flatten folders inside categories, and clean up directories.
"""

import os
import argparse

# Supported video formats
VIDEO_EXTENSIONS = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.mpg', '.mpeg', '.av1'}

def ensure_win32_long_path(path):
    if os.name != 'nt':
        return path
    abs_path = os.path.abspath(path)
    if abs_path.startswith(r"\\?\ "):
        return abs_path
    if abs_path.startswith(r"\\"):
        return r"\\?\UNC" + abs_path[1:]
    return r"\\?\\" + abs_path

def normalize(s):
    return "".join(c.lower() for c in s if c.isalnum())

def get_flattened_name(subdir_name, filename):
    norm_subdir = normalize(subdir_name)
    norm_filename = normalize(filename)
    
    # Keep original filename if it contains the subdir name or vice-versa
    if norm_subdir in norm_filename or norm_filename in norm_subdir:
        return filename
        
    # Check if a large portion (first 15 chars) is shared
    if norm_subdir[:15] in norm_filename or norm_filename[:15] in norm_subdir:
        return filename
        
    return f"{subdir_name} - {filename}"

def safe_rename(src, dst, dry_run=True):
    if os.path.exists(dst):
        src_size = os.path.getsize(src)
        dst_size = os.path.getsize(dst)
        if src_size == dst_size:
            print(f"Duplicate file with identical size found. Suggested cleanup: delete {src}")
            if not dry_run:
                try:
                    os.remove(src)
                except Exception as e:
                    print(f"Error removing duplicate source: {e}")
            return
            
        base, ext = os.path.splitext(dst)
        counter = 1
        while os.path.exists(f"{base}_{counter}{ext}"):
            counter += 1
        dst = f"{base}_{counter}{ext}"
        print(f"Destination exists with different size. Renaming to: {dst}")

    if not dry_run:
        os.rename(src, dst)
    else:
        print(f"[DRY RUN] Rename & Flatten: '{src}' -> '{dst}'")

def main():
    parser = argparse.ArgumentParser(description="Recursively remove non-video files and flatten performers/studio folders.")
    parser.add_argument("--dir", "-d", required=True, help="Target directory (e.g. your 'abe' root folder)")
    parser.add_argument("--dry-run", action="store_true", help="Show suggested actions without making changes")
    args = parser.parse_args()

    target_dir = ensure_win32_long_path(args.dir)

    if not os.path.exists(target_dir):
        print(f"Directory does not exist: {target_dir}")
        return

    print("=" * 60)
    print("EXECUTING FLATTENING & CLEANUP")
    print(f"Directory: {target_dir}")
    print(f"Dry Run:   {args.dry_run}")
    print("=" * 60)

    # 1. Gather all immediate performer/studio subfolders
    categories = [d for d in os.listdir(target_dir) if os.path.isdir(os.path.join(target_dir, d))]

    deletions_count = 0
    flatten_count = 0

    for cat in categories:
        cat_path = os.path.join(target_dir, cat)
        
        non_videos_to_delete = []
        videos_to_flatten = []

        # Recurse inside this category folder
        for root, dirs, files in os.walk(cat_path):
            for f in files:
                file_path = os.path.join(root, f)
                ext = os.path.splitext(f)[1].lower()
                
                if ext not in VIDEO_EXTENSIONS:
                    non_videos_to_delete.append(file_path)
                else:
                    rel_path = os.path.relpath(file_path, cat_path)
                    path_parts = rel_path.split(os.sep)
                    if len(path_parts) > 1:
                        # Nested file, needs flattening
                        subdir_name = path_parts[0]
                        new_filename = get_flattened_name(subdir_name, f)
                        target_flat_path = os.path.join(cat_path, new_filename)
                        videos_to_flatten.append((file_path, target_flat_path))

        # Perform non-video deletions
        for f_del in non_videos_to_delete:
            deletions_count += 1
            if not args.dry_run:
                try:
                    os.remove(f_del)
                except Exception as e:
                    print(f"Error deleting file {f_del}: {e}")
            else:
                print(f"[DRY RUN] Delete non-video: {os.path.relpath(f_del, target_dir)}")

        # Perform flattening moves
        for src, dst in videos_to_flatten:
            flatten_count += 1
            safe_rename(src, dst, dry_run=args.dry_run)

        # Remove empty directories inside this category
        if not args.dry_run:
            for root, dirs, files in os.walk(cat_path, topdown=False):
                for d in dirs:
                    dir_path = os.path.join(root, d)
                    try:
                        if not os.listdir(dir_path):
                            os.rmdir(dir_path)
                    except Exception as e:
                        print(f"Error removing folder {dir_path}: {e}")

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total non-video files deleted:      {deletions_count}")
    print(f"Total nested video files flattened: {flatten_count}")
    print("=" * 60)

if __name__ == "__main__":
    main()
