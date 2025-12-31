import requests, math, time, csv, os, datetime, sys, random
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
from zoneinfo import ZoneInfo
from dashboard.epaper_display import ImageDrawer
screen = ImageDrawer()

api_key = "2553~FvNmEDW7BY7JtDKnuTKXL9DfuGZ2w87ZhCTtMvD4F6keGHXGZ393HBvc9c8HvuCn"
BASE_URL = "https://nmt.instructure.com/api/v1"
headers = {"Authorization": f"Bearer {api_key}"}
LAST_TERM_ID = 43
COURSES_URL = f"{BASE_URL}/courses?per_page=100" #&enrollment_state=active


_last_update = 0
_cache_img = None

screen = ImageDrawer()


def render():
    global _last_update, _cache_img, BASE_URL, headers, COURSES_URL
    now = time.time()
    if _cache_img is None or now - _last_update >= 5 * 60:
        _last_update = now

        # Pull current canvas courses
        courses_response = requests.get(COURSES_URL, headers=headers)
        courses = courses_response.json()
        #courses = [c for c in courses if (c.get("id") is not None and c.get("id") == 35543)]
        random.shuffle(courses)
        courses = [c for c in courses if "Safety Training" not in c.get("name","")]
        

        # Pull semeser and time of year from course and display that
        first_course_name = courses[0]["name"]
        semester_year = first_course_name.split(" - ")[0] if " - " in first_course_name else ""
        screen.add_text([{"text":f"{semester_year}","size":26}], position=(0.5, 0.08), bold=True)

        # Add title text to canvas
        screen.add_text([{"text":"Canvas Courses","size":40}],position=(0.5, 0),bold=True)


        max_len = 14
        for idx, course in enumerate(courses[:10]):
            name = course["name"]
            remainder = name.split(" - ",1)[1] if " - " in name else name
            parts = remainder.split("-")
            code_parts = [p for p in parts[:3] if any(c.isalpha() or c.isdigit() for c in p)]
            code = "-".join(code_parts)
            title = "-".join(parts[len(code_parts):]).replace("&","& ").strip()
            words = title.split()
            lines, current = [], ""
            for w in words:
                if len(current + w) + (1 if current else 0) > max_len:
                    lines.append(current.strip())
                    current = w
                else:
                    current = current + " " + w if current else w
            if current: lines.append(current.strip())
            row,col = idx//5,idx%5
            screen.add_rectangle(position=(col*0.2+0.01,row*0.43+0.15), size=(0.18,0.39), fill=0, radius=15, thickness=2)
            screen.add_text([{"text":code,"size":14}], position=(col*0.2+0.1,row*0.43+0.16), bold=True)
            for i,l in enumerate(lines):
                font_size = 16 if len(lines) <= 3 else 14  # reduce font for very long titles
                screen.add_text([{"text":l,"size":font_size}], position=(col*0.2+0.1,row*0.43+0.45-0.05*(len(lines)-1-i)), bold=True)












        print("Your courses:")
        for course in courses: print(f"{course['id']}: {course['name']}")

        # Pull course assginments
        #for course in courses:
        #    assignments_url = f"{BASE_URL}/courses/{course['id']}/assignments?per_page=100"
        #    resp = requests.get(assignments_url, headers=headers)
        #    course_assignments = resp.json()

        # Filter only real, visible assignments
        #all_assignments = []
        #for a in course_assignments:
        #    points = a.get("points_possible", 0)
        #    muted = a.get("muted", False)
        #    published = a.get("workflow_state") == "published"

        #    if (points > 0) and not muted and published:
        #        # Keep course info if you want to display later
        #        a["course_name"] = course["name"]
        #        all_assignments.append(a)

        # Print filtered assignments
        #for a in all_assignments:
        #    print(f"{a['course_name']}: {a['name']} (Points: {a['points_possible']})")









        _cache_img=screen.render()
        if(_cache_img is None): return None, False
        else: return _cache_img, True 
    return _cache_img, False


# Image viewer script to run code without screen
def main():
    global _last_update
    _last_update=0
    img, show = render()
    img.show()

if __name__ == "__main__":
    main()