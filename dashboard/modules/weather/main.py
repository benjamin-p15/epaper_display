from PIL import Image, ImageDraw, ImageFont
import os
import requests
from datetime import datetime
import random

# ================= CONFIG =================
SCREEN_W, SCREEN_H = 800, 480
ICON_DIR = os.path.join(os.path.dirname(__file__), "icons")

# ================= FONTS =================
try:
    FONT_LARGE = ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80
    )
    FONT_MEDIUM = ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32
    )
    FONT_SMALL = ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24
    )
except:
    FONT_LARGE = ImageFont.load_default()
    FONT_MEDIUM = ImageFont.load_default()
    FONT_SMALL = ImageFont.load_default()

# ================= HELPERS =================
def load_icon_bw(path, size=None):
    """Load icon: transparent/white stays white, all else black"""
    if not os.path.exists(path):
        return None
    img = Image.open(path).convert("RGBA")
    bw = Image.new("1", img.size, 1)  # white background
    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = img.getpixel((x, y))
            if a > 0 and (r, g, b) != (255, 255, 255):
                bw.putpixel((x, y), 0)  # black
    if size:
        bw = bw.resize(size)
    return bw

def get_location():
    """Get location using IP geolocation"""
    try:
        r = requests.get("http://ip-api.com/json/", timeout=5)
        r.raise_for_status()
        data = r.json()
        lat = data.get("lat", 37.7749)
        lon = data.get("lon", -122.4194)
        city = data.get("city", "Unknown")
        state = data.get("regionName", "Unknown")
        return lat, lon, city, state
    except Exception as e:
        print(f"Warning: Failed to get location: {e}")
        return 37.7749, -122.4194, "San Francisco", "CA"

def fetch_weather(lat, lon):
    """Fetch weather from OpenWeatherMap"""
    API_KEY = os.environ.get("OPENWEATHER_API_KEY")
    if not API_KEY:
        print("Warning: OPENWEATHER_API_KEY not set, using dummy data")
        return None
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units=metric&appid={API_KEY}"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"Warning: Failed to fetch weather: {e}")
        return None

def c_to_f(c):
    return round(c * 9 / 5 + 32)

def choose_weather_icon(wx):
    """Map weather description to local icon"""
    if not wx:
        return "01d.png"
    wx = wx.lower()
    if "thunderstorm" in wx or "11" in wx:
        return "11d.png"
    if "snow" in wx or "13" in wx:
        return "13d.png"
    if "rain" in wx or "09" in wx or "10" in wx:
        return "09d.png"
    if "mist" in wx or "fog" in wx or "50" in wx:
        return "50d.png"
    if "cloud" in wx or "04" in wx or "03" in wx:
        return "04d.png"
    return "01d.png"

# ================= RENDER =================
def render():
    lat, lon, city, state = get_location()
    data = fetch_weather(lat, lon)

    # fallback dummy data
    if not data:
        weather_main = "Clear"
        temp_c = 20
        feels_c = 20
        wind_speed = "--"
        pressure = "--"
        visibility = "--"
        humidity = "--"
    else:
        weather_main = data["weather"][0]["main"]
        temp_c = data["main"]["temp"]
        feels_c = data["main"]["feels_like"]
        wind_speed = data["wind"].get("speed", "--")
        pressure = data["main"].get("pressure", "--")
        visibility = round(data.get("visibility", 0) / 1609.34, 1)  # meters → miles
        humidity = data["main"].get("humidity", "--")

    temp_f = c_to_f(temp_c)
    feels_f = c_to_f(feels_c)

    main_icon_name = choose_weather_icon(weather_main)

    img = Image.new("1", (SCREEN_W, SCREEN_H), 1)  # white background
    draw = ImageDraw.Draw(img)

    # ---------- HEADER: CENTERED CITY/STATE ----------
    header_text = f"{city}, {state}"
    w, h = draw.textsize(header_text, font=FONT_MEDIUM)
    draw.text(((SCREEN_W - w) // 2, 10), header_text, font=FONT_MEDIUM, fill=0)

    # ---------- LEFT: MAIN WEATHER ----------
    icon_size = (180, 180)
    main_icon = load_icon_bw(os.path.join(ICON_DIR, main_icon_name), size=icon_size)
    if main_icon:
        img.paste(main_icon, (50, 80))

    draw.text((260, 110), f"{temp_f}°", font=FONT_LARGE, fill=0)
    draw.text((265, 210), f"Feels like {feels_f}°", font=FONT_SMALL, fill=0)

    # ---------- RIGHT: INFO GRID ----------
    info = [
        ("windL.png", f"{wind_speed} m/s"),
        ("pressure.png", f"{pressure} hPa"),
        ("visibility.png", f"{visibility} mi"),
        ("humidity.png", f"{humidity}%"),
        ("sunrise.png", "--"),
        ("sunset.png", "--"),
        ("uvi.png", "--"),
        ("aqi.png", "--"),
    ]

    start_x = 480
    start_y = 80
    col_w = 160
    row_h = 100
    icon_size_small = (50, 50)

    for i, (icon_name, text) in enumerate(info):
        col = i % 2
        row = i // 2
        x = start_x + col * col_w
        y = start_y + row * row_h

        icon = load_icon_bw(os.path.join(ICON_DIR, icon_name), size=icon_size_small)
        if icon:
            img.paste(icon, (x, y))

        draw.text((x + 60, y + 10), str(text), font=FONT_SMALL, fill=0)

    return img
