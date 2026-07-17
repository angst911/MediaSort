#!/usr/bin/env python3
"""
deduplicate_folders.py: Group scene folders by core name/date and delete duplicate quality folders, preferring 1080p.
"""

import os
import re
import argparse
import shutil

def ensure_win32_long_path(path):
    if os.name != 'nt':
        return path
    abs_path = os.path.abspath(path)
    if abs_path.startswith(r"\\?\ "):
        return abs_path
    if abs_path.startswith(r"\\"):
        return r"\\?\UNC" + abs_path[1:]
    return r"\\?\\" + abs_path

def get_group_key(folder_name):
    """
    Extracts the core identifying part of the folder name.
    Matches: Start of string -> Site -> Date (YY.MM.DD) -> First Name
    """
    match = re.search(r'^(.+?\.\d{2,4}\.\d{2}\.\d{2}(?:\.[a-zA-Z0-9]+)?)', folder_name, re.IGNORECASE)
    
    if match:
        return match.group(1).lower()
    else:
        cleaned = re.sub(r'(?i)(\.?(1080p|2160p|720p|4k|8k|xxx|mp4|mkv))|(-[a-zA-Z0-9]+)$', '', folder_name)
        return cleaned.lower()

def get_quality_score(folder_name):
    """
    Assigns a numerical score based on resolution tags.
    1080p is preferred over 2160p and 720p.
    """
    name = folder_name.lower()
    score = 0
    
    if '1080p' in name:
        score += 300  # Highest priority
    elif '2160p' in name or '4k' in name:
        score += 200  # Second priority
    elif '720p' in name:
        score += 100  # Third priority
        
    return score

def main():
    parser = argparse.ArgumentParser(description="Recursively find duplicate scene directories and delete redundant qualities, preferring 1080p.")
    parser.add_argument("--dir", "-d", required=True, help="Parent directory containing scene folders to scan")
    parser.add_argument("--dry-run", action="store_true", help="Show proposed folder deletions without performing them")
    args = parser.parse_args()

    target_dir = ensure_win32_long_path(args.dir)

    if not os.path.exists(target_dir):
        print(f"Error: Directory '{target_dir}' does not exist.")
        return

    print("=" * 60)
    print("DEDUPLICATING SCENE DIRECTORIES")
    print(f"Directory: {target_dir}")
    print(f"Dry Run:   {args.dry_run}")
    print("=" * 60)
    
    groups = {}
    
    # 1. Group the folders
    try:
        items = os.listdir(target_dir)
    except Exception as e:
        print(f"Error listing target directory: {e}")
        return

    for item in items:
        full_path = os.path.join(target_dir, item)
        
        if os.path.isdir(full_path):
            key = get_group_key(item)
            score = get_quality_score(item)
            
            if key not in groups:
                groups[key] = []
                
            groups[key].append({
                "name": item,
                "score": score,
                "path": full_path
            })

    total_duplicate_groups = 0
    deletions_suggested = 0

    # 2. Process the duplicates
    for key, folders in sorted(groups.items()):
        if len(folders) > 1:
            total_duplicate_groups += 1
            # Sort by score highest first (1080p will be first)
            folders.sort(key=lambda x: x['score'], reverse=True)
            
            best_folder = folders[0]
            duplicates = folders[1:]
            
            print(f"--- Group Identified: '{key}' ---")
            print(f"  [KEEP] {best_folder['name']} (Score: {best_folder['score']})")
            
            for dup in duplicates:
                deletions_suggested += 1
                print(f"  [DEL]  {dup['name']} (Score: {dup['score']})")
                
                if not args.dry_run:
                    try:
                        shutil.rmtree(dup['path'])
                        print("         -> Deleted successfully.")
                    except Exception as e:
                        print(f"         -> Error deleting {dup['name']}: {e}")
            print("")

    print("=" * 60)
    print("DEDUPLICATION SUMMARY")
    print("=" * 60)
    print(f"Total Duplicate Groups:  {total_duplicate_groups}")
    print(f"Suggested Deletions:     {deletions_suggested}")
    print("=" * 60)

    if args.dry_run:
        print("\n*** DRY RUN COMPLETE ***")
        print("No folders were actually deleted. Omit --dry-run flag to execute deletions.")
    else:
        print("\n*** CLEANUP COMPLETE ***")

if __name__ == "__main__":
    main()
