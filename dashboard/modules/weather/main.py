from PIL import Image, ImageDraw, ImageFont

def _generate_weather_image():
    # create 1-bit black-and-white image
    width, height = 200, 100  # e-paper display size
    img = Image.new("1", (width, height), color=1)  # 1 = white background
    draw = ImageDraw.Draw(img)

    # Load a truetype font (you can use a default PIL font if none available)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
    except:
        font = ImageFont.load_default()

    text = "Weather Info"

    # Get size of the text
    text_width, text_height = draw.textsize(text, font=font)

    # Calculate centered position
    x = (width - text_width) // 2
    y = (height - text_height) // 2

    # Draw text in black
    draw.text((x, y), text, fill=0, font=font)

    return img
