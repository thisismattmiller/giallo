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

const PORT = 3001

const DATA_DIR = path.join(__dirname, '../../data')
const DATA_NN_DIR = path.join(__dirname, '../../data_nn')
const SCREENSHOTS_DIR = '/Volumes/NextGlum/giallo/screenshots'
const VIDEO_DIR = '/Volumes/NextGlum/giallo'
const TEMP_DIR = path.join(__dirname, 'temp-frames')
const SAVED_VIDEOS_DIR = '/Volumes/NextGlum/giallo/saved_videos'
const TAGS_FILE = path.join(__dirname, 'movie-tags.json')

// Create temp directory if it doesn't exist
if (!fs.existsSync(TEMP_DIR)) {
  fs.mkdirSync(TEMP_DIR, { recursive: true })
}

// Create saved videos directory if it doesn't exist
if (!fs.existsSync(SAVED_VIDEOS_DIR)) {
  fs.mkdirSync(SAVED_VIDEOS_DIR, { recursive: true })
}

// Load tags from file
let movieTags = {}
if (fs.existsSync(TAGS_FILE)) {
  try {
    movieTags = JSON.parse(fs.readFileSync(TAGS_FILE, 'utf-8'))
  } catch (error) {
    console.error('Error loading tags file:', error)
    movieTags = {}
  }
}

// Save tags to file
function saveTags() {
  try {
    fs.writeFileSync(TAGS_FILE, JSON.stringify(movieTags, null, 2))
  } catch (error) {
    console.error('Error saving tags file:', error)
  }
}

// Serve static files from screenshots directory
app.use('/screenshots', express.static(SCREENSHOTS_DIR))

// Serve temp frames
app.use('/temp-frames', express.static(TEMP_DIR))

// Get list of all movies
app.get('/api/movies', (req, res) => {
  try {
    const files = fs.readdirSync(DATA_DIR)
    const movies = files
      .filter(f => f.endsWith('.json'))
      .map(f => f.replace('.json', ''))
    res.json(movies)
  } catch (error) {
    console.error('Error reading movies:', error)
    res.status(500).json({ error: 'Failed to load movies' })
  }
})

// Get aggregated data from all movies
app.get('/api/aggregate', (req, res) => {
  try {
    const files = fs.readdirSync(DATA_DIR)
    const jsonFiles = files.filter(f => f.endsWith('.json'))

    const aggregatedTags = {}
    const aggregatedStriking = {}
    const screenshotIndex = {} // Maps tag/striking -> array of screenshot objects with movie info

    jsonFiles.forEach(file => {
      const movieName = file.replace('.json', '')
      const filePath = path.join(DATA_DIR, file)
      const data = JSON.parse(fs.readFileSync(filePath, 'utf-8'))

      Object.values(data).forEach(screenshot => {
        // Process tags
        if (screenshot.tags && Array.isArray(screenshot.tags)) {
          screenshot.tags.forEach(tag => {
            aggregatedTags[tag] = (aggregatedTags[tag] || 0) + 1

            if (!screenshotIndex[`tag:${tag}`]) {
              screenshotIndex[`tag:${tag}`] = []
            }
            screenshotIndex[`tag:${tag}`].push({
              ...screenshot,
              movieName
            })
          })
        }

        // Process striking features
        if (screenshot.striking && Array.isArray(screenshot.striking)) {
          screenshot.striking.forEach(striking => {
            aggregatedStriking[striking] = (aggregatedStriking[striking] || 0) + 1

            if (!screenshotIndex[`striking:${striking}`]) {
              screenshotIndex[`striking:${striking}`] = []
            }
            screenshotIndex[`striking:${striking}`].push({
              ...screenshot,
              movieName
            })
          })
        }
      })
    })

    // Sort by count descending
    const sortedTags = Object.fromEntries(
      Object.entries(aggregatedTags).sort((a, b) => b[1] - a[1])
    )
    const sortedStriking = Object.fromEntries(
      Object.entries(aggregatedStriking).sort((a, b) => b[1] - a[1])
    )

    res.json({
      tags: sortedTags,
      striking: sortedStriking,
      screenshotIndex
    })
  } catch (error) {
    console.error('Error aggregating data:', error)
    res.status(500).json({ error: 'Failed to aggregate data' })
  }
})

