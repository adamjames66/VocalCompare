import os
import sys
import librosa
import soundfile as sf
import noisereduce as nr
from pydub import AudioSegment
import numpy as np

print("Denoising vocals", flush=True)

# Path Setup
if len(sys.argv) != 2:
    print("Usage: python denoise-vocals.py <song_folder>")
    sys.exit(1)

song_folder = sys.argv[1]
raw_folder = os.path.join(song_folder, "raw")

data = {}
data_txt = os.path.join(song_folder, "data.txt")
with open(data_txt, encoding="utf-8") as f:
    for line in f:
        if "=" in line:
            k, v = line.strip().split("=", 1)
            data[k] = v

studio_vocals = os.path.join(raw_folder, "studio_vocals.wav")
live_vocals = os.path.join(raw_folder, "live_vocals.wav")

studio_denoised_file = os.path.join(raw_folder, "studio_vocals_denoised.wav")
live_denoised_file = os.path.join(raw_folder, "live_vocals_denoised.wav")

studio_trimmed_temp = os.path.join(raw_folder, "studio_vocals_trimmed.wav")
live_trimmed_temp = os.path.join(raw_folder, "live_vocals_trimmed.wav")

# Helpers
def reduce_constant_echo(y, sr):
    noise_sample = y[int(0 * sr): int(2 * sr)]
    return nr.reduce_noise(y=y, sr=sr, y_noise=noise_sample, prop_decrease=0.8)

def trim_silence(audio, silence_thresh=-40):
    start_trim = 0
    end_trim = len(audio)

    for i in range(len(audio)):
        if audio[i:i+1].dBFS > silence_thresh:
            start_trim = i
            break
    for i in range(len(audio) - 1, 0, -1):
        if audio[i:i+1].dBFS > silence_thresh:
            end_trim = i + 1
            break

    return audio[start_trim:end_trim], start_trim

def normalize_audio(y, sr, target_dB=-20):
    rms = np.sqrt(np.mean(y**2))
    gain = 10 ** ((target_dB - 20 * np.log10(rms)) / 20)
    return y * gain

# Processing
print("Loading vocals...", flush=True)
studio_audio, sr_studio = librosa.load(studio_vocals, sr=None)
live_audio, sr_live = librosa.load(live_vocals, sr=None)

print("Reducing noise...", flush=True)
studio_denoised = reduce_constant_echo(studio_audio, sr_studio)
live_denoised = reduce_constant_echo(live_audio, sr_live)

sf.write(studio_denoised_file, studio_denoised, sr_studio)
sf.write(live_denoised_file, live_denoised, sr_live)

print("Trimming silence...", flush=True)
studio_audio_pydub = AudioSegment.from_wav(studio_denoised_file)
live_audio_pydub = AudioSegment.from_wav(live_denoised_file)

studio_trimmed, studio_start_frame = trim_silence(studio_audio_pydub)
live_trimmed, live_start_frame = trim_silence(live_audio_pydub)

studio_trimmed.export(studio_trimmed_temp, format="wav")
live_trimmed.export(live_trimmed_temp, format="wav")

print("Normalizing audio...", flush=True)
studio_trimmed_np, _ = librosa.load(studio_trimmed_temp, sr=sr_studio)
live_trimmed_np, _ = librosa.load(live_trimmed_temp, sr=sr_live)

studio_final = normalize_audio(studio_trimmed_np, sr_studio)
live_final = normalize_audio(live_trimmed_np, sr_live)

sf.write(studio_denoised_file, studio_final, sr_studio)
sf.write(live_denoised_file, live_final, sr_live)

os.remove(studio_trimmed_temp)
os.remove(live_trimmed_temp)

# Save updated timing
studio_start_time = studio_start_frame / 1000.0
live_start_time = live_start_frame / 1000.0

data['studio_start'] = f"{studio_start_time:.3f}"
data['live_start'] = f"{live_start_time:.3f}"

with open(data_txt, "w", encoding="utf-8") as f:
    for k, v in data.items():
        f.write(f"{k}={v}\n")

print("Denoising, trimming, and normalization complete.", flush=True)
