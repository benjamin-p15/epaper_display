import requests, math, time, csv, os, datetime, sys, random
from PIL import Image
from typing import Optional, List, Tuple
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
script_directory = os.path.dirname(os.path.abspath(__file__))
from zoneinfo import ZoneInfo
from dashboard.epaper_display import ImageDrawer

# Class which handles the drawing of the weather screen modual and getting current weather data
class analogClockRenderer:
    def __init__(self, width: int, height: int):
        self.screen=ImageDrawer(width,height)
        self.scale_factor=width/height
        self._last_update=0
        #self.digits=["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"]
        self.digits=["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII"]
        self.days = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

    def renderClock(self):
        x_element_offset=0.25
        scale=0.85
        # Draw circles for clock
        self.screen.add_circle((x_element_offset,0.5),0.48*scale,thickness=1)
        self.screen.add_circle((x_element_offset,0.5),0.47*scale,thickness=1)
        # Draws dots for the clock
        for i in range(60):
            angle = 2 * math.pi * i / 60
            x = x_element_offset + 0.35 * scale * math.cos(angle)/self.scale_factor
            y = 0.5 + 0.35 * scale * math.sin(angle)
            self.screen.add_circle((x, y), 0.005*scale, fill=0, thickness=0)
        for i in range(12):
            angle = 2 * math.pi * i/12 - math.pi/3
            x = x_element_offset + 0.35 * scale * math.cos(angle)/self.scale_factor
            y = 0.5 + 0.35 * scale * math.sin(angle)
            self.screen.add_circle((x, y), 0.01*scale, fill=0, thickness=0)
            # Draw clock text
            self.screen.add_text([{"text": self.digits[i],"size": math.floor(20*scale),"bold": True}],position=(x+0.067*scale*math.cos(angle)/self.scale_factor, y+0.067*scale*math.sin(angle)-0.02),font="DejaVuSans-Bold.ttf")

        # Draw clock hands
        t = time.localtime()
        hour_angle = 2*math.pi*((t.tm_hour%12 + t.tm_min/60)/12) - math.pi/2
        minute_angle = 2*math.pi*(t.tm_min/60)-math.pi/2
        self.screen.add_line((x_element_offset - 0.025*math.sin(hour_angle)/self.scale_factor,0.5 + 0.025*math.cos(hour_angle)),(x_element_offset + 0.325*scale*math.cos(hour_angle)/self.scale_factor,0.5 + 0.325*scale*math.sin(hour_angle)),fill=0,thickness=1)
        self.screen.add_line((x_element_offset + 0.025*math.sin(hour_angle)/self.scale_factor,0.5 - 0.025*math.cos(hour_angle)),(x_element_offset + 0.325*scale*math.cos(hour_angle)/self.scale_factor,0.5 + 0.325*scale*math.sin(hour_angle)),fill=0,thickness=1)
        self.screen.add_line((x_element_offset - 0.025*math.sin(minute_angle)/self.scale_factor,0.5 + 0.025*math.cos(minute_angle)),(x_element_offset + 0.375*scale*math.cos(minute_angle)/self.scale_factor,0.5 + 0.375*scale*math.sin(minute_angle)),fill=0,thickness=1)
        self.screen.add_line((x_element_offset + 0.025*math.sin(minute_angle)/self.scale_factor,0.5 - 0.025*math.cos(minute_angle)),(x_element_offset + 0.375*scale*math.cos(minute_angle)/self.scale_factor,0.5 + 0.375*scale*math.sin(minute_angle)),fill=0,thickness=1)
        self.screen.add_circle((x_element_offset,0.5),0.05*scale,thickness=-1)
        self.screen.add_circle((x_element_offset,0.5),0.046*scale,thickness=-1,fill=1)

        # Add date and day to screen
        self.screen.add_rectangle((x_element_offset-0.09*scale,0.5-0.255*scale),(0.18*scale,0.07*scale),fill=1,thickness=None,radius=math.floor(10*scale))
        self.screen.add_rectangle((x_element_offset-0.09*scale,0.5-0.255*scale),(0.18*scale,0.07*scale),fill=0,thickness=1,radius=math.floor(10*scale))
        self.screen.add_rectangle((x_element_offset-0.09*scale,0.5+0.195*scale),(0.18*scale,0.07*scale),fill=1,thickness=None,radius=math.floor(10*scale))
        self.screen.add_rectangle((x_element_offset-0.09*scale,0.5+0.195*scale),(0.18*scale,0.07*scale),fill=0,thickness=1,radius=math.floor(10*scale))
        self.screen.add_text([{"text": f"{t.tm_year}-{t.tm_mon:02}-{t.tm_mday:02}","size": math.floor(20*scale),"bold": True,"algin":"center"}],position=(x_element_offset,0.5+0.2*scale),font="DejaVuSans-Bold.ttf")
        self.screen.add_text([{"text": f"{self.days[t.tm_wday]}","size": math.floor(20*scale),"bold": True,"algin":"center"}],position=(x_element_offset,0.5-0.25*scale),font="DejaVuSans-Bold.ttf")

    # Renders the screen
    def render(self, refreash_rate: float = 300) -> Tuple[Image.Image, bool]:
        self.now = time.time()
        if self.now - self._last_update >= refreash_rate:
            self._last_update = self.now

            self.renderClock()

            _cache_img=self.screen.render()
            if(_cache_img is None): return None, False
            else: return _cache_img, True 
        return None, False
    
# Image viewer script to run code without epaper screen
if __name__ == "__main__":
    img, show = analogClockRenderer(800, 480).render()
    img.show()