// Get movie data
app.get('/api/movie/:name', (req, res) => {
  try {
    const movieName = decodeURIComponent(req.params.name)
    const filePath = path.join(DATA_DIR, `${movieName}.json`)

    if (!fs.existsSync(filePath)) {
      return res.status(404).json({ error: 'Movie not found' })
    }

    const data = JSON.parse(fs.readFileSync(filePath, 'utf-8'))
    res.json(data)
  } catch (error) {
    console.error('Error reading movie data:', error)
    res.status(500).json({ error: 'Failed to load movie data' })
  }
})

// Get nearest neighbors for a screenshot
app.post('/api/nearest-neighbors', (req, res) => {
  try {
    const { fileName, movieName } = req.body

    console.log('Nearest neighbors request:', { fileName, movieName })

    // Extract video name from screenshot filename (format: videoname__0001.jpg)
    const match = fileName.match(/^(.+)__\d+\.jpg$/)
    if (!match) {
      return res.status(400).json({ error: 'Invalid screenshot filename format' })
    }

    const videoName = match[1]

    // Load the nearest neighbors data for this movie
    const nnFilePath = path.join(DATA_NN_DIR, `${videoName}.json`)

    if (!fs.existsSync(nnFilePath)) {
      console.error('NN file not found:', nnFilePath)
      return res.status(404).json({ error: 'Nearest neighbors data not found', path: nnFilePath })
    }

    const nnData = JSON.parse(fs.readFileSync(nnFilePath, 'utf-8'))

    // Get neighbors for this specific screenshot
    const neighbors = nnData[fileName]

    if (!neighbors) {
      console.error('No neighbors found for:', fileName)
      return res.json({ neighbors: [] })
    }

    console.log(`Found ${neighbors.length} neighbors for ${fileName}`)
    res.json({ neighbors })
  } catch (error) {
    console.error('Error reading nearest neighbors:', error)
    res.status(500).json({ error: 'Failed to load nearest neighbors', details: error.message })
  }
})

// Extract frames from video
app.post('/api/extract-frames', async (req, res) => {
  try {
    const { videoFile, startTime, endTime } = req.body

    console.log('Extract frames request:', { videoFile, startTime, endTime })

    const videoPath = path.join(VIDEO_DIR, videoFile)

    console.log('Looking for video at:', videoPath)

    if (!fs.existsSync(videoPath)) {
      console.error('Video file not found at:', videoPath)
      return res.status(404).json({ error: 'Video file not found', path: videoPath })
    }

    // Clear temp directory
    const files = fs.readdirSync(TEMP_DIR)
    files.forEach(file => {
      if (file.endsWith('.jpg') || file.endsWith('.mp4') || file.endsWith('.txt')) {
        fs.unlinkSync(path.join(TEMP_DIR, file))
      }
    })

    console.log('Temp directory cleared')

    // Extract frames using ffmpeg with unique session ID
    const sessionId = Date.now()
    const duration = endTime - startTime
    const outputPattern = path.join(TEMP_DIR, `frame_${sessionId}_%04d.jpg`)

    const command = `ffmpeg -ss ${startTime} -i "${videoPath}" -t ${duration} -vf "fps=30,scale=1920:1080:flags=lanczos" -q:v 2 "${outputPattern}"`

    console.log('Executing:', command)
    await execPromise(command)

    // Get list of extracted frames
    const frames = fs.readdirSync(TEMP_DIR)
      .filter(f => f.startsWith(`frame_${sessionId}_`) && f.endsWith('.jpg'))
      .sort()

    res.json({ frames, sessionId })
  } catch (error) {
    console.error('Error extracting frames:', error)
    res.status(500).json({ error: 'Failed to extract frames', details: error.message })
  }
})

