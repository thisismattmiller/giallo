#!/usr/bin/env python3
import json
import sys
from pathlib import Path
import numpy as np
from sklearn.neighbors import NearestNeighbors
import re

def extract_movie_and_frame(filename):
    """Extract movie name and frame number from filename."""
    # Format: MovieName__0001.jpg
    match = re.match(r'^(.+)__(\d+)\.jpg$', filename)
    if match:
        return match.group(1), int(match.group(2))
    return None, None

def should_exclude(query_file, candidate_file, window=10):
    """
    Check if candidate should be excluded.
    Exclude if from same movie and within 10 frames of query.
    """
    query_movie, query_frame = extract_movie_and_frame(query_file)
    candidate_movie, candidate_frame = extract_movie_and_frame(candidate_file)

    if query_movie is None or candidate_movie is None:
        return False

    # Different movies are OK
    if query_movie != candidate_movie:
        return False

    # Same movie - check if within window
    frame_distance = abs(query_frame - candidate_frame)
    return frame_distance <= window

def load_all_embeddings(embeddings_dir):
    """Load all embeddings from data_embeddings directory."""
    all_embeddings = {}
    json_files = sorted(embeddings_dir.glob('*.json'))

    if not json_files:
        print(f"No JSON files found in {embeddings_dir}")
        return None, None

    print(f"Found {len(json_files)} embedding files")

    for json_file in json_files:
        print(f"Loading {json_file.name}...")
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            all_embeddings.update(data)

    print(f"\nTotal screenshots with embeddings: {len(all_embeddings)}")

    # Convert to arrays
    keys = list(all_embeddings.keys())
    embeddings_matrix = np.array([all_embeddings[k] for k in keys])

    print(f"Embeddings matrix shape: {embeddings_matrix.shape}")

    return keys, embeddings_matrix

def build_nn_index(embeddings_matrix, n_neighbors=100):
    """Build nearest neighbors index."""
    print(f"\nBuilding nearest neighbors index...")
    print(f"This may take a while for large datasets...")

    # Request more neighbors than needed so we can filter
    nn = NearestNeighbors(
        n_neighbors=min(n_neighbors, len(embeddings_matrix)),
        metric='cosine',
        algorithm='auto',
        n_jobs=-1
    )
    nn.fit(embeddings_matrix)

    print("Index built successfully!")
    return nn

def find_filtered_neighbors(nn, embeddings_matrix, keys, query_idx, target_count=20):
    """Find nearest neighbors excluding those from same movie within window."""
    query_key = keys[query_idx]

    # Get more neighbors than needed to account for filtering
    k = min(100, len(keys))
    distances, indices = nn.kneighbors([embeddings_matrix[query_idx]], n_neighbors=k)

    neighbors = []
    for dist, idx in zip(distances[0], indices[0]):
        if idx == query_idx:
            continue  # Skip self

        candidate_key = keys[idx]

        # Check if should exclude
        if should_exclude(query_key, candidate_key):
            continue

        neighbors.append({
            'screenshot': candidate_key,
            'distance': float(dist)
        })

        if len(neighbors) >= target_count:
            break

    return neighbors

def process_all_neighbors(nn, embeddings_matrix, keys, target_count=20):
    """Process all screenshots to find their nearest neighbors."""
    print(f"\nFinding {target_count} nearest neighbors for each screenshot...")
    print(f"Excluding screenshots from same movie within 10 frames...")

    all_neighbors = {}
    total = len(keys)

    for i, key in enumerate(keys):
        if (i + 1) % 1000 == 0 or i == 0:
            print(f"Processing {i + 1}/{total} ({100 * (i + 1) / total:.1f}%)...")

        neighbors = find_filtered_neighbors(nn, embeddings_matrix, keys, i, target_count)
        all_neighbors[key] = neighbors

    print(f"Completed! Processed {total} screenshots.")
    return all_neighbors

def organize_by_movie(all_neighbors):
    """Organize neighbors by source movie file."""
    by_movie = {}

    for key, neighbors in all_neighbors.items():
        movie, _ = extract_movie_and_frame(key)
        if movie:
            if movie not in by_movie:
                by_movie[movie] = {}
            by_movie[movie][key] = neighbors

    return by_movie

def save_neighbors(by_movie, output_dir):
    """Save neighbor data organized by movie."""
    print(f"\nSaving neighbor data to {output_dir}...")

    for movie_name, movie_neighbors in by_movie.items():
        output_file = output_dir / f"{movie_name}.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(movie_neighbors, f, indent=2, ensure_ascii=False)
            f.write('\n')

        print(f"Saved {len(movie_neighbors)} screenshots for {movie_name}")

    print(f"\nAll neighbor data saved!")

def main():
    # Set up paths
    embeddings_dir = Path(__file__).parent.parent / 'data_embeddings'
    output_dir = Path(__file__).parent.parent / 'data_nn'

    if not embeddings_dir.exists():
        print(f"Error: {embeddings_dir} not found")
        print("Please run add_embeddings.py first to generate embeddings")
        sys.exit(1)

    # Create output directory
    output_dir.mkdir(exist_ok=True)

    print(f"Loading embeddings from: {embeddings_dir}")
    print(f"Neighbors will be saved to: {output_dir}\n")

    # Load all embeddings
    keys, embeddings_matrix = load_all_embeddings(embeddings_dir)

    if keys is None:
        sys.exit(1)

    # Build nearest neighbors index
    nn = build_nn_index(embeddings_matrix, n_neighbors=100)

    # Find neighbors for all screenshots
    all_neighbors = process_all_neighbors(nn, embeddings_matrix, keys, target_count=20)

    # Organize by movie
    by_movie = organize_by_movie(all_neighbors)

    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"Total screenshots: {len(keys)}")
    print(f"Total movies: {len(by_movie)}")
    print(f"Neighbors per screenshot: 20 (excluding same-movie within 10 frames)")

    # Save results
    save_neighbors(by_movie, output_dir)

    print(f"\n{'='*80}")
    print("DONE!")
    print(f"{'='*80}")
    print(f"Output directory: {output_dir}")

if __name__ == "__main__":
    main()
