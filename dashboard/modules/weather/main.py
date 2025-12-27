# modules/weather/main.py
from PIL import Image

DISPLAY_WIDTH = 800
DISPLAY_HEIGHT = 480

def render():
    """
    Returns a single 800x480 1-bit white image for the e-paper display,
    with update_flag always True.
    """
    img = Image.new("1", (DISPLAY_WIDTH, DISPLAY_HEIGHT), color=1)  # 1 = white
    return img, True
