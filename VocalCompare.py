import os
import subprocess
import numpy as np
import pyqtgraph as pg
import vlc
import time

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QPushButton, QFileDialog, QLabel, QStatusBar, QFrame,
    QLineEdit, QTextEdit
)
from PyQt5.QtCore import QTimer, Qt

pg.setConfigOptions(antialias=True)

base_folder = os.path.abspath("files")
current_song_path = os.path.join(base_folder, "current_song.txt")
default_folder = os.path.join(base_folder, "default")

os.makedirs(default_folder, exist_ok=True)
if not os.path.exists(current_song_path):
    with open(current_song_path, "w", encoding="utf-8") as f:
        f.write("default")

app = QApplication([])
window = QWidget()
window.setWindowTitle("VocalCompare")

tabs = QTabWidget()
playback_tab = QWidget()
download_tab = QWidget()
playback_layout = QVBoxLayout()
download_layout = QVBoxLayout()
playback_tab.setLayout(playback_layout)
download_tab.setLayout(download_layout)
tabs.addTab(playback_tab, "Playback")
tabs.addTab(download_tab, "Download")

live_pitch = studio_pitch = live_time = studio_time = []
trimmed_start = 0.0
song_folder = None

def ensure_placeholder_files(folder):
    empty_array = np.zeros(100)
    empty_time = np.linspace(0, 10, 100)
    for name in ["live_pitch.npy", "studio_pitch.npy", "live_pitch_times.npy", "studio_pitch_times.npy"]:
        path = os.path.join(folder, name)
        if not os.path.exists(path):
            np.save(path, empty_time if "times" in name else empty_array)
    video = os.path.join(folder, "live_performance.mp4")
    if not os.path.exists(video):
        open(video, "wb").close()

video_widget = QFrame()
video_widget.setStyleSheet("background-color: black")
instance = vlc.Instance('--aout=directsound', '--file-caching=1000')
player = instance.media_player_new()

plot_widget = pg.PlotWidget()
plot_widget.setBackground('w')
plot_widget.setLabel('left', 'Pitch (Hz)')
plot_widget.getAxis("bottom").setStyle(showValues=False)
plot_widget.addLegend()
plot_widget.setYRange(100, 1000)
plot_widget.setXRange(0, 5)
plot_widget.setMouseEnabled(x=False, y=False)
plot_widget.getViewBox().setMenuEnabled(False)

background_studio_curve = plot_widget.plot([], [], pen=pg.mkPen((150, 150, 150, 180), width=1), name='Studio')
live_curve = plot_widget.plot([], [], pen=pg.mkPen('red'), name='Live')
playhead = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen('lightgray', width=1))
plot_widget.addItem(playhead)

status_bar_playback = QStatusBar()
status_bar_download = QStatusBar()
current_script_label = QLabel("")
current_script_label.setStyleSheet("color: gray")

log_output = QTextEdit()
log_output.setReadOnly(True)
log_output.setStyleSheet("background-color: #f0f0f0;")
log_output.setMinimumHeight(150)

timer = QTimer()
timer.setInterval(33)
last_frame_index = [-1]

def append_log(msg):
    log_output.append(msg)
    log_output.verticalScrollBar().setValue(log_output.verticalScrollBar().maximum())
    app.processEvents()

def load_data():
    global live_pitch, studio_pitch, live_time, studio_time, trimmed_start, song_folder
    with open(current_song_path, "r", encoding="utf-8") as f:
        song_name = f.read().strip()
    song_folder = os.path.join(base_folder, song_name)
    ensure_placeholder_files(song_folder)

    data = {}
    with open(os.path.join(song_folder, "data.txt"), encoding="utf-8") as f:
        for line in f:
            if "=" in line:
                k, v = line.strip().split("=", 1)
                data[k] = v

    live_pitch = np.load(os.path.join(song_folder, "live_pitch.npy"))
    studio_pitch = np.load(os.path.join(song_folder, "studio_pitch.npy"))
    live_time = np.load(os.path.join(song_folder, "live_pitch_times.npy"))
    studio_time = np.load(os.path.join(song_folder, "studio_pitch_times.npy"))
    trimmed_start = float(data.get("live_start", 0.0))

    background_studio_curve.setData(studio_time, studio_pitch)
    live_curve.setData([], [])

def update_plot():
    if player.is_playing():
        position_s = (player.get_time() / 1000) - trimmed_start
        frame_index = np.searchsorted(live_time, position_s)
        frame_index = min(max(frame_index, 1), len(live_pitch))
        if frame_index != last_frame_index[0]:
            live_curve.setData(live_time[:frame_index], live_pitch[:frame_index])
            last_frame_index[0] = frame_index
        playhead.setValue(position_s)
        if position_s > 5:
            plot_widget.setXRange(position_s - 5, position_s + 5, padding=0)

timer.timeout.connect(update_plot)

