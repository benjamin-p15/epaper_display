# modules/weather/main.py
from PIL import Image, ImageDraw, ImageFont
import requests
import xml.etree.ElementTree as ET

SCREEN_W, SCREEN_H = 800, 480

# Font setup (keep your existing font code)
try:
    FONT_LARGE = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80)
    FONT_MEDIUM = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
    FONT_SMALL = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
except Exception:
    FONT_LARGE = ImageFont.load_default()
    FONT_MEDIUM = ImageFont.load_default()
    FONT_SMALL = ImageFont.load_default()

# METAR DATA FETCH
def fetch_metar(station="KSFO"):
    """GET THE FUCKING METAR DATA"""
    url = f"https://aviationweather.gov/api/data/metar?ids={station}&format=xml"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"ERROR: {e}")
        return None

def parse_metar(xml_text):
    """PARSE THE METAR XML"""
    if not xml_text:
        return None
    
    try:
        root = ET.fromstring(xml_text)
        metar = root.find(".//METAR")
        if metar is None:
            return None
            
        def get_text(tag):
            el = metar.find(tag)
            return el.text if el is not None else None
            
        return {
            "raw_text": get_text("raw_text"),
            "temp_c": get_text("temp_c"),
            "dewpoint_c": get_text("dewpoint_c"),
            "wind_speed_kt": get_text("wind_speed_kt"),
            "wind_gust_kt": get_text("wind_gust_kt"),
            "wind_dir_degrees": get_text("wind_dir_degrees"),
            "visibility_statute_mi": get_text("visibility_statute_mi"),
            "sea_level_pressure_mb": get_text("sea_level_pressure_mb"),
            "altim_in_hg": get_text("altim_in_hg"),
            "wx_string": get_text("wx_string"),
            "flight_category": get_text("flight_category")
        }
    except Exception as e:
        print(f"PARSE ERROR: {e}")
        return None

# RENDER FUNCTION (YOU NEED THIS)
def render():
    """RENDER FUNCTION - FIXED"""
    # Get the fucking data
    xml_data = fetch_metar("KSFO")
    metar = parse_metar(xml_data) if xml_data else None
    
    # Create image
    img = Image.new("1", (SCREEN_W, SCREEN_H), 1)  # White background
    draw = ImageDraw.Draw(img)
    
    # Show what we got
    if metar:
        # Print the raw METAR to console
        print(f"RAW METAR: {metar.get('raw_text')}")
        
        # Draw on image
        header = "KSFO San Francisco, CA"
        w, _ = draw.textsize(header, font=FONT_MEDIUM)
        draw.text(((SCREEN_W - w) // 2, 5), header, font=FONT_MEDIUM, fill=0)
        
        temp_c = metar.get("temp_c")
        if temp_c:
            temp_f = round(float(temp_c) * 9/5 + 32)
            draw.text((50, 100), f"Temp: {temp_f}°F", font=FONT_LARGE, fill=0)
        
        wind = f"{metar.get('wind_dir_degrees', '--')}° @ {metar.get('wind_speed_kt', '--')} kt"
        draw.text((50, 200), f"Wind: {wind}", font=FONT_SMALL, fill=0)
        
        draw.text((50, 250), f"RAW: {metar.get('raw_text', '--')}", font=FONT_SMALL, fill=0)
    else:
        draw.text((100, 200), "NO METAR DATA", font=FONT_LARGE, fill=0)
    
    return img

# TEST
if __name__ == "__main__":
    # Fetch and print data
    data = fetch_metar("KSFO")
    if data:
        print("METAR XML:")
        print(data[:500] + "..." if len(data) > 500 else data)
    
    # Test render
    image = render()
    image.save("test.png")
    print("Image saved as test.png")