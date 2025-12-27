# modules/weather/main.py
from PIL import Image, ImageDraw, ImageFont

DISPLAY_WIDTH = 800
DISPLAY_HEIGHT = 480

def render():
    """
    Returns a single 800x480 1-bit image with "Hello World" centered.
    """
    # Full screen white canvas
    img = Image.new("1", (DISPLAY_WIDTH, DISPLAY_HEIGHT), color=1)  # 1 = white
    draw = ImageDraw.Draw(img)
    # Font
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
    except:
        font = ImageFont.load_default()

    # Text
    text = "Hello World"
    text_width, text_height = draw.textsize(text, font=font)
    x = (DISPLAY_WIDTH - text_width) // 2
    y = (DISPLAY_HEIGHT - text_height) // 2

    draw.text((x, y), text, fill=1, font=font)  # 0 = black

    return img, True

# Test the module
if __name__ == "__main__":
    img = render()
    img.save("weather_test.png")
    print("Saved weather_test.png")