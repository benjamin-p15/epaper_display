from PIL import Image, ImageDraw, ImageFont
import os
import requests
import csv
from math import radians, cos, sin, asin

# ================= CONFIG =================
SCREEN_W, SCREEN_H = 800, 480
ICON_DIR = os.path.join(os.path.dirname(__file__), "icons")
AIRPORTS_FILE = os.path.join(os.path.dirname(__file__), "airports.csv")

PROXY = {
    # "http": "...",
    # "https": "..."
}

# ================= FONTS =================
try:
    FONT_LARGE = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80)
    FONT_MEDIUM = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
    FONT_SMALL = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
except Exception:
    FONT_LARGE = ImageFont.load_default()
    FONT_MEDIUM = ImageFont.load_default()
    FONT_SMALL = ImageFont.load_default()

# ================= ICON LOADING =================
def load_icon_bw(name, size=None):
    path = os.path.join(ICON_DIR, name)
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

# ================= HELPERS =================
def haversine(lat1, lon1, lat2, lon2):
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
    return 6371 * 2 * asin(a)

def get_location():
    try:
        r = requests.get("https://ipinfo.io/json", timeout=5)
        loc = r.json().get("loc", "").split(",")
        return float(loc[0]), float(loc[1])
    except Exception:
        return None, None

def find_nearest_airport(lat, lon):
    if lat is None or lon is None or not os.path.exists(AIRPORTS_FILE):
        return ("KSFO", "San Francisco", "CA")
    nearest = None
    min_dist = float("inf")
    with open(AIRPORTS_FILE, "r") as f:
        reader = csv.reader(f)
        for icao, a_lat, a_lon, city, state in reader:
            a_lat, a_lon = float(a_lat), float(a_lon)
            d = haversine(lat, lon, a_lat, a_lon)
            if d < min_dist:
                min_dist = d
                nearest = (icao, city, state)
    return nearest if nearest else ("KSFO", "San Francisco", "CA")

# ================= METAR FETCH =================
def fetch_metar(station):
    """
    Fetch METAR from NOAA AviationWeather JSON service
    Returns a dict or None if no real data exists.
    """
    base = "https://aviationweather.gov/adds/dataserver_current/httpparam"
    params = {
        "dataSource": "metars",
        "requestType": "retrieve",
        "format": "json",
        "stationString": station,
        "hoursBeforeNow": 1,
        "mostRecentForEachStation": "true"
    }
    try:
        r = requests.get(base, params=params, timeout=10, proxies=PROXY if PROXY else None)
        r.raise_for_status()
        j = r.json()
        mets = j.get("METAR", [])
        if not mets:
            return None
        report = mets[0]
        return report
    except Exception as e:
        print(f"METAR fetch failed: {e}")
        return None

# ================= ICON CHOOSER =================
def choose_weather_icon(metar):
    if not metar:
        return "50d.png"
    wx = metar.get("wx_string")
    if not wx:
        return "01d.png"
    lower = wx.lower()
    if "ts" in lower: return "11d.png"
    if "snow" in lower: return "13d.png"
    if "rain" in lower: return "09d.png"
    if "fog" in lower or "mist" in lower: return "50d.png"
    if "cloud" in lower or "ovc" in lower: return "04d.png"
    return "01d.png"

# ================= RENDER =================
def render():
    lat, lon = get_location()
    station, city, state = find_nearest_airport(lat, lon)
    metar = fetch_metar(station)

    img = Image.new("1", (SCREEN_W, SCREEN_H), 1)
    draw = ImageDraw.Draw(img)

    header = f"{station}  {city}, {state}"
    w, h = draw.textsize(header, font=FONT_MEDIUM)
    draw.text(((SCREEN_W-w)//2, 5), header, font=FONT_MEDIUM, fill=0)

    if not metar:
        # no real data
        no_txt = "No METAR data"
        w, h = draw.textsize(no_txt, font=FONT_LARGE)
        draw.text(((SCREEN_W-w)//2, SCREEN_H//2 - h//2), no_txt, font=FONT_LARGE, fill=0)
        return img

    # parse real values
    temp = metar.get("temp_c")
    dew = metar.get("dewpoint_c")
    vis = metar.get("visibility_statute_mi")
    wind_speed = metar.get("wind_speed_kt")
    wind_dir = metar.get("wind_dir_degrees")
    pressure = metar.get("sea_level_pressure_mb")
    raw = metar.get("raw_text")

    icon_name = choose_weather_icon(metar)
    icon = load_icon_bw(icon_name, (150, 150))
    if icon: img.paste(icon, ((SCREEN_W-icon.width)//2, 60))

    if temp is not None:
        try:
            tf = round(float(temp)*9/5+32)
            draw.text((50, 230), f"T: {tf}°F", font=FONT_LARGE, fill=0)
        except: pass

    info_y = 310
    draw.text((50, info_y), f"Wind: {wind_dir or '--'}° @ {wind_speed or '--'} kt", font=FONT_SMALL, fill=0)
    draw.text((50, info_y+30), f"Vis: {vis or '--'} mi", font=FONT_SMALL, fill=0)
    draw.text((50, info_y+60), f"Pres: {pressure or '--'} hPa", font=FONT_SMALL, fill=0)
    draw.text((50, info_y+90), raw or "--", font=FONT_SMALL, fill=0)

    return img
