# modules/weather/main.py - WORKING VERSION
from PIL import Image, ImageDraw, ImageFont
import requests
import xml.etree.ElementTree as ET

SCREEN_W, SCREEN_H = 800, 480

# Font setup
try:
    FONT_LARGE = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80)
    FONT_MEDIUM = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
    FONT_SMALL = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
except Exception:
    FONT_LARGE = ImageFont.load_default()
    FONT_MEDIUM = ImageFont.load_default()
    FONT_SMALL = ImageFont.load_default()

def fetch_metar(station="KSFO"):
    """Get METAR XML data"""
    url = f"https://aviationweather.gov/api/data/metar?ids={station}&format=xml"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"METAR fetch error: {e}")
        return None

def parse_metar(xml_text):
    """Parse METAR XML to dict"""
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
            "wind_speed_kt": get_text("wind_speed_kt"),
            "wind_gust_kt": get_text("wind_gust_kt"),
            "wind_dir_degrees": get_text("wind_dir_degrees"),
            "visibility_statute_mi": get_text("visibility_statute_mi"),
            "sea_level_pressure_mb": get_text("sea_level_pressure_mb"),
            "altim_in_hg": get_text("altim_in_hg"),
            "wx_string": get_text("wx_string")
        }
    except Exception as e:
        print(f"XML parse error: {e}")
        return None

# RENDER FUNCTION - THIS IS WHAT YOUR FLASK APP CALLS
def render():
    """Create weather display image - called by Flask app"""
    # Fetch and parse data
    xml_data = fetch_metar("KSFO")
    metar = parse_metar(xml_data)
    
    # Create blank image
    img = Image.new("1", (SCREEN_W, SCREEN_H), 1)  # White background
    draw = ImageDraw.Draw(img)
    
    if metar and metar.get("raw_text"):
        # Draw weather info
        header = "KSFO San Francisco"
        w, _ = draw.textsize(header, font=FONT_MEDIUM)
        draw.text(((SCREEN_W - w) // 2, 20), header, font=FONT_MEDIUM, fill=0)
        
        # Temperature
        if metar.get("temp_c"):
            temp_f = round(float(metar["temp_c"]) * 9/5 + 32)
            temp_text = f"{temp_f}°F"
            w, h = draw.textsize(temp_text, font=FONT_LARGE)
            draw.text(((SCREEN_W - w) // 2, 100), temp_text, font=FONT_LARGE, fill=0)
        
        # Wind
        wind_text = f"Wind: {metar.get('wind_dir_degrees', '--')}° @ {metar.get('wind_speed_kt', '--')}kt"
        if metar.get("wind_gust_kt"):
            wind_text += f" G{metar['wind_gust_kt']}kt"
        draw.text((50, 220), wind_text, font=FONT_SMALL, fill=0)
        
        # Visibility and pressure
        vis_text = f"Vis: {metar.get('visibility_statute_mi', '--')}mi"
        press_text = f"Press: {metar.get('altim_in_hg', '--')}inHg"
        draw.text((50, 260), vis_text, font=FONT_SMALL, fill=0)
        draw.text((50, 290), press_text, font=FONT_SMALL, fill=0)
        
        # Raw METAR at bottom
        raw = metar.get("raw_text", "")[:60] + "..." if len(metar.get("raw_text", "")) > 60 else metar.get("raw_text", "")
        draw.text((50, 350), f"RAW: {raw}", font=FONT_SMALL, fill=0)
        
        # Weather condition
        if metar.get("wx_string"):
            draw.text((50, 180), f"Weather: {metar['wx_string']}", font=FONT_SMALL, fill=0)
    else:
        # No data
        error_text = "NO METAR DATA"
        w, h = draw.textsize(error_text, font=FONT_LARGE)
        draw.text(((SCREEN_W - w) // 2, SCREEN_H // 2 - h // 2), error_text, font=FONT_LARGE, fill=0)
    
    return img

# Test the module
if __name__ == "__main__":
    print("Testing weather module...")
    
    # Test fetch
    xml = fetch_metar()
    if xml:
        print("✓ METAR fetch successful")
        
        # Test parse
        data = parse_metar(xml)
        if data:
            print(f"✓ Parsed METAR: {data.get('raw_text', 'No raw text')}")
            print(f"✓ Temperature: {data.get('temp_c', 'N/A')}°C")
            print(f"✓ Wind: {data.get('wind_dir_degrees', 'N/A')}° @ {data.get('wind_speed_kt', 'N/A')}kt")
        else:
            print("✗ Failed to parse METAR")
    else:
        print("✗ Failed to fetch METAR")
    
    # Test render
    image = render()
    image.save("weather_test.png")
    print("✓ Render test saved as weather_test.png")