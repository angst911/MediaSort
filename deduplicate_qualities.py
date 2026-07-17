#!/usr/bin/env python3
"""
deduplicate_qualities.py: Identify and delete different-quality versions of the same scene, preferring 1080p.
"""

import os
import re
import argparse
from collections import defaultdict

# Supported video formats
VIDEO_EXTENSIONS = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.mpg', '.mpeg', '.av1'}

# Quality patterns to strip
QUALITY_PATTERNS = [
    re.compile(r'\b2160p\b', re.IGNORECASE),
    re.compile(r'\b1080p\b', re.IGNORECASE),
    re.compile(r'\b720p\b', re.IGNORECASE),
    re.compile(r'\b480p\b', re.IGNORECASE),
    re.compile(r'\b4k\b', re.IGNORECASE),
    re.compile(r'\b1080\b', re.IGNORECASE),
    re.compile(r'\b720\b', re.IGNORECASE),
    re.compile(r'\bhevc\b', re.IGNORECASE),
    re.compile(r'\bh265\b', re.IGNORECASE),
    re.compile(r'\bx265\b', re.IGNORECASE),
    re.compile(r'\bh264\b', re.IGNORECASE),
    re.compile(r'\bx264\b', re.IGNORECASE),
    re.compile(r'\bav1\b', re.IGNORECASE),
    re.compile(r'\bweb-dl\b', re.IGNORECASE),
    re.compile(r'\bwebdl\b', re.IGNORECASE),
    re.compile(r'\bsiterip\b', re.IGNORECASE),
    re.compile(r'\bxxx\b', re.IGNORECASE),
    re.compile(r'\binternal\b', re.IGNORECASE),
    re.compile(r'\brepack\b', re.IGNORECASE),
    re.compile(r'\b(wrb|ktr|p0rnl0v3r|sendnudes|mami|smallpp|biuk|narcos|sweet|clipp|vsex|ieva|nbq|prt|xvx)\b', re.IGNORECASE),
    re.compile(r'_\d+$')
]

def ensure_win32_long_path(path):
    if os.name != 'nt':
        return path
    abs_path = os.path.abspath(path)
    if abs_path.startswith(r"\\?\ "):
        return abs_path
    if abs_path.startswith(r"\\"):
        return r"\\?\UNC" + abs_path[1:]
    return r"\\?\\" + abs_path

def get_scene_key(filename):
    name, ext = os.path.splitext(filename)
    name = name.lower()
    for pattern in QUALITY_PATTERNS:
        name = pattern.sub('', name)
    return "".join(c for c in name if c.isalnum())

def get_quality_label(filename):
    fn_lower = filename.lower()
    if '2160p' in fn_lower or '4k' in fn_lower:
        return '2160p (4K)'
    elif '1080p' in fn_lower or '1080' in fn_lower:
        return '1080p'
    elif '720p' in fn_lower or '720' in fn_lower:
        return '720p'
    elif '480p' in fn_lower:
        return '480p'
    else:
        return 'Unknown Quality'

def main():
    parser = argparse.ArgumentParser(description="Find and delete duplicate video qualities of the same scene, preferring 1080p.")
    parser.add_argument("--dir", "-d", required=True, help="Target directory (e.g. your 'abe' root folder)")
    parser.add_argument("--dry-run", action="store_true", help="Show proposed deletions without performing them")
    args = parser.parse_args()

    target_dir = ensure_win32_long_path(args.dir)

    if not os.path.exists(target_dir):
        print(f"Directory does not exist: {target_dir}")
        return

    print("=" * 60)
    print("DEDUPLICATING MULTI-QUALITY DUPLICATES")
    print(f"Directory: {target_dir}")
    print(f"Dry Run:   {args.dry_run}")
    print("=" * 60)

    # Group by tuple (parent_performer_studio_dir, scene_key)
    scene_groups = defaultdict(list)

    # Gather immediate category folders
    categories = [d for d in os.listdir(target_dir) if os.path.isdir(os.path.join(target_dir, d))]

    for cat in categories:
        cat_path = os.path.join(target_dir, cat)
        for root, dirs, files in os.walk(cat_path):
            for f in files:
                ext = os.path.splitext(f)[1].lower()
                if ext in VIDEO_EXTENSIONS:
                    file_path = os.path.join(root, f)
                    scene_key = get_scene_key(f)
                    
                    group_key = (cat, scene_key)
                    scene_groups[group_key].append(file_path)

    # Filter to groups with > 1 file
    quality_groups = {k: v for k, v in scene_groups.items() if len(v) > 1}

    if not quality_groups:
        print("No multi-quality duplicate groups found.")
        return

    print(f"Found {len(quality_groups)} multi-quality duplicate groups.")

    deletions_list = []
    total_reclaimed_bytes = 0

    for (fld, key), paths in sorted(quality_groups.items(), key=lambda x: (x[0][0], x[0][1])):
        file_infos = []
        for p in paths:
            filename = os.path.basename(p)
            size = os.path.getsize(p)
            quality = get_quality_label(filename)
            file_infos.append({'path': p, 'name': filename, 'size': size, 'quality': quality})
            
        # Rank:
        # Prefer 1080p, else prefer largest file size
        ranked_files = sorted(file_infos, key=lambda x: (0 if x['quality'] == '1080p' else 1, -x['size']))
        
        keep_file = ranked_files[0]
        delete_files = ranked_files[1:]

        print(f"\nGroup: Folder '{fld}' | Scene Key: '{key}'")
        print(f"  [KEEP]   {keep_file['name']} ({keep_file['quality']} - {keep_file['size'] / (1024*1024):.1f} MB)")
        
        for df in delete_files:
            print(f"  [DELETE] {df['name']} ({df['quality']} - {df['size'] / (1024*1024):.1f} MB)")
            deletions_list.append(df['path'])
            total_reclaimed_bytes += df['size']

    print("\n" + "=" * 60)
    print("DELETION STATISTICS")
    print("=" * 60)
    print(f"Multi-Quality Groups: {len(quality_groups)}")
    print(f"Suggested Deletions:  {len(deletions_list)}")
    print(f"Storage Reclaimed:    {total_reclaimed_bytes / (1024*1024*1024):.2f} GB")
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
