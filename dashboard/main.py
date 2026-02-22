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
from modules.image_display import main as image
from modules.grapher import main as grapher
from modules.analog_clock import main as analog_clock

current_layout = "clock"
update_state = False
image_threshold = 128
layouts=["clock", "weather", "image", "grapher", "analog_clock"]
ENABLE_WEB = False

# Start website
def start_dashboard():
    # Setup a blank flask website
    app = Flask(__name__)

    # Register incomming web requests 
    @app.route("/")
    def index():
        return render_template("index.html")
    
    # Listions to website server state changes then triggers the state function Which handles interactions
    @app.route("/set_layout", methods=["POST"])
    def set_layout():
        # When buttons are clicked saved thier changed state
        global current_layout, update_state
        layout = request.form.get("layout")
        if layout in layouts:
            current_layout = layout
            update_state = True
            return f"Layout set to {layout}"
        return "Invalid layout", 400
    
    # Images require a speical server state /display_image which it's interactions is handled here
    @app.route("/display_image", methods=["POST"])
    def download_image():
        global current_layout, update_state, image_threshold
        # If no image is sent, ir no file name is recived return error
        if "image" not in request.files:
            return "No image uploaded", 400
        file = request.files["image"]
        if file.filename == "":
            return "Empty filename", 400
        
        # Read threshold from the hidden input
        threshold_str = request.form.get("threshold")
        try:
            image_threshold = int(threshold_str)
        except ValueError:
            image_threshold = 128

        # Store image in memery for moduel to use, and update other required paremeters
        img = Image.open(file.stream).convert("1")
        image.set_image(img)     
        current_layout = "image" 
        update_state = True
        return "Image uploaded", 200
    
    # Start the web server
    app.run(host="0.0.0.0", port=5000, threaded=True)

# Check for display layout changes and run timmer circuits 
def display_loop(display):
    global weather
    last_layout = None
    current_display = None

    while True:
        # If layout changes refreash display
        global current_layout, update_state, image_threshold
        if current_layout != last_layout:    
            last_layout = current_layout
            current_display = None
        update_display = False

        # Depending on what layout is selected run indavidual classes which have thier own built in timing circuits
        # For images every time a new image is uplouded change image
        if(current_layout=="image"):
            if(update_state==True):
                update_state=False
                img, update_display = image.render()
                if update_display: current_display = img
        # Run weather time curcit
        elif(current_layout=="weather"):
            img, update_display = weather.render()
            if update_display: current_display = img
        # Run clock time curcit
        elif(current_layout=="clock"):
            img, update_display = clock.render()
            if update_display: current_display = img
        # Run analog clock curcit
        elif(current_layout=="analog_clock"):
            img, update_display = analog_clock.render()
            if update_display: current_display = img
        # Run Grapher time curcit
        elif(current_layout=="grapher"):
            img, update_display = grapher.render()
            if update_display: current_display = img

        # Update display if requested and wait before running check again
        if(update_display): display.display_image(current_display, image_threshold)
        time.sleep(1)

# Startup script when file is ran
def main():
    global weather, analog_clock
    # Initilize the Epaper display and it's helper class
    display = EpaperDisplay(800,480)
    weather = weather.weatherRender(display.width, display.height)
    analog_clock = analog_clock.analogClockRenderer(display.width, display.height)
    # Create background thread that starts and runs website
    if ENABLE_WEB: threading.Thread(target=start_dashboard, daemon=True).start()

    display_loop(display)

if __name__ == "__main__":
    main()