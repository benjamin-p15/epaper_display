from PIL import Image, ImageDraw, ImageFont
import os
import requests
import csv
from math import radians, cos, sin, asin, sqrt

# ================= CONFIG =================
SCREEN_W, SCREEN_H = 800, 480
ICON_DIR = os.path.join(os.path.dirname(__file__), "icons")
AIRPORTS_FILE = os.path.join(os.path.dirname(__file__), "airports.csv")  # CSV: ICAO,lat,lon,city,state

# Optional proxy configuration (if needed)
PROXY = {
    # "http": "http://IP:PORT",
    # "https": "http://IP:PORT"
}

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
def load_icon_bw(name, size=None):
    path = os.path.join(ICON_DIR, name)
    if not os.path.exists(path):
        return None
    img = Image.open(path).convert("RGBA")
    bw = Image.new("1", img.size, 1)  # white
    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = img.getpixel((x, y))
            if a > 0 and (r, g, b) != (255, 255, 255):
                bw.putpixel((x, y), 0)
    if size:
        bw = bw.resize(size)
    return bw

# ================= HELPERS =================
def haversine(lat1, lon1, lat2, lon2):
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
    return 6371 * 2 * asin(sqrt(a))  # km

def get_location():
    try:
        r = requests.get("https://ipinfo.io/json", timeout=5)
        loc = r.json().get("loc", "").split(",")
        return float(loc[0]), float(loc[1])
    except:
        return None, None

def find_nearest_airport(lat, lon):
    nearest = None
    min_dist = float('inf')
    if not os.path.exists(AIRPORTS_FILE):
        return "KSFO", "San Francisco", "CA"
    with open(AIRPORTS_FILE, "r") as f:
        reader = csv.reader(f)
        for icao, a_lat, a_lon, city, state in reader:
            a_lat, a_lon = float(a_lat), float(a_lon)
            d = haversine(lat, lon, a_lat, a_lon)
            if d < min_dist:
                min_dist = d
                nearest = (icao, city, state)
    return nearest or ("KSFO", "San Francisco", "CA")

# ================= METAR FETCH =================
def fetch_metar(station):
    """
    Use the Aviation Weather API to fetch JSON METAR data.
    Never crashes; falls back gracefully with defaults.
    """
    url = (
        "https://aviationweather.gov/api/data/metar"
        f"?ids={station}&format=json&mostRecent=true"
    )
    headers = {
        "User-Agent": "weather-display/1.0"
    }

    try:
        r = requests.get(url, headers=headers, proxies=PROXY if PROXY else None, timeout=10)
        r.raise_for_status()
        j = r.json()
        metars = j.get("data", [])
        report = metars[0] if metars else {}
    except Exception as e:
        print(f"METAR fetch error: {e}")
        report = {}

    def sf(k, default=None):
        v = report.get(k)
        return v if v not in (None, "") else default

    return {
        "temp_c": float(sf("temp_c", 20)),
        "dewpoint_c": float(sf("dewpoint_c", 20)),
        "wind_kt": sf("wind_speed_kt", "--"),
        "wind_dir": sf("wind_dir_degrees", "--"),
        "visibility_mi": sf("visibility_statute_mi", "--"),
        "pressure_hpa": sf("sea_level_pressure_mb", "--"),
        "weather": sf("wx_string", ""),
        "raw": sf("raw_text", "--"),
        "obs_time": sf("observation_time", "--")
    }

def c_to_f(c):
    return round(c * 9/5 + 32)

def choose_weather_icon(wx):
    if not wx: return "01d.png"
    w = wx.lower()
    if "ts" in w: return "11d.png"
    if "snow" in w: return "13d.png"
    if "rain" in w: return "09d.png"
    if "mist" in w or "fog" in w: return "50d.png"
    if "cloud" in w or "ovc" in w: return "04d.png"
    return "01d.png"

# ================= RENDER =================
def render():
    lat, lon = get_location()
    station, city, state = find_nearest_airport(lat, lon)
    data = fetch_metar(station)

    print(f"Weather @ {station} ({city}, {state})")
    print(data)

    temp_f = c_to_f(data["temp_c"])
    dew_f = c_to_f(data["dewpoint_c"])
    icon_name = choose_weather_icon(data["weather"])
    icon = load_icon_bw(icon_name, (150, 150))

    img = Image.new("1", (SCREEN_W, SCREEN_H), 1)
    draw = ImageDraw.Draw(img)

    # Header
    header = f"{city}, {state}"
    w, h = draw.textsize(header, font=FONT_MEDIUM)
    draw.text(((SCREEN_W - w)//2, 10), header, font=FONT_MEDIUM, fill=0)

    # Icon
    if icon:
        img.paste(icon, ((SCREEN_W - icon.width)//2, 60))

    # Temperature
    temp_text = f"{temp_f}°F"
    w, h = draw.textsize(temp_text, font=FONT_LARGE)
    draw.text(((SCREEN_W - w)//2, 230), temp_text, font=FONT_LARGE, fill=0)

    # Extra data
    info_y = 320
    draw.text((50, info_y), f"Feels: {dew_f}°F", font=FONT_SMALL, fill=0)
    draw.text((50, info_y + 30), f"Wind: {data['wind_dir']}° @ {data['wind_kt']} kt", font=FONT_SMALL, fill=0)
    draw.text((50, info_y + 60), f"Vis: {data['visibility_mi']} mi", font=FONT_SMALL, fill=0)
    draw.text((50, info_y + 90), f"Pressure: {data['pressure_hpa']} hPa", font=FONT_SMALL, fill=0)
    draw.text((50, info_y + 120), f"Raw: {data['raw']}", font=FONT_SMALL, fill=0)

    return img
