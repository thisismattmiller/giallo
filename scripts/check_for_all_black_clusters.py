#!/usr/bin/env python3
"""
Check for clusters that contain mostly black/empty screenshots.
These often indicate VLM hallucinations where the model generated descriptions
for black frames.
"""

import json
import os
from pathlib import Path
from PIL import Image
import numpy as np

# Paths
SCRIPT_DIR = Path(__file__).parent
BASE_DIR = SCRIPT_DIR.parent
CLUSTERS_FILE = BASE_DIR / "data_clusters" / "clusters.json"
SCREENSHOTS_DIR = Path("/Volumes/NextGlum/giallo/screenshots")

def is_black_image(image_path, threshold=10, black_percent=0.95):
    """
    Check if an image is mostly black.

    Args:
        image_path: Path to the image file
        threshold: Maximum average pixel value to consider as "black" (0-255)
        black_percent: Minimum percentage of pixels that must be black

    Returns:
        True if image is mostly black, False otherwise
    """
    try:
        with Image.open(image_path) as img:
            # Convert to grayscale for simpler analysis
            img_gray = img.convert('L')

            # Convert to numpy array
            img_array = np.array(img_gray)

            # Count pixels below threshold
            black_pixels = np.sum(img_array <= threshold)
            total_pixels = img_array.size

            # Calculate percentage of black pixels
            black_ratio = black_pixels / total_pixels

            return black_ratio >= black_percent

    except Exception as e:
        print(f"  Error reading {image_path}: {e}")
        return False

def get_screenshot_path(filename):
    """Get the full path to a screenshot file."""
    # Extract video name from filename (format: videoname__0001.jpg)
    match = filename.split('__')
    if len(match) >= 2:
        video_name = match[0]
        return SCREENSHOTS_DIR / video_name / filename
    return None

def check_cluster(cluster_id, screenshots, sample_size=None):
    """
    Check a cluster for black screenshots.

    Args:
        cluster_id: The cluster ID
        screenshots: List of screenshot filenames
        sample_size: If set, only check this many random screenshots

    Returns:
        dict with statistics about the cluster
    """
    print(f"\nChecking cluster {cluster_id} ({len(screenshots)} screenshots)...")

    # Optionally sample for faster checking
    screenshots_to_check = screenshots
    if sample_size and len(screenshots) > sample_size:
        import random
        screenshots_to_check = random.sample(screenshots, sample_size)
        print(f"  Sampling {sample_size} screenshots")

    black_count = 0
    missing_count = 0
    checked_count = 0

    for filename in screenshots_to_check:
        screenshot_path = get_screenshot_path(filename)

        if not screenshot_path or not screenshot_path.exists():
            missing_count += 1
            continue

        if is_black_image(screenshot_path):
            black_count += 1

        checked_count += 1

    # Calculate percentage
    if checked_count > 0:
        black_percent = (black_count / checked_count) * 100
    else:
        black_percent = 0

    result = {
        'cluster_id': cluster_id,
        'total_screenshots': len(screenshots),
        'checked': checked_count,
        'black': black_count,
        'missing': missing_count,
        'black_percent': black_percent
    }

    print(f"  Results: {black_count}/{checked_count} black ({black_percent:.1f}%)")
    if missing_count > 0:
        print(f"  Warning: {missing_count} screenshots not found")

    return result

