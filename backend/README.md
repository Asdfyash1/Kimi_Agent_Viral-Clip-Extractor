# Backend API - Viral Clip Extractor

This folder contains the complete backend API for the Viral Clip Extractor.

## Structure

```
backend/
├── api/
│   ├── index.py           # Main Flask API
│   └── proxy_manager.py   # Proxy management
├── ffmpeg/                # FFmpeg binaries
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker configuration
└── render.yaml           # Render deployment config
```

## Running Locally

```bash
cd backend
pip install -r requirements.txt
python api/index.py
```

## Environment Variables

See main README.md for full configuration details.

## Deployment

This backend is configured for Render deployment. The `render.yaml` file contains all deployment settings.
