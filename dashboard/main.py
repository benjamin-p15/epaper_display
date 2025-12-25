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
    FONT_TINY = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
except:
    FONT_LARGE = ImageFont.load_default()
    FONT_MEDIUM = ImageFont.load_default()
    FONT_SMALL = ImageFont.load_default()
    FONT_TINY = ImageFont.load_default()

FONT_HOLIDAY = FONT_SMALL
FONT_DAYS = FONT_TINY

# ================= US HOLIDAYS =================
def nth_weekday(year, month, weekday, n):
    d = datetime.date(year, month, 1)
    count = 0
    while True:
        if d.weekday() == weekday:
            count += 1
            if count == n:
                return d
        d += datetime.timedelta(days=1)

def first_weekday(year, month, weekday):
    return nth_weekday(year, month, weekday, 1)

def second_weekday(year, month, weekday):
    return nth_weekday(year, month, weekday, 2)

def third_weekday(year, month, weekday):
    return nth_weekday(year, month, weekday, 3)

def fourth_weekday(year, month, weekday):
    return nth_weekday(year, month, weekday, 4)

def last_weekday(year, month, weekday):
    d = datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)
    while d.weekday() != weekday:
        d -= datetime.timedelta(days=1)
    return d

def get_us_holidays(year=None):
    if year is None:
        year = datetime.date.today().year

    holidays = {}
    holidays[datetime.date(year, 1, 1)] = "New Year's Day"
    holidays[datetime.date(year, 6, 19)] = "Juneteenth"
    holidays[datetime.date(year, 7, 4)] = "Independence Day"
    holidays[datetime.date(year, 11, 11)] = "Veterans Day"
    holidays[datetime.date(year, 12, 25)] = "Christmas Day"
    holidays[third_weekday(year, 1, 0)] = "Martin Luther King Jr. Day"
    if (year - 2021) % 4 == 0:
        holidays[datetime.date(year, 1, 20)] = "Inauguration Day"
    holidays[third_weekday(year, 2, 0)] = "Presidents Day"
    holidays[last_weekday(year, 5, 0)] = "Memorial Day"
    holidays[first_weekday(year, 9, 0)] = "Labor Day"
    holidays[second_weekday(year, 10, 0)] = "Columbus Day"
    holidays[fourth_weekday(year, 11, 3)] = "Thanksgiving"

    return holidays

def get_holiday_info(today=None):
    if today is None:
        today = datetime.date.today()
    holidays = get_us_holidays(today.year)
    if today in holidays:
        return holidays[today], 0
    upcoming = []
    for date, name in holidays.items():
        if date < today:
            date = datetime.date(today.year + 1, date.month, date.day)
        days_until = (date - today).days
        upcoming.append((days_until, name))
    upcoming.sort()
    days, name = upcoming[0]
    return name, days

# ================= LAYOUT FUNCTIONS =================
def draw_clock_layout():
    now = datetime.datetime.now()
    hour = now.strftime("%I")       # 12-hour format
    minute = now.strftime("%M")
    am_pm = now.strftime("%p")
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
    x_time, y_time = 50, 50
    draw.text((x_time, y_time), time_text, font=FONT_LARGE, fill=0)

    # Draw AM/PM next to time
    time_width, time_height = draw.textsize(time_text, font=FONT_LARGE)
    draw.text((x_time + time_width + 10, y_time + time_height//2 + 10), am_pm, font=FONT_MEDIUM, fill=0)

    # Draw date
    draw.text((x_time, 250), date_str, font=FONT_MEDIUM, fill=0)

    # Draw day
    draw.text((x_time, 320), day_str, font=FONT_MEDIUM, fill=0)

    # Draw holiday bottom-right
    lines = holiday_text.split("\n")
    line_sizes = []
    total_height = 0
    for i, line in enumerate(lines):
        font = FONT_HOLIDAY if i == 0 else FONT_DAYS
        _, line_height = draw.textsize(line, font=font)
        line_sizes.append((line, font, line_height))
        total_height += line_height

    y = 480 - total_height - 20
    for line, font, line_height in line_sizes:
        line_width, _ = draw.textsize(line, font=font)
        x = 800 - line_width - 20
        draw.text((x, y), line, font=font, fill=0)
        y += line_height

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
