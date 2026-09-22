import os

import cv2
import numpy as np


def generate_shot_fixture(filepath: str):
    """
    Generates a mathematically deterministic MP4 physical fixture for Shot Detection.
    - 30 frames of solid black
    - 30 frames of solid white
    - Exactly 30 FPS
    
    This ensures that the cut occurs perfectly between frame 29 and frame 30,
    corresponding exactly to 1.0 second.
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    FPS = 30
    WIDTH = 640
    HEIGHT = 480
    BLACK_FRAMES = 30
    WHITE_FRAMES = 30
    
    # Use MP4V codec which is widely supported without extra system dependencies
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # type: ignore
    out = cv2.VideoWriter(filepath, fourcc, float(FPS), (WIDTH, HEIGHT))
    
    black_frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
    white_frame = np.ones((HEIGHT, WIDTH, 3), dtype=np.uint8) * 255
    
    for _ in range(BLACK_FRAMES):
        out.write(black_frame)
        
    for _ in range(WHITE_FRAMES):
        out.write(white_frame)
        
    out.release()
    
    # Validate the generated media can be read
    cap = cv2.VideoCapture(filepath)
    assert cap.isOpened(), f"Failed to open generated video fixture at {filepath}"
    
    # Verify the frame count is exactly 60
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    assert total_frames == BLACK_FRAMES + WHITE_FRAMES, f"Expected 60 frames, got {total_frames}"
    
    cap.release()
    print(f"Generated deterministic shot fixture at: {filepath}")

if __name__ == "__main__":
    filepath = os.path.join(os.path.dirname(__file__), "shot_fixture.mp4")
    generate_shot_fixture(filepath)
