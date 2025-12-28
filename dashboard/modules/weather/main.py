from PIL import Image
import requests, math, time, csv, os, datetime
from zoneinfo import ZoneInfo
from epaper_display import ImageDrawer
screen = ImageDrawer()

script_directory = os.path.dirname(os.path.abspath(__file__))

_last_update = 0
_cache_img = None
location_data = {
    'latitude': None,
    'longitude': None,
    'city': None,
    'region': None, # State
    'continent': None,
    'country': None,
    'timezone': None,
    'airport_icao_code': None,
    'airport_iata_code': None,
    'airport_distance': None,
    'airport_type': None,
    'airport_name': None,
    'elevation': None
}

weather_data = {}

def render():
    global _last_update, _cache_img, script_directory, weather_data
    now = time.time()
    if now - _last_update >= 5 * 60:
        _last_update = now

        # Log location data using ip
        if any(location_data[key] is None for key in ['latitude', 'longitude', 'city', 'region']):
            latitude, longitude, city, region, country, timezone = get_current_location()
            location_data.update({'latitude': latitude,'longitude': longitude, 'city': city,'region': region, 'country': country, 'timezone': timezone})
        
        # Log airport data using latitude longitude and stored airports
        if any(location_data[key] is None for key in ['airport_icao_code']):
            airports_csv = os.path.join(script_directory, "data", "airports.csv")
            airport, airport_distance = find_nearest_airport(location_data['latitude'], location_data['longitude'], airports_csv)
            location_data.update({'airport_icao_code': airport["icao_code"], 'continent': airport["continent"], 'airport_iata_code': airport["iata_code"], 'airport_type': airport["type"], 'airport_name': airport["name"], 'elevation': airport["elevation_ft"], 'airport_distance': airport_distance})
        
        # Get meter data and save it to weather data object
        metar_data = fetch_metar(location_data['airport_icao_code'])
        if metar_data: weather_data = metar_data[0]
        else: weather_data = {}

        for key, value in weather_data.items(): print(f"{key}: {value}")

        for i in range(7): screen.add_rectangle(position=(0.006+i*0.142, 0.74), size=(0.135,0.25), fill=0, radius=15, thickness=2)
        screen.add_text([{"text":f"{location_data['city']}, {location_data['region']}","size":40}],position=(0.5, 0.02))
        
        # Using helper functions display tempasure and what it feels like (tempasure, feels like)
        tempasure_f = celsius_to_fahrenheit(weather_data["temp"])
        feel_tempasure_f = wind_chill_f(tempasure_f,weather_data["wspd"])
        screen.add_text([{"text": f"{round(tempasure_f)}", "size": 96, "align": "top"},{"text": "°F", "size": 36, "align": "top"}], position=(0.3, 0.35), bold=True)
        screen.add_text([{"text":f"Feels like {round(feel_tempasure_f)}°","size":18}],position=(0.28, 0.42))
        
        # (sunrise, sunset)
        today = datetime.date.today()
        sunrise, sunset = calculate_sunrise_sunset(
            latitude=location_data['latitude'],
            longitude=location_data['longitude'],
            date=today,
            timezone_offset=get_timezone_offset_hours(location_data["timezone"])
        )
        sunrise_time = sunrise.strftime("%-I:%M")
        sunrise_period = sunrise.strftime("%p")
        sunset_time = sunset.strftime("%-I:%M")
        sunset_period = sunset.strftime("%p")
        screen.add_text([
            {"text": f"{sunrise_time}", "size": 36},
            {"text": f"{sunrise_period}", "size": 18, "align": "bottom"}
        ], position=(0.65, 0.25))
        screen.add_text([
            {"text": f"{sunset_time}", "size": 36},
            {"text": f"{sunset_period}", "size": 18, "align": "bottom"}
        ], position=(0.65, 0.35))


        #(humidity)
        precent = calulate_relative_humidity(weather_data['temp'], weather_data['dewp'])
        screen.add_text([
            {"text": f"{round(precent)}", "size": 36},
            {"text": "%", "size": 18, "align": "bottom"}
        ], position=(0.65, 0.45))

        #(dew point)
        dew_point_F=celsius_to_fahrenheit(weather_data['dewp'])
        screen.add_text([
            {"text": f"{round(dew_point_F)}", "size": 36, "align": "top"},
            {"text": "°F", "size": 18, "align": "top"}
        ], position=(0.85, 0.25))

        #(visibility)
        visibility,marker=parse_us_metar_vis(weather_data["visib"])
        screen.add_text([
            {"text": f"{visibility}", "size": 36},
            {"text": f"{marker}", "size": 28, "align": "center"},
            {"text": "mi", "size": 18, "align": "bottom"}
        ], position=(0.85, 0.35))

        #(pressure) 
        screen.add_text([
            {"text": f"{round(weather_data['altim'] / 33.8639, 1)}", "size": 36},
            {"text": "inHg", "size": 18, "align": "bottom"}
        ], position=(0.85, 0.45))

        #wind data UPDATE
        # Wind speed
        data=[]
        try:
            wind_speed = knots_to_mph(weather_data['wspd'])
            data.append({"text": f"{round(wind_speed)}", "size": 36})
            data.append({"text": "mph", "size": 18, "align": "bottom"})
        except Exception as error:
            data.append({"text": "--", "size": 36})
            data.append({"text": "mph", "size": 18, "align": "bottom"})
        # Wind direction
        try:
            data.append({"text": f" | {round(weather_data['wdir'])}°", "size": 36})
        except Exception as error:
            data.append({"text": " | --", "size": 36})
        # Wind gust
        try:
            wind_gust = knots_to_mph(weather_data['wgst'])
            data.append({"text": f" | {round(wind_gust)}", "size": 36})
            data.append({"text": "mph", "size": 18, "align": "bottom"})
        except Exception as error:
            data.append({"text": f" | --", "size": 36})
            data.append({"text": "mph", "size": 18, "align": "bottom"})
        screen.add_text(data, position=(0.65, 0.55))


        _cache_img=screen.render()

        if(_cache_img is None): return None, False
        else: return _cache_img, True 
    return None, False

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

        # Get location info
        city = location_data.get("city")
        region = location_data.get("region")
        timezone = location_data.get("timezone")
        country = location_data.get("country")

        # Return all location infomation
        return latitude, longitude, city, region, country, timezone

    except Exception as error:
        print("Error getting location:", error)
        return None, None, None, None, None, None
    
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

