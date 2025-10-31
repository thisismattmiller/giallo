# Giallo Film Visual Analysis

Blog Post: https://thisismattmiller.com/post/giallo/

Apps:

Cluster Viewer: https://thisismattmiller.github.io/giallo/apps/cluster-viewer-public/

Timeline Ploter: https://thisismattmiller.github.io/giallo/apps/timeline/




## Project Structure

### Scripts ([`scripts/`](scripts/))

Pipeline scripts for processing and analyzing the film collection:

| Script | Description |
|--------|-------------|
| [`prepare_dir.py`](scripts/prepare_dir.py) | Extracts screenshots from video files using FFmpeg (1 frame every 5 seconds) |
| [`send_images_to_llm.py`](scripts/send_images_to_llm.py) | Sends screenshots to VLM API to generate semantic descriptions |
| [`add_embeddings.py`](scripts/add_embeddings.py) | Generates text embeddings from screenshot descriptions using Google's Gemini API |
| [`build_nearest_neighbors.py`](scripts/build_nearest_neighbors.py) | Builds k-nearest neighbors index for finding similar screenshots |
| [`cluster_hdbscan.py`](scripts/cluster_hdbscan.py) | Clusters screenshots using HDBSCAN algorithm based on embeddings |
| [`extract_cluster_desc.py`](scripts/extract_cluster_desc.py) | Extracts descriptions for each cluster's screenshots |
| [`classify_clusters.py`](scripts/classify_clusters.py) | Uses LLM to generate semantic labels for each cluster |
| [`check_for_all_black_clusters.py`](scripts/check_for_all_black_clusters.py) | Identifies and filters clusters containing only dark/black screenshots |
| [`build_timeline_data.py`](scripts/build_timeline_data.py) | Generates timeline data showing cluster distribution across film runtimes |
| [`check_for_cluster_movie_count.py`](scripts/check_for_cluster_movie_count.py) | Analyzes how many films are represented in each cluster |
| [`check_cluster_screenshots_for_content.py`](scripts/check_cluster_screenshots_for_content.py) | Uses VLM to flag screenshots containing mature/sensitive content (nudity, violence) |
| [`description_analysis.py`](scripts/description_analysis.py) | Analyzes duplicate descriptions across the dataset |
| [`build_public_cluster_viewer.py`](scripts/build_public_cluster_viewer.py) | Generates static public version of cluster viewer with content filtering |
| [`convert_embeddings_to_parquet.py`](scripts/convert_embeddings_to_parquet.py) | Converts embedding JSON files to compressed NumPy format for better compression (~72% reduction) |

### Data Directories

| Directory | Description |
|-----------|-------------|
| [`data/`](data/) | VLM-generated descriptions and tags for each screenshot (JSON files per film) |
| [`data_embeddings/`](data_embeddings/) | Visual embeddings as compressed NumPy archives (.npz format, ~15-18MB per film). [See README](data_embeddings/README.md) for usage |
| [`data_nn/`](data_nn/) | Nearest neighbor indices for similarity search |
| [`data_clusters/`](data_clusters/) | Clustering results, cluster descriptions, and LLM-generated semantic labels |

Key files in `data_clusters/`:
- `clusters.json` - HDBSCAN clustering assignments
- `cluster_llm_labels.json` - Semantic classifications for each cluster
- `cluster_text_list.txt` - Human-readable list of all clusters sorted by size
- `content_check.json` - Nudity/violence flags for content filtering

### Applications ([`apps/`](apps/))

Interactive web-based visualization tools:

| App | Description |
|-----|-------------|
| [`cluster-viewer/`](apps/cluster-viewer/) | Full-featured cluster exploration tool with video compilation and content warnings |
| [`cluster-viewer-public/`](apps/cluster-viewer-public/) | Static GitHub Pages version with mature content filtered out, images hosted on S3 |
| [`timeline/`](apps/timeline/) | Visualize cluster distribution across movie runtime percentages |
| [`screenshot-browser/`](apps/screenshot-browser/) | Browse all screenshots with descriptions and embeddings |
| [`dupe-descriptions/`](apps/dupe-descriptions/) | Analyze duplicate VLM descriptions across the dataset |

## Pipeline Workflow

```
1. Extract Screenshots
   prepare_dir.py → screenshots/*.jpg

2. Generate Descriptions
   send_images_to_llm.py → data/*.json

3. Create Embeddings
   add_embeddings.py → data_embeddings/*.npz

4. Build Similarity Index
   build_nearest_neighbors.py → data_nn/*

5. Cluster Images
   cluster_hdbscan.py → data_clusters/clusters.json

6. Classify Clusters
   classify_clusters.py → data_clusters/cluster_llm_labels.json

7. Content Filtering
   check_cluster_screenshots_for_content.py → data_clusters/content_check.json

8. Build Visualizations
   build_timeline_data.py → apps/timeline/timeline_data.json
   build_public_cluster_viewer.py → apps/cluster-viewer-public/
```

## Installation

### Requirements

- Python 3.8+
- FFmpeg (for video processing)
- Node.js (for cluster viewer app)

### Python Dependencies

```bash
pip install numpy pandas scikit-learn hdbscan google-genai openai pyarrow
```

### API Keys

Required environment variables:
```bash
export NEBIUS_API_KEY="your-nebius-api-key"  # For VLM descriptions
export GEMINI_API_KEY="your-gemini-api-key"  # For embeddings and classifications
```

## Usage

### Running the Full Pipeline

```bash
# 1. Extract screenshots (requires video files)
python3 scripts/prepare_dir.py

# 2. Generate VLM descriptions
python3 scripts/send_images_to_llm.py

# 3. Generate embeddings
python3 scripts/add_embeddings.py

# 4. Cluster screenshots
python3 scripts/cluster_hdbscan.py

# 5. Classify clusters
python3 scripts/classify_clusters.py

# 6. Check for mature content
python3 scripts/check_cluster_screenshots_for_content.py

# 7. Build timeline data
python3 scripts/build_timeline_data.py
```

### Running the Cluster Viewer

```bash
cd apps/cluster-viewer
npm install
npm start
# Open http://localhost:3000
```

### Using Embeddings

See [`data_embeddings/README.md`](data_embeddings/README.md) for detailed examples of loading and working with embeddings.

## Dataset Statistics

- **Films Analyzed**: 50+ classic Italian Giallo films (1970-1979)
- **Total Screenshots**: ~8,831 clustered screenshots
- **Clusters Identified**: 331 thematic clusters
- **Largest Cluster**: 333 screenshots (fearful women's faces in shadows)
- **Embedding Dimension**: 3,072 (Google Gemini text embeddings)


## Content Warning

This project analyzes Italian Giallo horror films from the 1970s. The source material contains:
- Violence and blood
- Suspenseful and disturbing imagery
- Mature themes

The public viewer filters out explicit content, but the full dataset contains screenshots that may be disturbing.

## License

This repository contains analytical tools and metadata only. The source films are copyrighted works used for academic/analytical purposes under fair use.

