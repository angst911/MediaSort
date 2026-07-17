#!/usr/bin/env python3
"""
sort_media.py: Sort loose media folders/files into performer or studio directories.
"""

import os
import re
import argparse
import shutil

# Supported video formats
VIDEO_EXTENSIONS = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.mpg', '.mpeg', '.av1'}

# Recurring performer directories to dynamically create if requested
NEW_PERFORMERS = [
    "Blake Blossom", "Zarina Noir", "Little Angel", "Rebecca Volpetti",
    "Hailey Rose", "Rissa May", "Justine Jakobs", "Chanel Camryn",
    "Molly Little", "Leya Desantis"
]

# Recurring studio directories to dynamically create if requested
NEW_STUDIOS = [
    "MyFamilyPies", "SisLovesMe", "MyFriendsHotMom", "CumSwappingSis",
    "Nubiles", "SheSeducedMe", "MomsBangTeens", "MyDaughtersHotFriend",
    "Brazzers"
]

def ensure_win32_long_path(path):
    """
    Appends \\?\\UNC\\ or \\?\\ to path on Windows to bypass the 260 character MAX_PATH limit.
    """
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

def safe_move_file(src, dst, dry_run=True):
    if dry_run:
        print(f"[DRY RUN] Move File: '{src}' -> '{dst}'")
        return True

    dst_dir = os.path.dirname(dst)
    os.makedirs(dst_dir, exist_ok=True)

    if os.path.exists(dst):
        src_size = os.path.getsize(src)
        dst_size = os.path.getsize(dst)
        if src_size == dst_size:
            print(f"File exists with identical size. Deleting duplicate source: {src}")
            try:
                os.remove(src)
            except Exception as e:
                print(f"Error deleting duplicate file {src}: {e}")
        else:
            base, ext = os.path.splitext(dst)
            counter = 1
            while os.path.exists(f"{base}_{counter}{ext}"):
                counter += 1
            new_dst = f"{base}_{counter}{ext}"
            print(f"File exists with different size. Renaming target to: {new_dst}")
            shutil.move(src, new_dst)
    else:
        shutil.move(src, dst)
    return True

