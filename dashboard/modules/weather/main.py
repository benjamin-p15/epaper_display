from PIL import Image

def render():
    img = Image.new("1", (800, 480), color=1)
    return img, True
