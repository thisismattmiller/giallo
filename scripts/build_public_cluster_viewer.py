#!/usr/bin/env python3

import json
import shutil
from pathlib import Path

# Paths
CLUSTERS_FILE = Path(__file__).parent.parent / "data_clusters" / "clusters.json"
LABELS_FILE = Path(__file__).parent.parent / "data_clusters" / "cluster_llm_labels.json"
CONTENT_CHECK_FILE = Path(__file__).parent.parent / "data_clusters" / "content_check.json"
SCREENSHOTS_DIR = Path("/Volumes/NextGlum/giallo/screenshots")
OUTPUT_DIR = Path(__file__).parent.parent / "apps" / "cluster-viewer-public"
OUTPUT_IMAGES_DIR = OUTPUT_DIR / "images"
OUTPUT_DATA_DIR = OUTPUT_DIR / "data"

def load_data():
    """Load all necessary data files"""
    print("Loading data files...")

    with open(CLUSTERS_FILE) as f:
        clusters = json.load(f)

    with open(LABELS_FILE) as f:
        labels_data = json.load(f)
        cluster_labels = labels_data.get('classifications', {})

    with open(CONTENT_CHECK_FILE) as f:
        content_check = json.load(f)

    return clusters, cluster_labels, content_check

def filter_safe_clusters(clusters, content_check):
    """Filter out clusters that have any screenshots with nudity"""
    safe_clusters = {}
    unsafe_clusters = []

    for cluster_id, screenshots in clusters.items():
        if cluster_id == "-1":
            continue

        # Check if any screenshot has nudity
        has_nudity = any(
            content_check.get(filename, {}).get('nudity', False)
            for filename in screenshots
        )

        if has_nudity:
            unsafe_clusters.append(cluster_id)
        else:
            safe_clusters[cluster_id] = screenshots

    return safe_clusters, unsafe_clusters

def get_screenshot_path(filename):
    """Get full path to screenshot file"""
    if '__' not in filename:
        return None
    video_name = filename.rsplit('__', 1)[0]
    screenshot_path = SCREENSHOTS_DIR / video_name / filename
    if screenshot_path.exists():
        return screenshot_path
    return None

def copy_screenshots(safe_clusters):
    """Copy all screenshots from safe clusters to output directory"""
    print("\nCopying screenshots...")

    # Clear and create output directory
    if OUTPUT_IMAGES_DIR.exists():
        shutil.rmtree(OUTPUT_IMAGES_DIR)
    OUTPUT_IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    total_screenshots = sum(len(screenshots) for screenshots in safe_clusters.values())
    copied = 0
    errors = 0

    for cluster_id, screenshots in safe_clusters.items():
        for filename in screenshots:
            source_path = get_screenshot_path(filename)
            if source_path:
                dest_path = OUTPUT_IMAGES_DIR / filename
                try:
                    shutil.copy2(source_path, dest_path)
                    copied += 1
                    if copied % 100 == 0:
                        print(f"  Copied {copied}/{total_screenshots} screenshots...")
                except Exception as e:
                    print(f"  Error copying {filename}: {e}")
                    errors += 1
            else:
                print(f"  Warning: Screenshot not found: {filename}")
                errors += 1

    print(f"  ✅ Copied {copied} screenshots ({errors} errors)")
    return copied

def generate_public_data(safe_clusters, cluster_labels):
    """Generate public data JSON file"""
    print("\nGenerating public data JSON...")

    OUTPUT_DATA_DIR.mkdir(parents=True, exist_ok=True)

    public_data = {
        "clusters": {},
        "labels": {},
        "metadata": {
            "total_clusters": len(safe_clusters),
            "total_screenshots": sum(len(screenshots) for screenshots in safe_clusters.values()),
            "note": "This is a filtered public version excluding clusters with mature content"
        }
    }

    # Add clusters
    public_data["clusters"] = safe_clusters

    # Add labels for safe clusters only
    for cluster_id in safe_clusters.keys():
        if cluster_id in cluster_labels:
            public_data["labels"][cluster_id] = cluster_labels[cluster_id]

    # Save to file
    output_file = OUTPUT_DATA_DIR / "clusters_data.json"
    with open(output_file, 'w') as f:
        json.dump(public_data, f, indent=2)

    print(f"  ✅ Saved to {output_file}")
    print(f"  Total size: {output_file.stat().st_size / 1024 / 1024:.2f} MB")

def main():
    print("=" * 80)
    print("Building Public Cluster Viewer")
    print("=" * 80)
    print()

    # Load data
    clusters, cluster_labels, content_check = load_data()
    print(f"  Loaded {len(clusters)} clusters")
    print(f"  Loaded {len(cluster_labels)} labels")
    print(f"  Loaded {len(content_check)} content check entries")

    # Filter safe clusters
    print("\nFiltering safe clusters...")
    safe_clusters, unsafe_clusters = filter_safe_clusters(clusters, content_check)
    print(f"  Safe clusters: {len(safe_clusters)}")
    print(f"  Unsafe clusters (excluded): {len(unsafe_clusters)}")

    total_safe_screenshots = sum(len(screenshots) for screenshots in safe_clusters.values())
    print(f"  Total safe screenshots: {total_safe_screenshots}")

    # Copy screenshots
    copied = copy_screenshots(safe_clusters)

    # Generate public data
    generate_public_data(safe_clusters, cluster_labels)

    # Calculate directory size
    total_size = sum(f.stat().st_size for f in OUTPUT_DIR.rglob('*') if f.is_file())
    print(f"\n📦 Total package size: {total_size / 1024 / 1024:.2f} MB")

    print("\n✅ Public cluster viewer built successfully!")
    print(f"📁 Output directory: {OUTPUT_DIR}")
    print("\nNext steps:")
    print("  1. Review the generated files in apps/cluster-viewer-public/")
    print("  2. The static HTML viewer will be created next")
    print("  3. Deploy to GitHub Pages when ready")

if __name__ == "__main__":
    main()
