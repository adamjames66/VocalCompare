import os
import subprocess
import shutil
import sys

# Path Setup
if len(sys.argv) != 2:
    print("Usage: python extract-vocals.py <song_folder>")
    sys.exit(1)

song_folder = sys.argv[1]
raw_folder = os.path.join(song_folder, "raw")

data = {}
with open(os.path.join(song_folder, "data.txt"), encoding="utf-8") as f:
    for line in f:
        if "=" in line:
            k, v = line.strip().split("=", 1)
            data[k] = v

live_audio = os.path.join(raw_folder, "live_audio.wav")
studio_audio = os.path.join(raw_folder, "studio_audio.wav")

live_vocals_output = os.path.join(raw_folder, "live_vocals.wav")
studio_vocals_output = os.path.join(raw_folder, "studio_vocals.wav")

temp_demucs_out = os.path.join(raw_folder, "demucs_temp")

def separate_vocals(input_file, final_output_path):
    if not os.path.exists(input_file):
        print(f"Warning: {input_file} not found. Skipping.", flush=True)
        return

    print(f"Separating vocals for: {input_file}", flush=True)

    subprocess.run([
        "python", "-m", "demucs",
        "-n", "htdemucs",
        "--out", temp_demucs_out,
        "--two-stems", "vocals",
        input_file
    ], check=True)

    filename_only = os.path.splitext(os.path.basename(input_file))[0]
    vocals_source = os.path.join(temp_demucs_out, "htdemucs", filename_only, "vocals.wav")

    if os.path.exists(vocals_source):
        shutil.move(vocals_source, final_output_path)
        print(f"Saved vocals to: {final_output_path}", flush=True)
    else:
        print(f"Error: Expected vocals file not found for {input_file}", flush=True)

# Run for both live and studio
separate_vocals(live_audio, live_vocals_output)
separate_vocals(studio_audio, studio_vocals_output)