// Generate video from frames
app.post('/api/generate-video', async (req, res) => {
  try {
    const { sessionId, startFrame, endFrame, videoMode, videoFile, startTime } = req.body

    console.log('Generate video request:', { sessionId, startFrame, endFrame, videoMode, videoFile, startTime })

    // Generate unique output filename
    const timestamp = Date.now()
    const outputVideo = `output_${timestamp}.mp4`
    const outputPath = path.join(TEMP_DIR, outputVideo)

    // Remove old output files
    const oldOutputs = fs.readdirSync(TEMP_DIR).filter(f => f.startsWith('output_') && f.endsWith('.mp4'))
    oldOutputs.forEach(f => fs.unlinkSync(path.join(TEMP_DIR, f)))

    if (videoMode === 'ffmpeg') {
      // Extract video directly from source with audio
      const videoPath = path.join(VIDEO_DIR, videoFile)

      if (!fs.existsSync(videoPath)) {
        return res.status(404).json({ error: 'Video file not found', path: videoPath })
      }

      // Calculate timestamps based on frame numbers (30 fps)
      const frameStartTime = startTime + (startFrame / 30)
      const frameEndTime = startTime + (endFrame / 30)
      const duration = frameEndTime - frameStartTime

      console.log('Extracting video from source:', { frameStartTime, frameEndTime, duration })

      // Use high10 profile to support 10-bit sources, or just omit profile to let ffmpeg choose
      const command = `ffmpeg -ss ${frameStartTime} -i "${videoPath}" -t ${duration} -c:v libx264 -crf 18 -preset medium -pix_fmt yuv420p -movflags +faststart -s 1920x1080 -c:a aac -b:a 192k "${outputPath}"`

      console.log('Executing:', command)
      await execPromise(command)

      console.log('Video extracted with audio:', outputVideo)
      return res.json({ videoPath: outputVideo })
    }

    // Original frame-based method (no audio)

    // Create a temporary file list for ffmpeg
    const frameList = []
    for (let i = startFrame; i <= endFrame; i++) {
      const frameName = `frame_${sessionId}_${String(i + 1).padStart(4, '0')}.jpg`
      const framePath = path.join(TEMP_DIR, frameName)
      if (fs.existsSync(framePath)) {
        frameList.push(frameName)
      }
    }

    console.log('Frame list:', frameList.slice(0, 5), '...', frameList.slice(-5))
    console.log('Total frames:', frameList.length)

    if (frameList.length === 0) {
      return res.status(400).json({ error: 'No frames found in range' })
    }

    // Create concat file
    const concatFile = path.join(TEMP_DIR, 'concat.txt')
    const concatContent = frameList.map(f => `file '${f}'\nduration 0.033333`).join('\n') + '\n'
    fs.writeFileSync(concatFile, concatContent)

    const command = `ffmpeg -f concat -safe 0 -i "${concatFile}" -vsync vfr -pix_fmt yuv420p -c:v libx264 -crf 18 -preset slow -profile:v high -level 4.0 -movflags +faststart -s 1920x1080 "${outputPath}"`

    console.log('Executing:', command)
    await execPromise(command)

    console.log('Video generated:', outputVideo)

    res.json({ videoPath: outputVideo })
  } catch (error) {
    console.error('Error generating video:', error)
    res.status(500).json({ error: 'Failed to generate video', details: error.message })
  }
})

