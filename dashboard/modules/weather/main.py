from PIL import Image
import requests
import math
import time
import csv
import os

script_directory = os.path.dirname(os.path.abspath(__file__))

_last_update = 0
_cache_img = None
location_data = {
    'latitude': None,
    'longitude': None,
    'city': None,
    'region': None,
    'airport': None,
    'airport_distance': None
}

def render():
    global _last_update, _cache_img, script_directory
    now = time.time()
    if _cache_img is None or now - _last_update >= 5 * 60:
        _cache_img = Image.new("1", (800, 480), color=1)
        _last_update = now

        import os
        print(f"Current directory: {os.getcwd()}")
        print(f"File exists: {os.path.exists('data/airports.csv')}")

        if any(location_data[key] is None for key in ['latitude', 'longitude', 'city', 'region']):
            latitude, longitude, city, region = get_current_location()
            location_data.update({'latitude': latitude,'longitude': longitude, 'city': city,'region': region})
        
        if any(location_data[key] is None for key in ['airport', 'airport_distance']):
            airports_csv = os.path.join(script_directory, "data", "airports.csv")
            airport, airport_distance = find_nearest_airport(location_data['latitude'], location_data['longitude'], airports_csv)
            location_data.update({'airport': airport,'airport_distance': airport_distance})
        
        print(f"latitude: {location_data['latitude']}")
        print(f"longitude: {location_data['longitude']}")
        print(f"city: {location_data['city']}")
        print(f"region: {location_data['region']}")
        print(f"airport: {location_data['airport']}")
        print(f"airport_distance: {location_data['airport_distance']}")

    
        metar_data = fetch_metar(location_data['airport']['icao_code'])
        print(metar_data)


    return _cache_img, False 

# Get metter from a specific airport
def fetch_metar(icao_code):
    # Build aviationweather.gov with desierd station
    url = f"https://aviationweather.gov/api/data/metar?ids={icao_code}&format=json"

    # Make request to website for data
    resp = requests.get(url)
    resp.raise_for_status()

    # Parse and return JSON data
    data = resp.json()
    return data

# Get current location info using ip address
def get_current_location():
    try:
        # Attempt to get the location data from the current ip using ipinfo.io
        response = requests.get("https://ipinfo.io/json")
        response.raise_for_status()
        location_data = response.json()

        # Get latitude and longitude data
        location_str = location_data.get("loc")  # format: "lat,lon"
        if location_str:
            latitude, longitude = map(float, location_str.split(","))
        else:
            latitude, longitude = None, None

        # Get city and state info
        city = location_data.get("city")
        region = location_data.get("region")

        # Return all location infomation
        return latitude, longitude, city, region

    except Exception as error:
        print("Error getting location:", error)
        return None, None, None, None
    
# Calulates distances using sphereical coordinates .i.e. haversine distance of earth
def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371.0  
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# Finds closest airport to a location
def find_nearest_airport(latitude, longitude, airports_csv):
    # Airport types and used variables
    valid_types = {"small_airport", "medium_airport", "large_airport"}
    nearest_airport = None
    min_distance = float("inf")
    # Open cvs file to find airport data
    with open(airports_csv, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row["type"] not in valid_types: continue # Skip airport types not in list 

            # Search through list if a closer airport exist use it instead
            airport_lat = float(row["latitude_deg"])
            airport_lon = float(row["longitude_deg"])
            distance = haversine_distance(latitude, longitude, airport_lat, airport_lon)
            if distance < min_distance:
                min_distance = distance
                nearest_airport = row
    # return found airport data       
    return nearest_airport, min_distance