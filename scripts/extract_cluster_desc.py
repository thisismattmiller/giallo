#!/usr/bin/env python3
"""
Extract descriptions for screenshots in each cluster and create a new JSON file
with cluster ID as key and array of {filename, description} objects as value.
Excludes cluster "-1" (noise points).
"""

import json
import os
from pathlib import Path

# Paths
SCRIPT_DIR = Path(__file__).parent
BASE_DIR = SCRIPT_DIR.parent
CLUSTERS_FILE = BASE_DIR / "data_clusters" / "clusters.json"
DATA_DIR = BASE_DIR / "data"
OUTPUT_FILE = BASE_DIR / "data_clusters" / "clusters_with_descriptions.json"

def load_clusters():
    """Load the clusters.json file"""
    print(f"Loading clusters from {CLUSTERS_FILE}")
    with open(CLUSTERS_FILE, 'r') as f:
        clusters = json.load(f)
    print(f"Loaded {len(clusters)} clusters")
    return clusters

def load_all_data_files():
    """Load all data/*.json files into a single dict keyed by filename"""
    print(f"Loading data files from {DATA_DIR}")
    all_data = {}

    for json_file in DATA_DIR.glob("*.json"):
        print(f"  Loading {json_file.name}")
        with open(json_file, 'r') as f:
            data = json.load(f)
            # Merge into all_data dict
            all_data.update(data)

    print(f"Loaded {len(all_data)} total screenshots from data files")
    return all_data

def extract_cluster_descriptions(clusters, all_data):
    """Extract descriptions for each screenshot in each cluster"""
    result = {}

    for cluster_id, screenshot_list in clusters.items():
        # Skip cluster "-1" (noise points)
        if cluster_id == "-1":
            print(f"Skipping cluster -1 (noise)")
            continue

        print(f"Processing cluster {cluster_id} ({len(screenshot_list)} screenshots)")

        cluster_data = []
        missing_count = 0

        for filename in screenshot_list:
            if filename in all_data:
                description = all_data[filename].get('description', '')
                cluster_data.append({
                    'filename': filename,
                    'description': description
                })
            else:
                # Screenshot not found in data files
                missing_count += 1
                cluster_data.append({
                    'filename': filename,
                    'description': ''
                })

        if missing_count > 0:
            print(f"  Warning: {missing_count} screenshots not found in data files")

        result[cluster_id] = cluster_data

    return result

def main():
    print("Starting cluster description extraction...")

    # Load clusters
    clusters = load_clusters()

    # Load all data files
    all_data = load_all_data_files()

    # Extract descriptions
    cluster_descriptions = extract_cluster_descriptions(clusters, all_data)

    # Save output
    print(f"\nSaving to {OUTPUT_FILE}")
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(cluster_descriptions, f, indent=2)

    print(f"\nDone! Created {len(cluster_descriptions)} clusters with descriptions")
    print(f"Output saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
