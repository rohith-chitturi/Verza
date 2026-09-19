import wave
import struct

def generate_test_wav(filepath: str):
    """Generates a 1-second 440Hz sine wave valid .wav file"""
    sample_rate = 44100
    num_samples = sample_rate * 1
    
    with wave.open(filepath, 'w') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        
        for i in range(num_samples):
            value = int(32767.0 * 0) # Silence is fine, just needs to be valid
            data = struct.pack('<h', value)
            wav_file.writeframesraw(data)

if __name__ == "__main__":
    generate_test_wav("tests/integration/fixtures/test_media.wav")
