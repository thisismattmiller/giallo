<template>
  <div id="app">
    <div class="container">
      <!-- Left Column: Movie List or Mode Toggle -->
      <div class="sidebar">
        <div class="mode-toggle">
          <button
            @click="toggleViewMode"
            :class="{ active: viewMode === 'single' }"
            class="mode-btn"
          >
            Single Movie
          </button>
          <button
            @click="toggleViewMode"
            :class="{ active: viewMode === 'aggregate' }"
            class="mode-btn"
          >
            All Movies
          </button>
        </div>

        <div v-if="viewMode === 'single'">
          <div class="project-name-input">
            <label for="project-name">Project Name:</label>
            <input
              id="project-name"
              v-model="projectName"
              type="text"
              placeholder="Enter project name..."
              class="project-input"
            />
          </div>

          <h2>Movies</h2>

          <div class="click-mode-toggle">
            <h3>Click Action:</h3>
            <button
              @click="clickMode = 'extractor'"
              :class="{ active: clickMode === 'extractor' }"
              class="click-mode-btn"
            >
              Frame Extractor
            </button>
            <button
              @click="clickMode = 'neighbors'"
              :class="{ active: clickMode === 'neighbors' }"
              class="click-mode-btn"
            >
              Find Similar
            </button>
          </div>

          <div class="video-mode-toggle">
            <h3>Video Generation:</h3>
            <button
              @click="videoMode = 'frames'"
              :class="{ active: videoMode === 'frames' }"
              class="video-mode-btn"
            >
              From Frames (No Audio)
            </button>
            <button
              @click="videoMode = 'ffmpeg'"
              :class="{ active: videoMode === 'ffmpeg' }"
              class="video-mode-btn"
            >
              From Source (With Audio)
            </button>
          </div>

          <div class="movie-list">
          <div
            v-for="movie in movies"
            :key="movie"
            class="movie-item-wrapper"
          >
            <div
              class="movie-item"
              :class="{ active: selectedMovie === movie }"
              @click="selectMovie(movie)"
            >
              {{ movie }}
            </div>

            <div v-if="movieTags[movie] && movieTags[movie].length > 0" class="movie-tags">
              <span v-for="tag in movieTags[movie]" :key="tag" class="movie-tag">
                {{ tag }}
              </span>
            </div>

            <div v-if="editingTag === movie" class="tag-editor" @click.stop>
              <div class="preset-tags">
                <button @click="addPresetTagAndSave(movie, 'eyes_done')" class="preset-tag-btn">
                  eyes_done
                </button>
              </div>
              <input
                v-model="newTagText"
                @keyup.enter="saveMovieTags(movie)"
                @keyup.esc="cancelEditingTag"
                placeholder="tag1, tag2, tag3"
                class="tag-input"
                autofocus
              />
              <div class="tag-buttons">
                <button @click="saveMovieTags(movie)" class="tag-save">Save</button>
                <button @click="cancelEditingTag" class="tag-cancel">Cancel</button>
              </div>
            </div>
            <button v-else @click.stop="startEditingTag(movie)" class="tag-edit-btn">
              +
            </button>
          </div>
        </div>
        </div>

        <div v-if="viewMode === 'aggregate'" class="aggregate-info">
          <h2>All Movies</h2>
          <p class="info-text">Browse aggregated tags and striking features from all movies</p>
        </div>
      </div>

      <!-- Middle Column: Tags/Striking -->
      <div v-if="selectedMovie || viewMode === 'aggregate'" class="middle-column">
        <h2 v-if="viewMode === 'single'">{{ selectedMovie }}</h2>
        <h2 v-else>All Movies</h2>

        <div class="jump-links">
          <a href="#" @click.prevent="showAllScreenshots" class="show-all-link">Show All</a>
          <span class="separator">|</span>
          <a href="#striking" @click.prevent="scrollToStriking">Jump to Striking</a>
          <span class="separator">|</span>
          <a href="#tags" @click.prevent="scrollToTags">Jump to Tags</a>
        </div>

        <div class="aggregate-section" id="striking">
          <h3>Striking Features</h3>
          <div class="tag-list">
            <div
              v-for="(count, striking) in aggregatedStriking"
              :key="'striking-' + striking"
              class="tag-item"
              :class="{ active: selectedAggregate && selectedAggregate.type === 'striking' && selectedAggregate.value === striking }"
              @click="selectAggregate('striking', striking)"
            >
              {{ striking }} <span class="count">({{ count }})</span>
            </div>
          </div>
        </div>

        <div class="aggregate-section" id="tags">
          <h3>Tags</h3>
          <div class="tag-list">
            <div
              v-for="(count, tag) in aggregatedTags"
              :key="'tag-' + tag"
              class="tag-item"
              :class="{ active: selectedAggregate && selectedAggregate.type === 'tag' && selectedAggregate.value === tag }"
              @click="selectAggregate('tag', tag)"
            >
              {{ tag }} <span class="count">({{ count }})</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Right Column: Screenshots -->
      <div v-if="selectedMovie || viewMode === 'aggregate'" class="screenshots-column">
        <div v-if="selectedMovie || (viewMode === 'aggregate' && selectedAggregate)">
          <h3 v-if="selectedAggregate">{{ selectedAggregate.type }}: {{ selectedAggregate.value }}</h3>
          <h3 v-else-if="selectedMovie">All Screenshots</h3>

          <div v-if="viewMode === 'aggregate' && totalPages > 1" class="pagination">
            <button @click="prevPage" :disabled="currentPage === 1" class="page-btn">
              &laquo; Prev
            </button>
            <span class="page-info">
              Page {{ currentPage }} of {{ totalPages }} ({{ aggregateScreenshots.length }} total)
            </span>
            <button @click="nextPage" :disabled="currentPage === totalPages" class="page-btn">
              Next &raquo;
            </button>
          </div>

          <div class="screenshot-grid">
            <div
              v-for="screenshot in filteredScreenshots"
              :key="screenshot.file_name + (screenshot.movieName || '')"
              class="screenshot-item"
              @click="handleScreenshotClick(screenshot)"
            >
              <img
                :src="getScreenshotPath(screenshot.file_name, screenshot.movieName)"
                :alt="screenshot.description"
                :title="screenshot.description"
              />
              <div v-if="viewMode === 'aggregate' && screenshot.movieName" class="screenshot-movie">
                {{ screenshot.movieName }}
              </div>
            </div>
          </div>

          <div v-if="viewMode === 'aggregate' && totalPages > 1" class="pagination">
            <button @click="prevPage" :disabled="currentPage === 1" class="page-btn">
              &laquo; Prev
            </button>
            <span class="page-info">
              Page {{ currentPage }} of {{ totalPages }}
            </span>
            <button @click="nextPage" :disabled="currentPage === totalPages" class="page-btn">
              Next &raquo;
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Nearest Neighbors Modal -->
    <div v-if="nearestNeighbors.visible" class="modal-overlay" @click.self="closeNearestNeighbors">
      <div class="modal">
        <div class="modal-header">
          <h2>20 Nearest Neighbors</h2>
          <button @click="closeNearestNeighbors" class="close-btn">&times;</button>
        </div>

        <div class="modal-content">
          <div v-if="nearestNeighbors.loading" class="loading">
            Finding similar screenshots...
          </div>

          <div v-else-if="nearestNeighbors.screenshot">
            <div class="nn-original">
              <h3>Original Screenshot (Click to extract frames)</h3>
              <div class="nn-original-item" @click="openFrameExtractorFromNN(nearestNeighbors.screenshot)">
                <img
                  :src="getScreenshotPath(nearestNeighbors.screenshot.file_name, nearestNeighbors.screenshot.movieName)"
                  :alt="nearestNeighbors.screenshot.description"
                />
                <p>{{ nearestNeighbors.screenshot.file_name }}</p>
                <button
                  @click.stop="quickExtract(nearestNeighbors.screenshot.file_name)"
                  class="quick-extract-btn"
                  :disabled="isExtracting(nearestNeighbors.screenshot.file_name)"
                >
                  {{ getExtractButtonText(nearestNeighbors.screenshot.file_name) }}
                </button>
                <div v-if="getExtractStatus(nearestNeighbors.screenshot.file_name)" class="extract-status">
                  {{ getExtractStatus(nearestNeighbors.screenshot.file_name) }}
                </div>
              </div>
            </div>

            <div v-if="nearestNeighbors.neighbors.length > 0" class="nn-results">
              <h3>Similar Screenshots (Click to extract frames)</h3>
              <div class="screenshot-grid">
                <div
                  v-for="neighbor in nearestNeighbors.neighbors"
                  :key="neighbor.screenshot"
                  class="screenshot-item nn-item"
                >
                  <img
                    @click="openFrameExtractorFromNeighbor(neighbor)"
                    :src="getScreenshotPath(neighbor.screenshot)"
                    :alt="neighbor.screenshot"
                  />
                  <div class="nn-info">
                    <div class="nn-filename">{{ neighbor.screenshot }}</div>
                    <div class="nn-distance">Distance: {{ neighbor.distance.toFixed(3) }}</div>
                  </div>
                  <button
                    @click.stop="quickExtract(neighbor.screenshot)"
                    class="quick-extract-btn"
                    :disabled="isExtracting(neighbor.screenshot)"
                  >
                    {{ getExtractButtonText(neighbor.screenshot) }}
                  </button>
                  <div v-if="getExtractStatus(neighbor.screenshot)" class="extract-status">
                    {{ getExtractStatus(neighbor.screenshot) }}
                  </div>
                </div>
              </div>
            </div>

            <div v-else class="no-neighbors">
              No nearest neighbors found. Please ensure embeddings have been generated.
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Frame Extractor Modal -->
    <div v-if="frameExtractor.visible" class="modal-overlay" @click.self="closeFrameExtractor">
      <div class="modal">
        <div class="modal-header">
          <h2>Frame Extractor</h2>
          <button @click="closeFrameExtractor" class="close-btn">&times;</button>
        </div>

        <div class="modal-content">
          <div v-if="frameExtractor.loading" class="loading">
            Extracting frames...
          </div>

          <div v-else-if="frameExtractor.frames.length > 0">
            <div class="time-controls">
              <button @click="extendStart" :disabled="frameExtractor.processing">
                - 20s Start
              </button>
              <span class="time-display">
                {{ formatTime(frameExtractor.startTime) }} - {{ formatTime(frameExtractor.endTime) }}
                ({{ frameExtractor.frames.length }} frames)
              </span>
              <button @click="extendEnd" :disabled="frameExtractor.processing">
                + 20s End
              </button>
            </div>

            <div class="frames-grid">
              <div
                v-for="(frame, index) in frameExtractor.frames"
                :key="frame"
                class="frame-item"
                :class="{
                  'start-selected': index === frameExtractor.startFrame,
                  'end-selected': index === frameExtractor.endFrame,
                  'in-range': isInRange(index)
                }"
                @click="selectFrame(index)"
              >
                <img :src="`/temp-frames/${frame}`" :alt="`Frame ${index}`" />
                <div class="frame-number">{{ index }}</div>
              </div>
            </div>

            <div class="video-controls">
              <div class="selection-info">
                <span v-if="frameExtractor.startFrame !== null && frameExtractor.endFrame !== null">
                  Selected: Frame {{ frameExtractor.startFrame }} to {{ frameExtractor.endFrame }}
                  ({{ (frameExtractor.endFrame - frameExtractor.startFrame) / 30 }}s)
                </span>
                <span v-else>
                  Click frames to select start and end points
                </span>
              </div>

              <button
                @click="generateVideo"
                :disabled="frameExtractor.startFrame === null || frameExtractor.endFrame === null || frameExtractor.processing"
                class="generate-btn"
              >
                {{ frameExtractor.processing ? 'Generating...' : 'Generate Video' }}
              </button>
            </div>

            <div v-if="frameExtractor.videoPath" class="video-preview">
              <h3>Video Preview</h3>
              <video :src="`/temp-frames/${frameExtractor.videoPath}`" controls></video>
              <div class="save-controls">
                <button @click="saveVideo" class="save-btn">
                  Save Video
                </button>
                <div v-if="frameExtractor.saveMessage" class="save-message">
                  {{ frameExtractor.saveMessage }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'App',
  data() {
    return {
      viewMode: 'single', // 'single' or 'aggregate'
      clickMode: 'extractor', // 'extractor' or 'neighbors'
      videoMode: 'frames', // 'frames' or 'ffmpeg'
      projectName: '',
      movies: [],
      selectedMovie: null,
      movieData: {},
      aggregatedTags: {},
      aggregatedStriking: {},
      selectedAggregate: null,
      movieTags: {},
      editingTag: null,
      newTagText: '',
      aggregateData: null,
      aggregateScreenshots: [],
      currentPage: 1,
      itemsPerPage: 50,
      nearestNeighbors: {
        visible: false,
        loading: false,
        screenshot: null,
        neighbors: []
      },
      quickExtracts: {}, // Track quick extract status by filename
      frameExtractor: {
        visible: false,
        loading: false,
        processing: false,
        screenshot: null,
        videoFile: null,
        startTime: 0,
        endTime: 0,
        frames: [],
        sessionId: null,
        startFrame: null,
        endFrame: null,
        videoPath: null,
        saveMessage: null,
        returnToNN: false
      }
    }
  },
  computed: {
    filteredScreenshots() {
      if (this.viewMode === 'aggregate') {
        return this.paginatedAggregateScreenshots
      }

      if (!this.selectedMovie || !this.movieData[this.selectedMovie]) {
        return []
      }

      // If no aggregate selected, show all screenshots
      if (!this.selectedAggregate) {
        return Object.values(this.movieData[this.selectedMovie])
      }

      const data = this.movieData[this.selectedMovie]
      const { type, value } = this.selectedAggregate

      return Object.values(data).filter(screenshot => {
        if (type === 'tag') {
          return screenshot.tags && screenshot.tags.includes(value)
        } else if (type === 'striking') {
          return screenshot.striking && screenshot.striking.includes(value)
        }
        return false
      })
    },
    paginatedAggregateScreenshots() {
      const start = (this.currentPage - 1) * this.itemsPerPage
      const end = start + this.itemsPerPage
      return this.aggregateScreenshots.slice(start, end)
    },
    totalPages() {
      return Math.ceil(this.aggregateScreenshots.length / this.itemsPerPage)
    }
  },
  async mounted() {
    await this.loadMovieList()
    await this.loadTags()

    // Add keyboard listener for ESC key
    window.addEventListener('keydown', this.handleKeyDown)
  },
  beforeUnmount() {
    // Remove keyboard listener
    window.removeEventListener('keydown', this.handleKeyDown)
  },
  methods: {
    handleKeyDown(event) {
      if (event.key === 'Escape') {
        if (this.frameExtractor.visible) {
          this.closeFrameExtractor()
        } else if (this.nearestNeighbors.visible) {
          this.closeNearestNeighbors()
        }
      }
    },
    toggleViewMode() {
      if (this.viewMode === 'single') {
        this.viewMode = 'aggregate'
        this.loadAggregateData()
      } else {
        this.viewMode = 'single'
        this.selectedAggregate = null
        this.aggregateScreenshots = []
        this.currentPage = 1
      }
    },
    async loadAggregateData() {
      try {
        const response = await fetch('/api/aggregate')
        this.aggregateData = await response.json()
        this.aggregatedTags = this.aggregateData.tags
        this.aggregatedStriking = this.aggregateData.striking
      } catch (error) {
        console.error('Error loading aggregate data:', error)
      }
    },
    selectAggregateItem(type, value) {
      this.selectedAggregate = { type, value }
      this.currentPage = 1

      if (this.viewMode === 'aggregate') {
        const key = `${type}:${value}`
        this.aggregateScreenshots = this.aggregateData.screenshotIndex[key] || []
      }
    },
    async loadMovieList() {
      try {
        // Load the list of movies from data directory
        const response = await fetch('/api/movies')
        const movies = await response.json()
        this.movies = movies
      } catch (error) {
        console.error('Error loading movie list:', error)
      }
    },
    async selectMovie(movie) {
      this.selectedMovie = movie
      this.selectedAggregate = null

      // Load movie data if not already loaded
      if (!this.movieData[movie]) {
        try {
          const response = await fetch(`/api/movie/${encodeURIComponent(movie)}`)
          const data = await response.json()
          this.movieData[movie] = data
          this.aggregateMovieData(data)
        } catch (error) {
          console.error('Error loading movie data:', error)
        }
      } else {
        this.aggregateMovieData(this.movieData[movie])
      }
    },
    aggregateMovieData(data) {
      const tags = {}
      const striking = {}

      Object.values(data).forEach(screenshot => {
        // Aggregate tags
        if (screenshot.tags) {
          screenshot.tags.forEach(tag => {
            tags[tag] = (tags[tag] || 0) + 1
          })
        }

        // Aggregate striking features
        if (screenshot.striking) {
          screenshot.striking.forEach(strike => {
            striking[strike] = (striking[strike] || 0) + 1
          })
        }
      })

      // Sort by count descending
      this.aggregatedTags = Object.fromEntries(
        Object.entries(tags).sort((a, b) => b[1] - a[1])
      )
      this.aggregatedStriking = Object.fromEntries(
        Object.entries(striking).sort((a, b) => b[1] - a[1])
      )
    },
    selectAggregate(type, value) {
      if (this.viewMode === 'aggregate') {
        this.selectAggregateItem(type, value)
      } else {
        this.selectedAggregate = { type, value }
      }
    },
    nextPage() {
      if (this.currentPage < this.totalPages) {
        this.currentPage++
      }
    },
    prevPage() {
      if (this.currentPage > 1) {
        this.currentPage--
      }
    },
    goToPage(page) {
      this.currentPage = page
    },
    clearAggregate() {
      this.selectedAggregate = null
    },
    getScreenshotPath(fileName, movieName = null) {
      // Extract video base name from screenshot filename
      const match = fileName.match(/^(.+)__\d+\.jpg$/)
      if (match) {
        const videoName = movieName || match[1]
        return `/screenshots/${videoName}/${fileName}`
      }
      return ''
    },
    scrollToTags() {
      document.getElementById('tags')?.scrollIntoView({ behavior: 'smooth' })
    },
    scrollToStriking() {
      document.getElementById('striking')?.scrollIntoView({ behavior: 'smooth' })
    },
    showAllScreenshots() {
      this.selectedAggregate = null
    },
    handleScreenshotClick(screenshot) {
      if (this.clickMode === 'extractor') {
        this.openFrameExtractor(screenshot)
      } else {
        this.showNearestNeighbors(screenshot)
      }
    },
    async showNearestNeighbors(screenshot) {
      console.log('Showing nearest neighbors for:', screenshot.file_name)

      this.nearestNeighbors = {
        visible: true,
        loading: true,
        screenshot: screenshot,
        neighbors: []
      }

      try {
        const response = await fetch('/api/nearest-neighbors', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            fileName: screenshot.file_name,
            movieName: screenshot.movieName || this.selectedMovie
          })
        })

        const data = await response.json()
        this.nearestNeighbors.neighbors = data.neighbors || []
        this.nearestNeighbors.loading = false
      } catch (error) {
        console.error('Error loading nearest neighbors:', error)
        this.nearestNeighbors.loading = false
      }
    },
    closeNearestNeighbors() {
      this.nearestNeighbors.visible = false
    },
    openFrameExtractorFromNN(screenshot) {
      // Store nearest neighbors state before closing
      const savedNN = {
        screenshot: this.nearestNeighbors.screenshot,
        neighbors: this.nearestNeighbors.neighbors
      }

      // Close nearest neighbors modal
      this.nearestNeighbors.visible = false

      // Open frame extractor with this screenshot
      this.openFrameExtractor(screenshot)

      // Mark that we should return to NN modal
      this.frameExtractor.returnToNN = true
      this.frameExtractor.savedNN = savedNN
    },
    openFrameExtractorFromNeighbor(neighbor) {
      // Convert neighbor object to screenshot format
      const screenshot = {
        file_name: neighbor.screenshot,
        description: '',
        tags: [],
        striking: []
      }

      // Store nearest neighbors state before closing
      const savedNN = {
        screenshot: this.nearestNeighbors.screenshot,
        neighbors: this.nearestNeighbors.neighbors
      }

      // Close nearest neighbors modal
      this.nearestNeighbors.visible = false

      // Open frame extractor
      this.openFrameExtractor(screenshot)

      // Mark that we should return to NN modal
      this.frameExtractor.returnToNN = true
      this.frameExtractor.savedNN = savedNN
    },
    async openFrameExtractor(screenshot) {
      // Extract frame number and video file from screenshot filename
      const match = screenshot.file_name.match(/^(.+)__(\d+)\.jpg$/)
      if (!match) {
        console.error('Could not parse screenshot filename:', screenshot.file_name)
        return
      }

      const videoFile = match[1]
      const frameNumber = parseInt(match[2])
      const screenshotTime = frameNumber * 5 // Convert to seconds

      // Calculate start time (5 seconds before, but not negative)
      const startTime = Math.max(0, screenshotTime - 5)
      const endTime = startTime + 10 // 10 seconds total

      console.log('Opening frame extractor:', { videoFile, frameNumber, screenshotTime, startTime, endTime })

      this.frameExtractor = {
        visible: true,
        loading: true,
        processing: false,
        screenshot,
        videoFile,
        startTime,
        endTime,
        frames: [],
        startFrame: null,
        endFrame: null,
        videoPath: null
      }

      await this.extractFrames()
    },
    async extractFrames() {
      try {
        const response = await fetch('/api/extract-frames', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            videoFile: this.frameExtractor.videoFile,
            startTime: this.frameExtractor.startTime,
            endTime: this.frameExtractor.endTime
          })
        })

        const data = await response.json()
        this.frameExtractor.frames = data.frames
        this.frameExtractor.sessionId = data.sessionId
        this.frameExtractor.loading = false
      } catch (error) {
        console.error('Error extracting frames:', error)
        this.frameExtractor.loading = false
      }
    },
    closeFrameExtractor() {
      // Check if we should return to nearest neighbors modal
      if (this.frameExtractor.returnToNN && this.frameExtractor.savedNN) {
        // Restore nearest neighbors modal
        this.nearestNeighbors = {
          visible: true,
          loading: false,
          screenshot: this.frameExtractor.savedNN.screenshot,
          neighbors: this.frameExtractor.savedNN.neighbors
        }
      }

      this.frameExtractor.visible = false
      this.frameExtractor.returnToNN = false
      this.frameExtractor.savedNN = null
    },
    async extendStart() {
      const newStartTime = Math.max(0, this.frameExtractor.startTime - 20)
      if (newStartTime === this.frameExtractor.startTime) return

      this.frameExtractor.startTime = newStartTime
      this.frameExtractor.loading = true
      this.frameExtractor.frames = []
      this.frameExtractor.startFrame = null
      this.frameExtractor.endFrame = null
      this.frameExtractor.videoPath = null

      await this.extractFrames()
      this.frameExtractor.loading = false
    },
    async extendEnd() {
      this.frameExtractor.endTime += 20
      this.frameExtractor.loading = true
      this.frameExtractor.frames = []
      this.frameExtractor.startFrame = null
      this.frameExtractor.endFrame = null
      this.frameExtractor.videoPath = null

      await this.extractFrames()
      this.frameExtractor.loading = false
    },
    selectFrame(index) {
      if (this.frameExtractor.startFrame === null) {
        this.frameExtractor.startFrame = index
      } else if (this.frameExtractor.endFrame === null) {
        if (index > this.frameExtractor.startFrame) {
          this.frameExtractor.endFrame = index
        } else {
          // Swap if user clicks earlier frame
          this.frameExtractor.endFrame = this.frameExtractor.startFrame
          this.frameExtractor.startFrame = index
        }
      } else {
        // Reset selection
        this.frameExtractor.startFrame = index
        this.frameExtractor.endFrame = null
        this.frameExtractor.videoPath = null
      }
    },
    isInRange(index) {
      if (this.frameExtractor.startFrame === null || this.frameExtractor.endFrame === null) {
        return false
      }
      return index >= this.frameExtractor.startFrame && index <= this.frameExtractor.endFrame
    },
    async generateVideo() {
      this.frameExtractor.processing = true

      try {
        const response = await fetch('/api/generate-video', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            sessionId: this.frameExtractor.sessionId,
            startFrame: this.frameExtractor.startFrame,
            endFrame: this.frameExtractor.endFrame,
            videoMode: this.videoMode,
            videoFile: this.frameExtractor.videoFile,
            startTime: this.frameExtractor.startTime
          })
        })

        const data = await response.json()
        this.frameExtractor.videoPath = data.videoPath
        this.frameExtractor.processing = false
      } catch (error) {
        console.error('Error generating video:', error)
        this.frameExtractor.processing = false
      }
    },
    async saveVideo() {
      try {
        const response = await fetch('/api/save-video', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            videoPath: this.frameExtractor.videoPath,
            videoFile: this.frameExtractor.videoFile,
            projectName: this.projectName
          })
        })

        const data = await response.json()
        if (data.success) {
          this.frameExtractor.saveMessage = `Saved to: ${data.savedPath}`
          setTimeout(() => {
            this.frameExtractor.saveMessage = null
          }, 3000)
        } else {
          this.frameExtractor.saveMessage = 'Failed to save video'
        }
      } catch (error) {
        console.error('Error saving video:', error)
        this.frameExtractor.saveMessage = 'Failed to save video'
      }
    },
    formatTime(seconds) {
      const mins = Math.floor(seconds / 60)
      const secs = seconds % 60
      return `${mins}:${secs.toString().padStart(2, '0')}`
    },
    async loadTags() {
      try {
        const response = await fetch('/api/tags')
        this.movieTags = await response.json()
      } catch (error) {
        console.error('Error loading tags:', error)
      }
    },
    startEditingTag(movie) {
      this.editingTag = movie
      this.newTagText = (this.movieTags[movie] || []).join(', ')
    },
    cancelEditingTag() {
      this.editingTag = null
      this.newTagText = ''
    },
    addPresetTag(tag) {
      const currentTags = this.newTagText
        .split(',')
        .map(t => t.trim())
        .filter(t => t.length > 0)

      if (!currentTags.includes(tag)) {
        currentTags.push(tag)
        this.newTagText = currentTags.join(', ')
      }
    },
    async saveMovieTags(movie) {
      try {
        const tags = this.newTagText
          .split(',')
          .map(t => t.trim())
          .filter(t => t.length > 0)

        const response = await fetch(`/api/tags/${encodeURIComponent(movie)}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ tags })
        })

        const data = await response.json()
        if (data.success) {
          this.movieTags[movie] = tags
          this.editingTag = null
          this.newTagText = ''
        }
      } catch (error) {
        console.error('Error saving tags:', error)
      }
    },
    async addPresetTagAndSave(movie, tag) {
      try {
        const currentTags = this.movieTags[movie] || []

        if (!currentTags.includes(tag)) {
          const updatedTags = [...currentTags, tag]

          const response = await fetch(`/api/tags/${encodeURIComponent(movie)}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ tags: updatedTags })
          })

          const data = await response.json()
          if (data.success) {
            this.movieTags[movie] = updatedTags
            this.editingTag = null
            this.newTagText = ''
          }
        } else {
          // Tag already exists, just close the editor
          this.editingTag = null
          this.newTagText = ''
        }
      } catch (error) {
        console.error('Error saving preset tag:', error)
      }
    },
    async quickExtract(fileName) {
      console.log('Quick extract clicked:', fileName)

      // Set extracting status
      this.quickExtracts[fileName] = { status: 'extracting', message: null }

      try {
        // Extract video name and frame number from screenshot filename
        const match = fileName.match(/^(.+)__(\d+)\.jpg$/)
        if (!match) {
          this.quickExtracts[fileName] = { status: 'error', message: 'Invalid filename format' }
          return
        }

        const videoFile = match[1]
        const frameNumber = parseInt(match[2])
        const screenshotTime = frameNumber * 5 // Convert to seconds

        // Calculate start and end time (30 seconds before and after)
        const startTime = Math.max(0, screenshotTime - 30)
        const endTime = screenshotTime + 30
        const duration = endTime - startTime

        console.log('Quick extract params:', { videoFile, startTime, duration })

        // Call quick-extract API endpoint
        const response = await fetch('/api/quick-extract', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            videoFile,
            startTime,
            duration,
            videoMode: this.videoMode,
            projectName: this.projectName
          })
        })

        const data = await response.json()

        if (data.success) {
          this.quickExtracts[fileName] = {
            status: 'success',
            message: `Saved!`
          }
          // Clear message after 5 seconds
          setTimeout(() => {
            if (this.quickExtracts[fileName]?.status === 'success') {
              delete this.quickExtracts[fileName]
            }
          }, 5000)
        } else {
          this.quickExtracts[fileName] = { status: 'error', message: 'Failed!' }
        }
      } catch (error) {
        console.error('Error during quick extract:', error)
        this.quickExtracts[fileName] = { status: 'error', message: 'Failed!' }
      }
    },
    isExtracting(fileName) {
      return this.quickExtracts[fileName]?.status === 'extracting'
    },
    getExtractButtonText(fileName) {
      const status = this.quickExtracts[fileName]?.status
      if (status === 'extracting') return 'Extracting...'
      return 'Quick Extract (60s)'
    },
    getExtractStatus(fileName) {
      return this.quickExtracts[fileName]?.message || null
    }
  }
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html,
body {
  width: 100%;
  height: 100%;
  overflow: hidden;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  background: #1a1a1a;
  color: #e0e0e0;
}

