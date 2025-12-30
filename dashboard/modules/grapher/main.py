from PIL import Image, ImageDraw
import random, math, time

# Image dimensions
image_width = 400
image_height = 300

# Cache for rendering
_last_render_time = 0
_cached_image = None

# Default properties
default_graph_properties = {
    "scale_x": 20,           # pixels per x-step
    "scale_y": 20,           # pixels per y-step
    "graph_scale": 10,       # spacing for labeled ticks
    "number_of_numbers": 5   # how many labeled numbers in each direction
}

# Equations with individual graph properties
equation_list = [
    {
        "function": lambda x: math.sin(x / 10) * 20,
        "graph_properties": {"scale_x": 20, "scale_y": 20, "graph_scale": 10, "number_of_numbers": 5}
    },
    {
        "function": lambda x: math.cos(x / 15) * 30,
        "graph_properties": {"scale_x": 20, "scale_y": 25, "graph_scale": 10, "number_of_numbers": 6}
    },
    {
        "function": lambda x: x * 0.5,
        "graph_properties": {"scale_x": 20, "scale_y": 10, "graph_scale": 5, "number_of_numbers": 5}
    },
    {
        "function": lambda x: -x * 0.3,
        "graph_properties": {"scale_x": 20, "scale_y": 15, "graph_scale": 5, "number_of_numbers": 5}
    },
    {
        "function": lambda x: math.sin(x / 5) * x / 2,
        "graph_properties": {"scale_x": 15, "scale_y": 5, "graph_scale": 2, "number_of_numbers": 5}
    }
]

def draw_grid(image_draw, image_width, image_height, scale_x, scale_y, graph_scale, number_of_numbers):
    # Draw vertical grid lines and x-axis numbers
    for x_pixel in range(0, image_width + 1, scale_x):
        is_axis_line = (x_pixel == image_width // 2)
        line_color = 0 if is_axis_line else 128
        image_draw.line((x_pixel, 0, x_pixel, image_height), fill=line_color)

        # Draw number labels
        x_value = (x_pixel - image_width // 2) // scale_x
        if abs(x_value) <= number_of_numbers * graph_scale and x_value % graph_scale == 0:
            text_x = min(max(x_pixel + 2, 0), image_width - 20)
            text_y = image_height // 2 + 2
            image_draw.text((text_x, text_y), str(x_value), fill=0)

    # Draw horizontal grid lines and y-axis numbers
    for y_pixel in range(0, image_height + 1, scale_y):
        is_axis_line = (y_pixel == image_height // 2)
        line_color = 0 if is_axis_line else 128
        image_draw.line((0, y_pixel, image_width, y_pixel), fill=line_color)

        # Draw number labels
        y_value = (image_height // 2 - y_pixel) // scale_y
        if abs(y_value) <= number_of_numbers * graph_scale and y_value % graph_scale == 0:
            text_x = image_width // 2 + 2
            text_y = min(max(y_pixel + 2, 0), image_height - 10)
            image_draw.text((text_x, text_y), str(y_value), fill=0)

def draw_equation(image_draw, equation_function, image_width, image_height, scale_x, scale_y, graph_scale):
    previous_pixel = None
    for x_pixel in range(image_width):
        x_value = x_pixel - image_width // 2
        try:
            y_value = equation_function(x_value)
        except Exception:
            continue

        y_pixel = image_height // 2 - int(y_value * scale_y / graph_scale)
        y_pixel = max(0, min(image_height - 1, y_pixel))  # Clamp inside image

        if previous_pixel is not None:
            image_draw.line((previous_pixel[0], previous_pixel[1], x_pixel, y_pixel), fill=0)
        previous_pixel = (x_pixel, y_pixel)

def render():
    global _last_render_time, _cached_image
    current_time = time.time()
    if _cached_image is None or current_time - _last_render_time >= 5 * 60:
        _last_render_time = current_time

        image = Image.new("L", (image_width, image_height), 255)
        draw = ImageDraw.Draw(image)

        # Pick a random equation
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

        _cached_image = image
        return _cached_image, True

    return _cached_image, False

# Example usage
if __name__ == "__main__":
    img, updated = render_graph()
    img.show()
