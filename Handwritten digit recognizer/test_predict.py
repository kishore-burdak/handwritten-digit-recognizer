import numpy as np
from PIL import Image, ImageDraw
import sys

# Import functions from gui_digit_recognizer
try:
    from gui_digit_recognizer import predict_digits, model
    print("Successfully imported predict_digits and model")
except Exception as e:
    print(f"Error importing from gui_digit_recognizer: {e}")
    sys.exit(1)

def test_multiple_digits():
    print("Creating test image...")
    # Create an image similar to the canvas (300x300, white background)
    img = Image.new("RGB", (300, 300), "white")
    draw = ImageDraw.Draw(img)
    
    # Draw two separate strokes for "1" and "1"
    # Digit 1
    draw.line((100, 100, 100, 200), fill="black", width=15)
    
    # Digit 2
    draw.line((200, 100, 200, 200), fill="black", width=15)
    
    # Predict
    print("Running predict_digits...")
    digits, acc = predict_digits(img)
    print(f"Predicted digits: {digits}")
    print(f"Average accuracy: {acc:.2f}")
    
    if len(digits) >= 2:
        print("Test passed: Multiple digits recognized.")
    else:
        print("Test failed: Only recognized", len(digits), "digits.")

if __name__ == "__main__":
    test_multiple_digits()
