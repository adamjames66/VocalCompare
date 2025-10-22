## Overview
VocalCompare is a project for comparing live vocal performances to a song's studio recording.

## Demo Video 
https://youtu.be/mV6k7wrtUsI

## Features
- Audio synchronization using Dynamic Time Warping (DTW) algorithm
- Real-time pitch visualization dashboard
- Comparison of live performance against reference recordings
- Video playback with synchronized pitch analysis

## Technologies Used
- **Python** - Core programming language
- **Machine Learning** - Dynamic Time Warping for audio sync
- **Data Visualization** - Real-time pitch comparison
- **Audio Processing** - Signal analysis and feature extraction

## Open VocalCompare.py to begin your vocal comparison journey!

## Backend processes
1 dl-files  
	Uses yt-dlp to download audio/video files  
	Input:  
		Live Performance URL  
		Studio Performance URL  
	Output:   
		live_performance.mp4  
		live_audio.wav  
		studio_audio.wav  
2 extract-vocals  
	Uses Demucs to separate vocal track  
	Input:   
		live_audio.wav  
		studio_audio.wav  
	Output:   
		live_vocals.wav  
		studio_vocals.wav  
3 denoise-vocals  
	Denoises vocals by reducing echo, trimming leading and trailing silence, and normalizing  
	Input:   
		live_vocals.wav  
		studio_vocals.wav  
	Output:   
		live_vocals_denoised.wav  
		studio_vocals_denoised.wav  
4 audio-sync  
	Input:   
		live_vocals_denoised.wav  
		studio_vocals_denoised.wav  
	Output:   
		studio_vocals_warped.wav  
5 pitch-extraction  
	Input:   
		live_vocals_denoised.wav  
		studio_vocals_warped.wav  
	Output:   
		live_pitch.npy  
		studio_pitch.npy  
		live_pitch_times.npy  
		studio_pitch_times.npy  