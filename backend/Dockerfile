# Use Python 3.11 Slim image (Fixes deprecation warnings)
FROM python:3.11-slim

# Install system dependencies (FFmpeg)
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first (for caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py .
COPY api/ api/

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Expose port (Render sets PORT env var)
EXPOSE 5000

# Run with Uvicorn (FastAPI's recommended server)
# --host 0.0.0.0: Listen on all interfaces
# --port $PORT: Use Render's dynamic port
# --workers 1: Single worker to save RAM
# --timeout-keep-alive 120: 2-minute timeout for long processing
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-5000} --workers 1 --timeout-keep-alive 120
