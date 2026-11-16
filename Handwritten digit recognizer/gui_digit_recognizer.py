from keras.models import load_model
import tkinter as tk
from PIL import Image, ImageDraw, ImageOps
import numpy as np

# Load trained MNIST model
model = load_model("mnist.keras")


def find_bounding_boxes(img_gray):
    # img_gray is a 2D numpy array (inverted: black background, white digits)
    # Thresholding: values > 50 are considered foreground
    threshold = 50
    h, w = img_gray.shape
    visited = np.zeros((h, w), dtype=bool)
    boxes = []
    
    for y in range(h):
        for x in range(w):
            if img_gray[y, x] > threshold and not visited[y, x]:
                # Found a new connected component, use BFS
                q = [(x, y)]
                visited[y, x] = True
                min_x, max_x = x, x
                min_y, max_y = y, y
                
                head = 0
                while head < len(q):
                    cx, cy = q[head]
                    head += 1
                    
                    # 8-connected neighbors
                    for dx in [-1, 0, 1]:
                        for dy in [-1, 0, 1]:
                            if dx == 0 and dy == 0:
                                continue
                            nx, ny = cx + dx, cy + dy
                            if 0 <= nx < w and 0 <= ny < h:
                                if img_gray[ny, nx] > threshold and not visited[ny, nx]:
                                    visited[ny, nx] = True
                                    q.append((nx, ny))
                                    min_x = min(min_x, nx)
                                    max_x = max(max_x, nx)
                                    min_y = min(min_y, ny)
                                    max_y = max(max_y, ny)
                                    
                # Add bounding box (x, y, w, h)
                box_w = max_x - min_x + 1
                box_h = max_y - min_y + 1
                
                # Filter out very small noise components (e.g. area < 20)
                if box_w * box_h > 20:
                    boxes.append((min_x, min_y, box_w, box_h))
                    
    return boxes


def predict_digits(img):
    # Convert to grayscale NumPy array
    img_gray = np.array(img.convert("L"))
    
    # Invert colors (make background black, digits white)
    img_gray = 255 - img_gray
    
    # Find bounding boxes for each digit
    boxes = find_bounding_boxes(img_gray)
    
    if not boxes:
        return "", 0.0
        
    # Sort bounding boxes from left to right (by x-coordinate)
    boxes.sort(key=lambda b: b[0])
    
    predictions = []
    accuracies = []
    
    # Use inverted image for cropping
    img_inv = Image.fromarray(img_gray)
    
    for (x, y, w, h) in boxes:
        # Crop the region corresponding to the bounding box
        cropped = img_inv.crop((x, y, x + w, y + h))
        
        # Resize preserving aspect ratio
        if w > h:
            new_w = 20
            new_h = max(1, int(20 * (h / w)))
        else:
            new_h = 20
            new_w = max(1, int(20 * (w / h)))
            
        cropped = cropped.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        # Create a new 28x28 black canvas and paste the centered digit
        new_img = Image.new("L", (28, 28), "black")
        paste_x = (28 - new_w) // 2
        paste_y = (28 - new_h) // 2
        new_img.paste(cropped, (paste_x, paste_y))
        
        # Convert to NumPy array and normalize
        img_array = np.array(new_img).astype("float32") / 255.0
        
        # Reshape for model input
        img_array = img_array.reshape(1, 28, 28, 1)
        
        # Predict
        res = model.predict(img_array, verbose=0)[0]
        predictions.append(str(np.argmax(res)))
        accuracies.append(max(res))
        
    avg_acc = sum(accuracies) / len(accuracies) if accuracies else 0.0
    return "".join(predictions), avg_acc


class App(tk.Tk):

    def __init__(self):
        super().__init__()

        self.title("Handwritten Digit Recognizer")
        self.resizable(False, False)

        self.x = self.y = 0
        
        # Internal image for drawing, avoiding Wayland/Fedora screen capture issues
        self.image = Image.new("RGB", (300, 300), "white")
        self.draw = ImageDraw.Draw(self.image)

        # Canvas
        self.canvas = tk.Canvas(
            self,
            width=300,
            height=300,
            bg="white",
            cursor="cross"
        )

        # Result label
        self.label = tk.Label(
            self,
            text="Draw..",
            font=("Helvetica", 48)
        )

        # Buttons
        self.classify_btn = tk.Button(
            self,
            text="Recognise",
            command=self.classify_handwriting
        )

        self.button_clear = tk.Button(
            self,
            text="Clear",
            command=self.clear_all
        )

        # Layout
        self.canvas.grid(
            row=0,
            column=0,
            pady=2,
            padx=5
        )

        self.label.grid(
            row=0,
            column=1,
            pady=2,
            padx=10
        )

        self.classify_btn.grid(
            row=1,
            column=1,
            pady=5,
            padx=5
        )

        self.button_clear.grid(
            row=1,
            column=0,
            pady=5
        )

        # Mouse drawing
        self.canvas.bind(
            "<B1-Motion>",
            self.draw_lines
        )

    def clear_all(self):
        self.canvas.delete("all")
        self.label.configure(text="Draw..")
        self.image = Image.new("RGB", (300, 300), "white")
        self.draw = ImageDraw.Draw(self.image)

    def classify_handwriting(self):

        # Use the internally drawn image instead of capturing the screen
        # This resolves issues on Fedora/Wayland where screen grabbing fails
        im = self.image

        # Predict
        digits, acc = predict_digits(im)
        
        if not digits:
            self.label.configure(text="No digit")
            return

        # Display result
        self.label.configure(
            text=f"{digits}, {int(acc * 100)}%"
        )

    def draw_lines(self, event):

        r = 15  # Increased stroke thickness to match MNIST dataset properties

        self.canvas.create_oval(
            event.x - r,
            event.y - r,
            event.x + r,
            event.y + r,
            fill="black",
            outline="black"
        )
        self.draw.ellipse(
            [event.x - r, event.y - r, event.x + r, event.y + r],
            fill="black"
        )


# Start application
app = App()
app.mainloop()
