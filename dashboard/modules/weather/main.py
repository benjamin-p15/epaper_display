# modules/weather/main.py
import time
from PIL import Image, ImageDraw, ImageFont

_last_update = 0
_cache = None
UPDATE_INTERVAL = 5 * 60  # 5 minutes

def render():
    global _last_update, _cache
    now = time.time()
    if _cache is None or now - _last_update >= UPDATE_INTERVAL:
        _cache = _generate_weather_image()
        _last_update = now
        return _cache, True
    return _cache, False

def _generate_weather_image():
    # Create a black-and-white (1-bit) image
    img = Image.new("1", (200, 100), color=1)  # 1=white, 0=black
    draw = ImageDraw.Draw(img)
    # Example: draw text
    draw.text((10, 10), "Weather Info", fill=0)  # 0=black
    return img
