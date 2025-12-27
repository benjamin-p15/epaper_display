from PIL import Image

def render():
    img = Image.new("1", (800, 480), color=255)
    return img, True
