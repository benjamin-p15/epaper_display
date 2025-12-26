import requests

# JUST FETCH AND PRINT METAR DATA
def fetch_metar(station):
    url = f"https://aviationweather.gov/api/data/metar?ids={station}&format=xml"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.text
    except Exception as e:
        return f"ERROR: {e}"

# TEST WITH KSFO
print(fetch_metar("KSFO"))