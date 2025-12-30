import time, os, datetime, sys, datetime, calendar
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
from dashboard.epaper_display import ImageDrawer

screen = ImageDrawer()
script_directory = os.path.dirname(os.path.abspath(__file__))

_last_update = 0
_cache_img = None
seconds_until_next_minute=60

def render():
    global _last_update, _cache_img, script_directory, seconds_until_next_minute
    now = time.time()
    now_datetime = datetime.datetime.now()
    
    # Update only if we reached the next minute
    if now - _last_update >= seconds_until_next_minute:
        # Calulate seconds untill next minute for screen refreash 
        seconds_until_next_minute = round(60 - now_datetime.second - now_datetime.microsecond / 1_000_000)

        _last_update = now
        # Date/time data
        today = datetime.date.today()
        now = datetime.datetime.now()
        year = today.year

        # Calulate current time
        hour_12 = now.hour % 12 or 12  # Convert to 12 hour format
        minute = now.minute
        ampm = "am" if now.hour < 12 else "pm"
        # Display current time on screen
        screen.add_text([{"text": f"{hour_12}:{minute:02d}", "size": 160},{"text": f"{ampm}", "size": 56,"align": "bottom"}], position=(0.5,0),bold=True,align="center")

        # Add current date to display
        date = get_formatted_date(today)  
        screen.add_text([{"text": f"{date}", "size": 36}], position=(0.5,0.32),bold=True)

        # Display length of time until certain events
        name, days = get_holiday_info(today)
        screen.add_text([{"text": f"{name}", "size": 32}], position=(0.5,0.87),bold=True)
        if (days>1): screen.add_text([{"text": f"{days} days", "size": 17}], position=(0.5,0.95),bold=True)
        else: screen.add_text([{"text": f"{days} day", "size": 16}], position=(0.5,0.95),bold=True)

        # Calulate year number of days in year then use that data to show how complete the year is with a rectangle
        day_of_year = today.timetuple().tm_yday
        total_days = 366 if calendar.isleap(year) else 365
        precent_complete=day_of_year/total_days
        screen.add_rectangle(position=(0.1, 0.6), size=(0.8, 0.15), fill=1, radius=15, thickness=None)
        screen.add_rectangle(position=(0.1, 0.6), size=(0.8*precent_complete, 0.15), fill=0, radius=15, thickness=None)
        screen.add_rectangle(position=(0.1, 0.6), size=(0.8, 0.15), fill=0, radius=15, thickness=2)
        screen.add_text([{"text": f"{year}", "size": 32}], position=(0.5, 0.53),bold=True)
        screen.add_text([{"text": f"{round(precent_complete*100, 1)}% complete", "size": 16}], position=(0.5, 0.76),bold=True)

        # Render the screen
        _cache_img = screen.render()
        if _cache_img is None: return None, False
        else: return _cache_img, True
    return _cache_img, False

# Return prefix of number .i.e 3rd
def get_ordinal(n):
    if 10 <= n % 100 <= 20: return "th"
    else: return {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")

# Return date formated with full name of month and day
def get_formatted_date(today=None):
    if today is None: today = datetime.date.today()
    day = today.day
    suffix = get_ordinal(day)
    month = today.strftime("%B") 
    year = today.year
    return f"{month} {day}{suffix} {year}"

# Function to calulate date of holidays which do not fall on certain date but instead fall onto a certain part of a week/month
def weekday_of_month(year, month, weekday, n=None):
    if n is None: 
        d = datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)
        while d.weekday() != weekday:
            d -= datetime.timedelta(days=1)
        return d
    else:
        d = datetime.date(year, month, 1)
        count = 0
        while True:
            if d.weekday() == weekday:
                count += 1
                if count == n: return d
            d += datetime.timedelta(days=1)

# Calulate how many days away each holiday is and return closest one
def get_holiday_info(today=None):
    if today is None: today = datetime.date.today()
    year = today.year
    holidays = {
        datetime.date(year, 1, 1): "New Year's Day",
        datetime.date(year, 6, 19): "Juneteenth",
        datetime.date(year, 7, 4): "Independence Day",
        datetime.date(year, 11, 11): "Veterans Day",
        datetime.date(year, 12, 25): "Christmas Day",
        weekday_of_month(year, 1, 0, 3): "MLK Day",
        weekday_of_month(year, 2, 0, 3): "Presidents Day",
        weekday_of_month(year, 5, 0): "Memorial Day",
        weekday_of_month(year, 9, 0, 1): "Labor Day",
        weekday_of_month(year, 10, 0, 2): "Columbus Day",
        weekday_of_month(year, 11, 3, 4): "Thanksgiving",
        weekday_of_month(year, 5, 6, 2): "Mother's Day",
        weekday_of_month(year, 6, 6, 3): "Father's Day",
    }

    # Add birthdays to list from hiddel file
    birthdays_file = os.path.join(os.path.expanduser("~"), "birthdays.txt")
    with open(birthdays_file, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            line = line.replace("year", str(year))
            key, value = line.split(":", 1)
            key_date = eval(key.strip())          
            value_str = value.strip().strip(",").strip('"').strip("'")
            holidays[key_date] = value_str         

    if today in holidays: return holidays[today], 0

    nearest_name = None
    nearest_days = None

    for d, name in holidays.items():
        future = d if d >= today else datetime.date(year + 1, d.month, d.day)
        delta = (future - today).days
        if nearest_days is None or delta < nearest_days:
            nearest_days = delta
            nearest_name = name

    return nearest_name, nearest_days


# Image viewer script to run code without screen
def main():
    global _last_update
    _last_update=0
    img, show = render()
    img.show()

if __name__ == "__main__":
    main()