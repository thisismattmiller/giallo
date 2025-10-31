import express from 'express'
import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'
import { exec } from 'child_process'
import { promisify } from 'util'

const execPromise = promisify(exec)

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

const app = express()
app.use(express.json())

const PORT = 3002

const CLUSTERS_FILE = path.join(__dirname, '../../data_clusters/clusters.json')
const LABELS_FILE = path.join(__dirname, '../../data_clusters/cluster_llm_labels.json')
const CONTENT_CHECK_FILE = path.join(__dirname, '../../data_clusters/content_check.json')
const SCREENSHOTS_DIR = '/Volumes/NextGlum/giallo/screenshots'
const VIDEO_DIR = '/Volumes/NextGlum/giallo'
const SAVED_VIDEOS_DIR = '/Volumes/NextGlum/giallo/saved_videos'

// Function to load data
function loadData() {
  let clusters = {}
  let clusterLabels = {}
  let contentCheck = {}

  try {
    clusters = JSON.parse(fs.readFileSync(CLUSTERS_FILE, 'utf-8'))
    console.log(`Loaded ${Object.keys(clusters).length} clusters`)
  } catch (error) {
    console.error('Error loading clusters:', error)
  }

  try {
    const labelsData = JSON.parse(fs.readFileSync(LABELS_FILE, 'utf-8'))
    clusterLabels = labelsData.classifications || {}
    console.log(`Loaded ${Object.keys(clusterLabels).length} cluster labels`)
  } catch (error) {
    console.error('Error loading cluster labels:', error)
  }

  try {
    contentCheck = JSON.parse(fs.readFileSync(CONTENT_CHECK_FILE, 'utf-8'))
    console.log(`Loaded ${Object.keys(contentCheck).length} content check entries`)
  } catch (error) {
    console.error('Error loading content check:', error)
  }

  return { clusters, clusterLabels, contentCheck }
}

// Load initial data
let { clusters, clusterLabels, contentCheck } = loadData()

