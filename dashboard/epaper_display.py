import spidev
import RPi.GPIO as GPIO
import time
from PIL import ImageOps,Image, ImageDraw, ImageFont

# Epaper display class for displaying data to the display
class EpaperDisplay(): 
    def __init__(self):
        # Screen size
        self.width=800
        self.height=480   
        self.buffer_length = self.width * self.height // 8   # screen buffer size 
        self.color_white=0x00
        self.color_black=0xFF

        # Startup display
        self.spi = spidev.SpiDev()           # Setup spi class
        self.spi.open(0, 0)                  # Set spi modes
        self.spi.max_speed_hz = 2_000_000    # Set max spi pin speed
        self.spi.mode = 0b00                 # Set clock mode

        # Setup used pi pins and initalize them
        self.DC_pin=25
        self.BUSY_pin=24
        self.RST_pin=17
        GPIO.setmode(GPIO.BCM)      
        GPIO.setup(self.DC_pin, GPIO.OUT)   
        GPIO.setup(self.RST_pin, GPIO.OUT)   
        GPIO.setup(self.BUSY_pin, GPIO.IN)     
    
    # Send data array to the display
    def data(self, data):
        GPIO.output(self.DC_pin, GPIO.HIGH)
        self.spi.writebytes([data])

    # Send command to the display to proform diffrent operations
    def cmd(self, data):
        GPIO.output(self.DC_pin, GPIO.LOW)
        self.spi.writebytes([data])

    # Wait until display is able to reacive data
    def wait_busy(self):
        while GPIO.input(self.BUSY_pin) == 1: time.sleep(0.05)

    # Initalize display for new usage
    def initalize_display(self):
        # Reset display for new use
        GPIO.output(self.RST_pin, GPIO.LOW)
        time.sleep(0.2)
        GPIO.output(self.RST_pin, GPIO.HIGH)
        time.sleep(0.2)

        # Configure display settings
        self.cmd(0x01) 
        self.data(0x07)
        self.data(0x07)
        self.data(0x3F)
        self.data(0x3F)
        self.cmd(0x04)
        self.wait_busy()
        self.cmd(0x00) 
        self.data(0x1F)
        self.cmd(0x61) 
        self.data(0x03)
        self.data(0x20)
        self.data(0x01)
        self.data(0xE0)
        self.cmd(0x15) 
        self.data(self.color_white)
    
    # Clear display by changing it to white
    def clear_display(self):
        self.cmd(0x13)
        for i in range(self.buffer_length): # Set every pixel to white
            self.data(self.color_white)
        self.cmd(0x12)                      # send display refresh command
        self.wait_busy()

    # Send image to display and then render whole image to display
    def display_image(self, img, threshold):
        img = img.convert("L").resize((self.width, self.height))
        img=ImageOps.invert(img)
        #self.clear_display()                                                   # Clear old images off display first
        #img = img.convert("L").resize((self.width, self.height))                # Convert image to grayscale 
        #img = img.point(lambda x: 0 if x < 128 else 255, "1")                   # Fit image to screen
        pixels = img.load()                                                     # Load image data and write image data into bytes then send to screen to display image
        self.cmd(0x13)
        for y in range(self.height):
            for x in range(0, self.width, 8):
                byte = self.color_black
                for bit in range(8):
                    if x + bit >= self.width:
                        continue
                    if pixels[x + bit, y] < threshold:
                        byte &= ~(1 << (7 - bit))
                self.data(byte)
        self.cmd(0x12)
        self.wait_busy()

    # Shutdown down display when it's no longer being used
    def shutdown_display(self):
        self.cmd(0x02)
        self.wait_busy()
        self.cmd(0x07)
        self.data(0xA5)
        self.spi.close()
        GPIO.cleanup()

