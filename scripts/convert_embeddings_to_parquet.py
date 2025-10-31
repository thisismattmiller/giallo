#!/usr/bin/env python3
"""
Convert embedding JSON files to compressed NumPy format for better compression.

Each JSON file contains a dict mapping screenshot filenames to 3072-dimensional vectors.
Output is a .npz file (compressed NumPy archive) with two arrays:
- 'filenames': array of screenshot filenames
- 'embeddings': 2D array of shape (N, 3072) containing the vectors
"""

import json
import glob
import os
import numpy as np
from pathlib import Path


def convert_json_to_npz(json_path):
    """Convert a single JSON embedding file to compressed NumPy format."""
    print(f"Processing: {json_path}")

    # Load JSON data
    with open(json_path, 'r') as f:
        data = json.load(f)

    # Extract filenames and embeddings
    filenames = list(data.keys())
    embeddings = np.array([data[fn] for fn in filenames], dtype=np.float32)

    # Generate output path (same directory, .npz extension)
    npz_path = json_path.replace('.json', '.npz')

    # Save as compressed NumPy archive
    # Using savez_compressed which uses zlib compression (similar to gzip)
    np.savez_compressed(
        npz_path,
        filenames=filenames,
        embeddings=embeddings
    )

    # Get file sizes for comparison
    json_size = os.path.getsize(json_path) / (1024 * 1024)  # MB
    npz_size = os.path.getsize(npz_path) / (1024 * 1024)  # MB
    compression_ratio = (1 - npz_size / json_size) * 100

    print(f"  ✓ Created: {npz_path}")
    print(f"  JSON size: {json_size:.2f} MB")
    print(f"  NPZ size: {npz_size:.2f} MB")
    print(f"  Compression: {compression_ratio:.1f}%")
    print(f"  Shape: {embeddings.shape}")
    print()

    return {
        'json_path': json_path,
        'npz_path': npz_path,
        'json_size_mb': json_size,
        'npz_size_mb': npz_size,
        'compression_ratio': compression_ratio,
        'num_screenshots': len(filenames)
    }


def main():
    # Find all JSON files in data_embeddings directory
    embeddings_dir = Path(__file__).parent.parent / 'data_embeddings'
    json_files = sorted(glob.glob(str(embeddings_dir / '*.json')))

    if not json_files:
        print(f"No JSON files found in {embeddings_dir}")
        return

    print(f"Found {len(json_files)} JSON files to convert\n")

    # Convert each file
    results = []
    for json_file in json_files:
        try:
            result = convert_json_to_npz(json_file)
            results.append(result)
        except Exception as e:
            print(f"Error processing {json_file}: {e}\n")

    # Print summary
    if results:
        total_json_size = sum(r['json_size_mb'] for r in results)
        total_npz_size = sum(r['npz_size_mb'] for r in results)
        total_screenshots = sum(r['num_screenshots'] for r in results)
        overall_compression = (1 - total_npz_size / total_json_size) * 100

        print("=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print(f"Files converted: {len(results)}")
        print(f"Total screenshots: {total_screenshots}")
        print(f"Total JSON size: {total_json_size:.2f} MB")
        print(f"Total NPZ size: {total_npz_size:.2f} MB")
        print(f"Overall compression: {overall_compression:.1f}%")
        print(f"Space saved: {total_json_size - total_npz_size:.2f} MB")


if __name__ == '__main__':
    main()
