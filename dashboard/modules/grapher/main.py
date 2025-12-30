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
    {"function": lambda x: (x**2 - 1)**0.5 if x >= 1 else -(1 - x**2)**0.5, "graph_properties": {"scale_x": 50, "scale_y": 50, "graph_scale": 1, "number_of_numbers": 5}}
]

extra =[
    {"function": lambda x: (3*x - x**3)**(1/3) if x >= 0 else -(3*x - x**3)**(1/3), "graph_properties": {"scale_x": 5, "scale_y": 5, "graph_scale": 1, "number_of_numbers": 5}},
    {"function": lambda x: 4/(x-1) - 2, "graph_properties": {"scale_x": 5, "scale_y": 5, "graph_scale": 1, "number_of_numbers": 5}},
    {"function": lambda x: (x**5 - 1)**0.2, "graph_properties": {"scale_x": 2, "scale_y": 2, "graph_scale": 0.5, "number_of_numbers": 5}},
    {"function": lambda x: 2/(x + 1) if x != -1 else 0, "graph_properties": {"scale_x": 5, "scale_y": 5, "graph_scale": 1, "number_of_numbers": 5}},
    {"function": lambda x: (x**3 - x)/3, "graph_properties": {"scale_x": 5, "scale_y": 5, "graph_scale": 1, "number_of_numbers": 5}},
    {"function": lambda x: math.sin(x) + math.sin(3*x), "graph_properties": {"scale_x": 20, "scale_y": 3, "graph_scale": 2, "number_of_numbers": 5}},
    {"function": lambda x: math.cos(x) + math.cos(2*x), "graph_properties": {"scale_x": 20, "scale_y": 3, "graph_scale": 2, "number_of_numbers": 5}},
    {"function": lambda x: math.exp(-0.1*x)*math.sin(5*x), "graph_properties": {"scale_x": 20, "scale_y": 1, "graph_scale": 0.5, "number_of_numbers": 5}},
    {"function": lambda x: x*math.sin(x) + x*math.cos(x), "graph_properties": {"scale_x": 10, "scale_y": 10, "graph_scale": 2, "number_of_numbers": 5}},
    {"function": lambda x: math.exp(math.sin(x)) - 1, "graph_properties": {"scale_x": 10, "scale_y": 5, "graph_scale": 1, "number_of_numbers": 5}},
    {"function": lambda x: math.sin(x**2) - math.cos(x**3), "graph_properties": {"scale_x": 10, "scale_y": 5, "graph_scale": 1, "number_of_numbers": 5}},
    {"function": lambda x: math.tanh(x) + math.tanh(x), "graph_properties": {"scale_x": 5, "scale_y": 2, "graph_scale": 1, "number_of_numbers": 5}},
    {"function": lambda x: math.exp(x*x) - x**2, "graph_properties": {"scale_x": 5, "scale_y": 20, "graph_scale": 5, "number_of_numbers": 5}},
    {"function": lambda x: math.sin(x)*math.exp(-x**2), "graph_properties": {"scale_x": 5, "scale_y": 2, "graph_scale": 1, "number_of_numbers": 5}},
    {"function": lambda x: math.cos(x**2 + x**2) + math.sin(x*x), "graph_properties": {"scale_x": 5, "scale_y": 3, "graph_scale": 1, "number_of_numbers": 5}},
    {"function": lambda x: x**3, "graph_properties": {"scale_x": 5, "scale_y": 5, "graph_scale": 1, "number_of_numbers": 5}},
    {"function": lambda x: math.exp(x), "graph_properties": {"scale_x": 5, "scale_y": 20, "graph_scale": 5, "number_of_numbers": 5}},
    {"function": lambda x: math.sin(x), "graph_properties": {"scale_x": 20, "scale_y": 3, "graph_scale": 2, "number_of_numbers": 5}},
    {"function": lambda x: 1/x if x != 0 else 0, "graph_properties": {"scale_x": 5, "scale_y": 5, "graph_scale": 1, "number_of_numbers": 5}},
    {"function": lambda x: math.cosh(x), "graph_properties": {"scale_x": 5, "scale_y": 20, "graph_scale": 5, "number_of_numbers": 5}}
]


text_scale_factor = 10
font = ImageFont.load_default()

def draw_grid(draw, width, height, scale_x, scale_y, graph_scale, number_of_numbers):
    # Vertical lines
    for x_pixel in range(0, width + 1, scale_x):
        is_axis = (x_pixel == width // 2)
        draw.line((x_pixel, 0, x_pixel, height), fill=0 if is_axis else 128)
        # Label in graph units
        x_value = ((x_pixel - width // 2) / scale_x) * graph_scale
        if abs(x_value) <= number_of_numbers * graph_scale and x_pixel % scale_x == 0:
            draw.text((x_pixel + 2, height // 2 + 2), str(int(x_value)), fill=0, font=font)

    # Horizontal lines
    for y_pixel in range(0, height + 1, scale_y):
        is_axis = (y_pixel == height // 2)
        draw.line((0, y_pixel, width, y_pixel), fill=0 if is_axis else 128)
        y_value = ((height // 2 - y_pixel) / scale_y) * graph_scale
        if abs(y_value) <= number_of_numbers * graph_scale and y_pixel % scale_y == 0:
            draw.text((width // 2 + 2, y_pixel + 2), str(int(y_value)), fill=0, font=font)


def draw_equation(draw, equation_function, width, height, scale_x, scale_y, graph_scale):
    previous_pixel = None
    for x_pixel in range(width):
        x_value = x_pixel - width // 2
        try: 
            y_value = equation_function(x_value)
            if isinstance(y_value, complex): y_value = y_value.real
        except Exception: continue
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


# Image viewer script to run code without screen
def main():
    global _last_update
    _last_update=0
    img, show = render()
    img.show()

if __name__ == "__main__":
    main()
