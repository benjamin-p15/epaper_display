# modules/weather/main.py
import time
from PIL import Image, ImageDraw

_last_update = 0
_cache = None
UPDATE_INTERVAL = 5 * 60  # 5 minutes in seconds

def render():
    global _last_update, _cache
    now = time.time()

    if _cache is None or now - _last_update >= UPDATE_INTERVAL:
        _cache = _generate_weather_image()
        _last_update = now
        return _cache, True  # signal display should update

    return _cache, False  # no update needed

def _generate_weather_image():
    # create 1-bit black-and-white image
    img = Image.new("1", (200, 100), color=1)  # 1 = white background
    draw = ImageDraw.Draw(img)
    draw.text((10, 10), "Weather Info", fill=0)  # 0 = black
    return img
