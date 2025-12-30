from PIL import Image
import requests, math, time, csv, os, datetime
from zoneinfo import ZoneInfo
from epaper_display import ImageDrawer
screen = ImageDrawer()

script_directory = os.path.dirname(os.path.abspath(__file__))

_last_update = 0
_cache_img = None

def render():
    global _last_update, _cache_img, script_directory, weather_data
    now = time.time()
    now_datetime = datetime.datetime.now()
    today=datetime.datetime.today()
    print(today)
    if now - _last_update >= 5 * 60:
        _last_update = now


        # After image as been made render out image and send off to main.py to have it displayed
        _cache_img=screen.render()
        if(_cache_img is None): return None, False
        else: return _cache_img, True 
    return None, False