def main():
    parser = argparse.ArgumentParser(description="Sort loose files and folders into performer or studio folders.")
    parser.add_argument("--source", "-s", required=True, help="Source directory containing loose files")
    parser.add_argument("--dest", "-d", required=True, help="Destination directory containing performer/studio folders")
    parser.add_argument("--dry-run", action="store_true", help="Show suggested moves without performing them")
    parser.add_argument("--create-folders", action="store_true", help="Create recurring performer & studio folders dynamically")
    args = parser.parse_args()

    src_dir = ensure_win32_long_path(args.source)
    dst_dir = ensure_win32_long_path(args.dest)

    if not os.path.exists(src_dir):
        print(f"Source directory does not exist: {src_dir}")
        return
    if not os.path.exists(dst_dir):
        print(f"Destination directory does not exist: {dst_dir}")
        return

    print("=" * 60)
    print("RECURSIVE SORTING PROCESS")
    print(f"Source:      {src_dir}")
    print(f"Destination: {dst_dir}")
    print(f"Dry Run:     {args.dry_run}")
    print(f"Create New:  {args.create_folders}")
    print("=" * 60)

    # 1. Gather existing performer/studio folders in destination
    dest_subdirs = [d for d in os.listdir(dst_dir) if os.path.isdir(os.path.join(dst_dir, d))]
    
    performers = []
    studios = []

    for d in dest_subdirs:
        if d.startswith("#--"):
            perf_name = d[3:]
            clean_name = perf_name.replace("_", " ").replace(".", " ")
            norm_name = normalize(clean_name)
            performers.append({'dir_name': d, 'clean_name': clean_name, 'norm_name': norm_name, 'is_new': False})
        else:
            norm_name = normalize(d)
            studios.append({'dir_name': d, 'norm_name': norm_name, 'is_new': False})

    # Add optional new performer/studio folders
    if args.create_folders:
        for p in NEW_PERFORMERS:
            dir_name = f"#--{p.replace(' ', '_')}"
            norm_name = normalize(p)
            if not any(x['dir_name'] == dir_name for x in performers):
                performers.append({'dir_name': dir_name, 'clean_name': p, 'norm_name': norm_name, 'is_new': True})
        for s in NEW_STUDIOS:
            norm_name = normalize(s)
            if not any(x['dir_name'] == s for x in studios):
                studios.append({'dir_name': s, 'norm_name': norm_name, 'is_new': True})

    stepsis_existing = [s for s in studios if s['dir_name'] == "StepSibblings"]

    # 2. Gather all files in source recursively
    files_to_sort = []
    for root, dirs, files in os.walk(src_dir):
        for f in files:
            if f == "Thumbs.db":
                continue
            files_to_sort.append(os.path.join(root, f))

    moved_count = 0
    skipped_count = 0
    created_folders = set()

    for file_path in files_to_sort:
        filename = os.path.basename(file_path)
        rel_path = os.path.relpath(file_path, src_dir)
        norm_rel_path = normalize(rel_path)
        
        # Check if pre-classified in source (residing inside a #-- folder)
        path_parts = rel_path.split(os.sep)
        prematched_perf = None
        for part in path_parts[:-1]:
            if part.startswith("#--") and len(part) > 3:
                prematched_perf = part
                break

        target_dir = None
        match_type = ""
        match_details = ""

        if prematched_perf:
            target_dir = prematched_perf
            match_type = "pre-classified"
            match_details = prematched_perf
        else:
            # Perform name matching
            matched_perfs = [p for p in performers if p['norm_name'] in norm_rel_path]
            matched_studios = [s for s in studios if s['norm_name'] in norm_rel_path]

            if "stepsibling" in norm_rel_path and not matched_studios:
                if stepsis_existing:
                    matched_studios.append(stepsis_existing[0])

            if matched_perfs:
                target_dir = matched_perfs[0]['dir_name']
                match_type = "performer"
                match_details = matched_perfs[0]['clean_name']
            elif matched_studios:
                target_dir = matched_studios[0]['dir_name']
                match_type = "studio"
                match_details = matched_studios[0]['dir_name']

        if target_dir:
            # Check if folders need creating
            is_new = any(p['dir_name'] == target_dir and p['is_new'] for p in performers) or \
                     any(s['dir_name'] == target_dir and s['is_new'] for s in studios)

            if is_new:
                created_folders.add(target_dir)
                if not args.dry_run:
                    os.makedirs(os.path.join(dst_dir, target_dir), exist_ok=True)

            # Determine final destination path (preserving subdirectory tree structures under target folder)
            if prematched_perf:
                dst_rel = os.path.join(*path_parts[1:])
                dst_path = os.path.join(dst_dir, target_dir, dst_rel)
            elif len(path_parts) > 2:
                dst_rel = os.path.join(*path_parts[1:])
                dst_path = os.path.join(dst_dir, target_dir, dst_rel)
            else:
                dst_path = os.path.join(dst_dir, target_dir, filename)

            print(f"MATCHED [{match_type}] ({match_details}): {rel_path}")
            safe_move_file(file_path, dst_path, dry_run=args.dry_run)
            moved_count += 1
        else:
            print(f"SKIPPED (No match): {rel_path}")
            skipped_count += 1

    # 3. Clean up empty source subfolders
    if not args.dry_run:
        print("\nCleaning up empty source directories...")
        for root, dirs, files in os.walk(src_dir, topdown=False):
            for d in dirs:
                dir_to_check = os.path.join(root, d)
                try:
                    if not os.listdir(dir_to_check):
                        os.rmdir(dir_to_check)
                        print(f"Removed empty source folder: {dir_to_check}")
                except Exception as e:
                    print(f"Error cleaning folder {dir_to_check}: {e}")

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total processed files: {moved_count + skipped_count}")
    print(f"Moved / Matched:       {moved_count}")
    print(f"Skipped / Unmatched:   {skipped_count}")
    if created_folders:
        print(f"New directories created: {len(created_folders)}")
        for fld in sorted(created_folders):
            print(f"  + {fld}")
    print("=" * 60)

if __name__ == "__main__":
    main()
