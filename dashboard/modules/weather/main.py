from PIL import Image, ImageDraw, ImageFont

def test_image():
    width, height = 200, 100
    img = Image.new("1", (width, height), color=1)  # white background
    draw = ImageDraw.Draw(img)

    # Use a built-in font for simplicity
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
    except:
        font = ImageFont.load_default()

    text = "TEST"
    text_width, text_height = draw.textsize(text, font=font)
    x = (width - text_width) // 2
    y = (height - text_height) // 2

    draw.text((x, y), text, fill=0, font=font)  # 0 = black text

    return img

# Example usage:
img = test_image()
img.show()  # Opens image in default image viewer for testing
