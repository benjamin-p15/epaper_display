import requests, time, os, datetime, sys, re, json
from skyfield.api import load, wgs84        #sudo apt install python3-skyfield or pip3 install skyfield
import numpy as np
from zoneinfo import ZoneInfo
from datetime import datetime, timezone, timedelta
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
dashboard = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
from dashboard.epaper_display import ImageDrawer

class PlanetaryDisplayRender:
    def __init__(self, width: int, height: int):
        self.screen=ImageDrawer(width,height)
        self.scale_factor=width/height
        self._cache_img = None
        self._last_update = 0

        self.STATION_URL="https://celestrak.org/NORAD/elements/stations.txt"
        self.STATION_FILE = os.path.join(os.path.dirname(__file__), "data/stations.txt")
        self.STATION_UPDATE_INTERVAL = 2 * 60 * 60
        self.STATION_NAME = "ISS" # CSS
        self.STATION_ORBIT_PERIOD=92.5

        self.LAUNCH_URL = f"https://ll.thespacedevs.com/2.2.0/launch/upcoming/?limit=50&offset=0"
        self.LAUNCH_FILE = os.path.join(os.path.dirname(__file__), "data/launches.txt")
        self.LAUNCH_UPDATE_INTERVAL = 60 * 60
        self.LAUNCH_IMAGE_CATCHE=os.path.join(os.path.dirname(__file__), "data/last_image_url.txt")
        self.LAUNCH_IMAGE=os.path.join(os.path.dirname(__file__), "data/launch.png")

        self.SOLAR_XRAY_URL="https://services.swpc.noaa.gov/json/goes/primary/xrays-6-hour.json"
        self.SOLAR_KP_URL="https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json"
        self.SOLAR_WIND_URL="https://services.swpc.noaa.gov/products/solar-wind/plasma-1-day.json"
        self.SOLAR_FILE=os.path.join(os.path.dirname(__file__), "data/solarweather.json")
        self.SOLAR_UPDATE_INTERVAL=5 * 60

        self.LOCATION_FILE=os.path.join(dashboard, "data/location.json")
    
        self.latitude=None
        self.longitude=None
        self.timezone="UTC"

        self.rise_time=None
        self.set_time=None
        self.rise_direction=None
        self.set_direction=None
        self.orbit_number=0
        self.distance_km=0
        self.speed_km_per_s=0

        self.solar_speed=0
        self.solar_density=0
        self.solar_kp=0
        self.solar_xray=0

    # Finds data from the station based on the STATION_NAME
    def get_satellite_data(self, name, satellites):
        name = name.strip().upper()
        for satellite in satellites:
            if name in satellite.name.strip().upper(): return satellite
        raise ValueError(f"No satellite found with name containing '{name}'")

    # Get current station data, only updating when new data is availible 
    def get_stations(self):
        file = None
        # Check if local file exists, if file has been updated in last 2 hours pull most recent data
        if os.path.exists(self.STATION_FILE):
            last_mod = os.path.getmtime(self.STATION_FILE)
            if time.time() - last_mod < self.STATION_UPDATE_INTERVAL: file = load.tle_file(self.STATION_FILE)
        # Otherwise, fetch new station data
        if file is None:
            response = requests.get(self.STATION_URL, headers={'User-Agent':'Mozilla/5.0'})
            response.raise_for_status()
            with open(self.STATION_FILE, "w") as f: f.write(response.text)
            file = load.tle_file(self.STATION_FILE)

        return self.get_satellite_data(self.STATION_NAME,file)
    
    # Get upcomming rocket launches
    def get_upcoming_launches(self):
        # If catche file is updated return json file contents
        if os.path.exists(self.LAUNCH_FILE):
            last_mod = os.path.getmtime(self.LAUNCH_FILE)
            if time.time() - last_mod < self.LAUNCH_UPDATE_INTERVAL:
                with open(self.LAUNCH_FILE, "r") as f: return json.load(f)

        # Elsewise fatch newest data
        response = requests.get(self.LAUNCH_URL, headers={'User-Agent':'Mozilla/5.0'})
        response.raise_for_status()
        launches = response.json().get("results", [])
        with open(self.LAUNCH_FILE, "w") as f: json.dump(launches, f)
        return launches

    # Get current location info using ip address
    def getCurrentLocation(self):
        try:
            with open(self.LOCATION_FILE, "r") as f: data = json.load(f)
            self.latitude, self.longitude = map(float, self.location_data.get("loc").split(","))
            self.timezone = data.get("timezone", "UTC")

        except Exception as error:
            self.latitude=0
            self.longitude=0
            self.timezone="UTC"

    def getSolarFluxState(self):
        if self.solar_xray < 1e-7: return "A"
        elif self.solar_xray < 1e-6: return "B"
        elif self.solar_xray < 1e-5: return "C"
        elif self.solar_xray < 1e-4: return "M"
        else: return "X"

    def fetch_solar_data(self):
        if os.path.exists(self.SOLAR_FILE) and time.time() - os.path.getmtime(self.SOLAR_FILE) < self.SOLAR_UPDATE_INTERVAL: 
            jsonfile=json.load(open(self.SOLAR_FILE))
            xray=jsonfile["xray"]
            kp=jsonfile["kp"]
            wind=jsonfile["solar_wind"]
        else:
            xray = requests.get(self.SOLAR_XRAY_URL).json()[-1]
            kp = requests.get(self.SOLAR_KP_URL).json()[-1]
            wind = requests.get(self.SOLAR_WIND_URL).json()[-1]
            print(wind)

        self.solar_density=wind["density"] if "density" in wind else wind[1]
        self.solar_speed=wind["speed"] if "speed" in wind else wind[2]
        self.solar_kp=kp["kp_index"] if "kp_index" in kp else kp[1]
        self.solar_xray= xray["flux"]

        data = {
            "xray": {"flux": self.solar_xray},
            "kp": {"kp_index": self.solar_kp},
            "solar_wind": {"density": self.solar_density, "speed":self.solar_speed}
        }
        with open(self.SOLAR_FILE, "w") as f: json.dump(data, f)

    def fetch_station_data(self):
        # Send iss request to get name and spline info, used to get satellite and observer timescale/other data
        time_scale = load.timescale()
        satellite = self.get_stations()
        observer = wgs84.latlon(self.latitude, self.longitude)
        time_zero = time_scale.now()
        future_dt = time_zero.utc_datetime() + timedelta(days=3)
        time_one = time_scale.utc(future_dt.year, future_dt.month, future_dt.day)
        times, events = satellite.find_events(observer, time_zero, time_one, altitude_degrees=10)

        # Return direction of ISS based on rise/set angles
        def azimuth_to_direction(azimuth):
            directions = ['N','NE','E','SE','S','SW','W','NW','N']
            index = round(azimuth/45)
            return directions[index]
        
        # Used returned data to get current ISS data
        delta_rise_time = None
        delta_set_time = None

        now_utc = datetime.now(timezone.utc) 
        for timee, event in zip(times, events):
            difference = satellite - observer
            topocentric = difference.at(timee)
            altitude, azimuth, distance = topocentric.altaz()

            # Based on rise/max/set calulate times, directions, and speeds
            if event == 0: 
                delta_rise_time = timee.utc_datetime()
                if(delta_rise_time==None): continue
                self.rise_direction = azimuth_to_direction(azimuth.degrees)
            elif event == 1:
                altitude, azimuth, distance = (satellite - observer).at(time_zero).altaz()
                self.distance_km = distance.km
                self.speed_km_per_s = np.linalg.norm(topocentric.velocity.km_per_s)
            elif event == 2: 
                delta_set_time = timee.utc_datetime()
                if(delta_set_time==None): continue
                self.set_direction = azimuth_to_direction(azimuth.degrees)
            if delta_set_time is None or delta_rise_time is None: continue
            else: break

        self.rise_time = delta_rise_time.astimezone(ZoneInfo(self.timezone)).strftime("%I:%M")
        self.set_time = delta_set_time.astimezone(ZoneInfo(self.timezone)).strftime("%I:%M")

        # Calulate the the number of orbits of ISS based on orbit speed and launch date
        seconds_per_orbit = self.STATION_ORBIT_PERIOD * 60  
        epoch = datetime(1998, 11, 20, tzinfo=timezone.utc)
        elapsed_seconds = (now_utc - epoch).total_seconds()
        self.orbit_number = int(elapsed_seconds / seconds_per_orbit)

    def next_mission_launch(self, mission, fallback_mission):
        def process_launch(launch):
            name = launch.get("name", "")
            launch_date = launch.get("net")
            if not launch_date: return None
            launch_dt = datetime.fromisoformat(launch_date.replace("Z","+00:00"))
            now = datetime.now(timezone.utc) #+ timedelta(days=20)
            if launch_dt < now: return None

            # Download latest image if it hasn't been download before
            image_url = launch.get("image")
            download_image = False
            if image_url:
                if os.path.exists(self.LAUNCH_IMAGE_CATCHE):
                    with open(self.LAUNCH_IMAGE_CATCHE, "r") as f: last_url = f.read().strip()
                    if last_url != image_url: download_image = True
                else: download_image = True  
                if download_image:
                    try:
                        resp = requests.get(image_url, headers={"User-Agent": "Mozilla/5.0"})
                        resp.raise_for_status()
                        with open(self.LAUNCH_IMAGE, "wb") as f_img: f_img.write(resp.content)
                        with open(self.LAUNCH_IMAGE_CATCHE, "w") as f: f.write(image_url)
                    except Exception as e: image_url = None
            mission = launch.get("mission") or {}
            pad = launch.get("pad") or {}       
            return {
                "name": name,
                "launch_date_utc": launch_dt,
                "status": launch.get("status", {}).get("name"),
                "probability": launch.get("probability"),
                "webcast_live": launch.get("webcast_live"),

                "pad": pad.get("name"),
                "orbit": (mission.get("orbit") or {}).get("name"),
                "description": mission.get("description"),
            }

        with open(self.LAUNCH_FILE, "r") as f: launches = json.load(f)
        mission = mission.upper()
        fallback = fallback_mission.upper()

        for launch in launches:
            if mission in launch.get("name", "").upper() or mission in launch.get("launch_service_provider", {}).get("name", "").upper():
                result = process_launch(launch)
                if result: return result

        for launch in launches:
            if fallback in launch.get("name", "").upper() or fallback in launch.get("launch_service_provider", {}).get("name", "").upper():
                result = process_launch(launch)
                if result: return result

        return None

    def render(self,force=False):
        # Update screen every 10 minutes or if otherwise requested
        now = time.time()
        if force or (self._cache_img is None or now - self._last_update >= 10 * 60):
            self._last_update = now
            self.getCurrentLocation()

            # Fetch newest screen data
            self.fetch_station_data()
            self.get_upcoming_launches()
            self.fetch_solar_data()
            mission = self.next_mission_launch("artemis","spacex")

            print(f"{self.solar_xray} {self.solar_kp} {self.solar_density} {self.solar_speed}")

            # Render solar data
            exponent = int(f"{self.solar_xray:e}".split("e")[-1])
            scale = 10 ** -exponent
            xray_value=round(self.solar_xray * scale,2)
            magnetude=self.getSolarFluxState()

            self.screen.add_image(os.path.join(os.path.dirname(__file__), f"icons/solar_flare_{magnetude}.png"), position=(0.01, 0.5), size=(0.3, 0.3*self.scale_factor))
            self.screen.add_text([{"text": f"Flux: {magnetude}{xray_value} | Kp: {self.solar_kp}/9", "size": 18}], position=(0.01,0.45), align="left", bold=True)
            self.screen.add_text([
                {"text": f"Wind: {self.solar_density}p/cm", "size": 18},
                {"text": f"3 ", "size": 16, "offset":(0,-4)},
                {"text": f"| {self.solar_speed}km/s", "size": 18}
                ], position=(0.01,0.5), align="left", bold=True)

            # Render screen launch data
            launch_dt = mission["launch_date_utc"].astimezone(ZoneInfo(self.timezone))
            now = datetime.now(ZoneInfo(self.timezone))
            delta = launch_dt - now  

            if (timedelta(0) < delta <= timedelta(hours=2)) and mission["webcast_live"]: timee="Live!"
            else: timee=f"{delta.days}d:{delta.seconds//3600}h:{(delta.seconds%3600)//60}m"

            if mission["probability"] is not None: probability=f"| {mission['probability']}%"
            else: probability=""

            split_name=[s.strip() for s in mission['name'].split('|')]

            self.screen.add_rectangle(position=(0, 0), size=(0.5, 0.1), fill=0, radius=0, thickness=None)
            self.screen.add_rectangle(position=(0, 0), size=(0.5, 0.22), fill=0, radius=9, thickness=None)

            

            if len(mission['name']) <= 28: 
                self.screen.add_text([{"text": f"{split_name[1]} | {split_name[0]}", "size": 26}], position=(0.005, 0.02), align="left", bold=True, fill=1)
                status_padding=0
            else:
                self.screen.add_text([{"text": f"{split_name[1]}", "size": 26}], position=(0.005, 0.02), align="left", bold=True, fill=1)
                self.screen.add_text([{"text": f"{split_name[0]}", "size": 20}], position=(0.005, 0.07), align="left", bold=True, fill=1)
                status_padding=0.05

            self.screen.add_text([{"text": f"{timee}", "size": 20}], position=(0.97, 0.5+0.01), align="right", bold=True)

            status_text=f"Status: {mission['status']} {probability}"
            self.screen.add_text([{"text": status_text, "size": 18}], position=(0.005, 0.06+0.02+status_padding), align="left", bold=True, fill=1)

            self.screen.add_rectangle(position=(0.005, 0.1+0.025+status_padding), size=(len(status_text)*0.56*18,1.0), fill=1, radius=6, thickness=None)




            self.screen.add_text([{"text": f"Orbit: {mission['orbit']} {probability}", "size": 16}], position=(0.005, 0.09+0.04+status_padding), align="left", bold=True, fill=1)
            self.screen.add_text([{"text": f"Pad: {mission['pad']} {probability}", "size": 16}], position=(0.005, 0.13+0.04+status_padding), align="left", bold=True, fill=1)

            #description=re.sub(r'\s+', ' ', (mission["description"].replace('\x00', ''))).strip()
            #print(self.wrap_text(description))

            #self.screen.add_text([{"text": f"Info: ", "size": 16},{"text": f"{self.wrap_text(description,56)} {probability}", "size": 10}], position=(0.005, 0.17+0.04+status_padding), align="left", bold=True)


            self.screen.add_rectangle(position=(0.75, 0.45), size=(0.3, 0.125), fill=None, radius=6, thickness=2)
            self.screen.add_image(self.LAUNCH_IMAGE, position=(0.5, 0), size=(0.5, 0.5))
            self.screen.add_rectangle(position=(0.5, -0.1), size=(0.6, 0.6), fill=None, radius=2, thickness=2)

            # Render screen satilight data
            self.screen.add_rectangle(position=(0, 0.95), size=(1, 0.05), fill=0, radius=0, thickness=None)
            self.screen.add_text([{"text": f"{self.STATION_NAME} rise/set: {self.rise_time}-{self.rise_direction} | {self.set_time}-{self.set_direction}, Orbit: {self.orbit_number}, Range: {int(round(self.distance_km, 0))}km | {round(self.speed_km_per_s,1)}km/s", "size": 18}], position=(0.5, 0.96), align="center", bold=True, fill=1)

            # Screen render stuff
            self._cache_img=self.screen.render()
            if(self._cache_img is None): return None, False
            else: return self._cache_img, True 
        return self._cache_img, False
    
    def wrap_text(self, text, max_len=30):
        words = text.split()
        lines = []
        current_line = ""

        for word in words:
            if len(current_line) + len(word) + (1 if current_line else 0) <= max_len:
                if current_line: current_line += " "
                current_line += word
            else:
                lines.append(current_line)
                current_line = word
        if current_line: lines.append(current_line)
        return "\n".join(lines)
    


# Image viewer script to run code without screen
if __name__ == "__main__":
    img, show = PlanetaryDisplayRender(800, 480).render()
    img.show()