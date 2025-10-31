#!/usr/bin/env python3

import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Paths
data_clusters_dir = Path(__file__).parent.parent / "data_clusters"
clusters_file = data_clusters_dir / "clusters.json"
clusters_desc_file = data_clusters_dir / "clusters_with_descriptions.json"
clusters_labels_file = data_clusters_dir / "cluster_llm_labels.json"

def parse_filename(filename):
    """Parse screenshot filename to get video name"""
    if '__' not in filename:
        return None
    parts = filename.rsplit('__', 1)
    return parts[0]

def check_cluster_movies():
    """Check how many unique movies each cluster has"""
    print("Loading clusters.json...")
    with open(clusters_file) as f:
        clusters = json.load(f)

    single_movie_clusters = []
    multi_movie_clusters = []

    print(f"\nAnalyzing {len(clusters)} clusters...\n")

    for cluster_id, screenshots in clusters.items():
        if cluster_id == "-1":
            continue

        # Get unique movies
        movies = set()
        for filename in screenshots:
            movie = parse_filename(filename)
            if movie:
                movies.add(movie)

        if len(movies) < 2:
            single_movie_clusters.append({
                "cluster_id": cluster_id,
                "screenshot_count": len(screenshots),
                "movies": list(movies)
            })
        else:
            multi_movie_clusters.append(cluster_id)

    print(f"📊 Analysis Results:")
    print(f"  Total clusters (excluding -1): {len(clusters) - (1 if '-1' in clusters else 0)}")
    print(f"  Clusters with 2+ movies: {len(multi_movie_clusters)}")
    print(f"  Clusters with only 1 movie: {len(single_movie_clusters)}")

    if single_movie_clusters:
        print(f"\n❌ Clusters to remove (only 1 movie):")
        for cluster in sorted(single_movie_clusters, key=lambda x: x['screenshot_count'], reverse=True)[:20]:
            print(f"  Cluster {cluster['cluster_id']}: {cluster['screenshot_count']} screenshots from {cluster['movies'][0]}")
        if len(single_movie_clusters) > 20:
            print(f"  ... and {len(single_movie_clusters) - 20} more")

    return single_movie_clusters

def remove_clusters_from_files(cluster_ids_to_remove):
    """Remove specified clusters from all JSON files"""
    files_to_update = [
        clusters_file,
        clusters_desc_file,
        clusters_labels_file
    ]

    print(f"\nRemoving {len(cluster_ids_to_remove)} clusters from data_clusters files...\n")

    for file_path in files_to_update:
        if not file_path.exists():
            print(f"  ⚠️  {file_path.name} not found, skipping...")
            continue

        print(f"  Processing {file_path.name}...")

        # Create backup
        backup_path = file_path.with_suffix(file_path.suffix + '.backup')
        print(f"    Creating backup at {backup_path.name}")

        with open(file_path) as f:
            data = json.load(f)

        with open(backup_path, 'w') as f:
            json.dump(data, f, indent=2)

        # Remove clusters
        removed_count = 0

        if file_path == clusters_labels_file:
            # Special handling for cluster_llm_labels.json structure
            if 'classifications' in data:
                for cluster_id in cluster_ids_to_remove:
                    if cluster_id in data['classifications']:
                        del data['classifications'][cluster_id]
                        removed_count += 1

                # Update metadata
                if 'metadata' in data:
                    data['metadata']['last_updated'] = datetime.now().isoformat()
        else:
            # clusters.json and clusters_with_descriptions.json
            for cluster_id in cluster_ids_to_remove:
                if cluster_id in data:
                    del data[cluster_id]
                    removed_count += 1

        # Save updated file
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"    Removed {removed_count} clusters")
        print(f"    ✅ Updated {file_path.name}")

    print(f"\n✅ Cleanup complete! Removed clusters from all files.")
    print(f"💾 Backups saved with .backup extension")

def main():
    print("=" * 70)
    print("Cluster Movie Count Checker")
    print("=" * 70)
    print("\nThis script identifies clusters that contain screenshots from only")
    print("one movie and optionally removes them from all cluster JSON files.\n")

    single_movie_clusters = check_cluster_movies()

    if not single_movie_clusters:
        print("\n✅ All clusters have screenshots from 2 or more movies!")
        return

    print(f"\n" + "=" * 70)
    cluster_ids = [c['cluster_id'] for c in single_movie_clusters]
    print(f"Cluster IDs to remove: {cluster_ids}")

    response = input("\nDo you want to remove these clusters from data_clusters/*.json files? (y/n): ")

    if response.lower() == 'y':
        remove_clusters_from_files(cluster_ids)
    else:
        print("\n❌ No changes made.")

if __name__ == "__main__":
    main()
