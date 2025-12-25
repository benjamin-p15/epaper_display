from flask import Flask, render_template, request
from PIL import Image, ImageDraw, ImageFont
import datetime
import os
from driver import init_display, display_image, clear_display, sleep_display
import threading
import time

# ================= CONFIG =================
UPDATE_INTERVAL = 5  # seconds between checking time
UPLOAD_FOLDER = "images"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

update_time = True  # global flag for background clock updater

# ================= FONTS =================
try:
    FONT_LARGE = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 120)
    FONT_MEDIUM = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 50)
    FONT_SMALL = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)
except:
    FONT_LARGE = ImageFont.load_default()
    FONT_MEDIUM = ImageFont.load_default()
    FONT_SMALL = ImageFont.load_default()

# ================= US HOLIDAYS =================
US_HOLIDAYS = {
    (1, 1): "New Year's Day",
    (7, 4): "Independence Day",
    (12, 25): "Christmas",
    (11, 11): "Veterans Day",
    (1, 20): "MLK Day",
    # Add more as needed
}

def get_holiday_info(today=None):
    if today is None:
        today = datetime.date.today()
    today_key = (today.month, today.day)
    if today_key in US_HOLIDAYS:
        return US_HOLIDAYS[today_key], 0
    upcoming = []
    for (month, day), name in US_HOLIDAYS.items():
        holiday_date = datetime.date(today.year, month, day)
        if holiday_date < today:
            holiday_date = datetime.date(today.year + 1, month, day)
        days_until = (holiday_date - today).days
        upcoming.append((days_until, name))
    upcoming.sort()
    days, name = upcoming[0]
    return name, days

# ================= LAYOUT FUNCTIONS =================
def draw_clock_layout():
    now = datetime.datetime.now()
    hour = now.strftime("%I")
    minute = now.strftime("%M")
    time_text = f"{hour}:{minute}"

    holiday_name, days_until = get_holiday_info()
    if days_until == 0:
        holiday_text = holiday_name
    else:
        holiday_text = f"{holiday_name}\n{days_until} days"

    date_str = now.strftime("%m/%d/%y")
    day_str = now.strftime("%A")

    img = Image.new("1", (800, 480), 255)
    draw = ImageDraw.Draw(img)

    # Draw time
    draw.text((50, 50), time_text, font=FONT_LARGE, fill=0)

    # Draw holiday/AMPM next to time
    time_width, _ = draw.textsize(time_text, font=FONT_LARGE)
    draw.text((50 + time_width + 20, 70), holiday_text, font=FONT_MEDIUM, fill=0)

    # Draw date below
    draw.text((50, 250), date_str, font=FONT_MEDIUM, fill=0)

    # Draw day below date
    draw.text((50, 320), day_str, font=FONT_MEDIUM, fill=0)

    return img

def draw_weather_layout():
    img = Image.new("1", (800, 480), 255)
    draw = ImageDraw.Draw(img)
    weather_text = "San Francisco\n22°C\nSunny"
    draw.text((100, 150), weather_text, fill=0)
    return img

# ================= BACKGROUND CLOCK UPDATER =================
def clock_updater():
    last_minute = -1
    while True:
        if update_time:
            now = datetime.datetime.now()
            if now.minute != last_minute:
                img = draw_clock_layout()
                display_image(img)
                last_minute = now.minute
        time.sleep(UPDATE_INTERVAL)

# ================= FLASK APP =================
app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/display", methods=["POST"])
def display_layout():
    global update_time
    layout = request.form.get("layout")
    if layout == "time":
        update_time = True
        img = draw_clock_layout()
        display_image(img)
    elif layout == "weather":
        update_time = False
        img = draw_weather_layout()
        display_image(img)
    else:
        return "Unknown layout", 400
    return "Layout displayed successfully!"

@app.route("/display_image", methods=["POST"])
def display_uploaded_image():
    global update_time
    update_time = False
    file = request.files.get("image")
    if not file:
        return "No file uploaded", 400
    path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(path)
    img = Image.open(path)
    display_image(img)
    return "Image displayed successfully!"

# ================= MAIN =================
if __name__ == "__main__":
    init_display()
    threading.Thread(target=clock_updater, daemon=True).start()
    app.run(host="0.0.0.0", port=5000)
