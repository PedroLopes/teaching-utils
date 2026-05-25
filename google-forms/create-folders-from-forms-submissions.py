#!/usr/bin/env python3

from pathlib import Path
import shutil
import sys

# currently dir is comming from first argument
TARGET_DIR = Path(sys.argv[1])

for file_path in TARGET_DIR.iterdir():
    # Skip directories, I only act on files
    if not file_path.is_file():
        continue

    filename = file_path.name

    # Check if filename contains " - " (this is currently what google forms adds)
    if " - " not in filename:
        print(f"Skipping (no separator): {filename}")
        continue

    try:
        # Extract the student name after " - "
        student_part = filename.split(" - ", 1)[1]

        # Remove extension from the extracted part
        student_name = Path(student_part).stem.strip()

        # Create folder
        student_folder = TARGET_DIR / student_name
        student_folder.mkdir(exist_ok=True)

        # Move file into folder
        destination = student_folder / filename
        shutil.move(str(file_path), str(destination))

        print(f"Moved: {filename} -> {student_folder}/")

    except Exception as e:
        print(f"Error processing {filename}: {e}")
