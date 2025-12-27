# modules/weather/main.py
import time
from PIL import Image, ImageDraw, ImageFont

_last_update = 0
_cache = None
UPDATE_INTERVAL = 5 * 60  # 5 minutes in seconds

def render():
    global _last_update, _cache
    now = time.time()

    if _cache is None or now - _last_update >= UPDATE_INTERVAL:
        _cache = _generate_weather_image()
        _last_update = now
        return _cache, True   # signal display should update

    return _cache, False      # no update needed

def _generate_weather_image():
    width, height = 200, 100
    img = Image.new("1", (width, height), color=1)  # white background
    draw = ImageDraw.Draw(img)

    # Centered text
    text = "Weather Info"
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
    except:
        font = ImageFont.load_default()

    text_width, text_height = draw.textsize(text, font=font)
    x = (width - text_width) // 2
    y = (height - text_height) // 2
    draw.text((x, y), text, fill=0, font=font)

    return img
