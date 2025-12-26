from PIL import Image, ImageDraw, ImageFont
import os
import requests
import xml.etree.ElementTree as ET
from math import radians, cos, sin, asin, sqrt

# ================= CONFIG =================
SCREEN_W, SCREEN_H = 800, 480
ICON_DIR = os.path.join(os.path.dirname(__file__), "icons")
AIRPORTS_FILE = os.path.join(os.path.dirname(__file__), "airports.csv")  # CSV with ICAO,lat,lon,city,state

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

# ================= HELPER FUNCTIONS =================
def haversine(lat1, lon1, lat2, lon2):
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1; dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
    return 6371*2*asin(sqrt(a))

def get_location():
    try:
        ip_info = requests.get("https://ipinfo.io/json", timeout=5).json()
        lat, lon = map(float, ip_info["loc"].split(","))
        return lat, lon
    except Exception as e:
        print("Could not get location:", e)
        return None, None

def find_nearest_airport(lat, lon):
    nearest = None
    min_dist = float('inf')
    if not os.path.exists(AIRPORTS_FILE):
        return "KSFO", "San Francisco", "CA"
    with open(AIRPORTS_FILE, "r") as f:
        for line in f:
            parts = line.strip().split(",")
            icao, a_lat, a_lon, city, state = parts
            a_lat, a_lon = float(a_lat), float(a_lon)
            d = haversine(lat, lon, a_lat, a_lon)
            if d < min_dist:
                min_dist = d
                nearest = (icao, city, state)
    return nearest or ("KSFO", "San Francisco", "CA")

def fetch_metar(station):
    url = (
        "https://aviationweather.gov/adds/dataserver_current/httpparam"
        "?dataSource=metars&requestType=retrieve&format=xml"
        f"&stationString={station}&hoursBeforeNow=1"
    )
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/121.0 Safari/537.36",
        "Referer": "https://aviationweather.gov/metar"
    }

    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        root = ET.fromstring(r.text)
        metar = root.find(".//METAR")
        if metar is None:
            print("No METAR found. Full XML:")
            print(r.text)
            return None

        def get(tag):
            el = metar.find(tag)
            return el.text if el is not None else None

        return {
            "temp_c": get("temp_c"),
            "dewpoint_c": get("dewpoint_c"),
            "wind_kt": get("wind_speed_kt"),
            "wind_dir": get("wind_dir_degrees"),
            "visibility_mi": get("visibility_statute_mi"),
            "pressure_hpa": get("sea_level_pressure_mb"),
            "weather": get("wx_string"),
            "raw": get("raw_text"),
            "obs_time": get("observation_time")
        }

    except requests.HTTPError as e:
        print(f"HTTP error: {e}")
        return None
    except Exception as e:
        print(f"Other error fetching METAR: {e}")
        return None

def c_to_f(c):
    return round(float(c)*9/5+32) if c else "--"

def choose_weather_icon(wx):
    if not wx: return "01d.png"
    wx = wx.lower()
    if "ts" in wx: return "11d.png"
    if "snow" in wx: return "13d.png"
    if "rain" in wx: return "09d.png"
    if "mist" in wx or "fog" in wx: return "50d.png"
    if "cloud" in wx or "ovc" in wx: return "04d.png"
    return "01d.png"

# ================= RENDER =================
def render():
    lat, lon = get_location()
    station, city, state = find_nearest_airport(lat, lon)
    data = fetch_metar(station)

    if not data:
        print("Failed to fetch METAR data. Exiting render.")
        return None

    print(f"Station: {station}, City: {city}, State: {state}")
    print("Full METAR data:", data)

    temp_f = c_to_f(data["temp_c"])
    feels_f = c_to_f(data["dewpoint_c"])
    main_icon_name = choose_weather_icon(data["weather"])

    img = Image.new("1", (SCREEN_W, SCREEN_H), 1)
    draw = ImageDraw.Draw(img)

    header = f"{city}, {state}"
    w, h = draw.textsize(header, font=FONT_MEDIUM)
    draw.text(((SCREEN_W-w)//2, 10), header, font=FONT_MEDIUM, fill=0)

    icon = load_icon_bw(os.path.join(ICON_DIR, main_icon_name), size=(180,180))
    if icon: img.paste(icon,(50,80))
    draw.text((260,110), f"{temp_f}°", font=FONT_LARGE, fill=0)
    draw.text((265,210), f"Feels like {feels_f}°", font=FONT_SMALL, fill=0)

    info = [
        ("windL.png", f"{data['wind_dir']}° {data['wind_kt']} kt"),
        ("pressure.png", f"{data['pressure_hpa']} hPa"),
        ("visibility.png", f"{data['visibility_mi']} mi"),
        ("humidity.png", f"{data['dewpoint_c']}°C"),
    ]
    start_x=480; start_y=80; col_w=160; row_h=100; icon_size=(50,50)
    for i,(icon_name,text) in enumerate(info):
        col=i%2; row=i//2; x=start_x+col*col_w; y=start_y+row*row_h
        ic = load_icon_bw(os.path.join(ICON_DIR,icon_name), size=icon_size)
        if ic: img.paste(ic,(x,y))
        draw.text((x+60,y+10),str(text),font=FONT_SMALL,fill=0)

    return img

if __name__ == "__main__":
    render()