#app {
  width: 100%;
  height: 100vh;
  overflow: hidden;
}

.container {
  display: flex;
  height: 100%;
  width: 100%;
  justify-content: flex-start;
}

.sidebar {
  width: 300px;
  flex-shrink: 0;
  background: #252525;
  border-right: 1px solid #333;
  overflow-y: auto;
  padding: 15px 10px;
}

.sidebar h2 {
  margin-bottom: 15px;
  color: #fff;
  font-size: 18px;
}

.movie-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.movie-item-wrapper {
  position: relative;
  background: #2a2a2a;
  border-radius: 4px;
  padding: 10px;
}

.movie-item {
  cursor: pointer;
  transition: all 0.2s;
  word-wrap: break-word;
  font-size: 13px;
  margin-bottom: 5px;
}

.movie-item:hover {
  color: #4a90e2;
}

.movie-item.active {
  color: #4a90e2;
  font-weight: 600;
}

.movie-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 5px;
}

.movie-tag {
  font-size: 10px;
  padding: 2px 6px;
  background: #4a90e2;
  color: #fff;
  border-radius: 3px;
  display: inline-block;
}

.tag-edit-btn {
  position: absolute;
  top: 10px;
  right: 10px;
  width: 20px;
  height: 20px;
  background: #333;
  border: none;
  border-radius: 3px;
  color: #aaa;
  cursor: pointer;
  font-size: 16px;
  line-height: 1;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.tag-edit-btn:hover {
  background: #4a90e2;
  color: #fff;
}

.tag-editor {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid #333;
}

.preset-tags {
  display: flex;
  gap: 4px;
  margin-bottom: 6px;
}

.preset-tag-btn {
  padding: 4px 8px;
  background: #333;
  border: 1px solid #555;
  border-radius: 3px;
  color: #aaa;
  cursor: pointer;
  font-size: 11px;
}

.preset-tag-btn:hover {
  background: #4a90e2;
  color: #fff;
  border-color: #4a90e2;
}

.tag-input {
  width: 100%;
  padding: 6px;
  background: #1a1a1a;
  border: 1px solid #444;
  border-radius: 3px;
  color: #e0e0e0;
  font-size: 12px;
  margin-bottom: 6px;
}

.tag-input:focus {
  outline: none;
  border-color: #4a90e2;
}

.tag-buttons {
  display: flex;
  gap: 6px;
}

.tag-save,
.tag-cancel {
  flex: 1;
  padding: 4px 8px;
  border: none;
  border-radius: 3px;
  font-size: 11px;
  cursor: pointer;
}

.tag-save {
  background: #4ade80;
  color: #000;
}

.tag-save:hover {
  background: #5ae88f;
}

.tag-cancel {
  background: #333;
  color: #aaa;
}

.tag-cancel:hover {
  background: #444;
  color: #fff;
}

.middle-column {
  width: 300px;
  flex-shrink: 0;
  background: #252525;
  border-right: 1px solid #333;
  overflow-y: auto;
  padding: 15px 10px;
  display: flex;
  flex-direction: column;
}

.middle-column h2 {
  margin-bottom: 10px;
  color: #fff;
  font-size: 16px;
  flex-shrink: 0;
}

.jump-links {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #333;
  flex-shrink: 0;
}

.jump-links a {
  color: #4a90e2;
  text-decoration: none;
  font-size: 12px;
  cursor: pointer;
}

.jump-links a:hover {
  color: #66a3e8;
  text-decoration: underline;
}

.jump-links .show-all-link {
  color: #4ade80;
  font-weight: 600;
}

.jump-links .show-all-link:hover {
  color: #5ae88f;
}

.jump-links .separator {
  color: #555;
}

.aggregate-section {
  margin-bottom: 20px;
  flex-shrink: 0;
}

.aggregate-section h3 {
  margin-bottom: 10px;
  color: #aaa;
  font-size: 14px;
  font-weight: 600;
}

.tag-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.tag-item {
  padding: 8px 12px;
  background: #2a2a2a;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 13px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.tag-item:hover {
  background: #333;
}

.tag-item.active {
  background: #4a90e2;
  color: #fff;
}

.tag-item .count {
  color: #888;
  font-size: 12px;
}

.tag-item:hover .count,
.tag-item.active .count {
  color: #fff;
}

.screenshots-column {
  flex: 1;
  min-width: 0;
  overflow-y: auto;
  padding: 15px 10px;
  background: #1a1a1a;
}

.screenshots-column h3 {
  margin-bottom: 20px;
  color: #fff;
  font-size: 16px;
  position: sticky;
  top: 0;
  background: #1a1a1a;
  padding-bottom: 10px;
  z-index: 10;
}

.screenshot-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 15px;
}

