# modules/weather/main.py - FIXED VERSION
from PIL import Image, ImageDraw, ImageFont
import requests
import xml.etree.ElementTree as ET

SCREEN_W, SCREEN_H = 800, 480

# Font setup - MUST MATCH YOUR DISPLAY SIZE
try:
    FONT_LARGE = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80)
    FONT_MEDIUM = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
    FONT_SMALL = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
except:
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
        print(f"METAR fetch failed: {e}")
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
            "dewpoint_c": get_text("dewpoint_c"),
            "wind_speed_kt": get_text("wind_speed_kt"),
            "wind_gust_kt": get_text("wind_gust_kt"),
            "wind_dir_degrees": get_text("wind_dir_degrees"),
            "visibility_statute_mi": get_text("visibility_statute_mi"),
            "sea_level_pressure_mb": get_text("sea_level_pressure_mb"),
            "altim_in_hg": get_text("altim_in_hg"),
            "wx_string": get_text("wx_string")
        }
    except Exception as e:
        print(f"XML parse failed: {e}")
        return None

# ================= RENDER FUNCTION =================
def render():
    """MAIN RENDER FUNCTION - Returns 800x480 image for e-paper"""
    print("[WEATHER] Starting render()")
    
    # Get METAR data
    xml_data = fetch_metar("KSFO")
    metar = parse_metar(xml_data)
    
    # CREATE THE IMAGE - THIS IS WHAT WAS MISSING
    img = Image.new("1", (SCREEN_W, SCREEN_H), 1)  # 1-bit, white background
    draw = ImageDraw.Draw(img)
    
    if metar and metar.get("raw_text"):
        raw_metar = metar["raw_text"]
        print(f"[WEATHER] Got METAR: {raw_metar[:50]}...")
        
        # Print to terminal
        print("\n" + "="*60)
        print(f"RAW METAR DATA: {raw_metar}")
        print("="*60)
        
        # Draw header
        header = "KSFO - San Francisco"
        w, _ = draw.textsize(header, font=FONT_MEDIUM)
        draw.text(((SCREEN_W - w) // 2, 20), header, font=FONT_MEDIUM, fill=0)
        
        # Draw temperature
        if metar.get("temp_c"):
            temp_c = float(metar["temp_c"])
            temp_f = round(temp_c * 9/5 + 32)
            temp_text = f"{temp_f}°F"
            w_temp, h_temp = draw.textsize(temp_text, font=FONT_LARGE)
            draw.text(((SCREEN_W - w_temp) // 2, 120), temp_text, font=FONT_LARGE, fill=0)
            
            # Draw temperature in Celsius too
            draw.text(((SCREEN_W - w_temp) // 2, 210), f"({temp_c}°C)", font=FONT_SMALL, fill=0)
        
        # Draw wind info
        wind_text = f"Wind: {metar.get('wind_dir_degrees', '--')}° @ {metar.get('wind_speed_kt', '--')}kt"
        if metar.get("wind_gust_kt"):
            wind_text += f" G{metar['wind_gust_kt']}kt"
        draw.text((50, 280), wind_text, font=FONT_SMALL, fill=0)
        
        # Draw visibility
        if metar.get("visibility_statute_mi"):
            vis_text = f"Visibility: {metar['visibility_statute_mi']} miles"
            draw.text((50, 310), vis_text, font=FONT_SMALL, fill=0)
        
        # Draw pressure
        if metar.get("altim_in_hg"):
            press_text = f"Pressure: {metar['altim_in_hg']} inHg"
            draw.text((50, 340), press_text, font=FONT_SMALL, fill=0)
        elif metar.get("sea_level_pressure_mb"):
            press_text = f"Pressure: {metar['sea_level_pressure_mb']} hPa"
            draw.text((50, 340), press_text, font=FONT_SMALL, fill=0)
        
        # Draw weather condition
        if metar.get("wx_string"):
            wx_text = f"Weather: {metar['wx_string']}"
            draw.text((50, 250), wx_text, font=FONT_SMALL, fill=0)
        
        # Draw raw METAR at bottom
        raw_display = raw_metar
        if len(raw_display) > 70:
            raw_display = raw_display[:67] + "..."
        draw.text((20, 400), f"METAR: {raw_display}", font=FONT_SMALL, fill=0)
        
    else:
        print("[WEATHER] No METAR data available")
        # Draw error message
        error_text = "NO WEATHER DATA AVAILABLE"
        w_err, h_err = draw.textsize(error_text, font=FONT_LARGE)
        draw.text(((SCREEN_W - w_err) // 2, SCREEN_H // 2 - h_err // 2), 
                 error_text, font=FONT_LARGE, fill=0)
    
    print("[WEATHER] render() completed, returning image")
    return img

# Test the module
if __name__ == "__main__":
    print("Testing weather module...")
    test_image = render()
    test_image.save("weather_test.png")
    print("Saved weather_test.png for verification")