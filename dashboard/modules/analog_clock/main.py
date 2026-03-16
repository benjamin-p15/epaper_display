import requests, math, time, csv, os, datetime, sys, random, calendar
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
        self.seconds_until_next_minute=60

    # Render an analog clock
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
        self.screen.add_text([{"text": f"{t.tm_mon:02}-{t.tm_mday:02}-{t.tm_year}","size": math.floor(20*scale),"bold": True,"algin":"center"}],position=(x_element_offset,0.5+0.205*scale),font="DejaVuSans-Bold.ttf")
        self.screen.add_text([{"text": f"{self.days[t.tm_wday]}","size": math.floor(20*scale),"bold": True,"algin":"center"}],position=(x_element_offset,0.5-0.248*scale),font="DejaVuSans-Bold.ttf")

    # Renders a calender
    def renderCalender(self):
        columns, rows = 7, 5
        x_element_offset = 0.75
        rect_width = 0.05
        rect_height = 0.05 * self.scale_factor
        gap_x = 0.01
        gap_y = 0.01 * self.scale_factor
        start_x = x_element_offset - (columns * rect_width + (columns - 1) * gap_x) / 2
        start_y = 0.5 - (rows * rect_height + (rows - 1) * gap_y) / 2
        today = datetime.date.today()
        year, month = today.year, today.month
        month_grid = calendar.monthcalendar(year, month)
        first_weekday, days_in_month = calendar.monthrange(year, month)
        previous_month = month - 1 or 12
        previous_year = year - 1 if month == 1 else year
        _, days_in_previous_month = calendar.monthrange(previous_year, previous_month)
        next_day_counter = 1

        weekday_labels = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        label_y = start_y - rect_height * 0.6

        self.screen.add_rectangle((start_x,start_y-0.06),(rect_width*columns+gap_x*(columns-1),0.05),fill=0,thickness=1,radius=7)

        for week_index in range(rows):
            for weekday_index in range(columns):
                x = start_x + weekday_index * (rect_width + gap_x)
                self.screen.add_text([{"text": weekday_labels[weekday_index], "size": 14, "bold": True}],position=(x + rect_width * 0.5, label_y),font="DejaVuSans-Bold.ttf")


                x=start_x+weekday_index*(rect_width+gap_x)
                y=start_y+week_index*(rect_height+gap_y)
                if week_index<len(month_grid): day_value=month_grid[week_index][weekday_index]
                else: day_value=0
                if day_value == 0:
                    if week_index == 0: day_number=days_in_previous_month-(first_weekday-weekday_index-1)
                    else:
                        day_number=next_day_counter
                        next_day_counter+=1
                    fill_value=0
                    text_color=1
                    thickness=1
                    is_today=False
                else:
                    day_number=day_value
                    fill_value=0
                    text_color=0
                    thickness=1
                    is_today=(day_number == today.day)
                if is_today:
                    fill_value=0
                    text_color=1
                    thickness=None

                self.screen.add_rectangle((x, y),(rect_width, rect_height),fill=fill_value,thickness=thickness,radius=7)
                self.screen.add_text([{"text": str(day_number), "size": 18, "bold": True}],position=(x + rect_width * 0.5, y + rect_height * 0.55-0.02),font="DejaVuSans.ttf",fill=text_color,stroke_width=1,stroke_fill=0)



    # Renders the screen
    def render(self, force=False) -> Tuple[Image.Image, bool]:
        self.now = time.time()
        if force or (self.now - self._last_update >= self.seconds_until_next_minute):
            self._last_update = self.now
            self.now = datetime.datetime.now()
            self.seconds_until_next_minute = round(60 - self.now.second - self.now.microsecond / 1_000_000)

            self.renderClock()
            self.renderCalender()

            _cache_img=self.screen.render()
            if(_cache_img is None): return None, False
            else: return _cache_img, True 
        return None, False
    
# Image viewer script to run code without epaper screen
if __name__ == "__main__":
    img, show = analogClockRenderer(800, 480).render()
    img.show()