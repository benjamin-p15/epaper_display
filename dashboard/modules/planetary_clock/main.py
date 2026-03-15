import requests, time, os, datetime, sys, re, json
from skyfield.api import load, wgs84        #sudo apt install python3-skyfield
import numpy as np
from datetime import datetime, timezone, timedelta
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
from dashboard.epaper_display import ImageDrawer

class PlanetaryDisplayRender:
    def __init__(self, width: int, height: int):
        self.screen=ImageDrawer(width,height)
        self._cache_img = None
        self._last_update = 0

        self.STATION_URL="https://celestrak.org/NORAD/elements/stations.txt"
        self.STATION_FILE = os.path.join(os.path.dirname(__file__), "stations.txt")
        self.STATION_UPDATE_INTERVAL = 2 * 60 * 60
        self.STATION_NAME = "ISS" # CSS

        self.LAUNCH_URL = f"https://ll.thespacedevs.com/2.2.0/launch/upcoming/?limit=50&offset=0"
        self.LAUNCH_FILE = os.path.join(os.path.dirname(__file__), "launches.txt")
        self.LAUNCH_UPDATE_INTERVAL = 60 * 60
        self.LAUNCH_IMAGE_CATCHE=os.path.join(os.path.dirname(__file__), "last_image_url.txt")
        self.LAUNCH_IMAGE=os.path.join(os.path.dirname(__file__), "launch.png")
    
        self.latitude=None
        self.longitude=None
        self.rise_time=None
        self.set_time=None
        self.rise_direction=None
        self.set_direction=None
        self.orbit_number=0
        self.distance_km=0
        self.speed_km_per_s=0

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
            # Attempt to get the location data from the current ip using ipinfo.io
            response = requests.get("https://ipinfo.io/json")
            response.raise_for_status()
            location_data = response.json()

            # Get and return latitude and longitude data
            location_str = location_data.get("loc")  
            if location_str: self.latitude, self.longitude = map(float, location_str.split(","))
        
        except Exception as error: print("Error getting location:", error)

    def fetch_iss_data(self):
        self.getCurrentLocation()

        # Send iss request to get name and spline info, used to get satellite and observer timescale/other data
        time_scale = load.timescale()
        satellite = self.get_stations()
        observer = wgs84.latlon(self.latitude, self.longitude)
        time_zero = time_scale.now()
        time_one = time_scale.utc(time_zero.utc_datetime().year, time_zero.utc_datetime().month, time_zero.utc_datetime().day + 3)
        times, events = satellite.find_events(observer, time_zero, time_one, altitude_degrees=10)

        # Return direction of ISS based on rise/set angles
        def azimuth_to_direction(azimuth):
            directions = ['N','NE','E','SE','S','SW','W','NW','N']
            index = round(azimuth/45)
            return directions[index]
        
                # Used returned data to get current ISS data
        for timee, event in zip(times, events):
            difference = satellite - observer
            topocentric = difference.at(timee)
            altitude, azimuth, distance = topocentric.altaz()

            # Based on rise/max/set calulate times, directions, and speeds
            if event == 0: 
                self.rise_time=timee.utc_strftime('%I:%M')
                self.rise_direction = azimuth_to_direction(azimuth.degrees)
            elif event == 1:
                altitude, azimuth, distance = (satellite - observer).at(time_zero).altaz()
                self.distance_km = distance.km
                self.speed_km_per_s = np.linalg.norm(topocentric.velocity.km_per_s)
            elif event == 2: 
                self.set_time = timee.utc_strftime('%I:%M')
                self.set_direction = azimuth_to_direction(azimuth.degrees)

        # Calulate the the number of orbits of ISS based on orbit speed and launch date
        seconds_per_orbit = 92.5 * 60  
        epoch = datetime(1998, 11, 20, tzinfo=timezone.utc)
        now_utc = datetime.now(timezone.utc) 
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

            return {
                "name": name,
                "launch_date_utc": launch_dt,
                "status": launch.get("status", {}).get("name"),
                "probability": launch.get("probability"),
                "webcast_live": launch.get("webcast_live")
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

            self.fetch_iss_data()
            self.get_upcoming_launches()
            mission = self.next_mission_launch("artemis","spacex")

            launch_dt = mission["launch_date_utc"]
            now = datetime.now(timezone.utc)
            delta = launch_dt - now  

            if (timedelta(0) < delta <= timedelta(hours=2)) and mission["webcast_live"]: timee="Live!"
            else: timee=f"{delta.days}d:{delta.seconds//3600}h:{(delta.seconds%3600)//60}m"

            if mission["probability"] is not None: probability=f"| {mission['probability']}%"
            else: probability=""

            split_name=[s.strip() for s in mission['name'].split('|')]

            if len(mission['name']) <= 28: 
                self.screen.add_text([{"text": f"{split_name[1]} | {split_name[0]}", "size": 26}], position=(0, 0.02), align="left", bold=True)
                status_padding=0
            else:
                self.screen.add_text([{"text": f"{split_name[1]}", "size": 26}], position=(0, 0.02), align="left", bold=True)
                self.screen.add_text([{"text": f"{split_name[0]}", "size": 20}], position=(0, 0.07), align="left", bold=True)
                status_padding=0.05

            self.screen.add_text([{"text": f"{timee}", "size": 20}], position=(0.97, 0.5+0.01), align="right", bold=True)
            self.screen.add_text([{"text": f"Status: {mission['status']} {probability}", "size": 16}], position=(0, 0.06+0.02+status_padding), align="left", bold=True)

            self.screen.add_rectangle(position=(0.75, 0.45), size=(0.3, 0.125), fill=None, radius=6, thickness=2)
            self.screen.add_image(self.LAUNCH_IMAGE, position=(0.5, 0), size=(0.5, 0.5))
            self.screen.add_rectangle(position=(0.5, -0.1), size=(0.6, 0.6), fill=None, radius=2, thickness=2)


            self.screen.add_text([{"text": f"{self.STATION_NAME} rise/set: {self.rise_time}-{self.rise_direction} | {self.set_time}-{self.set_direction}, Orbit: {self.orbit_number}, Range: {int(round(self.distance_km, 0))}km | {round(self.speed_km_per_s,1)}km/s", "size": 18}], position=(0, 0.95), align="left", bold=True)

            # Screen render stuff
            self._cache_img=self.screen.render()
            if(self._cache_img is None): return None, False
            else: return self._cache_img, True 
        return self._cache_img, False
    


# Image viewer script to run code without screen
if __name__ == "__main__":
    img, show = PlanetaryDisplayRender(800, 480).render()
    img.show()