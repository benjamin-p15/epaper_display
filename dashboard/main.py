from flask import Flask, render_template, request
from PIL import Image, ImageDraw
import datetime
import os
from driver import  display_image, clear_display, sleep_display, init_display
from PIL import Image
import threading
import time

UPDATE_INTERVAL = 10

def draw_time_layout():
    img = Image.new("1", (800, 480), 255)
    draw = ImageDraw.Draw(img)
    now = time.strftime("%H:%M:%S")
    draw.text((200, 200), now, fill=0)
    return img

def time_updater():
    while True:
        img = draw_time_layout()
        display_image(img)
        time.sleep(UPDATE_INTERVAL)

threading.Thread(target=time_updater, daemon=True).start()


app = Flask(__name__)
UPLOAD_FOLDER = "images"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ===== Layout functions =====
def draw_time_layout():
    img = Image.new("1", (800, 480), 255)  # white background
    draw = ImageDraw.Draw(img)
    now = datetime.datetime.now().strftime("%H:%M:%S")
    draw.text((200, 200), now, fill=0)  # black text
    return img

def draw_weather_layout():
    img = Image.new("1", (800, 480), 255)
    draw = ImageDraw.Draw(img)
    # Example static weather text; later replace with API call
    weather_text = "San Francisco\n22°C\nSunny"
    draw.text((100, 150), weather_text, fill=0)
    return img

# ===== Routes =====
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/display", methods=["POST"])
def display_layout():
    layout = request.form.get("layout")
    if layout == "time":
        img = draw_time_layout()
    elif layout == "weather":
        img = draw_weather_layout()
    else:
        return "Unknown layout", 400
    display_image(img)
    return "Layout displayed successfully!"

@app.route("/display_image", methods=["POST"])
def display_uploaded_image():  # renamed
    file = request.files.get("image")
    if not file:
        return "No file uploaded", 400
    path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(path)
    img = Image.open(path)
    display_image(img)  # driver function
    return "Image displayed successfully!"

if __name__ == "__main__":
    init_display()
    threading.Thread(target=time_updater, daemon=True).start()
    app.run(host="0.0.0.0", port=5000)