.screenshot-item {
  position: relative;
  overflow: hidden;
  border-radius: 4px;
  background: #2a2a2a;
  transition: all 0.3s ease;
}

.screenshot-item img {
  width: 100%;
  height: auto;
  display: block;
  transition: transform 0.3s ease;
}

.screenshot-item:hover {
  transform: scale(2.5);
  z-index: 100;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.8);
}

.screenshot-item:hover img {
  transform: scale(1);
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.85);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: #252525;
  border-radius: 8px;
  width: 90vw;
  height: 90vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #333;
}

.modal-header h2 {
  color: #fff;
  font-size: 18px;
}

.close-btn {
  background: none;
  border: none;
  color: #aaa;
  font-size: 32px;
  cursor: pointer;
  line-height: 1;
  padding: 0;
  width: 32px;
  height: 32px;
}

.close-btn:hover {
  color: #fff;
}

.modal-content {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.loading {
  text-align: center;
  padding: 40px;
  color: #aaa;
  font-size: 16px;
}

.time-controls {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 20px;
  margin-bottom: 20px;
  padding: 15px;
  background: #2a2a2a;
  border-radius: 4px;
}

.time-controls button {
  padding: 8px 16px;
  background: #4a90e2;
  border: none;
  border-radius: 4px;
  color: #fff;
  cursor: pointer;
  font-size: 14px;
}

.time-controls button:hover:not(:disabled) {
  background: #5a9fe8;
}

.time-controls button:disabled {
  background: #333;
  cursor: not-allowed;
  opacity: 0.5;
}

.time-display {
  color: #fff;
  font-size: 14px;
}

.frames-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 10px;
  margin-bottom: 20px;
}

