from PIL import Image, ImageDraw, ImageFont
import random, math, time

image_width = 800
image_height = 480

_last_update = 0
_cache_img = None

default_graph_properties = {
    "scale_x": 20,
    "scale_y": 20,
    "graph_scale": 10,
    "number_of_numbers": 5
}

equation_list = [
    {"function": lambda x: math.sin(x / 10) * 20, "graph_properties": {"scale_x": 20, "scale_y": 20, "graph_scale": 10, "number_of_numbers": 5}},
    {"function": lambda x: math.cos(x / 15) * 30, "graph_properties": {"scale_x": 20, "scale_y": 25, "graph_scale": 10, "number_of_numbers": 6}},
    {"function": lambda x: x * 0.5, "graph_properties": {"scale_x": 20, "scale_y": 10, "graph_scale": 5, "number_of_numbers": 5}},
    {"function": lambda x: -x * 0.3, "graph_properties": {"scale_x": 20, "scale_y": 15, "graph_scale": 5, "number_of_numbers": 5}},
    {"function": lambda x: math.sin(x / 5) * x / 2, "graph_properties": {"scale_x": 15, "scale_y": 5, "graph_scale": 2, "number_of_numbers": 5}}
]

text_scale_factor = 10
font = ImageFont.load_default()

def draw_grid(draw, width, height, scale_x, scale_y, graph_scale, number_of_numbers):
    for x_pixel in range(0, width + 1, scale_x):
        is_axis_line = (x_pixel == width // 2)
        line_color = 0 if is_axis_line else 128
        draw.line((x_pixel, 0, x_pixel, height), fill=line_color)
        x_value = (x_pixel - width // 2) // scale_x
        if abs(x_value) <= number_of_numbers * graph_scale and x_value % graph_scale == 0:
            text_x = min(max(x_pixel + 2, 0), width - text_scale_factor * 2)
            text_y = height // 2 + 2
            draw.text((text_x, text_y), str(x_value), fill=0, font=font)

    for y_pixel in range(0, height + 1, scale_y):
        is_axis_line = (y_pixel == height // 2)
        line_color = 0 if is_axis_line else 128
        draw.line((0, y_pixel, width, y_pixel), fill=line_color)
        y_value = (height // 2 - y_pixel) // scale_y
        if abs(y_value) <= number_of_numbers * graph_scale and y_value % graph_scale == 0:
            text_x = width // 2 + 2
            text_y = min(max(y_pixel + 2, 0), height - text_scale_factor)
            draw.text((text_x, text_y), str(y_value), fill=0, font=font)

def draw_equation(draw, equation_function, width, height, scale_x, scale_y, graph_scale):
    previous_pixel = None
    for x_pixel in range(width):
        x_value = x_pixel - width // 2
        try:
            y_value = equation_function(x_value)
        except:
            continue
        y_pixel = height // 2 - int(y_value * scale_y / graph_scale)
        y_pixel = max(0, min(height - 1, y_pixel))
        if previous_pixel is not None:
            draw.line((previous_pixel[0], previous_pixel[1], x_pixel, y_pixel), fill=0)
        previous_pixel = (x_pixel, y_pixel)

def render():
    global _last_update, _cache_img
    now = time.time()
    if _cache_img is None or now - _last_update >= 5 * 60:
        _last_update = now
        img = Image.new("L", (image_width, image_height), 255)
        draw = ImageDraw.Draw(img)
        selected_equation = random.choice(equation_list)
        graph_properties = default_graph_properties.copy()
        graph_properties.update(selected_equation.get("graph_properties", {}))
        draw_grid(draw, image_width, image_height,
                  graph_properties["scale_x"],
                  graph_properties["scale_y"],
                  graph_properties["graph_scale"],
                  graph_properties["number_of_numbers"])
        draw_equation(draw, selected_equation["function"],
                      image_width, image_height,
                      graph_properties["scale_x"],
                      graph_properties["scale_y"],
                      graph_properties["graph_scale"])
        _cache_img = img
        return _cache_img, True
    return _cache_img, False
