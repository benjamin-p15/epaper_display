import requests, math, time, csv, os, datetime, sys, random, re
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
from zoneinfo import ZoneInfo
from dashboard.epaper_display import ImageDrawer
screen = ImageDrawer()

api_key = "2553~FvNmEDW7BY7JtDKnuTKXL9DfuGZ2w87ZhCTtMvD4F6keGHXGZ393HBvc9c8HvuCn"
BASE_URL = "https://nmt.instructure.com/api/v1"
headers = {"Authorization": f"Bearer {api_key}"}
LAST_TERM_ID = 43
COURSES_URL = f"{BASE_URL}/courses?per_page=100"


_last_update = 0
_cache_img = None

screen = ImageDrawer()


def render(force=False):
    global _last_update, _cache_img, BASE_URL, headers, COURSES_URL
    now = time.time()
    if force or (_cache_img is None or now - _last_update >= 30 * 60):
        _last_update = now

        # Pull all current canvas courses
        resp = requests.get(COURSES_URL, headers=headers)
        courses = resp.json()
        now = datetime.datetime.now(datetime.timezone.utc)
        current_term_id = None

        for c in courses:
            start = c.get("start_at")
            end = c.get("end_at")
            if start and end:
                start = datetime.datetime.fromisoformat(start.replace("Z","+00:00"))
                end = datetime.datetime.fromisoformat(end.replace("Z","+00:00"))
                if start <= now <= end:
                    current_term_id = c.get("enrollment_term_id")
                    break
        courses = [c for c in courses if c.get("enrollment_term_id") == current_term_id]

        # Get better course name
        def get_course_code(full_name):
            pattern = r"([A-Z]{2,4})[-/](\d{3,4}[A-Z]?)"
            match = re.search(pattern, full_name)
            if match: return f"{match.group(1)}-{match.group(2)}"
            else: return " ".join(full_name.split()[:3])

        # Get all feature assigments
        all_assignments = []
        now = datetime.datetime.now(datetime.timezone.utc)
        for course in courses:
            assignments_url = f"{BASE_URL}/courses/{course['id']}/assignments?per_page=100&include[]=submission"
            resp = requests.get(assignments_url, headers=headers)
            course_assignments = resp.json()
            for a in course_assignments:
                a["course_name"] = get_course_code(course["name"])
                due = a.get("due_at")
                if not due: continue
                due_time = datetime.datetime.fromisoformat(due.replace("Z","+00:00"))
                if due_time < now: continue
                submission = a.get("submission")
                if submission and submission.get("workflow_state") in ("submitted", "graded"): continue
                all_assignments.append(a)
        all_assignments.sort(key=lambda x: x["due_at"])

        # Assigment settings
        max_assignments = 8
        y_start = 0.15   
        y_gap = 0.10     
        font_size = 18
        max_line_length = 63  

        # Title at top
        screen.add_text([{"text":"Canvas Assigments","size":32}], position=(0.5, 0.03), bold=True)

        # Draw outer box around all assignments
        screen.add_rectangle(position=(0.01, y_start - 0.03), size=(0.98, 0.81), fill=None, radius=8, thickness=2)

        for idx, a in enumerate(all_assignments[:max_assignments]):
            due_time = datetime.datetime.fromisoformat(a['due_at'].replace("Z","+00:00"))
            due_str = due_time.strftime("%m/%d")
            y = y_start + idx * y_gap

            # Box/Text positions/sizes
            course_box_x = 0.015
            course_box_w = 0.17
            assignment_box_x = 0.19
            assignment_box_w = 0.705
            due_box_x = 0.9
            due_box_w = 0.084

            # Draw assigment boxes
            screen.add_rectangle(position=(course_box_x, y - 0.02), size=(course_box_w, y_gap - 0.01), fill=None, radius=4, thickness=2)
            screen.add_rectangle(position=(assignment_box_x, y - 0.02), size=(assignment_box_w, y_gap - 0.01), fill=None, radius=4, thickness=2)
            screen.add_rectangle(position=(due_box_x, y - 0.02), size=(due_box_w, y_gap - 0.01), fill=None, radius=4, thickness=2)

            # Course text
            screen.add_text([{"text": a['course_name'], "size": font_size}], position=(course_box_x + 0.01, y), align="left")

            # Assignment text (wrap max 2 lines)
            words = a['name'].split()
            lines = []
            current_line = ""
            for w in words:
                if len(current_line + " " + w) <= max_line_length:
                    current_line = (current_line + " " + w).strip()
                else:
                    lines.append(current_line)
                    current_line = w
            if current_line:
                lines.append(current_line)
            lines = lines[:2]

            for i, line in enumerate(lines):
                line_y = y - 0.01 if len(lines) == 2 else y
                screen.add_text([{"text": line, "size": font_size}], position=(assignment_box_x + 0.01, line_y + i * 0.03), align="left")

            # Due date text
            screen.add_text([{"text": due_str, "size": font_size}], position=(due_box_x + due_box_w - 0.01, y), align="right")

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