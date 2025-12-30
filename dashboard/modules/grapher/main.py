from PIL import Image, ImageDraw, ImageFont
import random, math, time

# Image size
img_width = 400
img_height = 300

# Default graph properties
default_properties = {
    "scale_x": 20,
    "scale_y": 20,
    "graph_scale": 10
}

_last_update = 0
_cache_img = None

# Define equations with optional properties
equations = [
    {"func": lambda x: math.sin(x / 10) * 20, "props": {"scale_y": 20, "graph_scale": 10}},
    {"func": lambda x: math.cos(x / 15) * 30, "props": {"scale_y": 25, "graph_scale": 10}},
    {"func": lambda x: x * 0.5, "props": {"scale_y": 10, "graph_scale": 5}},
    {"func": lambda x: -x * 0.3, "props": {"scale_y": 15, "graph_scale": 5}},
    {"func": lambda x: math.sin(x / 5) * x / 2, "props": {"scale_y": 5, "graph_scale": 2}}
]

def draw_grid(draw, width, height, scale_x, scale_y, graph_scale):
    # Draw vertical lines
    for i in range(0, width, scale_x):
        color = 0 if i == width // 2 else 128
        draw.line((i, 0, i, height), fill=color)
        if (i - width // 2) % (scale_x * graph_scale) == 0:
            num = (i - width // 2) // scale_x
            draw.text((i + 2, height // 2 + 2), str(num), fill=0)
    # Draw horizontal lines
    for j in range(0, height, scale_y):
        color = 0 if j == height // 2 else 128
        draw.line((0, j, width, j), fill=color)
        if (height // 2 - j) % (scale_y * graph_scale) == 0:
            num = (height // 2 - j) // scale_y
            draw.text((width // 2 + 2, j + 2), str(num), fill=0)

def draw_equation(draw, func, width, height, scale_x, scale_y, graph_scale):
    prev = None
    for px in range(width):
        x = px - width // 2
        try:
            y = func(x)
        except:
            continue
        # Clip y to image height to avoid "U" shapes
        py = max(0, min(height - 1, height // 2 - int(y * scale_y / graph_scale)))
        if prev is not None:
            draw.line((prev[0], prev[1], px, py), fill=0)
        prev = (px, py)

def render():
    global _last_update, _cache_img
    now = time.time()
    if now - _last_update >= 5 * 60 or _cache_img is None:
        _last_update = now

        img = Image.new("L", (img_width, img_height), 255)
        draw = ImageDraw.Draw(img)

        # Pick random equation
        eq = random.choice(equations)
        props = default_properties.copy()
        props.update(eq.get("props", {}))

        draw_grid(draw, img_width, img_height, props["scale_x"], props["scale_y"], props["graph_scale"])
        draw_equation(draw, eq["func"], img_width, img_height, props["scale_x"], props["scale_y"], props["graph_scale"])

        _cache_img = img
        return _cache_img, True
    return _cache_img, False

# Example usage:
if __name__ == "__main__":
    img, updated = render()
    img.show()