// Serve static HTML
app.get('/', (req, res) => {
  res.send(`
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Cluster Viewer</title>
  <style>
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }

    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
      background: #1a1a1a;
      color: #e0e0e0;
      padding: 20px;
    }

    h1 {
      text-align: center;
      margin-bottom: 30px;
      color: #fff;
    }

    .container {
      display: flex;
      gap: 20px;
      max-width: 2000px;
      margin: 0 auto;
    }

    .sidebar {
      width: 400px;
      flex-shrink: 0;
      background: #252525;
      border-radius: 8px;
      padding: 20px;
      max-height: calc(100vh - 120px);
      overflow-y: auto;
    }

    .sidebar h2 {
      margin-bottom: 20px;
      color: #fff;
      font-size: 18px;
    }

    .cluster-list {
      display: flex;
      flex-direction: column;
      gap: 10px;
    }

    .cluster-item {
      padding: 15px;
      background: #2a2a2a;
      border: 2px solid #333;
      border-radius: 4px;
      cursor: pointer;
      transition: all 0.2s;
    }

    .cluster-item:hover {
      background: #333;
      border-color: #4a90e2;
    }

    .cluster-item.active {
      background: #4a90e2;
      border-color: #4a90e2;
    }

    .cluster-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 5px;
    }

    .cluster-id {
      font-weight: 600;
      color: #4a90e2;
      font-size: 14px;
    }

    .cluster-item.active .cluster-id {
      color: #fff;
    }

    .cluster-count {
      background: #333;
      color: #aaa;
      padding: 2px 8px;
      border-radius: 12px;
      font-size: 12px;
      font-weight: 600;
    }

    .cluster-item.active .cluster-count {
      background: rgba(255, 255, 255, 0.2);
      color: #fff;
    }

    .cluster-label {
      color: #aaa;
      font-size: 13px;
      line-height: 1.4;
    }

    .cluster-item.active .cluster-label {
      color: #fff;
    }

    .content {
      flex: 1;
      min-width: 0;
    }

    .cluster-info {
      text-align: center;
      margin-bottom: 30px;
      padding: 20px;
      background: #252525;
      border-radius: 8px;
    }

    .cluster-info h2 {
      color: #4a90e2;
      margin-bottom: 10px;
      font-size: 24px;
    }

    .cluster-info .label {
      color: #fff;
      font-size: 16px;
      margin-bottom: 10px;
    }

    .cluster-info .count {
      color: #aaa;
      font-size: 14px;
      margin-bottom: 15px;
    }

    .compile-btn {
      background: #4a90e2;
      color: #fff;
      border: none;
      padding: 12px 24px;
      border-radius: 4px;
      font-size: 16px;
      font-weight: 600;
      cursor: pointer;
      margin-top: 10px;
      transition: background 0.2s;
    }

    .compile-btn:hover {
      background: #357abd;
    }

    .compile-btn:disabled {
      background: #555;
      cursor: not-allowed;
    }

    .compile-status {
      margin-top: 10px;
      font-size: 14px;
      color: #aaa;
    }

    .compile-status.success {
      color: #5cb85c;
    }

    .compile-status.error {
      color: #d9534f;
    }

    .screenshot-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
      gap: 15px;
    }

    .screenshot-item {
      position: relative;
      overflow: hidden;
      border-radius: 4px;
      background: #2a2a2a;
      transition: all 0.3s ease;
      cursor: pointer;
      border: 3px solid transparent;
    }

    .screenshot-item.selected {
      border-color: #4a90e2;
      box-shadow: 0 0 10px rgba(74, 144, 226, 0.5);
    }

    .screenshot-item.unselected {
      opacity: 0.4;
      border-color: #555;
    }

    .screenshot-item img {
      width: 100%;
      height: auto;
      display: block;
      transition: transform 0.3s ease;
    }

    .screenshot-item:hover {
      transform: scale(2);
      z-index: 100;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.8);
    }

    .screenshot-item.unselected:hover {
      opacity: 1;
    }

    .screenshot-item:hover img {
      transform: scale(1);
    }

    .screenshot-label {
      position: absolute;
      bottom: 0;
      left: 0;
      right: 0;
      background: rgba(0, 0, 0, 0.85);
      color: #fff;
      padding: 4px 8px;
      font-size: 10px;
      text-align: center;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .nudity-badge {
      position: absolute;
      top: 4px;
      right: 4px;
      background: rgba(217, 83, 79, 0.95);
      color: #fff;
      padding: 3px 6px;
      border-radius: 3px;
      font-size: 11px;
      font-weight: 600;
      z-index: 10;
      pointer-events: none;
    }

    .loading {
      text-align: center;
      padding: 40px;
      color: #aaa;
      font-size: 16px;
    }

    .no-data {
      text-align: center;
      padding: 40px;
      color: #aaa;
      font-size: 16px;
    }

    .welcome {
      text-align: center;
      padding: 60px 40px;
      color: #aaa;
      font-size: 16px;
    }

    .welcome h2 {
      color: #4a90e2;
      margin-bottom: 15px;
      font-size: 24px;
    }
  </style>
</head>
<body>
  <h1>Cluster Viewer</h1>

  <div class="container">
    <div class="sidebar">
      <h2>Clusters</h2>
      <div id="cluster-list" class="cluster-list"></div>
    </div>
    <div class="content">
      <div id="cluster-content">
        <div class="welcome">
          <h2>Welcome to Cluster Viewer</h2>
          <p>Select a cluster from the list to view screenshots</p>
        </div>
      </div>
    </div>
  </div>

  <script>
    let clusters = {};
    let labels = {};
    let contentCheck = {};
    let selectedCluster = null;
    let selectedScreenshots = new Set();
    let compiling = false;

    async function loadData() {
      try {
        const [clustersRes, labelsRes, contentCheckRes] = await Promise.all([
          fetch('/api/clusters'),
          fetch('/api/labels'),
          fetch('/api/content-check')
        ]);

        clusters = await clustersRes.json();
        labels = await labelsRes.json();
        contentCheck = await contentCheckRes.json();

        renderClusterList();
      } catch (error) {
        console.error('Error loading data:', error);
        document.getElementById('cluster-content').innerHTML = '<div class="no-data">Error loading data</div>';
      }
    }

    function renderClusterList() {
      // Sort by screenshot count (descending)
      const clusterIds = Object.keys(clusters).sort((a, b) => clusters[b].length - clusters[a].length);

      const html = clusterIds.map(clusterId => {
        const count = clusters[clusterId].length;
        const label = labels[clusterId]?.classification || 'No classification';

        // Check if any screenshot in this cluster has nudity
        const hasNudity = clusters[clusterId].some(filename => contentCheck[filename]?.nudity === true);
        const nudityIcon = hasNudity ? '<span style="color: #d9534f; margin-left: 6px; font-weight: bold;">18+</span>' : '';

        return \`
          <div class="cluster-item" onclick="selectCluster('\${clusterId}')" id="item-\${clusterId}">
            <div class="cluster-header">
              <span class="cluster-id">Cluster \${clusterId}\${nudityIcon}</span>
              <span class="cluster-count">\${count}</span>
            </div>
            <div class="cluster-label">\${label}</div>
          </div>
        \`;
      }).join('');

      document.getElementById('cluster-list').innerHTML = html;
    }

    function selectCluster(clusterId) {
      selectedCluster = clusterId;
      selectedScreenshots.clear();

      // Select all screenshots by default
      clusters[clusterId].forEach(filename => {
        selectedScreenshots.add(filename);
      });

      // Update active item
      document.querySelectorAll('.cluster-item').forEach(item => item.classList.remove('active'));
      document.getElementById(\`item-\${clusterId}\`).classList.add('active');

      renderCluster(clusterId);
    }

    function toggleScreenshot(filename) {
      if (selectedScreenshots.has(filename)) {
        selectedScreenshots.delete(filename);
      } else {
        selectedScreenshots.add(filename);
      }
      renderCluster(selectedCluster);
    }

    async function compileVideo() {
      if (compiling || selectedScreenshots.size === 0) return;

      compiling = true;
      const statusEl = document.getElementById('compile-status');
      const btnEl = document.getElementById('compile-btn');

      statusEl.textContent = \`Compiling video from \${selectedScreenshots.size} screenshots...\`;
      statusEl.className = 'compile-status';
      btnEl.disabled = true;

      try {
        const response = await fetch('/api/compile-video', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            screenshots: Array.from(selectedScreenshots),
            clusterId: selectedCluster
          })
        });

        const result = await response.json();

        if (result.success) {
          statusEl.textContent = \`✓ Successfully created \${result.filename} (\${result.clips} clips from \${result.screenshots} screenshots)\`;
          statusEl.className = 'compile-status success';
        } else {
          statusEl.textContent = \`✗ Error: \${result.error}\`;
          statusEl.className = 'compile-status error';
        }
      } catch (error) {
        statusEl.textContent = \`✗ Error: \${error.message}\`;
        statusEl.className = 'compile-status error';
      } finally {
        compiling = false;
        btnEl.disabled = false;
      }
    }

    function renderCluster(clusterId) {
      const screenshots = clusters[clusterId];
      const label = labels[clusterId]?.classification || 'No classification';

      const html = \`
        <div class="cluster-info">
          <h2>Cluster \${clusterId}</h2>
          <div class="label">\${label}</div>
          <div class="count">\${screenshots.length} screenshots | \${selectedScreenshots.size} selected</div>
          <button id="compile-btn" class="compile-btn" onclick="compileVideo()">
            Compile Selected to Video
          </button>
          <div id="compile-status" class="compile-status"></div>
        </div>
        <div class="screenshot-grid">
          \${screenshots.map(filename => {
            const videoName = filename.match(/^(.+)__\\d+\\.jpg$/)[1];
            const isSelected = selectedScreenshots.has(filename);
            const cssClass = isSelected ? 'selected' : 'unselected';
            const hasNudity = contentCheck[filename]?.nudity === true;
            const nudityBadge = hasNudity ? '<div class="nudity-badge">18+</div>' : '';
            return \`
              <div class="screenshot-item \${cssClass}" onclick="toggleScreenshot('\${filename}')">
                \${nudityBadge}
                <img src="/screenshots/\${videoName}/\${filename}" alt="\${filename}" />
                <div class="screenshot-label">\${filename}</div>
              </div>
            \`;
          }).join('')}
        </div>
      \`;

      document.getElementById('cluster-content').innerHTML = html;
    }

    loadData();
  </script>
</body>
</html>
  `)
})

