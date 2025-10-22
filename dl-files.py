import yt_dlp
import os
import sys
import subprocess
import shutil
import re
import unicodedata

if len(sys.argv) != 3:
    print("Usage: python dl-files.py <studio_url> <live_url>")
    sys.exit(1)

studio_url = sys.argv[1]
live_url = sys.argv[2]

base_folder = os.path.abspath("files")

# Get Clean Song Name
def get_video_title(url):
    with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
        title = ydl.extract_info(url, download=False)['title']
        # Remove illegal characters
        title = re.sub(r'[<>:"/\\|?*]', '', title)
        # Convert to ASCII
        title = unicodedata.normalize('NFKD', title).encode('ascii', 'ignore').decode('ascii')
        # Remove leading/trailing spaces
        return title.strip()


song_folder = os.path.join(base_folder, get_video_title(live_url))
raw_folder = os.path.join(song_folder, "raw")

os.makedirs(raw_folder, exist_ok=True)

# Paths
live_video = os.path.join(song_folder, "live_performance.mp4")
temp_h264_video = os.path.join(raw_folder, "live_performance_h264.mp4")
live_audio_wav = os.path.join(raw_folder, "live_audio.wav")
studio_audio_wav = os.path.join(raw_folder, "studio_audio.wav")

# Download Options
live_video_opts = {
    "format": "bestvideo[ext=mp4][vcodec^=avc1][height<=720]+bestaudio[ext=m4a]/best[ext=mp4][vcodec^=avc1][height<=720]",
    "outtmpl": os.path.join(raw_folder, "live_video.mp4"),
    "merge_output_format": "mp4",
    "quiet": True, "no_warnings": True,
}

fallback_video_opts = live_video_opts.copy()
fallback_video_opts['format'] = "bestvideo[ext=mp4][height<=720]+bestaudio[ext=m4a]/best[ext=mp4][height<=720]"

audio_opts = lambda name: {
    "format": "bestaudio/best",
    "outtmpl": os.path.join(raw_folder, f"{name}.m4a"),
    "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "wav", "preferredquality": "192"}],
    "quiet": True, "no_warnings": True
}

# Download Video
print("Running dl-files.py...", flush=True)
print("Downloading live performance video...", flush=True)
try:
    with yt_dlp.YoutubeDL(live_video_opts) as ydl:
        ydl.download([live_url])
except Exception:
    print("Fallback to non-h264 video...")
    with yt_dlp.YoutubeDL(fallback_video_opts) as ydl:
        ydl.download([live_url])

shutil.move(os.path.join(raw_folder, "live_video.mp4"), live_video)

# Check codec
def get_video_codec(path):
    result = subprocess.run([
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=codec_name",
        "-of", "default=noprint_wrappers=1:nokey=1", path
    ], capture_output=True, text=True)
    return result.stdout.strip()

codec = get_video_codec(live_video)
print(f"Downloaded video codec: {codec}")

if codec != "h264":
    print("Converting to H.264...")
    subprocess.run([
        "ffmpeg", "-i", live_video, "-vf", "scale=-2:720",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "192k",
        temp_h264_video, "-y"
    ], check=True)
    os.replace(temp_h264_video, live_video)

# Download Audio
print("Downloading live audio...", flush=True)
with yt_dlp.YoutubeDL(audio_opts("live_audio")) as ydl:
    ydl.download([live_url])

print("Downloading studio audio...", flush=True)
with yt_dlp.YoutubeDL(audio_opts("studio_audio")) as ydl:
    ydl.download([studio_url])

# Move .wav outputs
for f in os.listdir(raw_folder):
    src = os.path.join(raw_folder, f)
    if f.startswith("live_audio") and f.endswith(".wav"):
        shutil.move(src, live_audio_wav)
    if f.startswith("studio_audio") and f.endswith(".wav"):
        shutil.move(src, studio_audio_wav)

# Save song name
with open(os.path.join(song_folder, "data.txt"), "w", encoding="utf-8") as f:
    f.write(f"song_name={os.path.basename(song_folder)}\n")

print(f"Files saved in: {song_folder}", flush=True)
print(f"Raw files saved in: {raw_folder}", flush=True)
print("Download complete!", flush=True)
