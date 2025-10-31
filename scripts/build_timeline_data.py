#!/usr/bin/env python3

import json
import subprocess
import os
from pathlib import Path
from collections import defaultdict
import math

# Paths
CLUSTERS_FILE = Path(__file__).parent.parent / "data_clusters" / "clusters.json"
LABELS_FILE = Path(__file__).parent.parent / "data_clusters" / "cluster_llm_labels.json"
VIDEO_DIR = Path("/Volumes/NextGlum/giallo")
OUTPUT_FILE = Path(__file__).parent.parent / "apps" / "timeline" / "timeline_data.json"

def get_video_duration(video_name):
    """Get video duration in seconds using ffprobe"""
    # Try different extensions
    for ext in ['.mkv', '.mp4', '.avi', '.mov', '']:
        video_path = VIDEO_DIR / (video_name + ext)
        if video_path.exists():
            try:
                cmd = [
                    'ffprobe',
                    '-v', 'error',
                    '-show_entries', 'format=duration',
                    '-of', 'default=noprint_wrappers=1:nokey=1',
                    str(video_path)
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                return float(result.stdout.strip())
            except Exception as e:
                print(f"Error getting duration for {video_path}: {e}")
                return None

    print(f"Video not found: {video_name}")
    return None

def parse_filename(filename):
    """Parse screenshot filename to get video name and frame number"""
    # Format: videoname__0001.jpg
    if '__' not in filename:
        return None, None

    parts = filename.rsplit('__', 1)
    video_name = parts[0]
    frame_str = parts[1].replace('.jpg', '')

    try:
        frame_number = int(frame_str)
        return video_name, frame_number
    except ValueError:
        return None, None

def find_sequences(frame_numbers):
    """Find sequences of consecutive frame numbers"""
    if not frame_numbers:
        return []

    frame_numbers = sorted(frame_numbers)
    sequences = []
    current_seq = [frame_numbers[0]]

    for i in range(1, len(frame_numbers)):
        if frame_numbers[i] == current_seq[-1] + 1:
            current_seq.append(frame_numbers[i])
        else:
            sequences.append(current_seq)
            current_seq = [frame_numbers[i]]

    sequences.append(current_seq)
    return sequences

def round_up_to_nearest_5_percent(percentage):
    """Round up to nearest 5%"""
    return math.ceil(percentage * 20) / 20  # Multiply by 20, ceil, divide by 20

def main():
    print("Loading cluster data...")
    with open(CLUSTERS_FILE) as f:
        clusters = json.load(f)

    print("Loading cluster labels...")
    with open(LABELS_FILE) as f:
        labels_data = json.load(f)
        cluster_labels = labels_data.get('classifications', {})

    print(f"Processing {len(clusters)} clusters...")

    timeline_data = {
        "clusters": [],
        "metadata": {
            "total_clusters": 0,
            "movie_durations": {}
        }
    }

    # Cache for movie durations
    movie_durations = {}

    for cluster_id, screenshots in clusters.items():
        if cluster_id == "-1":
            continue

        print(f"Processing cluster {cluster_id} ({len(screenshots)} screenshots)...")

        # Get cluster label
        label = cluster_labels.get(cluster_id, {}).get('classification', 'No classification')

        # Group screenshots by video
        video_groups = defaultdict(list)
        for filename in screenshots:
            video_name, frame_number = parse_filename(filename)
            if video_name and frame_number:
                video_groups[video_name].append(frame_number)

        # Process each video group
        timeline_points = []
        for video_name, frame_numbers in video_groups.items():
            # Get video duration
            if video_name not in movie_durations:
                duration = get_video_duration(video_name)
                if duration:
                    movie_durations[video_name] = duration
                else:
                    continue

            duration = movie_durations[video_name]

            # Find sequences
            sequences = find_sequences(frame_numbers)

            for seq in sequences:
                # Use middle frame of sequence
                middle_frame = seq[len(seq) // 2]
                timestamp_seconds = middle_frame * 5

                # Calculate percentage
                percentage = timestamp_seconds / duration

                # Round up to nearest 5%
                rounded_percentage = round_up_to_nearest_5_percent(percentage)

                timeline_points.append({
                    "video": video_name,
                    "percentage": rounded_percentage,
                    "count": len(seq),  # How many screenshots in this sequence
                    "frames": seq,
                    "timestamp": timestamp_seconds
                })

        # Aggregate points at same percentage
        percentage_counts = defaultdict(lambda: {"count": 0, "videos": set()})
        for point in timeline_points:
            pct = point["percentage"]
            percentage_counts[pct]["count"] += point["count"]
            percentage_counts[pct]["videos"].add(point["video"])

        # Create final points
        final_points = []
        for pct, data in sorted(percentage_counts.items()):
            final_points.append({
                "percentage": pct,
                "count": data["count"],
                "videos": list(data["videos"])
            })

        cluster_data = {
            "cluster_id": cluster_id,
            "label": label,
            "screenshot_count": len(screenshots),
            "points": final_points
        }

        timeline_data["clusters"].append(cluster_data)

    # Sort clusters by screenshot count (descending)
    timeline_data["clusters"].sort(key=lambda c: c["screenshot_count"], reverse=True)
    timeline_data["metadata"]["total_clusters"] = len(timeline_data["clusters"])
    timeline_data["metadata"]["movie_durations"] = movie_durations

    # Save output
    print(f"Writing output to {OUTPUT_FILE}...")
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(timeline_data, f, indent=2)

    print(f"✓ Successfully created timeline data with {len(timeline_data['clusters'])} clusters")
    print(f"✓ Processed {len(movie_durations)} unique movies")

if __name__ == "__main__":
    main()