# Convert from celsius to fahrenheit
def celsius_to_fahrenheit(celsius):
    return celsius * 9 / 5 + 32

# Convert from knots to mph
def knots_to_mph(knots):
    return knots * 1.15078

# Use NOAA formula to calulate wind chill 
def wind_chill_f(tempasure_f, wind_mph):
    if(tempasure_f <= 50 and wind_mph >= 3):
        return (35.74+ 0.6215 * tempasure_f- 35.75 * (wind_mph ** 0.16)+ 0.4275 * tempasure_f * (wind_mph ** 0.16))
    else: return tempasure_f

# NOAA formula used to calulate sunset/sunrise
def calculate_sunrise_sunset(latitude, longitude, date, timezone_offset):
    def deg_to_rad(degrees): return degrees * math.pi / 180
    def rad_to_deg(radians): return radians * 180 / math.pi

    day_of_year = date.timetuple().tm_yday
    longitude_hour = longitude / 15

    def compute_sun_time(is_sunrise):
        approximate_time = day_of_year + ((6 if is_sunrise else 18) - longitude_hour) / 24
        solar_mean_anomaly = (0.9856 * approximate_time) - 3.289
        sun_true_longitude = solar_mean_anomaly + (1.916 * math.sin(deg_to_rad(solar_mean_anomaly))) + (0.020 * math.sin(2 * deg_to_rad(solar_mean_anomaly))) + 282.634
        sun_true_longitude %= 360
        sun_right_ascension = rad_to_deg(math.atan(0.91764 * math.tan(deg_to_rad(sun_true_longitude)))) % 360
        sun_longitude_quadrant = (math.floor(sun_true_longitude / 90)) * 90
        ra_quadrant = (math.floor(sun_right_ascension / 90)) * 90
        sun_right_ascension += (sun_longitude_quadrant - ra_quadrant)
        sun_right_ascension_hours = sun_right_ascension / 15
        sin_declination = 0.39782 * math.sin(deg_to_rad(sun_true_longitude))
        cos_declination = math.cos(math.asin(sin_declination))
        cos_local_hour_angle = (math.cos(deg_to_rad(90.833)) - (sin_declination * math.sin(deg_to_rad(latitude)))) / (cos_declination * math.cos(deg_to_rad(latitude)))
        if cos_local_hour_angle > 1 or cos_local_hour_angle < -1: return None
        local_hour_angle = (360 - rad_to_deg(math.acos(cos_local_hour_angle))) / 15 if is_sunrise else rad_to_deg(math.acos(cos_local_hour_angle)) / 15
        local_mean_time = local_hour_angle + sun_right_ascension_hours - (0.06571 * approximate_time) - 6.622
        utc_time = (local_mean_time - longitude_hour) % 24
        local_time = utc_time + timezone_offset
        hour = int(local_time) % 24
        minute = int((local_time - hour) * 60)
        return datetime.time(hour, minute)

    return compute_sun_time(True), compute_sun_time(False)

# Calulate timezone offset using zoneInfo data
def get_timezone_offset_hours(timezone_name):
    now = datetime.datetime.now(ZoneInfo(timezone_name))
    return now.utcoffset().total_seconds() / 3600

# Magnus-Tetens humidity approximation
def calulate_relative_humidity(temperature, dew_pount):
    saturated_vapor_pressure_T = 6.11 * 10 ** (7.5 * temperature / (237.7 + temperature))
    saturated_vapor_pressure_d = 6.11 * 10 ** (7.5 * dew_pount / (237.7 + dew_pount))
    return (saturated_vapor_pressure_d / saturated_vapor_pressure_T) * 100

# Rephrase from use standard visibility formate to decimal format 
def parse_us_metar_vis(visibility):
    vis = str(visibility).upper().strip()
    marker = ''
    if vis.startswith('M'):
        marker = '-'
        vis = vis[1:]
    elif vis.endswith('+'):
        marker = '+'
        vis = vis.rstrip('+')
    if ' ' in vis:
        whole, frac = vis.split()
        num, denom = frac.split('/')
        value = float(whole) + float(num)/float(denom)
    elif '/' in vis:
        num, denom = vis.split('/')
        value = float(num)/float(denom)
    else: value = float(vis)
    if value.is_integer(): value_str = str(int(value))
    else: value_str = str(round(value, 1))  
    return value_str, marker