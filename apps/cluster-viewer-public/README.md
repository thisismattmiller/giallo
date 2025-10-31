# Giallo Film Cluster Viewer - Public Version

A static website showcasing visual patterns and themes in Italian Giallo horror cinema from the 1970s.

## About

This visualization explores recurring motifs across classic Giallo films using machine learning. Screenshots have been analyzed with a Vision Language Model (VLM) and clustered using HDBSCAN to reveal common patterns in:

- Cinematography and composition
- Color palettes and lighting
- Subject matter and themes
- Visual striking elements

## Structure

```
cluster-viewer-public/
├── index.html              # Main viewer interface
├── data/
│   └── clusters_data.json  # Cluster metadata and labels
├── images/                 # All screenshot images
│   └── *.jpg              # Individual screenshots
└── README.md              # This file
```

## Building

To rebuild the public version from source data:

```bash
python3 scripts/build_public_cluster_viewer.py
```

This script:
1. Filters out clusters containing mature content
2. Copies safe screenshots to the public directory
3. Generates the combined data JSON file

## Deployment

This is a static site that can be deployed to:
- GitHub Pages
- Netlify
- Vercel
- Any static hosting service

Simply upload the contents of `apps/cluster-viewer-public/` to your hosting provider.

### GitHub Pages

1. Create a new repository
2. Copy the contents of this directory to the repository
3. Enable GitHub Pages in repository settings
4. Set source to `main` branch, root directory

## Features

- **Browse Clusters**: Explore visual themes sorted by frequency
- **View Details**: Click any cluster to see all screenshots
- **LLM Classifications**: Each cluster includes AI-generated descriptions
- **Image Preview**: Hover over screenshots for enlarged view
- **Responsive Design**: Works on desktop and mobile devices
- **Lazy Loading**: Images load on-demand for performance

## Content Filtering

This public version excludes:
- Clusters flagged with mature content
- Any screenshots containing nudity
- Approximately 30-40% of the original dataset

The full, unfiltered dataset is available in the private version for research purposes.

## Technical Details

- **Pure Static HTML/JS**: No server required, no dependencies
- **VLM Analysis**: Qwen/Qwen2.5-VL-72B-Instruct
- **Clustering**: HDBSCAN algorithm
- **Screenshot Format**: JPEG images at original quality
- **Data Format**: Single consolidated JSON file

## License

Screenshots are from public domain or fair use for educational/archival purposes.
Analysis and clustering methodology is original work.

## Credits

Built with vision language models and machine learning clustering algorithms.
