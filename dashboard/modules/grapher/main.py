from PIL import Image, ImageDraw
import random, math, time

# Example graphing parameters
img_width = 400
img_height = 300
graph_scale = 10
x_digits = 5
scale_x = 20
scale_y = 20

_last_update
_cache_img

equations = [
    lambda x: math.sin(x / 10) * 20,
    lambda x: math.cos(x / 15) * 30,
    lambda x: x * 0.5,
    lambda x: -x * 0.3,
    lambda x: math.sin(x / 5) * x / 2
]

def draw_grid(draw, width, height, scale_x, scale_y, graph_scale):
    for i in range(0, width, scale_x):
        color = 0 if i == width // 2 else 128
        draw.line((i, 0, i, height), fill=color)
        if i % (scale_x * graph_scale) == 0:
            num = (i - width // 2) // scale_x
            draw.text((i + 2, height // 2 + 2), str(num), fill=0)
    for j in range(0, height, scale_y):
        color = 0 if j == height // 2 else 128
        draw.line((0, j, width, j), fill=color)
        if j % (scale_y * graph_scale) == 0:
            num = (height // 2 - j) // scale_y
            draw.text((width // 2 + 2, j + 2), str(num), fill=0)

def draw_equation(draw, func, width, height, scale_x, scale_y):
    prev = None
    for px in range(width):
        x = px - width // 2
        try:
            y = func(x)
        except:
            continue
        py = height // 2 - int(y * scale_y / graph_scale)
        if prev is not None:
            draw.line((prev[0], prev[1], px, py), fill=0)
        prev = (px, py)

def render():
    global _last_update, _cache_img
    now = time.time()
    if now - _last_update >= 5 * 60:
        _last_update = now

        img = Image.new("L", (img_width, img_height), 255)
        draw = ImageDraw.Draw(img)

        draw_grid(draw, img_width, img_height, scale_x, scale_y, graph_scale)

        func = random.choice(equations)
        draw_equation(draw, func, img_width, img_height, scale_x, scale_y)

        _cache_img = img
        return _cache_img, True
    return None, False