// Quick extract - extract and save video in one go
app.post('/api/quick-extract', async (req, res) => {
  try {
    const { videoFile, startTime, duration, videoMode, projectName } = req.body

    console.log('Quick extract request:', { videoFile, startTime, duration, videoMode, projectName })

    const videoPath = path.join(VIDEO_DIR, videoFile)

    if (!fs.existsSync(videoPath)) {
      return res.status(404).json({ error: 'Video file not found', path: videoPath })
    }

    // Determine save directory (with or without project subdirectory)
    let saveDir = SAVED_VIDEOS_DIR
    if (projectName && projectName.trim()) {
      saveDir = path.join(SAVED_VIDEOS_DIR, projectName.trim())
      if (!fs.existsSync(saveDir)) {
        fs.mkdirSync(saveDir, { recursive: true })
        console.log('Created project directory:', saveDir)
      }
    }

    // Generate unique filename
    const timestamp = Date.now()
    const savedFileName = `${videoFile}_${timestamp}.mp4`
    const savedPath = path.join(saveDir, savedFileName)

    // Extract video directly to saved location
    if (videoMode === 'ffmpeg') {
      // Extract with audio using ffmpeg
      const command = `ffmpeg -ss ${startTime} -i "${videoPath}" -t ${duration} -c:v libx264 -crf 18 -preset medium -pix_fmt yuv420p -movflags +faststart -s 1920x1080 -c:a aac -b:a 192k "${savedPath}"`

      console.log('Executing:', command)
      await execPromise(command)
      console.log('Quick extract complete with audio:', savedPath)
    } else {
      // Extract frames and create video without audio
      const sessionId = Date.now()
      const framePattern = path.join(TEMP_DIR, `frame_${sessionId}_%04d.jpg`)

      // Extract frames
      const extractCommand = `ffmpeg -ss ${startTime} -i "${videoPath}" -t ${duration} -vf "fps=30,scale=1920:1080:flags=lanczos" -q:v 2 "${framePattern}"`
      console.log('Extracting frames:', extractCommand)
      await execPromise(extractCommand)

      // Create concat file
      const frames = fs.readdirSync(TEMP_DIR).filter(f => f.startsWith(`frame_${sessionId}_`)).sort()
      const concatFile = path.join(TEMP_DIR, `concat_${sessionId}.txt`)
      const concatContent = frames.map(f => `file '${f}'\nduration 0.033333`).join('\n') + '\n'
      fs.writeFileSync(concatFile, concatContent)

      // Create video
      const videoCommand = `ffmpeg -f concat -safe 0 -i "${concatFile}" -vsync vfr -pix_fmt yuv420p -c:v libx264 -crf 18 -preset medium -movflags +faststart -s 1920x1080 "${savedPath}"`
      console.log('Creating video:', videoCommand)
      await execPromise(videoCommand)

      // Clean up temp files
      fs.unlinkSync(concatFile)
      frames.forEach(f => fs.unlinkSync(path.join(TEMP_DIR, f)))

      console.log('Quick extract complete without audio:', savedPath)
    }

    res.json({ success: true, savedPath })
  } catch (error) {
    console.error('Error during quick extract:', error)
    res.status(500).json({ error: 'Failed to quick extract', details: error.message })
  }
})

// Save video to permanent location
app.post('/api/save-video', async (req, res) => {
  try {
    const { videoPath, videoFile, projectName } = req.body
    const sourcePath = path.join(TEMP_DIR, videoPath)

    if (!fs.existsSync(sourcePath)) {
      return res.status(404).json({ error: 'Video not found' })
    }

    // Determine save directory (with or without project subdirectory)
    let saveDir = SAVED_VIDEOS_DIR
    if (projectName && projectName.trim()) {
      // Create project subdirectory if it doesn't exist
      saveDir = path.join(SAVED_VIDEOS_DIR, projectName.trim())
      if (!fs.existsSync(saveDir)) {
        fs.mkdirSync(saveDir, { recursive: true })
        console.log('Created project directory:', saveDir)
      }
    }

    // Generate unique filename
    const timestamp = Date.now()
    const savedFileName = `${videoFile}_${timestamp}.mp4`
    const savedPath = path.join(saveDir, savedFileName)

    // Copy file to saved location
    fs.copyFileSync(sourcePath, savedPath)

    console.log('Video saved to:', savedPath)
    res.json({ success: true, savedPath })
  } catch (error) {
    console.error('Error saving video:', error)
    res.status(500).json({ error: 'Failed to save video', details: error.message })
  }
})

// Get all movie tags
app.get('/api/tags', (req, res) => {
  res.json(movieTags)
})

// Update tags for a specific movie
app.post('/api/tags/:movie', (req, res) => {
  try {
    const movie = decodeURIComponent(req.params.movie)
    const { tags } = req.body

    if (!Array.isArray(tags)) {
      return res.status(400).json({ error: 'Tags must be an array' })
    }

    movieTags[movie] = tags
    saveTags()

    res.json({ success: true, tags })
  } catch (error) {
    console.error('Error updating tags:', error)
    res.status(500).json({ error: 'Failed to update tags' })
  }
})

app.listen(PORT, () => {
  console.log(`API server running on http://localhost:${PORT}`)
})
