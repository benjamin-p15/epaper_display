# Imports needed to run website dashboard and other used stuff
from flask import Flask, render_template, request
from PIL import Image
import threading
import time
import os

# Import classes to talk to epaper display and all of the modules
from epaper_display import EpaperDisplay
from modules.clock import main as clock
from modules.weather import main as weather

current_layout = "weather"
update_display = False

# Start website
def start_dashboard():
    # Setup a blank flask website
    app = Flask(__name__)

    # Register incomming web requests 
    @app.route("/")
    def index():
        return render_template("index.html")
    
    # Listions to website server state changes then triggers the state function 
    # which handles interactions
    @app.route("/set_layout", methods=["POST"])
    def set_layout():
        # When buttons are clicked saved thier changed state
        global current_layout
        layout = request.form.get("layout")
        if layout in ("time", "weather", "image"):
            current_layout = layout
            return f"Layout set to {layout}"
        return "Invalid layout", 400
    
    # Start the web server
    app.run(host="0.0.0.0", port=5000)




def display_loop(display):
    last_layout = None
    current_display = None

    while True:
        # react to current_layout
        global current_layout
        if current_layout != last_layout:    
            last_layout = current_layout
            current_display = None
        
        update_display = False

        # Update modual data
        if(current_layout=="weather"):
            img, update_display = weather.render()
            if update_display:
                current_display = img

        if(update_display): 
            display.display_image(current_display)

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