.frame-item {
  position: relative;
  cursor: pointer;
  border: 3px solid transparent;
  border-radius: 4px;
  overflow: hidden;
  transition: all 0.2s;
}

.frame-item:hover {
  border-color: #4a90e2;
  transform: scale(1.05);
}

.frame-item.start-selected {
  border-color: #4ade80;
}

.frame-item.end-selected {
  border-color: #f87171;
}

.frame-item.in-range {
  border-color: #fbbf24;
}

.frame-item img {
  width: 100%;
  height: auto;
  display: block;
}

.frame-number {
  position: absolute;
  top: 4px;
  right: 4px;
  background: rgba(0, 0, 0, 0.7);
  color: #fff;
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 11px;
}

.video-controls {
  display: flex;
  flex-direction: column;
  gap: 15px;
  padding: 20px;
  background: #2a2a2a;
  border-radius: 4px;
  margin-bottom: 20px;
}

.selection-info {
  text-align: center;
  color: #aaa;
  font-size: 14px;
}

.generate-btn {
  padding: 12px 24px;
  background: #4ade80;
  border: none;
  border-radius: 4px;
  color: #000;
  font-weight: 600;
  cursor: pointer;
  font-size: 14px;
}

.generate-btn:hover:not(:disabled) {
  background: #5ae88f;
}

