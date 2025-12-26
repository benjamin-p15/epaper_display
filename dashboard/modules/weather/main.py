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
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22
    )
except:
    FONT_LARGE = ImageFont.load_default()
    FONT_MEDIUM = ImageFont.load_default()
    FONT_SMALL = ImageFont.load_default()

# ================= HELPERS =================
def load_icon(name, size=None, invert=True):
    """Load an icon and optionally invert for e-paper display"""
    path = os.path.join(ICON_DIR, name)
    if not os.path.exists(path):
        return None
    icon = Image.open(path).convert("1")
    if invert:
        icon = Image.eval(icon, lambda x: 255 - x)
    if size:
        icon = icon.resize(size)
    return icon

def get_location():
    """Get location automatically using IP geolocation"""
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
        # fallback to San Francisco
        return 37.7749, -122.4194, "San Francisco", "CA"

def fetch_weather(lat, lon):
    """Fetch weather data from OpenWeatherMap using coordinates"""
    API_KEY = os.environ.get("OPENWEATHER_API_KEY")
    if not API_KEY:
        print("Warning: OPENWEATHER_API_KEY not set, using dummy data")
        return None

    url = (
        f"https://api.openweathermap.org/data/2.5/weather?"
        f"lat={lat}&lon={lon}&units=metric&appid={API_KEY}"
    )

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
    """Map OpenWeather icon codes to local icons"""
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

    # Fallback dummy data if API fails
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

    img = Image.new("1", (SCREEN_W, SCREEN_H), 255)
    draw = ImageDraw.Draw(img)

    # ---------- HEADER ----------
    draw.text((20, 10), f"{city}, {state}", font=FONT_MEDIUM, fill=0)

    # ---------- LEFT: MAIN WEATHER ----------
    icon_size = (150, 150)
    main_icon = load_icon(main_icon_name, size=icon_size)
    if main_icon:
        img.paste(main_icon, (40, 80))

    draw.text((220, 110), f"{temp_f}°", font=FONT_LARGE, fill=0)
    draw.text((225, 200), f"Feels like {feels_f}°", font=FONT_SMALL, fill=0)

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
    col_w = 150
    row_h = 90
    icon_size_small = (36, 36)

    for i, (icon_name, text) in enumerate(info):
        col = i % 2
        row = i // 2
        x = start_x + col * col_w
        y = start_y + row * row_h

        icon = load_icon(icon_name, size=icon_size_small)
        if icon:
            img.paste(icon, (x, y))

        draw.text((x + 50, y + 8), str(text), font=FONT_SMALL, fill=0)

    return img
