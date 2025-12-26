from PIL import Image, ImageDraw, ImageFont
import os
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import random

# ================= CONFIG =================
SCREEN_W, SCREEN_H = 800, 480
ICON_DIR = os.path.join(os.path.dirname(__file__), "icons")

STATION = "KSFO"          # San Francisco Intl
CITY = "San Francisco"
STATE = "CA"

# ================= FONTS =================
try:
    FONT_LARGE = ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80
    )
    FONT_MEDIUM = ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32
    )
    FONT_SMALL = ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22
    )
except:
    FONT_LARGE = ImageFont.load_default()
    FONT_MEDIUM = ImageFont.load_default()
    FONT_SMALL = ImageFont.load_default()

# ================= HELPERS =================
def load_icon(name, size=None):
    path = os.path.join(ICON_DIR, name)
    if not os.path.exists(path):
        return None
    icon = Image.open(path).convert("1")
    if size:
        icon = icon.resize(size)
    return icon

def fetch_metar():
    url = (
        "https://aviationweather.gov/adds/dataserver_current/httpparam"
        "?dataSource=metars"
        "&requestType=retrieve"
        "&format=xml"
        f"&stationString={STATION}"
        "&hoursBeforeNow=1"
    )

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; EPaperDashboard/1.0; +https://example.com)"
    }

    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        root = ET.fromstring(r.text)
        metar = root.find(".//METAR")
        if metar is None:
            raise RuntimeError("No METAR data found")

        def get(tag):
            el = metar.find(tag)
            return el.text if el is not None else None

        return {
            "temp_c": float(get("temp_c")),
            "dewpoint_c": float(get("dewpoint_c")),
            "wind_kt": get("wind_speed_kt"),
            "visibility_mi": get("visibility_statute_mi"),
            "pressure_hpa": get("sea_level_pressure_mb"),
            "weather": get("wx_string"),
            "raw": get("raw_text"),
        }
    except Exception as e:
        print(f"Warning: Failed to fetch METAR data: {e}")
        # Return dummy data to prevent crashing
        return {
            "temp_c": 20.0,
            "dewpoint_c": 15.0,
            "wind_kt": "--",
            "visibility_mi": "--",
            "pressure_hpa": "--",
            "weather": None,
            "raw": "--",
        }

def c_to_f(c):
    return round(c * 9 / 5 + 32)

def choose_weather_icon(wx):
    if not wx:
        return "01d.png"

    wx = wx.lower()
    if "ts" in wx:
        return "11d.png"
    if "snow" in wx:
        return "13d.png"
    if "rain" in wx:
        return "09d.png"
    if "mist" in wx or "fog" in wx:
        return "50d.png"
    if "cloud" in wx or "ovc" in wx:
        return "04d.png"

    return random.choice(["01d.png", "02d.png", "03d.png"])

# ================= RENDER =================
def render():
    data = fetch_metar()

    temp_f = c_to_f(data["temp_c"])
    feels_f = c_to_f(data["dewpoint_c"])

    main_icon_name = choose_weather_icon(data["weather"])

    img = Image.new("1", (SCREEN_W, SCREEN_H), 255)
    draw = ImageDraw.Draw(img)

    # ---------- HEADER ----------
    draw.text((20, 10), f"{CITY}, {STATE}", font=FONT_MEDIUM, fill=0)

    # ---------- LEFT: MAIN WEATHER ----------
    main_icon = load_icon(main_icon_name, size=(180, 180))
    if main_icon:
        img.paste(main_icon, (40, 80))

    draw.text((240, 110), f"{temp_f}°", font=FONT_LARGE, fill=0)
    draw.text(
        (245, 200),
        f"Feels like {feels_f}°",
        font=FONT_SMALL,
        fill=0
    )

    # ---------- RIGHT: INFO GRID ----------
    info = [
        ("sunrise.png", "--"),
        ("windL.png", f"{data['wind_kt']} kt"),
        ("pressure.png", f"{data['pressure_hpa']} hPa"),
        ("visibility.png", f"{data['visibility_mi']} mi"),
        ("sunset.png", "--"),
        ("humidity.png", "--"),
        ("uvi.png", "--"),
        ("aqi.png", "--"),
    ]

    start_x = 480
    start_y = 80
    col_w = 150
    row_h = 90

    for i, (icon_name, text) in enumerate(info):
        col = i % 2
        row = i // 2
        x = start_x + col * col_w
        y = start_y + row * row_h

        icon = load_icon(icon_name, size=(36, 36))
        if icon:
            img.paste(icon, (x, y))

        draw.text((x + 50, y + 8), text, font=FONT_SMALL, fill=0)

    return img
