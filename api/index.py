"""
Viral Clip Extractor API
Deploy to Vercel for YouTube viral clip analysis
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp
import requests
from io import StringIO
import os
import re
from typing import Dict, List, Optional, Any

app = Flask(__name__)
CORS(app)

# ============== CONFIGURATION ==============
DEFAULT_CLIP_LENGTH = 40
DEFAULT_WINDOW_STEP = 10
DEFAULT_MIN_CLIP_LENGTH = 25
DEFAULT_MAX_CLIP_LENGTH = 60

HOOK_WORDS = [
    "wait", "shocking", "unbelievable", "secret", "crazy", "exposed", "omg", "wtf",
    "plot twist", "insane", "cheating", "stunning", "mind blowing", "truth", "lie",
    "revealed", "hidden", "discover", "amazing", "incredible", "must see", "urgent"
]

EMOTION_WORDS = [
    "laugh", "cry", "angry", "shocked", "surprised", "scream", "love", "hate",
    "disgusted", "horrified", "amazed", "excited", "sad", "happy", "furious"
]

# ============== UTILITY FUNCTIONS ==============

def extract_video_id(url: str) -> Optional[str]:
    """Extract YouTube video ID from various URL formats"""
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/|youtube\.com\/v\/|youtube\.com\/shorts\/)([a-zA-Z0-9_-]{11})',
        r'^([a-zA-Z0-9_-]{11})$'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def time_to_seconds(t) -> float:
    """Convert time string to seconds"""
    if isinstance(t, (int, float)):
        return float(t)
    if ':' in str(t):
        parts = list(map(int, str(t).split(':')))
        if len(parts) == 3:
            return parts[0] * 3600 + parts[1] * 60 + parts[2]
        elif len(parts) == 2:
            return parts[0] * 60 + parts[1]
        elif len(parts) == 1:
            return parts[0]
    return float(t)

def seconds_to_time(s: float) -> str:
    """Convert seconds to MM:SS format"""
    minutes = int(s // 60)
    seconds = int(s % 60)
    return f"{minutes}:{seconds:02d}"

def parse_vtt_content(vtt_text: str) -> List[Dict]:
    """Parse VTT subtitle content"""
    segments = []
    lines = vtt_text.strip().split('\n')
    
    # Skip WEBVTT header
    i = 0
    while i < len(lines) and not '-->' in lines[i]:
        i += 1
    
    current_text = []
    current_start = None
    current_end = None
    
    while i < len(lines):
        line = lines[i].strip()
        
        if '-->' in line:
            # Save previous segment if exists
            if current_text and current_start is not None:
                segments.append({
                    'start': current_start,
                    'end': current_end,
                    'text': ' '.join(current_text)
                })
            
            # Parse timestamp
            times = line.split('-->')
            if len(times) == 2:
                start_str = times[0].strip().split('.')[0]
                end_str = times[1].strip().split()[0].split('.')[0]
                
                current_start = time_to_seconds(start_str)
                current_end = time_to_seconds(end_str)
                current_text = []
        elif line and not line.startswith('NOTE') and not line.startswith('STYLE'):
            # Clean HTML tags
            clean_line = re.sub(r'<[^>]+>', '', line)
            if clean_line:
                current_text.append(clean_line)
        
        i += 1
    
    # Don't forget the last segment
    if current_text and current_start is not None:
        segments.append({
            'start': current_start,
            'end': current_end,
            'text': ' '.join(current_text)
        })
    
    return segments

def parse_srt_content(srt_text: str) -> List[Dict]:
    """Parse SRT subtitle content"""
    segments = []
    blocks = re.split(r'\n\n+', srt_text.strip())
    
    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) >= 2:
            # Check if first line is a number (subtitle index)
            if lines[0].strip().isdigit():
                time_line = lines[1]
                text_lines = lines[2:]
            else:
                time_line = lines[0]
                text_lines = lines[1:]
            
            # Parse time line
            time_match = re.match(r'(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})', time_line)
            if time_match:
                start_str = time_match.group(1).replace(',', '.')
                end_str = time_match.group(2).replace(',', '.')
                text = ' '.join(text_lines)
                # Clean HTML tags
                text = re.sub(r'<[^>]+>', '', text)
                
                segments.append({
                    'start': time_to_seconds(start_str),
                    'end': time_to_seconds(end_str),
                    'text': text
                })
    
    return segments

# ============== CORE CLASSES ==============

class ViralClipExtractor:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }
    
    def extract_video_info(self, url: str) -> Dict:
        """Get video metadata"""
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'simulate': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            chapters = []
            if 'chapters' in info and info['chapters']:
                for ch in info['chapters']:
                    chapters.append({
                        "start": ch['start_time'],
                        "end": ch.get('end_time') or ch['start_time'] + DEFAULT_CLIP_LENGTH,
                        "title": ch.get('title', 'Untitled')
                    })
            
            thumbnails = []
            if 'thumbnails' in info:
                thumbnails = [t.get('url') for t in info['thumbnails'] if t.get('url')][-5:]
            
            return {
                "id": info.get("id"),
                "title": info.get("title"),
                "uploader": info.get("uploader"),
                "duration": info.get("duration"),
                "description": info.get("description", "")[:500],
                "view_count": info.get("view_count"),
                "like_count": info.get("like_count"),
                "upload_date": info.get("upload_date"),
                "thumbnail": info.get("thumbnail"),
                "thumbnails": thumbnails,
                "chapters": chapters
            }
    
    def get_transcript(self, url: str, start: float, end: float) -> str:
        """Get transcript for specific time range"""
        ydl_opts = {
            'skip_download': True,
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': ['en'],
            'quiet': True,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                sub_url = None
                sub_format = None
                
                # Try manual subtitles first
                if 'subtitles' in info and 'en' in info['subtitles']:
                    for sub in info['subtitles']['en']:
                        if sub.get('ext') in ['vtt', 'srt']:
                            sub_url = sub.get('url')
                            sub_format = sub.get('ext')
                            break
                
                # Fall back to auto-generated
                if not sub_url and 'automatic_captions' in info and 'en' in info['automatic_captions']:
                    for sub in info['automatic_captions']['en']:
                        if sub.get('ext') in ['vtt', 'srt', 'json3']:
                            sub_url = sub.get('url')
                            sub_format = sub.get('ext')
                            break
                
                if not sub_url:
                    return ""
                
                # Fetch subtitle content
                response = requests.get(sub_url, headers=self.headers, timeout=15)
                response.raise_for_status()
                sub_text = response.text
                
                # Parse based on format
                segments = []
                if sub_format == 'vtt' or sub_url.endswith('.vtt'):
                    segments = parse_vtt_content(sub_text)
                elif sub_format == 'srt' or sub_url.endswith('.srt'):
                    segments = parse_srt_content(sub_text)
                elif sub_format == 'json3' or sub_url.endswith('.json'):
                    try:
                        import json
                        data = json.loads(sub_text)
                        if 'events' in data:
                            for event in data['events']:
                                if 'segs' in event:
                                    start_time = event.get('tStartMs', 0) / 1000
                                    duration = event.get('dDurationMs', 0) / 1000
                                    text = ''.join(seg.get('utf8', '') for seg in event['segs'])
                                    segments.append({
                                        'start': start_time,
                                        'end': start_time + duration,
                                        'text': text
                                    })
                    except:
                        pass
                
                # Filter to time range
                relevant = [
                    seg["text"] for seg in segments
                    if seg["end"] >= start and seg["start"] <= end and seg["text"].strip()
                ]
                return " ".join(relevant)
                
        except Exception as e:
            print(f"Transcript error: {e}")
            return ""
    
    def score_clip(self, url: str, start: float, end: float, transcript: str = None) -> Dict:
        """Calculate viral score for clip"""
        if transcript is None:
            transcript = self.get_transcript(url, start, end).lower()
        else:
            transcript = transcript.lower()
        
        score = 0
        reasons = []
        
        # Hook words (up to 50 points)
        hooks = [w for w in HOOK_WORDS if w in transcript]
        hook_score = min(len(hooks) * 10, 50)
        score += hook_score
        if hooks:
            reasons.append(f"Hooks: {', '.join(hooks[:3])}")
        
        # Emotion words (up to 30 points)
        emotions = [w for w in EMOTION_WORDS if w in transcript]
        emotion_score = min(len(emotions) * 6, 30)
        score += emotion_score
        if emotions:
            reasons.append(f"Emotion: {', '.join(emotions[:2])}")
        
        # Conflict indicators (20 points)
        conflict_words = ["but", "however", "argument", "fight", "wrong", "disagree", "no way", "impossible"]
        if any(w in transcript for w in conflict_words):
            score += 20
            reasons.append("Conflict detected")
        
        # Duration bonus
        duration = end - start
        if DEFAULT_MIN_CLIP_LENGTH <= duration <= DEFAULT_MAX_CLIP_LENGTH:
            score += 10
            reasons.append("Optimal duration")
        elif duration < DEFAULT_MIN_CLIP_LENGTH:
            score -= 10
            reasons.append("Short clip")
        elif duration > DEFAULT_MAX_CLIP_LENGTH:
            score -= 5
            reasons.append("Long clip")
        
        # Transcript quality bonus
        word_count = len(transcript.split())
        if word_count > 10:
            score += 5
            reasons.append("Good content density")
        
        return {
            "start": start,
            "end": end,
            "duration": round(duration, 1),
            "viral_score": max(0, min(score, 100)),
            "reasons": reasons,
            "transcript_preview": transcript[:150] + "..." if len(transcript) > 150 else transcript,
            "word_count": word_count
        }
    
    def generate_candidates(self, video_info: Dict, clip_length: int = None, window_step: int = None) -> List[Dict]:
        """Generate candidate clips"""
        duration = video_info.get("duration", 0)
        clip_length = clip_length or DEFAULT_CLIP_LENGTH
        window_step = window_step or DEFAULT_WINDOW_STEP
        candidates = []
        
        # Use chapters if available
        if video_info.get("chapters"):
            for ch in video_info["chapters"]:
                clip_start = ch["start"]
                clip_end = min(ch["end"], clip_start + clip_length)
                if clip_end - clip_start >= DEFAULT_MIN_CLIP_LENGTH:
                    candidates.append({
                        "start": clip_start,
                        "end": clip_end,
                        "title": ch.get("title", "Untitled")
                    })
        else:
            # Sliding windows
            for start in range(0, int(duration) - clip_length, window_step):
                candidates.append({
                    "start": start,
                    "end": min(start + clip_length, duration)
                })
        
        return candidates
    
    def get_download_url(self, url: str, start: float, end: float, quality: str = "720") -> Dict:
        """Get download information for a clip"""
        ydl_opts = {
            'format': f'bestvideo[height<={quality}]+bestaudio/best[height<={quality}]/best',
            'quiet': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = []
            
            for fmt in info.get('formats', []):
                if fmt.get('vcodec') != 'none' and fmt.get('acodec') != 'none':
                    height = fmt.get('height', 0)
                    if height and height <= int(quality):
                        formats.append({
                            'format_id': fmt.get('format_id'),
                            'ext': fmt.get('ext'),
                            'quality': height,
                            'url': fmt.get('url'),
                            'filesize': fmt.get('filesize'),
                            'filesize_approx': fmt.get('filesize_approx')
                        })
            
            # Sort by quality descending
            formats.sort(key=lambda x: x.get('quality', 0) or 0, reverse=True)
            
            return {
                'video_id': info.get('id'),
                'title': info.get('title'),
                'start': start,
                'end': end,
                'start_formatted': seconds_to_time(start),
                'end_formatted': seconds_to_time(end),
                'formats': formats[:5],
                'download_url': formats[0].get('url') if formats else None
            }

# ============== API ROUTES ==============

@app.route('/', methods=['GET'])
def index():
    """Root endpoint - API info"""
    return jsonify({
        "name": "Viral Clip Extractor API",
        "version": "1.0.0",
        "description": "Extract and analyze viral clips from YouTube videos",
        "endpoints": {
            "/": "API information (this endpoint)",
            "/health": "Health check",
            "/analyze": "POST - Analyze a YouTube video for viral clips",
            "/extract": "POST - Extract video info only",
            "/score": "POST - Score a specific time range",
            "/download": "POST - Get download URL for a clip"
        },
        "documentation": "See README.md for detailed usage"
    })

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "viral-clip-extractor"
    })

@app.route('/extract', methods=['POST'])
def extract_video():
    """Extract basic video information"""
    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({"error": "Missing 'url' parameter"}), 400
        
        url = data['url']
        video_id = extract_video_id(url)
        
        if not video_id:
            return jsonify({"error": "Invalid YouTube URL"}), 400
        
        extractor = ViralClipExtractor()
        info = extractor.extract_video_info(url)
        
        return jsonify({
            "success": True,
            "video_id": video_id,
            "data": info
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/analyze', methods=['POST'])
def analyze_video():
    """Full viral clip analysis"""
    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({"error": "Missing 'url' parameter"}), 400
        
        url = data['url']
        video_id = extract_video_id(url)
        
        if not video_id:
            return jsonify({"error": "Invalid YouTube URL"}), 400
        
        # Configuration options
        num_clips = data.get('num_clips', 5)
        clip_length = data.get('clip_length', DEFAULT_CLIP_LENGTH)
        window_step = data.get('window_step', DEFAULT_WINDOW_STEP)
        quality = data.get('quality', '720')
        
        extractor = ViralClipExtractor()
        
        # Get video info
        video_info = extractor.extract_video_info(url)
        
        # Generate candidates
        candidates = extractor.generate_candidates(video_info, clip_length, window_step)
        
        # Score candidates
        scored_clips = []
        for i, cand in enumerate(candidates):
            score_data = extractor.score_clip(url, cand['start'], cand['end'])
            score_data['title'] = cand.get('title', f'Clip {i+1}')
            scored_clips.append(score_data)
        
        # Sort by viral score
        scored_clips.sort(key=lambda x: x['viral_score'], reverse=True)
        
        # Select top non-overlapping clips
        final_clips = []
        used_ranges = []
        
        for clip in scored_clips:
            # Check for overlap
            overlaps = False
            for used in used_ranges:
                if not (clip['end'] <= used['start'] or clip['start'] >= used['end']):
                    overlaps = True
                    break
            
            if not overlaps:
                final_clips.append(clip)
                used_ranges.append(clip)
                
                if len(final_clips) >= num_clips:
                    break
        
        # Add formatted times and download info
        for clip in final_clips:
            clip['start_formatted'] = seconds_to_time(clip['start'])
            clip['end_formatted'] = seconds_to_time(clip['end'])
            clip['youtube_url'] = f"https://youtube.com/clip/{video_id}?start={int(clip['start'])}&end={int(clip['end'])}"
        
        return jsonify({
            "success": True,
            "video_id": video_id,
            "video_title": video_info.get('title'),
            "video_duration": video_info.get('duration'),
            "configuration": {
                "clip_length": clip_length,
                "window_step": window_step,
                "quality": quality,
                "requested_clips": num_clips,
                "returned_clips": len(final_clips)
            },
            "clips": final_clips
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/score', methods=['POST'])
def score_range():
    """Score a specific time range"""
    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({"error": "Missing 'url' parameter"}), 400
        
        if 'start' not in data or 'end' not in data:
            return jsonify({"error": "Missing 'start' or 'end' parameter"}), 400
        
        url = data['url']
        start = time_to_seconds(data['start'])
        end = time_to_seconds(data['end'])
        
        video_id = extract_video_id(url)
        if not video_id:
            return jsonify({"error": "Invalid YouTube URL"}), 400
        
        extractor = ViralClipExtractor()
        score_data = extractor.score_clip(url, start, end)
        score_data['start_formatted'] = seconds_to_time(score_data['start'])
        score_data['end_formatted'] = seconds_to_time(score_data['end'])
        
        return jsonify({
            "success": True,
            "video_id": video_id,
            "clip": score_data
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/download', methods=['POST'])
def get_download():
    """Get download URL for a clip"""
    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({"error": "Missing 'url' parameter"}), 400
        
        if 'start' not in data or 'end' not in data:
            return jsonify({"error": "Missing 'start' or 'end' parameter"}), 400
        
        url = data['url']
        start = time_to_seconds(data['start'])
        end = time_to_seconds(data['end'])
        quality = data.get('quality', '720')
        
        video_id = extract_video_id(url)
        if not video_id:
            return jsonify({"error": "Invalid YouTube URL"}), 400
        
        extractor = ViralClipExtractor()
        download_info = extractor.get_download_url(url, start, end, quality)
        
        return jsonify({
            "success": True,
            "video_id": video_id,
            "download_info": download_info
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/transcript', methods=['POST'])
def get_transcript():
    """Get transcript for a specific time range"""
    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({"error": "Missing 'url' parameter"}), 400
        
        url = data['url']
        start = time_to_seconds(data.get('start', 0))
        end = time_to_seconds(data.get('end', 60))
        
        video_id = extract_video_id(url)
        if not video_id:
            return jsonify({"error": "Invalid YouTube URL"}), 400
        
        extractor = ViralClipExtractor()
        transcript = extractor.get_transcript(url, start, end)
        
        return jsonify({
            "success": True,
            "video_id": video_id,
            "start": start,
            "end": end,
            "start_formatted": seconds_to_time(start),
            "end_formatted": seconds_to_time(end),
            "transcript": transcript,
            "word_count": len(transcript.split()) if transcript else 0
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# ============== VERCEL HANDLER ==============

# For Vercel serverless deployment
def handler(request, context):
    """Vercel serverless handler"""
    with app.request_context(request.environ):
        return app(request.environ, lambda status, headers: None)

# Local development
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
