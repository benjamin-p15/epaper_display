from PIL import Image
import requests

import time

_last_update = 0
_cache_img = None

def render():
    global _last_update, _cache_img
    now = time.time()
    if _cache_img is None or now - _last_update >= 5 * 60:
        _cache_img = Image.new("1", (800, 480), color=1)
        _last_update = now
        return _cache_img, True  
    
    metar_data = fetch_metar(["KSFO"])
    print(metar_data)


    return _cache_img, False 

def fetch_metar(icao_codes):
    # Join the list into a comma-separated string
    station_str = ",".join(icao_codes)

    # Build the API URL 
    url = f"https://aviationweather.gov/api/data/metar?ids={station_str}&format=json"

    # Make the request
    resp = requests.get(url)

    # Check for HTTP errors
    resp.raise_for_status()

    # Parse JSON
    data = resp.json()

    # Return raw JSON
    return data