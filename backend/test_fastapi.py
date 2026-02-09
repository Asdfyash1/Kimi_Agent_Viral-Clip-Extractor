import logging
import json
from main import ViralClipExtractor, extract_video_id

logging.basicConfig(level=logging.INFO)

def test():
    url = "https://youtu.be/uVkFrqugXFQ"
    nvidia_key = "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"
    
    print("=== FASTAPI LOCAL TEST ===")
    print(f"URL: {url}")
    
    extractor = ViralClipExtractor()
    
    # 1. Video Info
    print("\n1. Fetching Video Info...")
    video_info = extractor.extract_video_info(url)
    print(f"   Title: {video_info.get('title')}")
    print(f"   Duration: {video_info.get('duration')} seconds")
    
    # 2. Transcript
    print("\n2. Fetching Transcript...")
    transcript = extractor.fetch_full_transcript(url)
    print(f"   Transcript Segments: {len(transcript)}")
    if transcript:
        print(f"   Sample: {transcript[0]}")
    else:
        print("   [FAIL] No transcript found!")
        return
    
    # 3. AI Analysis
    print("\n3. Running Nvidia AI Analysis...")
    clips = extractor.analyze_with_nvidia(transcript, nvidia_key)
    print(f"   Clips Found: {len(clips)}")
    
    # 4. Final Response
    response = {
        "success": True,
        "video_id": extract_video_id(url),
        "video_title": video_info.get('title'),
        "video_duration": video_info.get('duration'),
        "mode": "nvidia",
        "clips": clips,
        "clips_count": len(clips)
    }
    
    print("\n=== FINAL RESPONSE ===")
    print(json.dumps(response, indent=2))

if __name__ == "__main__":
    test()