btn_load = QPushButton("Load Video")
def load_video():
    filepath, _ = QFileDialog.getOpenFileName(window, "Select Video", "", "Videos (*.mp4 *.mov *.avi)")
    if not filepath:
        return
    folder = os.path.dirname(filepath)
    with open(current_song_path, "w", encoding="utf-8") as f:
        f.write(os.path.basename(folder))
    load_data()
    media = instance.media_new(filepath)
    player.set_media(media)
    player.set_hwnd(video_widget.winId())
    status_bar_playback.showMessage("Video loaded.", 3000)

btn_load.clicked.connect(load_video)

btn_play = QPushButton("Play")
btn_play.clicked.connect(lambda: [player.play(), timer.start()])

btn_pause = QPushButton("Pause")
btn_pause.clicked.connect(lambda: [player.pause(), timer.stop()])

btn_reset = QPushButton("Reset")
def reset_playback():
    player.set_time(0)
    live_curve.setData([], [])
    last_frame_index[0] = -1
    status_bar_playback.showMessage("Reset.", 3000)

btn_reset.clicked.connect(reset_playback)

studio_url_input = QLineEdit()
studio_url_input.setPlaceholderText("Studio YouTube URL")
live_url_input = QLineEdit()
live_url_input.setPlaceholderText("Live YouTube URL")

btn_download = QPushButton("Download")
btn_process = QPushButton("Process Vocals")
btn_process.setEnabled(False)

def run_download():
    studio_url = studio_url_input.text()
    live_url = live_url_input.text()
    if not studio_url or not live_url:
        status_bar_download.showMessage("Enter both URLs", 3000)
        return

    append_log("Starting YouTube download...")
    current_script_label.setText("Downloading from YouTube...")
    status_bar_download.showMessage("Downloading...", 3000)

    try:
        process = subprocess.Popen(
            ["python", "dl-files.py", studio_url, live_url],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        new_song_folder = None
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                append_log(output.strip())
                if output.startswith("Files saved in:"):
                    new_song_folder = output.split("Files saved in:")[-1].strip()

        if process.returncode == 0 and new_song_folder:
            with open(current_song_path, "w", encoding="utf-8") as f:
                f.write(os.path.basename(new_song_folder))
            append_log("Download complete!")
            status_bar_download.showMessage("Download complete.", 3000)
            btn_process.setEnabled(True)
            load_data()
        else:
            status_bar_download.showMessage("Download failed.", 5000)

    except Exception as e:
        status_bar_download.showMessage(f"Error: {e}", 5000)

    current_script_label.setText("")

def run_processing():
    try:
        with open(current_song_path, "r", encoding="utf-8") as f:
            song_name = f.read().strip()
        folder_path = os.path.join(base_folder, song_name)

        for script in ["extract-vocals.py", "denoise-vocals.py", "sync-vocals.py", "pitch-extraction.py"]:
            append_log(f"Starting {script}...")
            current_script_label.setText(f"Running {script}...")
            status_bar_download.showMessage(f"Running {script}...", 3000)
            app.processEvents()

            start_time = time.time()
            subprocess.run(["python", script, folder_path], check=True)
            elapsed = time.time() - start_time
            append_log(f"Finished {script} in {elapsed:.1f}s")

        load_data()
        append_log("Processing complete!")
        status_bar_download.showMessage("Processing complete.", 3000)

    except Exception as e:
        status_bar_download.showMessage(f"Error: {e}", 5000)

    current_script_label.setText("")

btn_download.clicked.connect(run_download)
btn_process.clicked.connect(run_processing)

# Layouts
video_layout = QHBoxLayout()
video_layout.addWidget(video_widget, 2)
video_layout.addWidget(plot_widget, 3)

controls_layout = QHBoxLayout()
controls_layout.addWidget(btn_load)
controls_layout.addWidget(btn_play)
controls_layout.addWidget(btn_pause)
controls_layout.addWidget(btn_reset)

playback_layout.addLayout(video_layout)
playback_layout.addLayout(controls_layout)
playback_layout.addWidget(status_bar_playback)

studio_row = QHBoxLayout(); studio_row.addWidget(QLabel("Studio URL:")); studio_row.addWidget(studio_url_input)
live_row = QHBoxLayout(); live_row.addWidget(QLabel("Live URL:")); live_row.addWidget(live_url_input)
btn_row = QHBoxLayout(); btn_row.addWidget(btn_download); btn_row.addWidget(btn_process)

download_layout.addLayout(studio_row)
download_layout.addLayout(live_row)
download_layout.addLayout(btn_row)
download_layout.addWidget(current_script_label)
download_layout.addWidget(log_output)
download_layout.addWidget(status_bar_download)

main_layout = QVBoxLayout()
main_layout.addWidget(tabs)
window.setLayout(main_layout)
window.resize(1280, 720)
window.show()
app.exec_()
