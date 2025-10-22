import os
import sys
import librosa
import numpy as np

# Path Setup
if len(sys.argv) != 2:
    print("Usage: python pitch-extraction.py <song_folder>")
    sys.exit(1)

song_folder = sys.argv[1]
raw_folder = os.path.join(song_folder, "raw")

data = {}
with open(os.path.join(song_folder, "data.txt"), encoding="utf-8") as f:
    for line in f:
        if "=" in line:
            k, v = line.strip().split("=", 1)
            data[k] = v

# Audio Settings
sr = 22050
hop_length = 256

# Input Files
live_vocals = os.path.join(raw_folder, "live_vocals_denoised.wav")
studio_vocals = os.path.join(song_folder, "studio_vocals_warped.wav")

# Output Files
live_pitch_file = os.path.join(song_folder, "live_pitch.npy")
studio_pitch_file = os.path.join(song_folder, "studio_pitch.npy")
live_time_file = os.path.join(song_folder, "live_pitch_times.npy")
studio_time_file = os.path.join(song_folder, "studio_pitch_times.npy")

def extract_pitch(y, sr, fmin=80, fmax=1000):
    f0, _, _ = librosa.pyin(
        y=y,
        sr=sr,
        fmin=fmin,
        fmax=fmax,
        frame_length=1024,
        hop_length=hop_length
    )
    return f0

def save_pitch_data():
    print("Extracting pitch from live vocals...", flush=True)
    live_y, live_sr = librosa.load(live_vocals, sr=sr)
    live_pitch = extract_pitch(live_y, live_sr)
    live_times = librosa.frames_to_time(np.arange(len(live_pitch)), sr=live_sr, hop_length=hop_length)
    np.save(live_pitch_file, live_pitch)
    np.save(live_time_file, live_times)

    print("Extracting pitch from studio vocals...", flush=True)
    studio_y, studio_sr = librosa.load(studio_vocals, sr=sr)
    studio_pitch = extract_pitch(studio_y, studio_sr)
    studio_times = librosa.frames_to_time(np.arange(len(studio_pitch)), sr=studio_sr, hop_length=hop_length)
    np.save(studio_pitch_file, studio_pitch)
    np.save(studio_time_file, studio_times)

    print(f"Saved pitch data to:\n  {live_pitch_file}\n  {studio_pitch_file}", flush=True)

save_pitch_data()
