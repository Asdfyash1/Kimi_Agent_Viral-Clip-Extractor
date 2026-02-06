# 🔥 Viral Clip Extractor API

A powerful API for extracting and analyzing viral clips from YouTube videos. Deployed on Vercel for serverless scalability.

## Features

- 📹 **Video Analysis** - Extract metadata and info from any YouTube video
- 🎯 **Viral Scoring** - AI-powered scoring based on hooks, emotions, and engagement
- 📝 **Transcript Extraction** - Get subtitles for specific time ranges
- ⬇️ **Download Links** - Generate direct download URLs for clips
- ⚡ **Fast & Scalable** - Serverless deployment on Vercel

## API Endpoints

### Base URL
```
https://your-project.vercel.app
```

### Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API info |
| `/health` | GET | Health check |
| `/extract` | POST | Extract video info |
| `/analyze` | POST | Full viral clip analysis |
| `/score` | POST | Score a specific time range |
| `/transcript` | POST | Get transcript for range |
| `/download` | POST | Get download URL for clip |

## Quick Start

### 1. Analyze a Video for Viral Clips

```bash
curl -X POST https://your-project.vercel.app/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://youtube.com/watch?v=VIDEO_ID",
    "num_clips": 5,
    "clip_length": 40,
    "quality": "720"
  }'
```

**Response:**
```json
{
  "success": true,
  "video_id": "VIDEO_ID",
  "video_title": "Video Title",
  "clips": [
    {
      "start": 120,
      "end": 160,
      "duration": 40,
      "viral_score": 85,
      "reasons": ["Hooks: shocking, exposed", "Emotion: surprised", "Optimal duration"],
      "transcript_preview": "You won't believe what happened...",
      "start_formatted": "2:00",
      "end_formatted": "2:40",
      "youtube_url": "https://youtube.com/clip/VIDEO_ID?start=120&end=160"
    }
  ]
}
```

### 2. Extract Video Info Only

```bash
curl -X POST https://your-project.vercel.app/extract \
  -H "Content-Type: application/json" \
  -d '{"url": "https://youtube.com/watch?v=VIDEO_ID"}'
```

### 3. Score a Specific Time Range

```bash
curl -X POST https://your-project.vercel.app/score \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://youtube.com/watch?v=VIDEO_ID",
    "start": "2:00",
    "end": "2:40"
  }'
```

### 4. Get Transcript

```bash
curl -X POST https://your-project.vercel.app/transcript \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://youtube.com/watch?v=VIDEO_ID",
    "start": 120,
    "end": 180
  }'
```

### 5. Get Download URL

```bash
curl -X POST https://your-project.vercel.app/download \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://youtube.com/watch?v=VIDEO_ID",
    "start": "2:00",
    "end": "2:40",
    "quality": "720"
  }'
```

## Deployment

### Deploy to Vercel (One Click)

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/yourusername/viral-clip-extractor-api)

### Manual Deployment

1. **Fork/Clone this repository**
   ```bash
   git clone https://github.com/yourusername/viral-clip-extractor-api.git
   cd viral-clip-extractor-api
   ```

2. **Install Vercel CLI**
   ```bash
   npm i -g vercel
   ```

3. **Deploy**
   ```bash
   vercel --prod
   ```

### GitHub + Vercel Integration

1. Push this code to your GitHub repository
2. Go to [vercel.com](https://vercel.com)
3. Click "New Project"
4. Import your GitHub repository
5. Vercel will auto-detect Python and deploy

## Configuration Options

### `/analyze` Endpoint Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `url` | string | required | YouTube video URL |
| `num_clips` | int | 5 | Number of clips to return |
| `clip_length` | int | 40 | Target clip length in seconds |
| `window_step` | int | 10 | Sliding window step size |
| `quality` | string | "720" | Video quality (360, 720, 1080) |

### Viral Scoring Algorithm

The API scores clips based on:

- **Hook Words** (up to 50 pts): shocking, unbelievable, secret, exposed, etc.
- **Emotion Words** (up to 30 pts): laugh, cry, angry, surprised, etc.
- **Conflict Detection** (20 pts): but, however, argument, fight, etc.
- **Duration Bonus** (10 pts): Optimal 25-60 second clips
- **Content Density** (5 pts): Transcript word count

## Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run locally
python api/index.py

# API will be available at http://localhost:5000
```

## Project Structure

```
viral-clip-extractor-api/
├── api/
│   └── index.py          # Main API application
├── requirements.txt      # Python dependencies
├── vercel.json          # Vercel configuration
└── README.md            # This file
```

## Limitations

- **Vercel Timeout**: 60 seconds max (configured in vercel.json)
- **Video Length**: Very long videos (>2 hours) may timeout
- **Transcripts**: Only English subtitles are supported
- **Download URLs**: Expire after a few hours (YouTube limitation)

## Troubleshooting

### Timeout Issues
- Reduce `clip_length` or `num_clips`
- Use `/extract` first to check video duration

### No Transcript Found
- Video may not have captions
- Try auto-generated captions

### Download URL Not Working
- URLs expire quickly; generate fresh ones when needed
- Some videos may be restricted

## Tech Stack

- **Flask** - Web framework
- **yt-dlp** - YouTube video extraction
- **Vercel** - Serverless deployment
- **Python 3.9** - Runtime

## License

MIT License - feel free to use and modify!

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

---

Made with 🔥 by [Your Name]
