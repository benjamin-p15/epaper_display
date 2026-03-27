import requests, time, os, datetime, sys, re
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
from dashboard.epaper_display import ImageDrawer
screen = ImageDrawer()

# Api settings/paths
API_KEY = "2553~FvNmEDW7BY7JtDKnuTKXL9DfuGZ2w87ZhCTtMvD4F6keGHXGZ393HBvc9c8HvuCn"
BASE_URL = "https://nmt.instructure.com/api/v1"
HEADER = {"Authorization": f"Bearer {API_KEY}"}
LAST_TERM_ID = 43
COURSES_URL = f"{BASE_URL}/courses?per_page=100"

# Screen class and timing variables
_last_update = 0
screen = ImageDrawer()

# Screen render
def render(force=False):
    global _last_update, BASE_URL, HEADER, COURSES_URL
    # Update screen every 30 minutes or if otherwise requested
    now = time.time()
    if force or (now - _last_update >= 30 * 60): 
        _last_update = now

        # Pull all canvas courses and assiciated data
        request = requests.get(COURSES_URL, headers=HEADER)
        courses = request.json()
        now = datetime.datetime.now(datetime.timezone.utc)
        current_term_id = None

        # Look through all canvas courses, deleting any that have dates that are not concurrent. 
        for course in courses:
            start = course.get("start_at")
            end = course.get("end_at")
            if start and end:
                start = datetime.datetime.fromisoformat(start.replace("Z","+00:00"))
                end = datetime.datetime.fromisoformat(end.replace("Z","+00:00"))
                if start <= now <= end:
                    current_term_id = course.get("enrollment_term_id")
                    break
        courses = [course for course in courses if course.get("enrollment_term_id") == current_term_id]


        # Get all feature assigments
        all_assignments = []
        now = datetime.datetime.now(datetime.timezone.utc)
        for course in courses:
            # For list of current courses request all course assigments
            assignments_url = f"{BASE_URL}/courses/{course['id']}/assignments?per_page=100&include[]=submission"
            request = requests.get(assignments_url, headers=HEADER)
            course_assignments = request.json()

            # Look through assigments to pick out assigments the best assigments
            for assignment in course_assignments:
                # Find the MENG-####L course name, deleting the rest for displaying a clean course name
                pattern = r"([A-Z]{2,4})[-/](\d{3,4}[A-Z]?)"
                match = re.search(pattern, course["name"])
                if match: assignment["course_name"] = f"{match.group(1)}-{match.group(2)}"
                else: assignment["course_name"] = " ".join(course["name"].split()[:3])

                # Delete assigments which due dates has passed, or if assigment has been compleated
                due = assignment.get("due_at")
                if not due: continue
                due_time = datetime.datetime.fromisoformat(due.replace("Z","+00:00"))
                if due_time < now: continue
                assignment['due_at']=due_time
                submission = assignment.get("submission")
                if submission and submission.get("workflow_state") in ("submitted", "graded"): continue
                all_assignments.append(assignment)
        # Ensure due dates are orderd correctly
        all_assignments.sort(key=lambda x: x["due_at"])

        # Assigment boxes settings
        max_assignments = 8
        y_start = 0.15   
        y_gap = 0.10     
        font_size = 18
        max_line_length = 63  

        # Add top title text and rectangle around assigment boxes
        screen.add_text([{"text":"Canvas Assigments","size":32}], position=(0.5, 0.03), bold=True)
        #screen.add_rectangle(position=(0.01, y_start - 0.03), size=(0.98, 0.81), fill=None, radius=8, thickness=2)

        # Loop through next assigments and add next (max_assignments) to screen
        for idx, assignment in enumerate(all_assignments[:max_assignments]):
            # Reformat time into month/day, and calulate assigment box hight
            due_str = assignment['due_at'].strftime("%m/%d")
            y = y_start + idx * y_gap

            # Assigment boxes/text position/size settings
            course_box_x = 0.015
            course_box_w = 0.17
            assignment_box_x = 0.19
            assignment_box_w = 0.705
            due_box_x = 0.9
            due_box_w = 0.084

            # Draw three boxes, one around course name, assigment name, and due date 
            screen.add_rectangle(position=(course_box_x, y - 0.02), size=(course_box_w, y_gap - 0.01), fill=None, radius=4, thickness=2)
            screen.add_rectangle(position=(assignment_box_x, y - 0.02), size=(assignment_box_w, y_gap - 0.01), fill=None, radius=4, thickness=2)
            screen.add_rectangle(position=(due_box_x, y - 0.02), size=(due_box_w, y_gap - 0.01), fill=None, radius=4, thickness=2)

            # Add course name, and due date to screen
            screen.add_text([{"text": assignment['course_name'], "size": font_size}], position=(course_box_x + 0.01, y), align="left")
            screen.add_text([{"text": due_str, "size": font_size}], position=(due_box_x + due_box_w - 0.01, y), align="right")

            # Increment loop that adds words, counting characters spliting text into two lines if max_line_length is passed
            words = assignment['name'].split()
            lines = []
            current_line = ""
            for word in words:
                if len(current_line + " " + word) <= max_line_length: current_line = (current_line + " " + word).strip()
                else:
                    lines.append(current_line)
                    current_line = word
            if current_line: lines.append(current_line)
            lines = lines[:2]

            # For Add assigment to screen, if there are multiple text lines, add both with correct spacing 
            for i, line in enumerate(lines):
                line_y =y-0.01 if len(lines) == 2 else y
                screen.add_text([{"text": line, "size": font_size}], position=(assignment_box_x + 0.01, line_y + i * 0.03), align="left")

        # Screen render stuff
        _cache_img=screen.render()
        if(_cache_img is None): return None, False
        else: return _cache_img, True 
    return None, False


# Image viewer script to run code without screen
def main():
    global _last_update
    _last_update=0
    img, show = render()
    img.show()

if __name__ == "__main__":
    main()