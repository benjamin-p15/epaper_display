# weather_display.py - FIXED VERSION
from PIL import Image, ImageDraw, ImageFont
import os
import requests
import xml.etree.ElementTree as ET

# ================= CONFIG =================
SCREEN_W, SCREEN_H = 800, 480
ICON_DIR = os.path.join(os.path.dirname(__file__), "icons")

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

# ================= METAR FETCH =================
def fetch_metar(station="KSFO"):
    """Fetch METAR from working API"""
    url = f"https://aviationweather.gov/api/data/metar?ids={station}&format=xml"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"Warning: Failed to fetch METAR: {e}")
        return None

def parse_metar_data(xml_text):
    """Parse the actual METAR data"""
    if not xml_text:
        return None
    
    try:
        root = ET.fromstring(xml_text)
        metar = root.find(".//METAR")
        if metar is None:
            return None
            
        def get(tag):
            el = metar.find(tag)
            return el.text if el is not None else None
        
        # Get raw text first - this is the actual METAR string
        raw_text = get("raw_text")
        
        # Try to extract values from XML
        temp_c = get("temp_c")
        dewpoint_c = get("dewpoint_c")
        wind_kt = get("wind_speed_kt")
        wind_gust_kt = get("wind_gust_kt")
        wind_dir = get("wind_dir_degrees")
        visibility_mi = get("visibility_statute_mi")
        pressure_mb = get("sea_level_pressure_mb")
        altim_hg = get("altim_in_hg")
        weather = get("wx_string")
        
        return {
            "raw": raw_text,
            "temp_c": float(temp_c) if temp_c else None,
            "dewpoint_c": float(dewpoint_c) if dewpoint_c else None,
            "wind_kt": wind_kt,
            "wind_gust_kt": wind_gust_kt,
            "wind_dir": wind_dir,
            "visibility_mi": visibility_mi,
            "pressure_mb": pressure_mb,
            "altim_hg": altim_hg,
            "weather": weather,
        }
        
    except Exception as e:
        print(f"Parse error: {e}")
        return None

def c_to_f(c):
    if c is None:
        return None
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
def render(station="KSFO", city="San Francisco", state="CA"):
    """Main render function for e-paper display"""
    # Get METAR data
    xml_data = fetch_metar(station)
    data = parse_metar_data(xml_data)
    
    print(f"\n=== METAR for {station} ===")
    if data and data.get("raw"):
        print(f"RAW: {data['raw']}")
        if data.get("temp_c"):
            print(f"Temp: {data['temp_c']}°C ({c_to_f(data['temp_c'])}°F)")
        if data.get("wind_dir") and data.get("wind_kt"):
            print(f"Wind: {data['wind_dir']}° @ {data['wind_kt']}kt" + 
                  (f" G{data['wind_gust_kt']}" if data.get("wind_gust_kt") else ""))
    else:
        print("No METAR data available")
    
    # Create display image
    img = Image.new("1", (SCREEN_W, SCREEN_H), 1)  # White background for e-paper
    draw = ImageDraw.Draw(img)
    
    # Header
    header_text = f"{city}, {state}"
    w, h = draw.textsize(header_text, font=FONT_MEDIUM)
    draw.text(((SCREEN_W - w) // 2, 10), header_text, font=FONT_MEDIUM, fill=0)
    
    # Station ID below header
    station_text = f"{station}"
    w_station, _ = draw.textsize(station_text, font=FONT_SMALL)
    draw.text(((SCREEN_W - w_station) // 2, 50), station_text, font=FONT_SMALL, fill=0)
    
    if not data:
        # No data available
        error_text = "NO WEATHER DATA"
        w_err, h_err = draw.textsize(error_text, font=FONT_LARGE)
        draw.text(((SCREEN_W - w_err) // 2, SCREEN_H // 2 - h_err // 2), 
                 error_text, font=FONT_LARGE, fill=0)
        return img
    
    # Main weather icon and temperature
    icon_size = (180, 180)
    main_icon_name = choose_weather_icon(data.get("weather"))
    main_icon_path = os.path.join(ICON_DIR, main_icon_name)
    main_icon = load_icon_bw(main_icon_path, size=icon_size)
    
    if main_icon:
        img.paste(main_icon, (50, 100))
    
    # Temperature display
    temp_f = c_to_f(data.get("temp_c"))
    if temp_f is not None:
        draw.text((260, 120), f"{temp_f}°F", font=FONT_LARGE, fill=0)
    
    # Feels like (using dew point approximation)
    dewpoint_f = c_to_f(data.get("dewpoint_c"))
    if dewpoint_f is not None:
        draw.text((265, 220), f"Dew: {dewpoint_f}°F", font=FONT_SMALL, fill=0)
    
    # Info grid - only show available data
    info_items = []
    
    # Wind
    if data.get("wind_dir") and data.get("wind_kt"):
        wind_text = f"{data['wind_dir']}° @ {data['wind_kt']}kt"
        if data.get("wind_gust_kt"):
            wind_text += f" G{data['wind_gust_kt']}"
        info_items.append(("windL.png", wind_text))
    
    # Pressure (prefer inHg for US)
    if data.get("altim_hg"):
        info_items.append(("pressure.png", f"{data['altim_hg']} inHg"))
    elif data.get("pressure_mb"):
        info_items.append(("pressure.png", f"{data['pressure_mb']} hPa"))
    
    # Visibility
    if data.get("visibility_mi"):
        info_items.append(("visibility.png", f"{data['visibility_mi']} mi"))
    
    # Weather condition
    if data.get("weather"):
        info_items.append(("humidity.png", data['weather']))
    
    # Add some static info if we need more items
    while len(info_items) < 8:
        info_items.append((f"empty.png", "--"))
    
    # Draw info grid
    start_x = 480
    start_y = 100
    col_w = 160
    row_h = 100
    icon_size_small = (50, 50)
    
    for i, (icon_name, text) in enumerate(info_items):
        col = i % 2
        row = i // 2
        x = start_x + col * col_w
        y = start_y + row * row_h
        
        icon_path = os.path.join(ICON_DIR, icon_name)
        if os.path.exists(icon_path):
            icon = load_icon_bw(icon_path, size=icon_size_small)
            if icon:
                img.paste(icon, (x, y))
        
        draw.text((x + 60, y + 10), str(text), font=FONT_SMALL, fill=0)
    
    # Raw METAR at bottom (truncated if too long)
    if data.get("raw"):
        raw_display = data['raw']
        if len(raw_display) > 80:
            raw_display = raw_display[:77] + "..."
        draw.text((20, 430), f"METAR: {raw_display}", font=FONT_SMALL, fill=0)
    
    return img

# Test function
if __name__ == "__main__":
    print("Testing e-paper weather display...")
    image = render()
    image.save("weather_display_test.png")
    print("Saved to weather_display_test.png")