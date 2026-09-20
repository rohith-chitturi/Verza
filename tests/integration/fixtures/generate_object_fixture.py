import os
import urllib.request

import cv2


def generate_object_fixture(output_dir: str):
    """
    Downloads bus.jpg and yolov8n.pt ONCE, and generates a 30-frame MP4.
    This script is intended for one-time acquisition before committing to Git.
    """
    os.makedirs(output_dir, exist_ok=True)
    models_dir = os.path.join(output_dir, "models")
    os.makedirs(models_dir, exist_ok=True)
    
    # 1. Download yolov8n.pt to models dir (avoiding auto-download in CI)
    yolo_model_path = os.path.join(models_dir, "yolov8n.pt")
    if not os.path.exists(yolo_model_path):
        print(f"Downloading yolov8n.pt to {yolo_model_path}...")
        urllib.request.urlretrieve(
            "https://github.com/ultralytics/assets/releases/download/v8.1.0/yolov8n.pt", 
            yolo_model_path
        )
        print("Downloaded model.")

    # 2. Download bus.jpg
    img_path = os.path.join(output_dir, "bus.jpg")
    if not os.path.exists(img_path):
        print(f"Downloading bus.jpg to {img_path}...")
        urllib.request.urlretrieve(
            "https://raw.githubusercontent.com/ultralytics/yolov5/master/data/images/bus.jpg", 
            img_path
        )
        print("Downloaded image.")
        
    # 3. Create MP4
    mp4_path = os.path.join(output_dir, "object_fixture.mp4")
    if not os.path.exists(mp4_path):
        print(f"Generating 30-frame MP4 at {mp4_path}...")
        img = cv2.imread(img_path)
        h, w, _ = img.shape
        
        # mp4v codec is standard for deterministic cv2 video writing
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        fps = 30.0
        out = cv2.VideoWriter(mp4_path, fourcc, fps, (w, h))
        
        for _ in range(30):
            out.write(img)
            
        out.release()
        print("Generated video.")
        
    # Clean up the raw image
    if os.path.exists(img_path):
        os.remove(img_path)
        
if __name__ == "__main__":
    fixtures_dir = os.path.dirname(os.path.abspath(__file__))
    generate_object_fixture(fixtures_dir)
