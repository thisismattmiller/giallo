#!/usr/bin/env python3
import json
import sys
from pathlib import Path
import numpy as np
import hdbscan
from collections import defaultdict

def load_all_embeddings(embeddings_dir):
    """Load all embeddings from data_embeddings directory."""
    print("=" * 80)
    print("STEP 1: Loading embeddings")
    print("=" * 80)

    all_embeddings = {}
    json_files = sorted(embeddings_dir.glob('*.json'))

    if not json_files:
        print(f"ERROR: No JSON files found in {embeddings_dir}")
        return None, None

    print(f"Found {len(json_files)} embedding files\n")

    for i, json_file in enumerate(json_files, 1):
        print(f"[{i}/{len(json_files)}] Loading {json_file.name}...", end=" ", flush=True)
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            all_embeddings.update(data)
        print(f"({len(data)} screenshots)")

    print(f"\n✓ Total screenshots with embeddings: {len(all_embeddings)}")

    print("\nConverting to numpy array...", flush=True)
    keys = list(all_embeddings.keys())
    embeddings_matrix = np.array([all_embeddings[k] for k in keys])

    print(f"✓ Embeddings matrix shape: {embeddings_matrix.shape}")
    print(f"  - Number of samples: {embeddings_matrix.shape[0]}")
    print(f"  - Embedding dimensions: {embeddings_matrix.shape[1]}")
    print(f"  - Memory size: {embeddings_matrix.nbytes / (1024**2):.1f} MB")

    return keys, embeddings_matrix

def perform_clustering(embeddings_matrix, min_cluster_size=5, min_samples=3):
    """Perform HDBSCAN clustering on embeddings."""
    print("\n" + "=" * 80)
    print("STEP 2: Performing HDBSCAN clustering")
    print("=" * 80)
    print(f"Parameters:")
    print(f"  - min_cluster_size: {min_cluster_size}")
    print(f"  - min_samples: {min_samples}")
    print(f"  - metric: euclidean")
    print(f"  - cluster_selection_method: eom")

    print(f"\nCreating HDBSCAN clusterer object...", flush=True)
    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=min_cluster_size,
        min_samples=min_samples,
        metric='euclidean',
        cluster_selection_method='eom'
    )
    print("✓ Clusterer created")

    print(f"\nRunning fit_predict on {embeddings_matrix.shape[0]} samples...")
    print("NOTE: This step can take a VERY long time for large datasets (potentially hours)")
    print("      The algorithm has O(n²) complexity in the worst case")
    print("      Please be patient...\n", flush=True)

    import time
    start = time.time()

    # Try to give some indication of progress by checking if verbose works
    try:
        print("Starting clustering computation...", flush=True)
        cluster_labels = clusterer.fit_predict(embeddings_matrix)
        elapsed = time.time() - start
        print(f"\n✓ Clustering completed in {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
    except Exception as e:
        print(f"\nERROR during clustering: {e}")
        raise

    print("\nAnalyzing results...", flush=True)
    # Get cluster statistics
    unique_labels = np.unique(cluster_labels)
    n_clusters = len(unique_labels[unique_labels >= 0])  # Exclude noise (-1)
    n_noise = np.sum(cluster_labels == -1)

    print(f"✓ Clustering complete!")
    print(f"  - Number of clusters: {n_clusters}")
    print(f"  - Number of noise points: {n_noise}")
    print(f"  - Percentage clustered: {100 * (len(cluster_labels) - n_noise) / len(cluster_labels):.1f}%")

    return cluster_labels, clusterer

def analyze_clusters(keys, cluster_labels):
    """Analyze and display cluster information."""
    print("\n" + "=" * 80)
    print("STEP 3: Analyzing cluster assignments")
    print("=" * 80)

    print("Building cluster dictionary...", flush=True)
    clusters = defaultdict(list)

    for key, label in zip(keys, cluster_labels):
        clusters[int(label)].append(key)

    print(f"✓ Created {len(clusters)} clusters")

    # Sort by cluster size
    print("Sorting clusters by size...", flush=True)
    sorted_clusters = sorted(clusters.items(), key=lambda x: len(x[1]), reverse=True)

    print(f"\n{'='*80}")
    print("CLUSTER SIZES (Top 20)")
    print(f"{'='*80}")

    for label, members in sorted_clusters[:20]:  # Show top 20 clusters
        if label == -1:
            print(f"Noise: {len(members)} screenshots")
        else:
            print(f"Cluster {label}: {len(members)} screenshots")

    if len(sorted_clusters) > 20:
        remaining = sum(len(members) for label, members in sorted_clusters[20:] if label != -1)
        print(f"... and {len(sorted_clusters) - 20} more clusters with {remaining} total screenshots")

    return clusters

def save_clusters(clusters, output_file):
    """Save cluster assignments to JSON file."""
    print("\n" + "=" * 80)
    print("STEP 4: Saving cluster assignments")
    print("=" * 80)

    print(f"Converting to serializable format...", flush=True)
    # Convert to serializable format
    output_data = {
        str(label): members for label, members in clusters.items()
    }

    print(f"Writing to {output_file}...", flush=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
        f.write('\n')

    print(f"✓ Cluster assignments saved to: {output_file}")

def save_reverse_index(keys, cluster_labels, output_file):
    """Save a reverse index mapping each screenshot to its cluster."""
    print(f"\nCreating reverse index...", flush=True)
    reverse_index = {}

    for key, label in zip(keys, cluster_labels):
        reverse_index[key] = int(label)

    print(f"Writing to {output_file}...", flush=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(reverse_index, f, indent=2, ensure_ascii=False)
        f.write('\n')

    print(f"✓ Reverse index saved to: {output_file}")

def main():
    print("\n" + "=" * 80)
    print("HDBSCAN CLUSTERING SCRIPT")
    print("=" * 80)

    # Set up paths
    embeddings_dir = Path(__file__).parent.parent / 'data_embeddings'
    output_dir = Path(__file__).parent.parent / 'clusters'

    print(f"\nConfiguration:")
    print(f"  - Embeddings directory: {embeddings_dir}")
    print(f"  - Output directory: {output_dir}")

    if not embeddings_dir.exists():
        print(f"\nERROR: {embeddings_dir} not found")
        print("Please run add_embeddings.py first to generate embeddings")
        sys.exit(1)

    # Create output directory
    print(f"\nCreating output directory...", flush=True)
    output_dir.mkdir(exist_ok=True)
    print(f"✓ Output directory ready")

    # Load all embeddings
    keys, embeddings_matrix = load_all_embeddings(embeddings_dir)

    if keys is None:
        print("\nERROR: Failed to load embeddings")
        sys.exit(1)

    # Perform clustering
    cluster_labels, clusterer = perform_clustering(
        embeddings_matrix,
        min_cluster_size=10,
        min_samples=3
    )

    # Analyze clusters
    clusters = analyze_clusters(keys, cluster_labels)

    # Save results
    clusters_file = output_dir / 'clusters.json'
    save_clusters(clusters, clusters_file)

    reverse_index_file = output_dir / 'screenshot_to_cluster.json'
    save_reverse_index(keys, cluster_labels, reverse_index_file)

    print(f"\n{'='*80}")
    print("✓ ALL DONE!")
    print(f"{'='*80}")
    print(f"Total screenshots: {len(keys)}")
    print(f"Total clusters: {len([label for label in clusters.keys() if label >= 0])}")
    print(f"\nOutput files:")
    print(f"  - {clusters_file}")
    print(f"  - {reverse_index_file}")
    print("\nClustering complete! You can now use these clusters in your analysis.")
    print("=" * 80)

if __name__ == "__main__":
    main()
