# Screenshot Browser

A Vue 3 application for browsing movie screenshots with tag and feature aggregation.

## Features

- **Two-column layout**: Movie list on the left, content on the right
- **Tag aggregation**: View all tags from screenshots with occurrence counts
- **Striking features**: Browse screenshots by striking visual features
- **Thumbnail grid**: Hover to enlarge thumbnails
- **Fast browsing**: Click through movies and tags to find specific scenes

## Running the App

```bash
npm install
npm run dev
```

This will start both the Express API server (port 3001) and Vite dev server (port 5173).

Open [http://localhost:5173](http://localhost:5173) in your browser.

## How to Use

1. Select a movie from the left sidebar
2. View aggregated tags and striking features with occurrence counts
3. Click on any tag or feature to see all matching screenshots
4. Hover over thumbnails to enlarge them
5. Click "Back" to return to the tag/feature list
