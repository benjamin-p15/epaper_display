import requests, math, time, csv, os, datetime, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
from zoneinfo import ZoneInfo
from dashboard.epaper_display import ImageDrawer
screen = ImageDrawer()

_last_update = 0
_cache_img = None

screen = ImageDrawer()


def render():
    global _last_update, _cache_img
    now = time.time()
    if _cache_img is None or now - _last_update >= 5 * 60:
        _last_update = now




        _cache_img=screen.render()
        if(_cache_img is None): return None, False
        else: return _cache_img, True 
    return _cache_img, False


# Image viewer script to run code without screen
def main():
    global _last_update
    _last_update=0
    img, show = render()
    img.show()

if __name__ == "__main__":
    main()