// API endpoint to get clusters (reload on each request)
app.get('/api/clusters', (req, res) => {
  const data = loadData()
  clusters = data.clusters
  clusterLabels = data.clusterLabels
  contentCheck = data.contentCheck
  res.json(clusters)
})

// API endpoint to get labels (reload on each request)
app.get('/api/labels', (req, res) => {
  const data = loadData()
  clusters = data.clusters
  clusterLabels = data.clusterLabels
  contentCheck = data.contentCheck
  res.json(clusterLabels)
})

// API endpoint to get content check data
app.get('/api/content-check', (req, res) => {
  const data = loadData()
  contentCheck = data.contentCheck
  res.json(contentCheck)
})

// Serve screenshots from the mounted directory
app.use('/screenshots', express.static(SCREENSHOTS_DIR))

// API endpoint to compile selected screenshots into a video
app.post('/api/compile-video', async (req, res) => {
  try {
    const { screenshots, clusterId } = req.body

    if (!screenshots || screenshots.length === 0) {
      return res.status(400).json({ error: 'No screenshots selected' })
    }

    console.log(`Compiling video for cluster ${clusterId} with ${screenshots.length} screenshots`)

    // Parse screenshots and group by video
    const videoGroups = {}
    screenshots.forEach(filename => {
      const match = filename.match(/^(.+)__(\d+)\.jpg$/)
      if (match) {
        const videoName = match[1]
        const frameNumber = parseInt(match[2])
        const timestamp = frameNumber * 5 // Convert to seconds

        if (!videoGroups[videoName]) {
          videoGroups[videoName] = []
        }
        videoGroups[videoName].push({ filename, frameNumber, timestamp })
      }
    })

    // Sort video groups alphabetically
    const sortedVideoNames = Object.keys(videoGroups).sort()

    // Merge sequential screenshots and create clip specifications
    const clips = []
    for (const videoName of sortedVideoNames) {
      const frames = videoGroups[videoName].sort((a, b) => a.frameNumber - b.frameNumber)

      let currentClip = null
      for (const frame of frames) {
        if (!currentClip) {
          // Start new clip
          currentClip = {
            videoName,
            startTime: Math.max(0, frame.timestamp - 5),
            endTime: frame.timestamp + 5,
            firstFrame: frame.frameNumber,
            lastFrame: frame.frameNumber
          }
        } else {
          // Check if this frame is adjacent to the last frame in current clip
          if (frame.frameNumber === currentClip.lastFrame + 1) {
            // Extend current clip
            currentClip.endTime = frame.timestamp + 5
            currentClip.lastFrame = frame.frameNumber
          } else {
            // Save current clip and start new one
            clips.push(currentClip)
            currentClip = {
              videoName,
              startTime: Math.max(0, frame.timestamp - 5),
              endTime: frame.timestamp + 5,
              firstFrame: frame.frameNumber,
              lastFrame: frame.frameNumber
            }
          }
        }
      }
      if (currentClip) {
        clips.push(currentClip)
      }
    }

    console.log(`Created ${clips.length} clips from ${screenshots.length} screenshots`)

    // Create temp directory for clips
    const tempDir = path.join(__dirname, 'temp-clips')
    if (!fs.existsSync(tempDir)) {
      fs.mkdirSync(tempDir, { recursive: true })
    }

    // Extract each clip
    const clipFiles = []
    for (let i = 0; i < clips.length; i++) {
      const clip = clips[i]

      // Find the actual video file (check for common extensions)
      let videoPath = null
      const extensions = ['.mkv', '.mp4', '.avi', '.mov', '']
      for (const ext of extensions) {
        const testPath = path.join(VIDEO_DIR, clip.videoName + ext)
        if (fs.existsSync(testPath)) {
          videoPath = testPath
          break
        }
      }

      if (!videoPath) {
        console.error(`Video file not found for: ${clip.videoName}`)
        continue
      }

      const clipPath = path.join(tempDir, `clip_${i.toString().padStart(4, '0')}.mp4`)
      const duration = clip.endTime - clip.startTime

      console.log(`Extracting clip ${i + 1}/${clips.length}: ${path.basename(videoPath)} from ${clip.startTime}s to ${clip.endTime}s (${duration}s)`)

      const ffmpegCmd = `ffmpeg -y -ss ${clip.startTime} -i "${videoPath}" -t ${duration} -c:v libx264 -crf 18 -preset medium -pix_fmt yuv420p -c:a aac -b:a 192k "${clipPath}"`

      try {
        await execPromise(ffmpegCmd)
        clipFiles.push(clipPath)
      } catch (error) {
        console.error(`Failed to extract clip ${i}:`, error.message)
      }
    }

    if (clipFiles.length === 0) {
      return res.status(500).json({ error: 'Failed to extract any clips' })
    }

    // Ensure saved videos directory exists
    if (!fs.existsSync(SAVED_VIDEOS_DIR)) {
      fs.mkdirSync(SAVED_VIDEOS_DIR, { recursive: true })
    }

    // Stitch clips together
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5)
    const outputFilename = `cluster_${clusterId}_${timestamp}.mp4`
    const outputPath = path.join(SAVED_VIDEOS_DIR, outputFilename)

    console.log(`Stitching ${clipFiles.length} clips into ${outputFilename}`)

    // Use filter_complex to properly handle clips with different properties
    // This normalizes everything to the same resolution, frame rate, and audio settings
    let filterComplex = ''
    let concatInputs = ''

    for (let i = 0; i < clipFiles.length; i++) {
      filterComplex += `[${i}:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=24[v${i}];`
      filterComplex += `[${i}:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo[a${i}];`
      concatInputs += `[v${i}][a${i}]`
    }

    filterComplex += `${concatInputs}concat=n=${clipFiles.length}:v=1:a=1[outv][outa]`

    const inputs = clipFiles.map(f => `-i "${f}"`).join(' ')
    const concatCmd = `ffmpeg -y ${inputs} -filter_complex "${filterComplex}" -map "[outv]" -map "[outa]" -c:v libx264 -crf 18 -preset medium -pix_fmt yuv420p -c:a aac -b:a 192k "${outputPath}"`

    try {
      await execPromise(concatCmd)

      // Clean up temp files
      clipFiles.forEach(f => {
        try { fs.unlinkSync(f) } catch (e) {}
      })

      console.log(`Successfully created video: ${outputFilename}`)

      // Generate metadata files with timestamps
      const formatTime = (seconds) => {
        const mins = Math.floor(seconds / 60)
        const secs = Math.floor(seconds % 60)
        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
      }

      let currentTime = 0
      const metadataJson = []
      const metadataText = []

      for (const clip of clips) {
        const duration = clip.endTime - clip.startTime
        const startFormatted = formatTime(currentTime)
        const endFormatted = formatTime(currentTime + duration)
        const sourceStartFormatted = formatTime(clip.startTime)
        const sourceEndFormatted = formatTime(clip.endTime)

        metadataJson.push({
          timeline: `${startFormatted}-${endFormatted}`,
          movie: clip.videoName,
          sourceTimestamp: `${sourceStartFormatted}-${sourceEndFormatted}`
        })

        metadataText.push(`${startFormatted}-${endFormatted} ${clip.videoName} (${sourceStartFormatted}-${sourceEndFormatted})`)

        currentTime += duration
      }

      // Write JSON file
      const jsonPath = outputPath.replace('.mp4', '.json')
      fs.writeFileSync(jsonPath, JSON.stringify(metadataJson, null, 2))

      // Write text file
      const txtPath = outputPath.replace('.mp4', '.txt')
      fs.writeFileSync(txtPath, metadataText.join('\n'))

      console.log(`Created metadata files: ${path.basename(jsonPath)}, ${path.basename(txtPath)}`)

      res.json({
        success: true,
        filename: outputFilename,
        path: outputPath,
        clips: clips.length,
        screenshots: screenshots.length
      })
    } catch (error) {
      console.error('Failed to stitch clips:', error.message)
      res.status(500).json({ error: 'Failed to stitch clips', details: error.message })
    }

  } catch (error) {
    console.error('Error compiling video:', error)
    res.status(500).json({ error: 'Failed to compile video', details: error.message })
  }
})

app.listen(PORT, () => {
  console.log(`Cluster viewer running on http://localhost:${PORT}`)
})
