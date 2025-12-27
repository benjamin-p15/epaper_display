# modules/weather/main.py
from PIL import Image, ImageDraw, ImageFont
import os
import requests
import xml.etree.ElementTree as ET

# ================= CONFIG =================
SCREEN_W, SCREEN_H = 800, 480
ICON_DIR = os.path.join(os.path.dirname(__file__), "icons")
STATION = "KSFO"  # default airport
CITY = "Unknown"
STATE = "Unknown"

# ================= FONTS =================
try:
    FONT_LARGE = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80)
    FONT_MEDIUM = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
    FONT_SMALL = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
except:
    FONT_LARGE = ImageFont.load_default()
    FONT_MEDIUM = ImageFont.load_default()
    FONT_SMALL = ImageFont.load_default()

# ================= ICON LOADING =================
def load_icon_bw(path, size=None):
    """Load icon: transparent/white stays white, all else black"""
    if not os.path.exists(path):
        return None
    img = Image.open(path).convert("RGBA")
    bw = Image.new("1", img.size, 1)
    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = img.getpixel((x, y))
            if a > 0 and (r, g, b) != (255, 255, 255):
                bw.putpixel((x, y), 0)
    if size:
        bw = bw.resize(size)
    return bw

# ================= METAR FETCH =================
def fetch_metar(station=STATION):
    """Fetch latest METAR XML and parse fields"""
    url = (
        "https://aviationweather.gov/adds/dataserver_current/httpparam"
        "?dataSource=metars"
        "&requestType=retrieve"
        "&format=xml"
        f"&stationString={station}"
        "&hoursBeforeNow=1"
    )
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/xml",
        "Referer": "https://aviationweather.gov/metar",
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
            "temp_c": float(get("temp_c")) if get("temp_c") else "--",
            "dewpoint_c": float(get("dewpoint_c")) if get("dewpoint_c") else "--",
            "wind_kt": get("wind_speed_kt") or "--",
            "wind_dir": get("wind_dir_degrees") or "--",
            "visibility_mi": get("visibility_statute_mi") or "--",
            "pressure_hpa": get("sea_level_pressure_mb") or "--",
            "weather": get("wx_string"),
            "raw": get("raw_text") or "--",
            "observation_time": get("observation_time") or "--",
        }

    except Exception as e:
        print(f"[WARN] Failed to fetch METAR: {e}")
        return {
            "temp_c": 20,
            "dewpoint_c": 15,
            "wind_kt": "--",
            "wind_dir": "--",
            "visibility_mi": "--",
            "pressure_hpa": "--",
            "weather": None,
            "raw": "--",
            "observation_time": "--",
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
    return "01d.png"

# ================= RENDER =================
def render():
    data = fetch_metar()
    print("[DEBUG] METAR data:", data)

    temp_f = c_to_f(data["temp_c"]) if data["temp_c"] != "--" else "--"
    feels_f = c_to_f(data["dewpoint_c"]) if data["dewpoint_c"] != "--" else "--"
    main_icon_name = choose_weather_icon(data["weather"])

    img = Image.new("1", (SCREEN_W, SCREEN_H), 1)
    draw = ImageDraw.Draw(img)

    # Header
    header_text = f"{CITY}, {STATE}"
    w, h = draw.textsize(header_text, font=FONT_MEDIUM)
    draw.text(((SCREEN_W - w) // 2, 10), header_text, font=FONT_MEDIUM, fill=0)

    # Main weather icon and temperature
    icon_size = (180, 180)
    main_icon = load_icon_bw(os.path.join(ICON_DIR, main_icon_name), size=icon_size)
    if main_icon:
        img.paste(main_icon, (50, 80))

    draw.text((260, 110), f"{temp_f}°", font=FONT_LARGE, fill=0)
    draw.text((265, 210), f"Feels like {feels_f}°", font=FONT_SMALL, fill=0)

    # Info grid
    info = [
        ("windL.png", f"{data['wind_dir']}° {data['wind_kt']} kt"),
        ("pressure.png", f"{data['pressure_hpa']} hPa"),
        ("visibility.png", f"{data['visibility_mi']} mi"),
        ("humidity.png", f"{data['dewpoint_c']}°C"),
        ("sunrise.png", "--"),
        ("sunset.png", "--"),
        ("uvi.png", "--"),
        ("aqi.png", "--"),
    ]
    start_x, start_y, col_w, row_h = 480, 80, 160, 100
    icon_size_small = (50, 50)

    for i, (icon_name, text) in enumerate(info):
        col, row = i % 2, i // 2
        x, y = start_x + col * col_w, start_y + row * row_h
        icon = load_icon_bw(os.path.join(ICON_DIR, icon_name), size=icon_size_small)
        if icon:
            img.paste(icon, (x, y))
        draw.text((x + 60, y + 10), str(text), font=FONT_SMALL, fill=0)

    return img

# ================= TEST =================
if __name__ == "__main__":
    img = render()
    img.save("weather_test.png")
    print("[DEBUG] Saved test image as weather_test.png")
