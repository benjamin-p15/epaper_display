from flask import Flask, render_template, request
from PIL import Image
import threading
import time
import os

from dashboard.driver2 import init_display, display_image

# FIX: import the module as `clock`
from modules.clock import main as clock
from dashboard.modules.weather import main2 as weather

# ================= CONFIG =================
CLOCK_CHECK_INTERVAL = 5        # seconds
WEATHER_UPDATE_INTERVAL = 300   # 5 minutes
UPLOAD_FOLDER = "images"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

update_clock = False

# ================= WEATHER CACHE =================
last_weather_update = 0
cached_weather_image = None

# ================= CLOCK UPDATER =================
def clock_updater():
    last_minute = -1

    while True:
        if update_clock:
            now = time.localtime()
            if now.tm_min != last_minute:
                display_image(clock.render())
                last_minute = now.tm_min

        time.sleep(CLOCK_CHECK_INTERVAL)

# ================= WEATHER UPDATER =================
def weather_updater():
    global last_weather_update, cached_weather_image
    while True:
        now = time.time()
        if cached_weather_image is None or now - last_weather_update >= WEATHER_UPDATE_INTERVAL:
            cached_weather_image = weather.render()
            last_weather_update = now
        time.sleep(WEATHER_UPDATE_INTERVAL)

# ================= FLASK APP =================
app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/display", methods=["POST"])
def display_layout():
    global update_clock, last_weather_update, cached_weather_image

    layout = request.form.get("layout")

    if layout == "time":
        update_clock = True
        display_image(clock.render())
        return "OK"

    elif layout == "weather":
        update_clock = False

        now = time.time()
        if cached_weather_image is None or now - last_weather_update >= WEATHER_UPDATE_INTERVAL:
            cached_weather_image = weather.render()
            last_weather_update = now

        display_image(cached_weather_image)
        return "OK"

    return "Unknown layout", 400

@app.route("/display_image", methods=["POST"])
def display_uploaded_image():
    global update_clock
    update_clock = False

    file = request.files.get("image")
    if not file:
        return "No file", 400

    path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(path)

    img = Image.open(path)
    display_image(img)

    return "OK"

# ================= MAIN =================
if __name__ == "__main__":
    init_display()
    # Start clock updater thread
    threading.Thread(target=clock_updater, daemon=True).start()
    # Start weather updater thread
    threading.Thread(target=weather_updater, daemon=True).start()
    # Start Flask
    app.run(host="0.0.0.0", port=5000)
