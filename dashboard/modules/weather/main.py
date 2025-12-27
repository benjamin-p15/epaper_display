# modules/weather/main.py
import time
from PIL import Image, ImageDraw, ImageFont

# Internal cache to manage update timing
_last_update = 0
_cache = None
UPDATE_INTERVAL = 5 * 60  # 5 minutes in seconds

DISPLAY_WIDTH = 800
DISPLAY_HEIGHT = 480
TEXT_IMG_WIDTH = 200
TEXT_IMG_HEIGHT = 100

def render():
    """
    Returns the current image and whether the display should update.
    The image is refreshed every 5 minutes.
    """
    global _last_update, _cache
    now = time.time()

    if _cache is None or now - _last_update >= UPDATE_INTERVAL:
        _cache = _generate_weather_image()
        _last_update = now
        return _cache, True  # signal display should update

    return _cache, False  # no update needed

def _generate_weather_image():
    """
    Generates an 800x480 white image with centered black text.
    """
    # Small image with text
    text_img = Image.new("1", (TEXT_IMG_WIDTH, TEXT_IMG_HEIGHT), color=1)  # 1 = white
    draw = ImageDraw.Draw(text_img)

    text = "Hello World"
    try:
        font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24
        )
    except:
        font = ImageFont.load_default()

    # Center text on small image
    text_width, text_height = draw.textsize(text, font=font)
    x = (TEXT_IMG_WIDTH - text_width) // 2
    y = (TEXT_IMG_HEIGHT - text_height) // 2
    draw.text((x, y), text, fill=0, font=font)  # black text

    # Full display canvas
    img_full = Image.new("1", (DISPLAY_WIDTH, DISPLAY_HEIGHT), color=1)  # white
    # Paste small image centered
    paste_x = (DISPLAY_WIDTH - TEXT_IMG_WIDTH) // 2
    paste_y = (DISPLAY_HEIGHT - TEXT_IMG_HEIGHT) // 2
    img_full.paste(text_img, (paste_x, paste_y))

    return img_full
