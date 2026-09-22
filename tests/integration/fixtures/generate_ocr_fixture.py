import os

import cv2
import numpy as np


def generate_test_image(filepath: str):
    """
    Generates a deterministic physical image fixture containing 'VERZA OCR SYSTEM'.
    Uses OpenCV to ensure the font rendering is deterministic across CI environments 
    without relying on system fonts.
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    # Create a white high-contrast background image (Height: 300, Width: 800)
    image = np.ones((300, 800, 3), dtype=np.uint8) * 255
    
    # Use OpenCV's built-in Hershey font
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 2.5
    font_color = (0, 0, 0) # Black text
    thickness = 5
    
    # Text to render
    text = "VERZA OCR SYSTEM"
    
    # Get text size to center it
    text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
    text_x = (image.shape[1] - text_size[0]) // 2
    text_y = (image.shape[0] + text_size[1]) // 2
    
    # Draw text
    cv2.putText(image, text, (text_x, text_y), font, font_scale, font_color, thickness, cv2.LINE_AA)
    
    # Save the physical fixture
    cv2.imwrite(filepath, image)
    print(f"Generated OCR physical fixture at: {filepath}")

if __name__ == "__main__":
    filepath = os.path.join(os.path.dirname(__file__), "ocr_fixture.png")
    generate_test_image(filepath)
