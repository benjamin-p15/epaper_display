from PIL import Image, ImageDraw

def render():
    img = Image.new("1", (800, 480), 255)
    draw = ImageDraw.Draw(img)

    text = "San Francisco\n22°C\nSunny"
    draw.text((100, 150), text, fill=0)

    return img
