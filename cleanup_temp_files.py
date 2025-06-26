#!/usr/bin/env python3
"""
Cleanup script for temporary files created during FHIR development process.
This script moves temporary test and debug files to an archive folder.
"""

import os
import shutil
from pathlib import Path

def main():
    """Move temporary files to archive folder."""
    
    # Create archive directory
    archive_dir = Path("temp_files_archive")
    archive_dir.mkdir(exist_ok=True)
    
    # List of temporary files to archive
    temp_files = [
        # Test files
        "test_correct_name_search.py",
        "test_correct_name_search_fixed.py", 
        "test_name_search_fixed.py",
        "test_backend_only.py",
        "test_current_system.py",
        "test_direct_search.py",
        "test_failed_names.py",
        "test_multiple_names.py",
        "test_sophie_prach.py",
        "test_specialty_search.py",
        "test_xai.py",
        
        # Debug and fix files
        "debug_ai_interpreter.py",
        "fix_ai_interpreter.py",
        "simple_fix.py",
        "quick_fix_json.py",
    ]
    
    # Files to keep (important for production)
    keep_files = [
        "test_practitioner_role.py",  # Core functionality test
        "test_practitioner_role_specialty.py",  # Final working test
    ]
    
    moved_count = 0
    
    for filename in temp_files:
        if filename in keep_files:
            print(f"⚠️  Keeping {filename} (production-relevant)")
            continue
            
        if Path(filename).exists():
            try:
                shutil.move(filename, archive_dir / filename)
                print(f"✅ Moved {filename} to archive")
                moved_count += 1
            except Exception as e:
                print(f"❌ Error moving {filename}: {e}")
        else:
            print(f"⚠️  File not found: {filename}")
    
    print(f"\n📦 Archived {moved_count} temporary files")
    print(f"📁 Archive location: {archive_dir.absolute()}")
    
    # Create a summary of what was archived
    summary_file = archive_dir / "ARCHIVE_SUMMARY.md"
    with open(summary_file, 'w') as f:
        f.write("# Temporary Files Archive\n\n")
        f.write("This folder contains temporary files created during the FHIR development process.\n\n")
        f.write("## Archived Files:\n\n")
        for file in archive_dir.glob("*.py"):
            if file.name != "ARCHIVE_SUMMARY.md":
                f.write(f"- `{file.name}` - Development/testing file\n")
        f.write(f"\n## Archive Date: {archive_dir.stat().st_mtime}\n")
        f.write("\nThese files can be safely deleted if no longer needed for debugging.\n")
    
    print(f"📝 Created archive summary: {summary_file}")

if __name__ == "__main__":
    main()
