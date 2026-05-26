import requests, math, time, csv, os, datetime, sys, json
from PIL import Image
from typing import Tuple
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
dashboard = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
script_directory = os.path.dirname(os.path.abspath(__file__))
from zoneinfo import ZoneInfo
from dashboard.epaper_display import ImageDrawer

# Class which handles the drawing of the weather screen modual and getting current weather data
class weatherRender:
    def __init__(self, width: int, height: int):
        self.location_data = {
            'latitude': None,
            'longitude': None,
            'city': None,
            'region': None,
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
        self.weather_data={}
        self.forecast_data={}
        self.pilot_mode=False
        self.metric=False
        self.screen=ImageDrawer(width,height)
        self.scale_factor=width/height
        self._last_update=0

        self.LOCATION_FILE=os.path.join(dashboard, "data/location.json")

        self.moon_phases=["new.png", "wax_c.png", "first_q.png", "wax_g.png", "full.png", "wan_g.png", "last_q.png", "wan_c.png"]
        if(self.metric==False): self.unit="F"
        else: self.unit="C"

    # Renders the screen
    def render(self, refreash_rate: float = 300, force=False) -> Tuple[Image.Image, bool]:
        self.now = time.time()
        if force or (self.now - self._last_update >= refreash_rate):
            self._last_update = self.now
            self.updateData("airports.csv")
            self.renderWeatherPrediction()
            self.renderTitle()
            self.renderCurrentWeather()
            self.renderColumeDate()

            _cache_img=self.screen.render()
            if(_cache_img is None): return None, False
            else: return _cache_img, True 
        return None, False

    # Render the weather forcast to the screen
    def renderWeatherPrediction(self):
        # Draw rectangles forecast text
        hours = []
        for i in range(7):
            # Generate hourly text
            if i < 6:
                hour = (self.now_datetime + datetime.timedelta(hours=i+1)).hour 
                hour_str = f"{hour%12 or 12}{'am' if hour<12 else 'pm'}"
            # Generate next day text
            else:
                next_day = self.now_datetime + datetime.timedelta(days=1)
                hour_str = next_day.strftime('%a').lower() 
            hours.append(hour_str)
        for i in range(7):
            self.screen.add_rectangle(position=(0.006+i*0.142, 0.74), size=(0.135,0.25), fill=0, radius=15, thickness=2)
            self.screen.add_text([{"text": hours[i], "size": 16}], position=(0.006+i*0.142 + 0.0675, 0.745),bold=True)

        
        # Pull icons for current weather
        icons_data = self.forecast_data.get("hourly", [])[:6] + ([self.forecast_data["tomorrow"]] if self.forecast_data.get("tomorrow") else [])

        for i, data in enumerate(icons_data):
            invert, icon = self.weatherToIcon(data.get("weather"))
            x_pos = -0.031 + i*0.142 + 0.047
            self.screen.add_image(os.path.join(script_directory, "icons", icon),(x_pos+0.02, 0.78),(0.075, 0.075*self.scale_factor),invert=invert,color_black=True)
            
            # Draw estimated tempasure
            temp=self.toNumber(data.get('temperature','--'))
            if(self.metric==True): 
                temp=self.fahrenheitToCelsius(temp)
                if isinstance(temp, (int, float)): temp=round(temp,1)
            self.screen.add_text([{"text": f"{temp}°{self.unit}", "size": 18}], position=(x_pos+0.06, 0.915), bold=True)

            # Draw estimated precipitation 
            precip = data.get("precipitation_prob")
            precip_text = f"{precip}%" if precip is not None else "--"
            self.screen.add_image(os.path.join(script_directory, "icons", 'chance.png'),(x_pos+0.029, 0.955),(0.02, 0.02*self.scale_factor))
            self.screen.add_text([{"text": precip_text, "size": 18}], position=(x_pos+0.053, 0.95),bold=True,align="left")

    # Renders title with location and date
    def renderTitle(self):
        # Add city and date and state to screen
        self.screen.add_text([{"text":f"{self.location_data['city']}, {self.location_data['region']}","size":40}],position=(0.5, 0.01),bold=True)
        todays_date = datetime.date.today().strftime("%m/%d/%Y")
        self.screen.add_text([{"text": todays_date, "size": 18}], position=(0.5, 0.1), bold=True)
   
    # Render current weathyer
    def renderCurrentWeather(self):
        global script_directory
        # Get current weather and draw it onto the screen
        current = self.forecast_data.get("current", {})
        invert, icon_file = self.weatherToIcon(current.get("weather_text"))
        self.screen.add_image(os.path.join(script_directory, "icons", icon_file),(0, 0.11),(0.27, 0.27*self.scale_factor),invert=invert,color_black=True)

        # Using helper functions display tempasure and what it feels like (tempasure, feels like)
        tempasure_c = self.weather_data["temp"]
        tempasure = self.celsiusToFahrenheit(tempasure_c)
        feel_tempasure = self.windChillF(tempasure,self.weather_data["wspd"])

        if(self.metric==True):
            tempasure=tempasure_c
            feel_tempasure=self.fahrenheitToCelsius(feel_tempasure)
            if isinstance(tempasure, (int, float)): tempasure=round(tempasure,1)
            if isinstance(feel_tempasure, (int, float)): feel_tempasure=round(feel_tempasure,1)
        
        self.screen.add_text([{"text": f"{round(tempasure)}", "size": 96, "align": "top"},{"text": f"°{self.unit}", "size": 36, "align": "top"}], position=(0.4, 0.33), bold=True)
        self.screen.add_text([{"text":f"Feels like {round(feel_tempasure)}°","size":18}],position=(0.38, 0.42))

        # Add currect weather and precipitation to screen
        precip=current.get("precipitation_last_hour")
        if(precip is None): precip=0
        self.screen.add_image(os.path.join(script_directory, "icons", "chance.png"),(0, 0.65),(0.03, 0.03*self.scale_factor),invert=False,color_black=True)
        self.screen.add_text([{"text":f"{self.weatherToText(current.get('weather_text'))}","size":48,"align": "center"}],position=(0, 0.55),align="left",bold=True)
        self.screen.add_text([{"text":f"Rain {round(precip/25.4, 1)}","size":24,"align": "center"},{"text":"in","size":12,"align":"bottom"}],position=(0.03, 0.65),align="left",bold=True)
    
    # Renders columes of usful data
    def renderColumeDate(self):
        data_column_y=0.11
        # (Sunrise, sunset)
        # Using longitude and latitude estimate sunrise and sunset time
        today = datetime.date.today()
        sunrise, sunset = self.calculateSunriseSunset(
            latitude=self.location_data['latitude'],
            longitude=self.location_data['longitude'],
            date=today,
            timezone_offset=self.getTimezoneOffsetHours(self.location_data["timezone"])
        )
        # Convert data into correct format 
        sunrise_time = sunrise.strftime("%-I:%M")
        sunrise_period = sunrise.strftime("%p")
        sunset_time = sunset.strftime("%-I:%M")
        sunset_period = sunset.strftime("%p")
        # Add sunrise and sunset images and text to screen
        self.screen.add_image(os.path.join(script_directory, "icons", "sunrise.png"),(0.6, data_column_y*1),(0.05,0.08),invert=True, color_black=True)
        self.screen.add_text([
            {"text": f"{sunrise_time}", "size": 36},
            {"text": f"{sunrise_period}", "size": 18, "align": "bottom"}
        ], position=(0.65, data_column_y*1),align="left")
        self.screen.add_image(os.path.join(script_directory, "icons", "sunset.png"),(0.8, data_column_y*1),(0.05,0.08),invert=True,color_black=True)
        self.screen.add_text([
            {"text": f"{sunset_time}", "size": 36},
            {"text": f"{sunset_period}", "size": 18, "align": "bottom"}
        ], position=(0.85, data_column_y*1),align="left")

        # (Pressure) 
        # Convert pressure to inHg and add image and text to screen
        self.screen.add_image(os.path.join(script_directory, "icons", "pressure.png"),(0.8, data_column_y*2),(0.04,0.07),invert=True, color_black=False)
        self.screen.add_text([
            {"text": f"{round(self.weather_data['altim'] / 33.8639, 1)}", "size": 36},
            {"text": "inHg", "size": 18, "align": "bottom"}
        ], position=(0.84, data_column_y*2-0.01),align="left")

        # (Visibility)
        # Reformat US meter visibility data into screen friendly formate then add text, marker, and icon to screen
        visibility,marker=self.parseUsMetarVis(self.weather_data["visib"])
        self.screen.add_image(os.path.join(script_directory, "icons", "visibility.png"),(0.6, data_column_y*3),(0.05,0.08),invert=True, color_black=True)
        self.screen.add_text([
            {"text": f"{visibility}", "size": 36},
            {"text": f"{marker}", "size": 28, "align": "center"},
            {"text": "mi", "size": 18, "align": "bottom"}
        ], position=(0.65, data_column_y*3-0.01),align="left")

        #(Humidity, dew point)
        # Usig dew point calulate relative humidity
        precent = self.calulateRelativeHumidity(self.weather_data['temp'], self.weather_data['dewp'])
        dew_point_F=self.celsiusToFahrenheit(self.weather_data['dewp'])
        # Add humidity text and icon to screen and dew point under it
        self.screen.add_image(os.path.join(script_directory, "icons", "humidity.png"),(0.6, data_column_y*2),(0.04,0.07),invert=True, color_black=True)
        self.screen.add_text([
            {"text": f"{round(precent)}", "size": 36},
            {"text": "%", "size": 18, "align": "bottom"}
        ], position=(0.64, data_column_y*2-0.01),align="left")
        self.screen.add_text([
            {"text": f"Dew {round(dew_point_F)}", "size": 18, "align": "top"},
            {"text": "°F", "size": 9, "align": "top"}
        ], position=(0.64, data_column_y*2+0.08),align="left")

        # (Cloud coverage)
        # Estimate cloud coverage by taking an weighted average of the clouds then display on screen with icon
        data=[]
        self.screen.add_image(os.path.join(script_directory, "icons", "cloudy.png"),(0.8, data_column_y*3),(0.05,0.08),invert=True, color_black=True)
        try:
            coverage = self.calculateWeightedCloudCoverage(self.weather_data['clouds'])
            data.append({"text": f"{coverage}", "size": 36})
            data.append({"text": "%", "size": 18, "align": "bottom"})
        except Exception as error:
            data.append({"text": "--", "size": 36})
            data.append({"text": "%", "size": 18, "align": "bottom"})
        self.screen.add_text(data, position=(0.86, data_column_y*3),align="left")

        #(Air quaility)
        latitude, longitude = map(float, self.location_data.get("loc").split(","))
        air,aqi_state,pollutant=self.fetchAirQuality(latitude, longitude,"e68ce140b337a07f309590d691db0e80")
        self.screen.add_image(os.path.join(script_directory, "icons", "aqi.png"),(0.6, data_column_y*4),(0.05,0.08),invert=False, color_black=True)
        self.screen.add_text([{"text": f"{air}/500", "size": 26}], position=(0.65, data_column_y*4+0.01),align="left")
        self.screen.add_text([{"text": f"{aqi_state} | {pollutant}", "size": 12,"algin":"below"}], position=(0.65, data_column_y*4+0.06),align="left")

        #(UV index)
        uv=self.fetchUvIndex(latitude, longitude)
        self.screen.add_image(os.path.join(script_directory, "icons", "uvi.png"),(0.8, data_column_y*4),(0.05,0.08),invert=False, color_black=True)
        self.screen.add_text([{"text": f"{uv}", "size": 36}], position=(0.85, data_column_y*4-0.01),align="left")


        # (Wind speed, wind direction, gust speed)
        # Convert speeds to mph then add icon and text to screen
        data=[]
        self.screen.add_image(os.path.join(script_directory, "icons", "wind.png"),(0.6, data_column_y*5),(0.04,0.07),invert=True,color_black=True)
        try:
            wind_speed = self.knotsToMph(self.weather_data['wspd'])
            data.append({"text": f"{round(wind_speed)}", "size": 36, "align": "bottom"})
            data.append({"text": "mph", "size": 18, "align": "bottom"})
        except Exception as error:
            data.append({"text": "--", "size": 36, "align": "bottom"})
            data.append({"text": "mph", "size": 18, "align": "bottom"})
        # Wind direction
        try:
            data.append({"text": f" | {round(self.weather_data['wdir'])}°", "size": 36, "align": "bottom"})
        except Exception as error:
            data.append({"text": "|--", "size": 36, "align": "bottom"})
        # Wind gust
        try:
            wind_gust = self.knotsToMph(self.weather_data['wgst'])
            data.append({"text": f"|{round(wind_gust)}", "size": 36, "align": "bottom"})
            data.append({"text": "mph", "size": 18, "align": "bottom"})
        except Exception as error:
            data.append({"text": f"|--", "size": 36, "align": "bottom"})
            data.append({"text": "mph", "size": 18, "align": "bottom"})
        self.screen.add_text(data, position=(0.65, data_column_y*5-0.02),align="left")

        #(Moon phase)
        index, moon=self.getMoonPhase()
        moon_image=self.moon_phases[index]
        self.screen.add_image(os.path.join(script_directory, "icons", moon_image),(0.6, data_column_y*6-0.02),(0.05,0.08),invert=True, color_black=True)
        self.screen.add_text([{"text": f"{moon}", "size": 24,"align": "center"}], position=(0.67, data_column_y*6-0.01),align="left",bold=True)

    # Pulls most current weather data
    def updateData(self, airport_database: str):
        self.now_datetime = datetime.datetime.now()
        self.today=datetime.datetime.today()

        # Log location data using ip
        if any(self.location_data[key] is None for key in ['latitude', 'longitude', 'city', 'region']):
            latitude, longitude, city, region, country, timezone = self.getCurrentLocation()
            self.location_data.update({'latitude': latitude,'longitude': longitude, 'city': city,'region': region, 'country': country, 'timezone': timezone})

        # Log airport data using latitude longitude and stored airports
        if any(self.location_data.get(key) is None for key in ['airport_icao_code']):
            airports_csv = os.path.join(script_directory, "static_data", airport_database)

            airport, airport_distance = self.findNearestAirport(self.location_data['latitude'], self.location_data['longitude'], airports_csv)
            self.location_data.update({'airport_icao_code': airport["icao_code"], 'continent': airport["continent"], 'airport_iata_code': airport["iata_code"], 'airport_type': airport["type"], 'airport_name': airport["name"], 'elevation': airport["elevation_ft"], 'airport_distance': airport_distance})

        # Get meter data and save it to weather data object, keep old data if new data is not provided
        metar_data = self.fetchMetar(self.location_data['airport_icao_code'])
        if metar_data: self.weather_data = metar_data[0]
        else: self.weather_data = {}

        # Get forcast data and save it to weather forcast object
        latitude, longitude = map(float, self.location_data.get("loc").split(","))
        self.forecast_data = self.fetchForecast(latitude, longitude) or {}
        self.forecast_data.setdefault("current", {})
        self.forecast_data.setdefault("hourly", [])
        self.forecast_data.setdefault("tomorrow", {})

    # Get current location info using ip address
    def getCurrentLocation(self) -> Tuple[float, float, str, str, str, str]:
        try:
            with open(self.LOCATION_FILE, "r") as f: self.location_data = json.load(f)
            city = self.location_data.get("city")
            region = self.location_data.get("region")
            timezone = self.location_data.get("timezone")
            country = self.location_data.get("country")
            latitude, longitude = map(float, self.location_data.get("loc").split(","))
            return latitude, longitude, city, region, country, timezone

        except Exception as error: return 0, 0, "Unknown", "Unknown", "Unknown", "UTC"
        
    # Finds closest airport to a location from csv file
    def findNearestAirport(self, latitude: float, longitude: float, airports_csv: str) -> Tuple[str, float]:
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
                distance = self.haversine_distance(latitude, longitude, airport_lat, airport_lon)
                if distance < min_distance:
                    min_distance = distance
                    nearest_airport = row
        # Return found airport data       
        return nearest_airport, min_distance
    
    # Calulates distances using sphereical coordinates .i.e. haversine distance of earth
    def haversine_distance(self, latitude1: float, longitude1: float, latitude2: float, longitude2: float, radius: float = 6371.0) -> float:  
        phi1, phi2 = math.radians(latitude1), math.radians(latitude2)
        delta_phi = math.radians(latitude2 - latitude1)
        delta_lambda = math.radians(longitude2 - longitude1)
        
        a = math.sin(delta_phi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return radius * c

    # Get meter from a specific airport
    def fetchMetar(self, icao_code: str):
        # Build aviationweather.gov meter api link with desierd station
        url = f"https://aviationweather.gov/api/data/metar?ids={icao_code}&format=json"

        # Make request to website for data
        resp = requests.get(url)
        resp.raise_for_status()

        # Parse and return JSON data
        data = resp.json()
        return data

    # Fetch forcast from NWS
    def fetchForecast(self, latitude: float, longitude: float):
        # Appear as user agent to prevent botting issues
        headers = {"User-Agent": "example@example.com"}

        # Setup url for the NWS api, pull current json point data, then pull out the day/hour/current point data
        point_url = f"https://api.weather.gov/points/{latitude},{longitude}"
        point_data = requests.get(point_url, headers=headers).json()
        hourly_url = point_data["properties"]["forecastHourly"]
        daily_url  = point_data["properties"]["forecast"]
        stations_url = point_data["properties"]["observationStations"]

        # Using pulled point data of area and closest station pull current forcast data
        stations_data = requests.get(stations_url, headers=headers).json()
        station_id = stations_data["features"][0]["properties"]["stationIdentifier"]
        obs_url = f"https://api.weather.gov/stations/{station_id}/observations/latest"
        obs_data = requests.get(obs_url, headers=headers).json()
        obs_props = obs_data["properties"]

        # Take current conditions and format them
        current = {
            "temperature": obs_props.get("temperature", {}).get("value"),
            "temperature_unit": obs_props.get("temperature", {}).get("unitCode"),
            "wind_speed": obs_props.get("windSpeed", {}).get("value"),
            "wind_direction": obs_props.get("windDirection", {}).get("value"),
            "humidity": obs_props.get("relativeHumidity", {}).get("value"),
            "precipitation_last_hour": obs_props.get("precipitationLastHour", {}).get("value"),
            "cloud_layers": [
                {
                    "amount": layer["amount"],
                    "base": layer.get("base", {}).get("value"),
                    "type": layer.get("type")
                } for layer in obs_props.get("cloudLayers", [])
            ],
            "weather_text": obs_props.get("textDescription")
        }

        # Request current hourly conditions and format them
        hourly_data = requests.get(hourly_url, headers=headers).json()
        hourly = [{
            "time": p["startTime"],
            "temperature": p["temperature"],
            "unit": p.get("temperatureUnit"),
            "precipitation_prob": p.get("probabilityOfPrecipitation", {}).get("value"),
            "weather": p.get("shortForecast")
        } for p in hourly_data["properties"]["periods"][:6]]

        # Request current daily conditions and format them
        daily_data = requests.get(daily_url, headers=headers).json()
        today = datetime.date.today()
        tomorrow = None
        for p in daily_data["properties"]["periods"]:
            p_date = datetime.date.fromisoformat(p["startTime"][:10])
            if p_date > today:
                tomorrow = {
                    "name": p["name"],
                    "temperature": p["temperature"],
                    "unit": p.get("temperatureUnit"),
                    "precipitation_prob": p.get("probabilityOfPrecipitation", {}).get("value"),
                    "weather": p.get("shortForecast")
                }
                break
        # Return current weather, hourly forcast for next 6 hours, and tomarrows forcast
        return {"current": current,"hourly": hourly,"tomorrow": tomorrow}

    # Using the data return form the NWS calulate which icon to use for display depending on weather type
    def weatherToIcon(self, text: str) -> Tuple[bool,str]:
        t = (text or "").lower()
        match t:
            case _ if "thunder" in t or "thunderstorms" in t: return True, "thunderstorms.png"
            case _ if "snow" in t: return True, "snowy.png"
            case _ if "rain" in t or "showers" in t: return True, "rain_shower.png"
            case _ if "drizzle" in t: return True, "drizzle.png"
            case _ if "fog" in t or "mist" in t: return False, "fog.png"
            case _ if "mostly cloudy" in t: return False, "mostly_cloudy.png"
            case _ if "partly cloudy" in t: return False, "partly_cloudy.png"
            case _ if "cloudy" in t: return True, "cloudy.png"
            case _ if "patchy" in t: return False, "partly_cloudy.png"
            case _ if "sunny" in t or "clear" in t: return True, "sunny.png"
            case _: return False, "sunny.png"
    
    # Converts strings to numbers
    def toNumber(self, string: str) -> float | str | None: 
        try: return float(string)
        except(ValueError): return string
        except(TypeError): return None

    # Convert from celsius to fahrenheit
    def celsiusToFahrenheit(self, celsius: float) -> float:
        return celsius * 9 / 5 + 32

    # Convert from fahrenheit to celsius
    def fahrenheitToCelsius(self, fahrenheit: float) -> float:
        return (fahrenheit-32)*5/9

    # Fetch current locations uv index from openweathermap
    def fetchUvIndex(self, latitude: float, longitude: float) -> str:
        # Setup url and api call parms
        url = "https://api.open-meteo.com/v1/forecast"
        params = {"latitude": latitude, "longitude": longitude, "hourly": "uv_index"}

        try:
            # Request data
            r = requests.get(url, params=params, timeout=10)
            r.raise_for_status()
            data = r.json()

            # Get hourly times and uv index list
            times = data.get("hourly", {}).get("time", [])
            uv_list = data.get("hourly", {}).get("uv_index", [])
            if not uv_list or not times: return "--"

            # Find current hour in UTC
            now_utc = datetime.datetime.now(datetime.timezone.utc).replace(minute=0, second=0, microsecond=0)
            now_iso = now_utc.strftime("%Y-%m-%dT%H:00")
            if now_iso in times: idx = times.index(now_iso)
            # If that fails return closest hour
            else: idx = min(range(len(times)), key=lambda i: abs(datetime.fromisoformat(times[i]) - now_utc))

            # Get current hours uv index and return it
            uvi = uv_list[idx]
            return f"{round(uvi)}/11"
        except Exception as error:
            print(error)
            return "--"
    
    # Fetch current locations aqi from openweathermap
    def fetchAirQuality(self, latitude: float, longitude: float, api_key: float) -> Tuple[float, str, str] | Tuple[str, None, None]:
        # Setup url and api call parms
        url = "https://api.openweathermap.org/data/2.5/air_pollution"
        params = {"lat": latitude,"lon": longitude,"appid": api_key}
        try:
            # Request data
            r = requests.get(url, params=params, timeout=10)
            r.raise_for_status()
            data = r.json()["list"][0]
            aqi_state = data.get("main", {}).get("aqi")
            aqi_state = ["Unknown","Good","Fair","Moderate","Poor","Very Poor"][aqi_state]
            aqi, pollutant = self.calculateAqi(data.get("components"))
            # Return air quility which is on a 0-500 scale
            return f"{round(aqi)}", aqi_state, pollutant
        # If it fails return no data
        except Exception:
            return "--", "", ""
        
    def calculateAqi(self, components) -> float:
        breakpoints = {
            "pm2_5": [(0.0,12.0,0,50),(12.1,35.4,51,100),(35.5,55.4,101,150),(55.5,150.4,151,200),(150.5,250.4,201,300),(250.5,350.4,301,400),(350.5,500.4,401,500)],
            "pm10": [(0,54,0,50),(55,154,51,100),(155,254,101,150),(255,354,151,200),(355,424,201,300),(425,504,301,400),(505,604,401,500)],
            "co": [(0.0,4.4,0,50),(4.5,9.4,51,100),(9.5,12.4,101,150),(12.5,15.4,151,200),(15.5,30.4,201,300),(30.5,40.4,301,400),(40.5,50.4,401,500)],
            "o3": [(0.0,54,0,50),(55,70,51,100),(71,85,101,150),(86,105,151,200),(106,200,201,300)],
            "no2": [(0,53,0,50),(54,100,51,100),(101,360,101,150),(361,649,151,200),(650,1249,201,300),(1250,1649,301,400),(1650,2049,401,500)],
            "so2": [(0,35,0,50),(36,75,51,100),(76,185,101,150),(186,304,151,200),(305,604,201,300),(605,804,301,400),(805,1004,401,500)]
        }

        mol_weights = {"co":28.01,"o3":48.00,"no2":46.01,"so2":64.07}

        def aqi_linear(C, C_low, C_high, I_low, I_high):
            return ((I_high - I_low)/(C_high - C_low))*(C - C_low) + I_low

        aqi_list = []

        for pollutant, bp_list in breakpoints.items():
            value = components.get(pollutant)
            if value is None:
                continue
            # Convert gases from µg/m³ to ppm
            if pollutant in mol_weights:
                value = (value * 24.45) / mol_weights[pollutant]
            for C_low, C_high, I_low, I_high in bp_list:
                if C_low <= value <= C_high:
                    aqi_list.append((round(aqi_linear(value, C_low, C_high, I_low, I_high)),pollutant))
                    break
        return max(aqi_list, key=lambda x: x[0]) if aqi_list else (None, None)

    # Calulate the text that corrasponds to certain types of weather
    def weatherToText(self, text: str) -> str:
        t = (text or "").lower()
        if "thunder" in t: return "Stormy"
        if "snow" in t: return "Snowing"
        if "rain" in t or "showers" in t: return "Raining"
        if "drizzle" in t: return "Lightly Raining"
        if "fog" in t or "mist" in t: return "Foggy"
        if "mostly cloudy" in t: return "Overcast"
        if "partly cloudy" in t: return "Partly Clear"
        if "cloudy" in t: return "Cloudy"
        if "sunny" in t or "clear" in t: return "Clear"
        return "Clear"

    # Convert from knots to mph
    def knotsToMph(self, knots: float) -> float:
        return knots * 1.15078

    # Use NOAA formula to calulate wind chill 
    def windChillF(self, tempasure_f: float, wind_mph: float) -> float:
        if(tempasure_f <= 50 and wind_mph >= 3):
            return (35.74+ 0.6215 * tempasure_f- 35.75 * (wind_mph ** 0.16)+ 0.4275 * tempasure_f * (wind_mph ** 0.16))
        else: return tempasure_f

    # NOAA formula used to calulate sunset/sunrise
    def calculateSunriseSunset(self, latitude: float, longitude: float, date: datetime.datetime, timezone_offset: float) -> Tuple[datetime.time, datetime.time]:
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
            local_time = (utc_time + timezone_offset) % 24
            hour = int(local_time)
            minute = int(round((local_time - hour) * 60))
            # Clamp time to prevent range errors
            if minute == 60:
                minute = 0
                hour = (hour + 1) % 24
            return datetime.time(hour, minute)

        return compute_sun_time(True), compute_sun_time(False)

    # Calulate timezone offset using zoneInfo data
    def getTimezoneOffsetHours(self, timezone_name: str) -> float:
        now = datetime.datetime.now(ZoneInfo(timezone_name))
        return now.utcoffset().total_seconds() / 3600

    # Magnus-Tetens humidity approximation
    def calulateRelativeHumidity(self, temperature: float, dew_pount: float) -> float:
        saturated_vapor_pressure_T = 6.11 * 10 ** (7.5 * temperature / (237.7 + temperature))
        saturated_vapor_pressure_d = 6.11 * 10 ** (7.5 * dew_pount / (237.7 + dew_pount))
        return (saturated_vapor_pressure_d / saturated_vapor_pressure_T) * 100

    # Rephrase from use standard visibility formate to decimal format 
    def parseUsMetarVis(self,visibility: float) -> Tuple[str, str]:
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

    # Calulate the weighted precentage of cloud coverage
    def calculateWeightedCloudCoverage(self, cloud_layers) -> float:
        cover_values = {'SKC': 0, 'CLR': 0, 'FEW': 25, 'SCT': 50, 'BKN': 75, 'OVC': 100}
        if not cloud_layers: return 0
        
        # Sort cloud layers by height
        layers = sorted(cloud_layers, key=lambda x: x['base'])
        weighted_sum = 0
        total_weight = 0
        # Calulate weight sum of cloud layers
        for i, layer in enumerate(layers):
            cover_pct = cover_values.get(layer['cover'], 0)
            
            # Calulate thickess between layers or assume 2000 as a general bases the sum them
            if i < len(layers) - 1: thickness = layers[i+1]['base'] - layer['base']
            else: thickness = 2000
            weighted_sum += cover_pct * thickness
            total_weight += thickness
        # Return weight average
        return round(weighted_sum / total_weight)

    # Calulate current moon phase
    def getMoonPhase(self) -> Tuple[int, str]:
        # Requires utc date
        date = datetime.datetime.now(datetime.timezone.utc)

        # Using a known date as an refrence to calulate moon phase off of
        known_new_moon = datetime.datetime(2000, 1, 6, 18, 14, tzinfo=datetime.timezone.utc)  # UTC
        synodic_month = 29.530588853  # Average length of a synodic month

        # Calulate number of days since known moon apperence and calulate where it should be now
        days_since_new_moon = (date-known_new_moon).total_seconds()/86400
        phase_fraction = (days_since_new_moon % synodic_month) / synodic_month

        # Return current moon phase
        if phase_fraction < 0.0625 or phase_fraction >= 0.9375: return 0, "New Moon"
        elif phase_fraction < 0.1875: return 1, "Waxing Crescent"
        elif phase_fraction < 0.3125: return 2, "First Quarter"
        elif phase_fraction < 0.4375: return 3, "Waxing Gibbous"
        elif phase_fraction < 0.5625: return 4, "Full Moon"
        elif phase_fraction < 0.6875: return 5, "Waning Gibbous"
        elif phase_fraction < 0.8125: return 6, "Last Quarter"
        else: return 7, "Waning Crescent"

# Image viewer script to run code without epaper screen
if __name__ == "__main__":
    img, show = weatherRender(800, 480).render()
    img.show()