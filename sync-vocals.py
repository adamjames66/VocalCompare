import os
import sys
import librosa
import soundfile as sf
import numpy as np
from dtw import dtw
from scipy.interpolate import interp1d

# Path Setup
if len(sys.argv) != 2:
    print("Usage: python sync-vocals.py <song_folder>")
    sys.exit(1)

song_folder = sys.argv[1]
raw_folder = os.path.join(song_folder, "raw")

data = {}
with open(os.path.join(song_folder, "data.txt"), encoding="utf-8") as f:
    for line in f:
        if "=" in line:
            k, v = line.strip().split("=", 1)
            data[k] = v

studio_vocals = os.path.join(raw_folder, "studio_vocals_denoised.wav")
live_vocals = os.path.join(raw_folder, "live_vocals_denoised.wav")
warped_studio_output = os.path.join(song_folder, "studio_vocals_warped.wav")

# Parameters
sr = 22050
hop_length = 1024

# Helpers
def load_audio(path):
    if not os.path.exists(path):
        print(f"Error: File not found -> {path}")
        sys.exit(1)
    audio, _ = librosa.load(path, sr=sr, mono=True)
    return audio

def extract_chroma(y):
    return librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=hop_length)

def compute_alignment_path(chroma_ref, chroma_target):
    dist_fn = lambda x, y: np.linalg.norm(x - y, ord=1)
    _, _, _, path = dtw(chroma_ref.T, chroma_target.T, dist=dist_fn)
    return path

def warp_audio_interpolated(y, path_ref, path_target):
    times_ref = np.array(path_ref) * hop_length / sr
    times_target = np.array(path_target) * hop_length / sr

    time_map = interp1d(times_target, times_ref, kind='linear', fill_value='extrapolate')
    target_duration = np.max(times_target)
    target_times = np.linspace(0, target_duration, int(target_duration * sr))

    studio_time = np.linspace(0, len(y) / sr, num=len(y))
    warped_audio = np.interp(target_times, studio_time, y)

    return np.nan_to_num(warped_audio, nan=0.0, posinf=1.0, neginf=-1.0)

# Main Process
print("Starting vocal sync...", flush=True)

print("Loading audio...", flush=True)
studio_audio = load_audio(studio_vocals)
live_audio = load_audio(live_vocals)

print("Extracting chroma features...", flush=True)
chroma_studio = extract_chroma(studio_audio)
chroma_live = extract_chroma(live_audio)

print("Computing DTW alignment path...", flush=True)
path_studio, path_live = compute_alignment_path(chroma_studio, chroma_live)

print("Warping studio audio to sync with live performance...", flush=True)
warped_studio = warp_audio_interpolated(studio_audio, path_studio, path_live)

print("Saving warped audio...", flush=True)
sf.write(warped_studio_output, warped_studio, sr)

print("Alignment complete. Warped studio file saved.")
