# modules/weather/main.py - WITH DEBUG PRINTING
from PIL import Image, ImageDraw, ImageFont
import requests
import xml.etree.ElementTree as ET
import sys

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
    print(f"[DEBUG] Fetching from: {url}")
    try:
        r = requests.get(url, timeout=10)
        print(f"[DEBUG] Response status: {r.status_code}")
        print(f"[DEBUG] Response length: {len(r.text)} chars")
        
        if r.status_code == 200:
            print(f"[DEBUG] First 200 chars: {r.text[:200]}")
        
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"[ERROR] METAR fetch failed: {e}")
        return None

def parse_metar(xml_text):
    """Parse METAR XML to dict"""
    print(f"[DEBUG] parse_metar called, xml_text type: {type(xml_text)}, length: {len(xml_text) if xml_text else 0}")
    
    if not xml_text:
        print("[DEBUG] No XML text to parse")
        return None
    
    try:
        print("[DEBUG] Parsing XML...")
        root = ET.fromstring(xml_text)
        print(f"[DEBUG] Root tag: {root.tag}")
        
        metar = root.find(".//METAR")
        print(f"[DEBUG] Found METAR element: {metar is not None}")
        
        if metar is None:
            print("[DEBUG] No METAR element found in XML")
            return None
            
        def get_text(tag):
            el = metar.find(tag)
            value = el.text if el is not None else None
            print(f"[DEBUG] Tag '{tag}': {value}")
            return value
            
        result = {
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
        
        print(f"[DEBUG] Parsed result: {result}")
        return result
        
    except Exception as e:
        print(f"[ERROR] XML parse failed: {e}")
        import traceback
        traceback.print_exc()
        return None

# RENDER FUNCTION
def render():
    """Create weather display image"""
    print("\n" + "="*50)
    print("[DEBUG] render() function called")
    print("="*50)
    
    # Fetch and parse data
    xml_data = fetch_metar("KSFO")
    metar = parse_metar(xml_data)
    
    print(f"[DEBUG] metar data after parse: {metar}")
    
    # Create blank image
    img = Image.new("1", (SCREEN_W, SCREEN_H), 1)
    draw = ImageDraw.Draw(img)
    
    if metar and metar.get("raw_text"):
        print(f"[DEBUG] Drawing METAR data: {metar.get('raw_text')}")
        
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
            print(f"[DEBUG] Temperature: {temp_f}°F ({metar['temp_c']}°C)")
        
        # Wind
        wind_text = f"Wind: {metar.get('wind_dir_degrees', '--')}° @ {metar.get('wind_speed_kt', '--')}kt"
        if metar.get("wind_gust_kt"):
            wind_text += f" G{metar['wind_gust_kt']}kt"
        draw.text((50, 220), wind_text, font=FONT_SMALL, fill=0)
        print(f"[DEBUG] Wind: {wind_text}")
        
        # RAW METAR - PRINT TO CONSOLE
        raw_metar = metar.get("raw_text", "")
        print(f"\n{'='*50}")
        print("RAW METAR DATA:")
        print(f"{raw_metar}")
        print(f"{'='*50}\n")
        
    else:
        print("[DEBUG] No METAR data available")
        error_text = "NO METAR DATA"
        w, h = draw.textsize(error_text, font=FONT_LARGE)
        draw.text(((SCREEN_W - w) // 2, SCREEN_H // 2 - h // 2), error_text, font=FONT_LARGE, fill=0)
    
    print("[DEBUG] render() returning image")
    return img

# Test the module
if __name__ == "__main__":
    print("="*50)
    print("TESTING WEATHER MODULE")
    print("="*50)
    
    # Test render
    print("\nCalling render()...")
    image = render()
    
    # Save test image
    image.save("weather_test.png")
    print(f"\n[DEBUG] Test image saved as weather_test.png")
    
    # Also test direct fetch
    print("\n" + "="*50)
    print("DIRECT FETCH TEST:")
    print("="*50)
    
    xml = fetch_metar("KSFO")
    if xml:
        data = parse_metar(xml)
        if data and data.get("raw_text"):
            print(f"\nDIRECT RAW METAR: {data.get('raw_text')}")
        else:
            print("\nNo data parsed from XML")
    else:
        print("\nFailed to fetch XML")