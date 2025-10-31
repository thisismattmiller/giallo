# Embeddings Data

This directory contains visual embeddings for all screenshots from the Giallo film collection. Each file represents embeddings for one film.

## File Format

**Format:** Compressed NumPy archive (`.npz`)

Each `.npz` file contains two arrays:
- `filenames`: Array of screenshot filenames (strings)
- `embeddings`: 2D NumPy array of shape `(N, 3072)` containing float32 embeddings

## Why NPZ?

The embeddings were originally stored as JSON but converted to compressed NumPy format for better compression:
- **JSON**: ~53-62 MB per file
- **NPZ (compressed)**: ~15-18 MB per file (~72% compression)

This provides similar compression to gzipped JSON but with faster loading and direct NumPy array access.

## Usage

### Load Embeddings

```python
import numpy as np

# Load the data
data = np.load('A.Bay.of.Blood.1971.mkv.npz')

# Access filenames and embeddings
filenames = data['filenames']  # Array of screenshot names
embeddings = data['embeddings']  # Shape: (N, 3072)

# Example: Get embedding for a specific screenshot
idx = 0
screenshot_name = filenames[idx]
embedding_vector = embeddings[idx]  # Shape: (3072,)

print(f"Screenshot: {screenshot_name}")
print(f"Embedding shape: {embedding_vector.shape}")
print(f"Total screenshots: {len(filenames)}")
```

### Convert Back to Dictionary

```python
import numpy as np

# Load and convert to dict format (like original JSON)
data = np.load('A.Bay.of.Blood.1971.mkv.npz')
embeddings_dict = {
    filename: embedding.tolist()
    for filename, embedding in zip(data['filenames'], data['embeddings'])
}
```

### Search for Similar Screenshots

```python
import numpy as np
from numpy.linalg import norm

def cosine_similarity(a, b):
    return np.dot(a, b) / (norm(a) * norm(b))

# Load embeddings
data = np.load('A.Bay.of.Blood.1971.mkv.npz')
filenames = data['filenames']
embeddings = data['embeddings']

# Find most similar screenshots to index 0
query_embedding = embeddings[0]
similarities = np.array([
    cosine_similarity(query_embedding, emb)
    for emb in embeddings
])

# Get top 5 most similar (excluding self)
top_indices = np.argsort(similarities)[-6:-1][::-1]
print(f"Query: {filenames[0]}")
print("\nMost similar:")
for idx in top_indices:
    print(f"  {filenames[idx]}: {similarities[idx]:.3f}")
```

### Batch Loading Multiple Films

```python
import numpy as np
from pathlib import Path
import glob

# Load all embeddings
embeddings_dir = Path('data_embeddings')
all_filenames = []
all_embeddings = []

for npz_file in sorted(glob.glob(str(embeddings_dir / '*.npz'))):
    data = np.load(npz_file)
    all_filenames.extend(data['filenames'])
    all_embeddings.append(data['embeddings'])

# Combine into single array
combined_embeddings = np.vstack(all_embeddings)
print(f"Total screenshots across all films: {len(all_filenames)}")
print(f"Combined embeddings shape: {combined_embeddings.shape}")
```

## Converting from JSON

If you have JSON embedding files, convert them using:

```bash
python3 scripts/convert_embeddings_to_parquet.py
```

This will create `.npz` files alongside the JSON files in the same directory.

## File Listing

To see what files are available:

```bash
ls -lh data_embeddings/*.npz
```

## Technical Details

- **Embedding dimension**: 3072 (OpenAI CLIP ViT-L/14 or similar model)
- **Data type**: `float32` (4 bytes per value)
- **Compression**: zlib (Python's `np.savez_compressed`)
- **Uncompressed size per file**: ~N × 3072 × 4 bytes (e.g., 4000 screenshots = ~49 MB uncompressed)
- **Compressed size**: ~70-75% reduction from JSON, ~65-70% reduction from uncompressed

## Memory Considerations

Loading all embeddings at once requires significant memory:
- Single film: ~50-150 MB uncompressed in memory
- All films: Estimate ~2-5 GB total (depending on number of films)

For large-scale operations, consider loading embeddings on-demand or using memory-mapped arrays.
