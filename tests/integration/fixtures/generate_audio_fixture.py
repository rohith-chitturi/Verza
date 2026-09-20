import math
import os
import struct
import wave


def generate_audio_fixture(filepath: str):
    """
    Generates a mathematically deterministic WAV physical fixture for Audio Segmentation.
    Structure:
    - 0.0s -> 1.0s: Active audio (440Hz Sine wave)
    - 1.0s -> 2.0s: Digital Silence (0 PCM)
    - 2.0s -> 3.0s: Active audio (440Hz Sine wave)
    
    This exact mathematically-defined payload ensures FFmpeg's silencedetect filter 
    will perfectly isolate the middle 1.0s region.
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    SAMPLE_RATE = 44100
    FREQ = 440.0
    AMPLITUDE = 32767.0
    
    # Generate 1.0s of Sine Wave (Active)
    active_samples = []
    for i in range(SAMPLE_RATE):
        value = int(AMPLITUDE * math.sin(2.0 * math.pi * FREQ * i / SAMPLE_RATE))
        active_samples.append(struct.pack('<h', value))
    
    # Generate 1.0s of Zero PCM (Silence)
    silence_samples = [struct.pack('<h', 0) for _ in range(SAMPLE_RATE)]
    
    # Combine: Active + Silence + Active (Total 3.0 seconds)
    all_samples = active_samples + silence_samples + active_samples
    
    # Write to WAV
    with wave.open(filepath, 'wb') as wav_file:
        wav_file.setnchannels(1)      # Mono
        wav_file.setsampwidth(2)      # 16-bit (2 bytes per sample)
        wav_file.setframerate(SAMPLE_RATE)
        wav_file.writeframes(b''.join(all_samples))
        
    # Validation: Ensure it can be read and is 3.0s long
    with wave.open(filepath, 'rb') as wav_file:
        frames = wav_file.getnframes()
        rate = wav_file.getframerate()
        duration = frames / float(rate)
        
        assert duration == 3.0, f"Expected exactly 3.0s duration, got {duration}s"
        
    print(f"Generated deterministic audio fixture at: {filepath}")

if __name__ == "__main__":
    filepath = os.path.join(os.path.dirname(__file__), "audio_fixture.wav")
    generate_audio_fixture(filepath)