.generate-btn:disabled {
  background: #333;
  color: #666;
  cursor: not-allowed;
}

.video-preview {
  padding: 20px;
  background: #2a2a2a;
  border-radius: 4px;
}

.video-preview h3 {
  color: #fff;
  margin-bottom: 15px;
  font-size: 16px;
}

.video-preview video {
  width: 100%;
  max-width: 800px;
  display: block;
  margin: 0 auto 15px;
  border-radius: 4px;
}

.save-controls {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

.save-btn {
  padding: 12px 24px;
  background: #4a90e2;
  border: none;
  border-radius: 4px;
  color: #fff;
  font-weight: 600;
  cursor: pointer;
  font-size: 14px;
}

.save-btn:hover {
  background: #5a9fe8;
}

.save-message {
  color: #4ade80;
  font-size: 13px;
  text-align: center;
  padding: 8px 16px;
  background: rgba(74, 222, 128, 0.1);
  border-radius: 4px;
  border: 1px solid rgba(74, 222, 128, 0.3);
}

/* Mode Toggle */
.mode-toggle {
  display: flex;
  gap: 8px;
  margin-bottom: 15px;
}

.click-mode-toggle {
  margin-bottom: 20px;
  padding: 12px;
  background: #2a2a2a;
  border-radius: 4px;
}

.click-mode-toggle h3 {
  color: #aaa;
  font-size: 11px;
  text-transform: uppercase;
  margin-bottom: 8px;
  font-weight: 600;
}

.click-mode-btn {
  width: 100%;
  padding: 8px 12px;
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 4px;
  color: #aaa;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.2s;
  margin-bottom: 6px;
}

.click-mode-btn:last-child {
  margin-bottom: 0;
}

.click-mode-btn:hover {
  background: #333;
  color: #fff;
}

.click-mode-btn.active {
  background: #4ade80;
  color: #000;
  border-color: #4ade80;
  font-weight: 600;
}

/* Video Mode Toggle */
.video-mode-toggle {
  margin-bottom: 20px;
  padding: 12px;
  background: #2a2a2a;
  border-radius: 4px;
}

.video-mode-toggle h3 {
  color: #aaa;
  font-size: 11px;
  text-transform: uppercase;
  margin-bottom: 8px;
  font-weight: 600;
}

.video-mode-btn {
  width: 100%;
  padding: 8px 12px;
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 4px;
  color: #aaa;
  cursor: pointer;
  font-size: 11px;
  transition: all 0.2s;
  margin-bottom: 6px;
}

.video-mode-btn:last-child {
  margin-bottom: 0;
}

.video-mode-btn:hover {
  background: #333;
  color: #fff;
}

.video-mode-btn.active {
  background: #f59e0b;
  color: #000;
  border-color: #f59e0b;
  font-weight: 600;
}

/* Project Name Input */
.project-name-input {
  margin-bottom: 20px;
  padding: 12px;
  background: #2a2a2a;
  border-radius: 4px;
}

.project-name-input label {
  display: block;
  color: #aaa;
  font-size: 11px;
  text-transform: uppercase;
  margin-bottom: 8px;
  font-weight: 600;
}

.project-input {
  width: 100%;
  padding: 8px 12px;
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 4px;
  color: #fff;
  font-size: 13px;
  transition: all 0.2s;
}

.project-input:focus {
  outline: none;
  border-color: #4a90e2;
  background: #252525;
}

.project-input::placeholder {
  color: #666;
}

.mode-btn {
  flex: 1;
  padding: 10px 15px;
  background: #2a2a2a;
  border: 1px solid #333;
  border-radius: 4px;
  color: #aaa;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;
}

.mode-btn:hover {
  background: #333;
  color: #fff;
}

.mode-btn.active {
  background: #4a90e2;
  color: #fff;
  border-color: #4a90e2;
}

/* Aggregate Info */
.aggregate-info {
  padding-top: 10px;
}

.info-text {
  color: #aaa;
  font-size: 12px;
  line-height: 1.5;
}

/* Screenshot Movie Label */
.screenshot-movie {
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

/* Pagination */
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 15px;
  margin: 20px 0;
  padding: 15px;
  background: #252525;
  border-radius: 4px;
}

.page-btn {
  padding: 8px 16px;
  background: #4a90e2;
  border: none;
  border-radius: 4px;
  color: #fff;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.page-btn:hover:not(:disabled) {
  background: #5a9fe8;
}

.page-btn:disabled {
  background: #333;
  color: #666;
  cursor: not-allowed;
  opacity: 0.5;
}

.page-info {
  color: #aaa;
  font-size: 14px;
}

/* Nearest Neighbors Modal */
.nn-original {
  margin-bottom: 30px;
  padding: 20px;
  background: #2a2a2a;
  border-radius: 4px;
}

.nn-original h3 {
  color: #fff;
  margin-bottom: 15px;
  font-size: 16px;
}

.nn-original-item {
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
}

.nn-original-item:hover {
  transform: scale(1.02);
}

.nn-original-item img {
  max-width: 400px;
  width: 100%;
  border-radius: 4px;
  margin-bottom: 10px;
  border: 2px solid transparent;
  transition: all 0.2s;
}

.nn-original-item:hover img {
  border-color: #4a90e2;
}

.nn-original-item p {
  color: #aaa;
  font-size: 13px;
}

.nn-results {
  margin-top: 20px;
}

.nn-results h3 {
  color: #fff;
  margin-bottom: 20px;
  font-size: 16px;
}

.nn-item {
  position: relative;
  transition: all 0.2s;
  display: flex;
  flex-direction: column;
}

.nn-item:hover {
  transform: scale(1.05);
  z-index: 10;
}

.nn-item img {
  border: 2px solid transparent;
  transition: all 0.2s;
  cursor: pointer;
  width: 100%;
}

.nn-item:hover img {
  border-color: #4a90e2;
}

.nn-info {
  background: rgba(0, 0, 0, 0.9);
  padding: 6px 8px;
  width: 100%;
}

.nn-filename {
  color: #fff;
  font-size: 10px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 2px;
}

.nn-distance {
  color: #4a90e2;
  font-size: 9px;
  font-weight: 600;
}

.no-neighbors {
  text-align: center;
  padding: 40px;
  color: #aaa;
  font-size: 14px;
}

/* Quick Extract Button */
.quick-extract-btn {
  width: 100%;
  padding: 8px 12px;
  margin-top: 8px;
  background: #f59e0b;
  border: 2px solid #f59e0b;
  border-radius: 4px;
  color: #000;
  font-weight: 700;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.2s;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.quick-extract-btn:hover:not(:disabled) {
  background: #fbbf24;
  border-color: #fbbf24;
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(245, 158, 11, 0.3);
}

.quick-extract-btn:disabled {
  background: #555;
  border-color: #555;
  color: #aaa;
  cursor: not-allowed;
}

.nn-item .quick-extract-btn {
  font-size: 10px;
  padding: 6px 10px;
}

.extract-status {
  margin-top: 6px;
  padding: 6px 10px;
  background: rgba(74, 222, 128, 0.2);
  border: 1px solid rgba(74, 222, 128, 0.5);
  border-radius: 4px;
  color: #4ade80;
  font-size: 11px;
  font-weight: 600;
  text-align: center;
}
</style>
