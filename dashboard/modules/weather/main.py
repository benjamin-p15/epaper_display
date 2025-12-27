# modules/weather/main.py
import time
from PIL import Image, ImageDraw, ImageFont

# Screen size
DISPLAY_WIDTH = 800
DISPLAY_HEIGHT = 480

# Internal cache to manage update timing
_last_update = 0
_cache = None
UPDATE_INTERVAL = 5 * 60  # seconds

def render():
    """
    Returns a tuple (image, update_flag)
    - image: 800x480 1-bit PIL image
    - update_flag: True if the display should refresh
    """
    global _last_update, _cache
    now = time.time()

    if _cache is None or now - _last_update >= UPDATE_INTERVAL:
        _cache = _generate_image()
        _last_update = now
        return _cache, True  # Refresh needed

    return _cache, False  # No refresh needed

def _generate_image():
    """
    Generates a full-screen white image with centered black text "Hello World".
    """
    img = Image.new("1", (DISPLAY_WIDTH, DISPLAY_HEIGHT), color=1)  # 1 = white
    draw = ImageDraw.Draw(img)

    # Load font
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
    except:
        font = ImageFont.load_default()

    # Center text
    text = "Hello World"
    text_width, text_height = draw.textsize(text, font=font)
    x = (DISPLAY_WIDTH - text_width) // 2
    y = (DISPLAY_HEIGHT - text_height) // 2

    draw.text((x, y), text, fill=0, font=font)  # 0 = black
    return img
