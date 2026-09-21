import os
import urllib.request
import numpy as np
import cv2
import wave
import struct
import subprocess


def generate_activity_fixture():
    fixture_dir = os.path.dirname(__file__)
    img_path = os.path.join(fixture_dir, "lena.jpg")
    audio_path = os.path.join(fixture_dir, "activity_audio.wav")
    video_no_audio_path = os.path.join(fixture_dir, "activity_video.mp4")
    final_path = os.path.join(fixture_dir, "activity_fixture.mp4")

    if not os.path.exists(img_path):
        print("Downloading standard test image...")
        url = "https://raw.githubusercontent.com/opencv/opencv/master/samples/data/lena.jpg"
        urllib.request.urlretrieve(url, img_path)

    img = cv2.imread(img_path)
    if img is None:
        raise RuntimeError("Failed to load test image.")

    fps = 30
    duration = 1.0
    total_frames = int(fps * duration)
    crop_size = 256

    print("Generating video track (panning face)...")
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(video_no_audio_path, fourcc, fps, (crop_size, crop_size))

    start_x, start_y = 100, 100
    end_x, end_y = 180, 100  # Panning right by 80 pixels (significant movement)

    for i in range(total_frames):
        alpha = i / (total_frames - 1)
        curr_x = int(start_x + alpha * (end_x - start_x))
        curr_y = int(start_y + alpha * (end_y - start_y))
        
        frame = img[curr_y:curr_y+crop_size, curr_x:curr_x+crop_size]
        out.write(frame)

    out.release()

    print("Generating audio track (440Hz sine wave for 1s)...")
    sample_rate = 44100
    num_samples = int(sample_rate * duration)
    
    with wave.open(audio_path, 'w') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        
        for i in range(num_samples):
            # 440Hz sine wave
            value = int(32767.0 * math.sin(2.0 * math.pi * 440.0 * i / sample_rate))
            data = struct.pack('<h', value)
            wav_file.writeframesraw(data)

    print("Muxing video and audio with FFmpeg...")
    subprocess.run([
        "ffmpeg", "-y", 
        "-i", video_no_audio_path, 
        "-i", audio_path, 
        "-c:v", "copy", 
        "-c:a", "aac", 
        final_path
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Cleanup intermediate files
    os.remove(video_no_audio_path)
    os.remove(audio_path)
    print(f"Successfully generated {final_path}")


if __name__ == "__main__":
    import math
    generate_activity_fixture()
