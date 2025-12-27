import time
from PIL import Image

_last_update = 0
_cache = None
UPDATE_INTERVAL = 5 * 60

def render():
    global _last_update, _cache
    now = time.time()
    if _cache is None or now - _last_update >= UPDATE_INTERVAL:
        # Update weather data here
        _cache = _generate_weather_image()
        _last_update = now
        return _cache, True  # True signals display should update
    return _cache, False     # No update needed

def _generate_weather_image():
    # Create a PIL Image with current weather info
    img = Image.new("RGB", (200, 100), color="blue")
    return img