def main():
    import argparse

    parser = argparse.ArgumentParser(description='Check for clusters with mostly black screenshots')
    parser.add_argument('--sample', type=int, default=None,
                      help='Sample size per cluster (default: check all)')
    parser.add_argument('--threshold', type=float, default=50.0,
                      help='Minimum black percentage to report cluster (default: 50)')
    parser.add_argument('--output', type=str, default=None,
                      help='Output JSON file for detailed results')

    args = parser.parse_args()

    print("="*60)
    print("BLACK SCREENSHOT CLUSTER CHECKER")
    print("="*60)

    # Load clusters
    print(f"\nLoading clusters from {CLUSTERS_FILE}")
    with open(CLUSTERS_FILE, 'r') as f:
        clusters = json.load(f)

    print(f"Loaded {len(clusters)} clusters")

    # Check if screenshots directory exists
    if not SCREENSHOTS_DIR.exists():
        print(f"\nError: Screenshots directory not found: {SCREENSHOTS_DIR}")
        return

    print(f"Screenshots directory: {SCREENSHOTS_DIR}")

    if args.sample:
        print(f"Sampling {args.sample} screenshots per cluster")
    else:
        print("Checking all screenshots")

    print(f"Reporting clusters with >{args.threshold}% black screenshots")

    # Process each cluster
    results = []
    problematic_clusters = []

    for cluster_id, screenshots in clusters.items():
        # Skip noise cluster
        if cluster_id == "-1":
            print(f"\nSkipping cluster -1 (noise)")
            continue

        result = check_cluster(cluster_id, screenshots, sample_size=args.sample)
        results.append(result)

        # Flag if mostly black
        if result['black_percent'] >= args.threshold:
            problematic_clusters.append(result)

    # Print summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    print(f"\nTotal clusters checked: {len(results)}")
    print(f"Clusters with >{args.threshold}% black screenshots: {len(problematic_clusters)}")

    if problematic_clusters:
        print(f"\n🚩 PROBLEMATIC CLUSTERS (sorted by black percentage):")
        print(f"{'Cluster':<10} {'Screenshots':<12} {'Black':<10} {'Percent':<10}")
        print("-" * 50)

        # Sort by black percentage descending
        problematic_clusters.sort(key=lambda x: x['black_percent'], reverse=True)

        for result in problematic_clusters:
            print(f"{result['cluster_id']:<10} "
                  f"{result['total_screenshots']:<12} "
                  f"{result['black']}/{result['checked']:<10} "
                  f"{result['black_percent']:.1f}%")

        # Print just the cluster IDs for easy reference
        cluster_ids = [r['cluster_id'] for r in problematic_clusters]
        print(f"\nProblematic cluster IDs: {cluster_ids}")
    else:
        print("\n✅ No clusters with mostly black screenshots found!")

    # Save detailed results if requested
    if args.output:
        output_path = Path(args.output)
        output_data = {
            'metadata': {
                'sample_size': args.sample,
                'threshold_percent': args.threshold,
                'total_clusters_checked': len(results),
                'problematic_clusters_count': len(problematic_clusters)
            },
            'problematic_clusters': problematic_clusters,
            'all_results': results
        }

        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)

        print(f"\n💾 Detailed results saved to: {output_path}")

    print("\n" + "="*60)

    # Prompt user to remove problematic clusters
    if problematic_clusters:
        print("\n" + "="*60)
        print("CLEANUP OPTIONS")
        print("="*60)

        cluster_ids_to_remove = [r['cluster_id'] for r in problematic_clusters]
        print(f"\nFound {len(cluster_ids_to_remove)} clusters with mostly black screenshots.")
        print(f"Cluster IDs: {cluster_ids_to_remove}")

        response = input("\nDo you want to remove these clusters from data_clusters/*.json files? (y/n): ")

        if response.lower() == 'y':
            remove_clusters_from_files(cluster_ids_to_remove)
        else:
            print("No changes made.")

def remove_clusters_from_files(cluster_ids_to_remove):
    """Remove specified cluster IDs from all data_clusters/*.json files."""
    from datetime import datetime

    print(f"\nRemoving {len(cluster_ids_to_remove)} clusters from data_clusters files...")

    data_clusters_dir = BASE_DIR / "data_clusters"
    cluster_ids_set = set(cluster_ids_to_remove)

    # Files to update
    files_to_update = [
        data_clusters_dir / "clusters.json",
        data_clusters_dir / "clusters_with_descriptions.json",
        data_clusters_dir / "cluster_llm_labels.json"
    ]

    for filepath in files_to_update:
        if not filepath.exists():
            print(f"  Skipping {filepath.name} (not found)")
            continue

        print(f"\n  Processing {filepath.name}...")

        try:
            with open(filepath, 'r') as f:
                data = json.load(f)

            # Create backup before modifying
            backup_path = filepath.with_suffix('.json.backup')
            print(f"    Creating backup at {backup_path.name}")
            with open(backup_path, 'w') as f:
                json.dump(data, f, indent=2)

            # Handle different file structures
            if filepath.name == "cluster_llm_labels.json":
                # This file has metadata and classifications
                if 'classifications' in data:
                    original_count = len(data['classifications'])
                    data['classifications'] = {
                        k: v for k, v in data['classifications'].items()
                        if k not in cluster_ids_set
                    }
                    removed_count = original_count - len(data['classifications'])

                    # Update metadata
                    if 'metadata' in data:
                        data['metadata']['total_clusters'] = len(data['classifications'])
                        data['metadata']['last_updated'] = datetime.now().isoformat()

                    print(f"    Removed {removed_count} clusters from classifications")
            else:
                # clusters.json and clusters_with_descriptions.json are just cluster_id: data
                original_count = len(data)
                data = {
                    k: v for k, v in data.items()
                    if k not in cluster_ids_set
                }
                removed_count = original_count - len(data)
                print(f"    Removed {removed_count} clusters")

            # Save updated file
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)

            print(f"    ✅ Updated {filepath.name}")

        except Exception as e:
            print(f"    ❌ Error processing {filepath.name}: {e}")

    print(f"\n✅ Cleanup complete! Removed clusters from all files.")
    print(f"💾 Backups saved with .backup extension")

if __name__ == "__main__":
    main()