# Image drawer to render things to screen
class ImageDrawer:
    def __init__(self, width=800, height=480, background=1):
        self.image = Image.new("1", (width, height), color=background) # Base image color
        self.width = width
        self.height = height
        self.commands = []

    # Add text to render que
    def add_text(self, text, position, font=None, size=12, fill=0, align="center", bold=False):
        if font is None: font = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        px = int(position[0] * self.width) if position[0] <= 1 else position[0]
        py = int(position[1] * self.height) if position[1] <= 1 else position[1]
        self.commands.append({"type": "text","text": text,"position": (px, py),"font_path": font,"fill": fill, "align": align, "bold": bold})

    # Add image to render que
    def add_image(self, img, position, size=None):
        px = int(position[0] * self.width) if position[0] <= 1 else position[0]
        py = int(position[1] * self.height) if position[1] <= 1 else position[1]
        # Convert size percentage to pixels if 0-1
        if size and size[0] <= 1 and size[1] <= 1:
            size = (int(size[0] * self.width), int(size[1] * self.height))
        self.commands.append({ "type": "image", "img": img, "position": (px, py), "size": size })

    # Add shape to render que
    def add_rectangle(self, position, size, fill=0, radius=0, thickness=None):
        px = int(position[0] * self.width) if position[0] <= 1 else position[0]
        py = int(position[1] * self.height) if position[1] <= 1 else position[1]
        # Convert size percentage to pixels if 0-1
        if size[0] <= 1 and size[1] <= 1:
            size = (int(size[0] * self.width), int(size[1] * self.height))
        self.commands.append({"type": "rectangle","position": (px, py),"size": size,"fill": fill,"radius": radius, "thickness": thickness})

    # Render diffrent data to display image
    def render(self):
        draw = ImageDraw.Draw(self.image)
        for cmd in self.commands:
            # Add text to screen, and align based and selected option
            if cmd["type"] == "text":
                x, y = cmd["position"]

                fonts = []
                widths = []
                heights = []
                ascents = []
                descents = []

                for block in cmd["text"]:
                    font_path = cmd["font_path"]
                    if cmd.get("bold", False):
                        font_path = font_path.replace(".ttf", "-Bold.ttf")
                    font = ImageFont.truetype(font_path, block.get("size", 12))
                    fonts.append(font)
                    w, h = font.getsize(block["text"])
                    ascent, descent = font.getmetrics()
                    widths.append(w)
                    heights.append(h)
                    ascents.append(ascent)
                    descents.append(descent)

                # Get the maximum ascent and descent among all text blocks
                max_ascent = max(ascents)
                max_descent = max(descents)
                max_total_height = max(heights)
                total_width = sum(widths)

                # Determine starting x for horizontal alignment
                if cmd["align"] == "center":
                    x_start = x - total_width // 2
                elif cmd["align"] == "right":
                    x_start = x - total_width
                else:  # left
                    x_start = x

                # Calculate reference positions
                # y is the TOP reference point for "top" alignment
                # y + max_total_height is the BOTTOM reference point for "bottom" alignment
                
                x_offset = 0
                for i, block in enumerate(cmd["text"]):
                    font = fonts[i]
                    t = block["text"]
                    ascent = ascents[i]
                    descent = descents[i]
                    h = heights[i]
                    
                    block_align = block.get("align", "middle")
                    
                    if block_align == "top":
                        # For "top" alignment: all text tops should be at y
                        # Baseline = y + ascent
                        baseline_y = y + ascent
                    elif block_align == "bottom":
                        # For "bottom" alignment: all text bottoms should be at y + max_total_height
                        # Baseline = (y + max_total_height) - descent
                        baseline_y = (y + max_total_height) - descent
                    else:  # middle/default
                        # For "middle" alignment: center vertically within max_total_height
                        # Baseline = y + max_total_height//2 - (descent - ascent)//2
                        baseline_y = y + max_total_height//2 - (descent - ascent)//2
                    
                    draw.text((x_start + x_offset, baseline_y), t, font=font, fill=cmd["fill"])
                    x_offset += widths[i]







            # Add image to screen
            elif cmd["type"] == "image":
                img = cmd["img"]
                if cmd["size"]:
                    img = img.resize(cmd["size"])
                self.image.paste(img, cmd["position"])
            # Draw rectangle to screen with rounded edges
            elif cmd["type"] == "rectangle":
                x, y = cmd["position"]
                w, h = cmd["size"]
                radius = cmd.get("radius", 0)
                fill = cmd.get("fill", 0)
                thickness = cmd.get("thickness")
                # If thickness is None draw solid rectangle like normal uing rounded function
                if thickness is None:
                    if radius > 0: draw.rounded_rectangle([x, y, x + w, y + h], radius=radius, fill=fill)
                    else: draw.rectangle([x, y, x + w, y + h], fill=fill)
                # If thickness is not solid draw 2 rectangles to produce a hollow rectangle
                else:
                    # If round rectangle is being drown
                    if radius > 0:
                        draw.rounded_rectangle([x, y, x + w, y + h], radius=radius, fill=fill)
                        ix, iy = x + thickness, y + thickness
                        iw, ih = w - (2 * thickness), h - (2 * thickness)
                        if iw > 0 and ih > 0: draw.rounded_rectangle([ix, iy, ix + iw, iy + ih], radius=max(0, radius - thickness), fill=1 - fill)
                    # If normal rectangle is being drown 
                    else:
                        draw.rectangle([x, y, x + w, y + h], fill=fill)
                        ix, iy = x + thickness, y + thickness
                        iw, ih = w - (2 * thickness), h - (2 * thickness)
                        if iw > 0 and ih > 0: draw.rectangle([ix, iy, ix + iw, iy + ih], fill=1 - fill)

        # Clear commands after render
        self.commands = []
        return self.image