# Imports needed to run website dashboard and other used stuff
from flask import Flask, render_template, request
from PIL import Image
import threading
import time
import os

# Import classes to talk to epaper display and all of the modules
from epaper_display import EpaperDisplay
from modules.clock import main as clock
from modules.weather import main2 as weather

def start_dashboard():
    # Setup a blank flask website
    app = Flask(__name__)
    current_layout = "none"

    # Register incomming web requests 
    @app.route("/")
    def index():
        return render_template("index.html")
    
    # Listions to website server state changes then triggers the state function 
    # which handles interactions
    @app.route("/set_layout", methods=["POST"])
    def set_layout():
        # When buttons are clicked saved thier changed state
        nonlocal current_layout
        layout = request.form.get("layout")
        if layout in ("time", "weather", "image"):
            current_layout = layout
            return f"Layout set to {layout}"
        return "Invalid layout", 400
    
    # Start the web server
    app.run(host="0.0.0.0", port=5000)

def display_loop(display):
    last_layout = None

    while True:
        global current_layout
        if current_layout != last_layout:
            print(current_layout)
            last_layout = current_layout
        # react to current_layout
        time.sleep(1)





# Startup script when file is ran
def main():
    # Initilize the Epaper display
    display = EpaperDisplay()
    display.initalize_display()
    
    # Create background thread that starts and runs website
    threading.Thread(target=start_dashboard, daemon=True).start()

    display_loop(display)

if __name__ == "__main__":
    main()