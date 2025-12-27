from PIL import Image, ImageDraw, ImageFont
import datetime

# ================= FONTS =================
try:
    FONT_LARGE = ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 120
    )
    FONT_MEDIUM = ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 50
    )
    FONT_SMALL = ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40
    )
    FONT_TINY = ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20
    )
except:
    FONT_LARGE = ImageFont.load_default()
    FONT_MEDIUM = ImageFont.load_default()
    FONT_SMALL = ImageFont.load_default()
    FONT_TINY = ImageFont.load_default()

FONT_HOLIDAY = FONT_SMALL
FONT_DAYS = FONT_TINY

# ================= HOLIDAYS =================
def nth_weekday(year, month, weekday, n):
    d = datetime.date(year, month, 1)
    count = 0
    while True:
        if d.weekday() == weekday:
            count += 1
            if count == n:
                return d
        d += datetime.timedelta(days=1)

def first_weekday(year, month, weekday):
    return nth_weekday(year, month, weekday, 1)

def second_weekday(year, month, weekday):
    return nth_weekday(year, month, weekday, 2)

def third_weekday(year, month, weekday):
    return nth_weekday(year, month, weekday, 3)

def fourth_weekday(year, month, weekday):
    return nth_weekday(year, month, weekday, 4)

def last_weekday(year, month, weekday):
    d = datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)
    while d.weekday() != weekday:
        d -= datetime.timedelta(days=1)
    return d

def get_holiday_info(today=None):
    if today is None:
        today = datetime.date.today()

    year = today.year
    holidays = {
        datetime.date(year, 1, 1): "New Year's Day",
        datetime.date(year, 6, 19): "Juneteenth",
        datetime.date(year, 7, 4): "Independence Day",
        datetime.date(year, 11, 11): "Veterans Day",
        datetime.date(year, 12, 25): "Christmas Day",
        third_weekday(year, 1, 0): "MLK Day",
        third_weekday(year, 2, 0): "Presidents Day",
        last_weekday(year, 5, 0): "Memorial Day",
        first_weekday(year, 9, 0): "Labor Day",
        second_weekday(year, 10, 0): "Columbus Day",
        fourth_weekday(year, 11, 3): "Thanksgiving",
    }

    if today in holidays:
        return holidays[today], 0

    upcoming = []
    for d, name in holidays.items():
        future = d if d >= today else datetime.date(year + 1, d.month, d.day)
        upcoming.append(((future - today).days, name))

    upcoming.sort()
    return upcoming[0][1], upcoming[0][0]

# ================= RENDER =================
def render():
    now = datetime.datetime.now()
    time_text = now.strftime("%I:%M")
    am_pm = now.strftime("%p")
    date_str = now.strftime("%m/%d/%y")
    day_str = now.strftime("%A")

    holiday_name, days_until = get_holiday_info()
    holiday_text = (
        holiday_name if days_until == 0
        else f"{holiday_name}\n{days_until} days"
    )

    img = Image.new("1", (800, 480), 255)
    draw = ImageDraw.Draw(img)

    x, y = 50, 50
    draw.text((x, y), time_text, font=FONT_LARGE, fill=0)

    w, h = draw.textsize(time_text, font=FONT_LARGE)
    draw.text((x + w + 10, y + h // 2), am_pm, font=FONT_MEDIUM, fill=0)

    draw.text((x, 250), date_str, font=FONT_MEDIUM, fill=0)
    draw.text((x, 320), day_str, font=FONT_MEDIUM, fill=0)

    lines = holiday_text.split("\n")
    total_h = sum(
        draw.textsize(l, FONT_HOLIDAY if i == 0 else FONT_DAYS)[1]
        for i, l in enumerate(lines)
    )

    y = 480 - total_h - 20
    for i, line in enumerate(lines):
        font = FONT_HOLIDAY if i == 0 else FONT_DAYS
        w, h = draw.textsize(line, font)
        draw.text((800 - w - 20, y), line, font=font, fill=0)
        y += h

    return img
