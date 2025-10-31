import os
import subprocess
from pathlib import Path

SOURCE_DIR = "/Volumes/NextGlum/giallo"
SCREENSHOTS_DIR = "/Volumes/NextGlum/giallo/screenshots"

def has_jpg_files(directory):
    """Check if directory contains any jpg files."""
    if not os.path.exists(directory):
        return False
    return any(f.lower().endswith('.jpg') for f in os.listdir(directory))

def extract_screenshots(video_file, output_dir):
    """Extract screenshots from video file using ffmpeg."""
    video_path = os.path.join(SOURCE_DIR, video_file)
    output_pattern = os.path.join(output_dir, f"{video_file}__%04d.jpg")

    cmd = [
        "ffmpeg",
        "-i", video_path,
        "-vf", "select='isnan(prev_selected_t)+gte(t-prev_selected_t,5)'",
        "-q:v", "1",
        "-vsync", "0",
        output_pattern
    ]

    print(f"  Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"  ✗ Error running ffmpeg:")
        print(f"    {result.stderr}")
        return False

    return True

def main():
    """Scan for video files and create corresponding screenshot directories."""
    if not os.path.exists(SOURCE_DIR):
        print(f"Error: Source directory not found: {SOURCE_DIR}")
        return

    # Create screenshots directory if it doesn't exist
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

    # Scan for video files
    video_files = []
    for file in os.listdir(SOURCE_DIR):
        if file.lower().endswith(('.mkv', '.mp4')):
            video_files.append(file)

    print(f"Found {len(video_files)} video files\n")

    created = 0
    existing = 0
    extracted = 0
    skipped = 0

    for video_file in sorted(video_files):
        dir_path = os.path.join(SCREENSHOTS_DIR, video_file)

        # Create directory if it doesn't exist
        if os.path.exists(dir_path):
            existing += 1
        else:
            os.makedirs(dir_path)
            print(f"+ Created directory: {video_file}")
            created += 1

        # Check if screenshots need to be extracted
        if has_jpg_files(dir_path):
            print(f"✓ {video_file} (has screenshots, skipping)")
            skipped += 1
        else:
            print(f"→ {video_file} (extracting screenshots...)")
            if extract_screenshots(video_file, dir_path):
                print(f"  ✓ Screenshots extracted")
                extracted += 1
            else:
                print(f"  ✗ Failed to extract screenshots")

    print(f"\nSummary:")
    print(f"  Directories: {created} created, {existing} already existed")
    print(f"  Screenshots: {extracted} extracted, {skipped} skipped")

if __name__ == "__main__":
    main()
