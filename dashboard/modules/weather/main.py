from PIL import Image
import time

_last_update = 0
_cache_img = None

def render():
    global _last_update, _cache_img
    now = time.time()
    if _cache_img is None or now - _last_update >= 5 * 60:
        _cache_img = Image.new("1", (800, 480), color=0)
        _last_update = now
        return _cache_img, True  
    return _cache_img, False 
