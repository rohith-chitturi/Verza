import os
import urllib.request

import cv2


def generate_face_fixture():
    fixture_dir = os.path.dirname(__file__)
    os.makedirs(fixture_dir, exist_ok=True)
    
    mp4_path = os.path.join(fixture_dir, "face_fixture.mp4")
    if os.path.exists(mp4_path):
        print(f"Fixture already exists at {mp4_path}")
        return

    # Download a standard test image known to trigger Haar cascades (Lenna)
    url = "https://raw.githubusercontent.com/opencv/opencv/master/samples/data/lena.jpg"
    img_path = os.path.join(fixture_dir, "lena.jpg")
    
    if not os.path.exists(img_path):
        print("Downloading standard test image...")
        urllib.request.urlretrieve(url, img_path)
        
    img = cv2.imread(img_path)
    if img is None:
        raise RuntimeError("Failed to load test image.")
        
    _ = img.shape
    
    # We will create a 30 frame (1 second) video at 30 FPS.
    # The video will pan slightly to simulate motion so the tracker has to work.
    
    fps = 30
    duration = 1.0
    total_frames = int(fps * duration)
    
    # Define a 256x256 crop window that pans
    crop_size = 256
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(mp4_path, fourcc, fps, (crop_size, crop_size))
    
    start_x, start_y = 100, 100
    end_x, end_y = 130, 100  # Panning right by 30 pixels
    
    print("Generating face_fixture.mp4...")
    for i in range(total_frames):
        alpha = i / (total_frames - 1)
        curr_x = int(start_x + alpha * (end_x - start_x))
        curr_y = int(start_y + alpha * (end_y - start_y))
        
        frame = img[curr_y:curr_y+crop_size, curr_x:curr_x+crop_size]
        out.write(frame)
        
    out.release()
    print(f"Successfully generated {mp4_path}")

if __name__ == "__main__":
    generate_face_fixture()
