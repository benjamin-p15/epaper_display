import spidev
try: import RPi.GPIO as GPIO
except: pass

import time
from PIL import ImageOps,Image, ImageDraw, ImageFont

# Epaper display class for displaying data to the display
class EpaperDisplay: 
    def __init__(self, width: int=800, height: int=480):
        # Screen size
        self.width=width
        self.height=height
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
        #GPIO.setmode(GPIO.BCM)      
        GPIO.setup(self.DC_pin, GPIO.OUT)   
        GPIO.setup(self.RST_pin, GPIO.OUT)   
        GPIO.setup(self.BUSY_pin, GPIO.IN)     
        self.initalize_display()

    def scale(self) -> float:
        return self.width/self.height
    
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

# Image drawer to render things to an image that can be render to the screen
class ImageDrawer:
    def __init__(self, width=800, height=480, background=1):
        self.background=background
        self.image = Image.new("1", (width, height), color=background) # Base image color
        self.width = width
        self.height = height
        self.commands = []

    # Add text to render que
    def add_text(self, text, position, font=None, size=12, fill=0, align="center", bold=False, stroke_fill=1, stroke_width=0):
        if font is None: font = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        px = int(position[0] * self.width) if position[0] <= 1 else position[0]
        py = int(position[1] * self.height) if position[1] <= 1 else position[1]
        self.commands.append({"type": "text","text": text,"position": (px, py),"font_path": font,"fill": fill, "align": align, "bold": bold, "size": size, "stroke_fill": stroke_fill, "stroke_width": stroke_width})

    # Add image to render que
    def add_image(self, img, position, size=None, invert=False, color_black=False):
        px = int(position[0] * self.width) if position[0] <= 1 else int(position[0])
        py = int(position[1] * self.height) if position[1] <= 1 else int(position[1])
        img = Image.open(img)
        if(invert==True): img=ImageOps.invert(img.convert("RGB"))
        # Shading option
        if color_black:
            img=img.convert("RGBA")
            pixels = img.load()
            w,h = img.size
            for y in range(h):
                for x in range(w):
                    r,g,b,a = pixels[x,y]
                    if a > 0 and (r,g,b) != (255,255,255):
                        pixels[x,y] = (0,0,0,a)
        # Convert size percentage to pixels if 0-1
        if size and size[0] <= 1 and size[1] <= 1:
            size = (int(size[0] * self.width), int(size[1] * self.height))
        self.commands.append({ "type": "image", "img": img, "position": (px, py), "size": size })

    # Add rectangle to render que
    def add_rectangle(self, position, size, fill=0, radius=0, thickness=None):
        px = int(position[0] * self.width) if position[0] <= 1 else position[0]
        py = int(position[1] * self.height) if position[1] <= 1 else position[1]
        # Convert size percentage to pixels if 0-1
        if size[0] <= 1 and size[1] <= 1:
            size = (int(size[0] * self.width), int(size[1] * self.height))
        self.commands.append({"type": "rectangle","position": (px, py),"size": size,"fill": fill,"radius": radius, "thickness": thickness})

    # Add line to render que
    def add_line(self, start, end, fill=0, thickness=1):
        x1 = int(start[0] * self.width) if start[0] <= 1 else int(start[0])
        y1 = int(start[1] * self.height) if start[1] <= 1 else int(start[1])
        x2 = int(end[0] * self.width) if end[0] <= 1 else int(end[0])
        y2 = int(end[1] * self.height) if end[1] <= 1 else int(end[1])
        self.commands.append({"type": "line","start": (x1, y1),"end": (x2, y2),"fill": fill,"thickness": thickness})

    # Add circle to render que
    def add_circle(self, center, radius, fill=0, thickness=1):
        cx = int(center[0] * self.width) if center[0] <= 1 else int(center[0])
        cy = int(center[1] * self.height) if center[1] <= 1 else int(center[1])
        r = int(radius * min(self.width, self.height)) if radius <= 1 else int(radius)
        self.commands.append({"type": "circle","center": (cx, cy),"radius": r,"fill": fill,"thickness": thickness})

    # Render diffrent data to display image
    def render(self):
        draw = ImageDraw.Draw(self.image)
        for cmd in self.commands:
            # Add text to screen, and align based and selected options
            if cmd["type"]=="text":
                # variables used to algin text
                x,y=cmd["position"]
                fonts=[]; text_sizes=[]
                max_height=0; max_ascent=0; total_width=0

                # Loop through array to display all text
                for element in cmd["text"]:
                    font_path=cmd["font_path"]
                    # If text is set as bold switch to bold font
                    if cmd.get("bold",False): font_path=font_path.replace(".ttf","-Bold.ttf")

                    # Create font object of certain size, and look all text sizes
                    font=ImageFont.truetype(font_path,element.get("size",12))
                    fonts.append(font)
                    #w,h=font.getsize(element["text"])
                    bbox = font.getbbox(element["text"])
                    w = bbox[2] - bbox[0]
                    h = bbox[3] - bbox[1]

                    ascent, descent = font.getmetrics()
                    text_sizes.append({"width": w, "height": h, "ascent": ascent, "descent": descent})

                    # Find the maximum font being displayed 
                    if(ascent>max_ascent): max_ascent=ascent
                    if(descent>max_ascent): max_ascent=descent
                    if(h>max_height): max_height=h
                    total_width+=w

                # Shift text to align it to correct location
                if cmd["align"]=="center": x_start=x-total_width//2
                elif cmd["align"]=="right": x_start=x-total_width
                else: x_start=x

                x_offset=0
                for i,text_element in enumerate(cmd["text"]):
                    # get element alginment data
                    element_height=text_sizes[i]["height"]
                    element_alignment=text_element.get("align","middle")
                    # Figure out where to draw next text element, no clue why /4 works
                    if element_alignment=="top": draw_y = y-max_height/2-element_height/4
                    elif element_alignment=="bottom": draw_y = y + (max_ascent - text_sizes[i]["ascent"])
                    else:draw_y=y+(max_height-element_height)//2
                    # Draw text and record it's size for next alginment
                    draw.text((x_start+x_offset,draw_y),text_element["text"],font=fonts[i],fill=cmd["fill"],stroke_fill=cmd["stroke_fill"],stroke_width=cmd["stroke_width"])
                    x_offset+=text_sizes[i]["width"]
            # Add image to screen
            elif cmd["type"] == "image":
                img = cmd["img"]
                if cmd["size"]:
                    img = img.resize(cmd["size"])
                self.image.paste(img, cmd["position"])
            # Draw rectangle to screen with rounded edges
            elif cmd["type"] == "rectangle":
                # Get rectangle variables
                x, y = cmd["position"]
                w, h = cmd["size"]
                radius = cmd.get("radius", 0)
                fill = cmd.get("fill", 0)
                thickness = cmd.get("thickness")

                # If rectangle has no thickness draw solid rectangle 
                if thickness is None:
                    # Use diffrent draw commands depending on if a rounded corner is being drawn
                    if radius > 0: draw.rounded_rectangle([x, y, x + w, y + h], radius=radius, fill=fill)
                    else: draw.rectangle([x, y, x + w, y + h], fill=fill)

                # If rectangle has a thickness draw hollow rectangle 
                else:
                    # Use diffrent draw commands depending on if a rounded corner is being drawn
                    if radius > 0: draw.rounded_rectangle([x, y, x + w, y + h], radius=radius, outline=fill, width=thickness)
                    else:draw.rectangle([x, y, x + w, y + h], outline=fill, width=thickness)
            # Draws a line between two points
            elif cmd["type"] == "line":
                x1, y1 = cmd["start"]
                x2, y2 = cmd["end"]
                fill = cmd.get("fill", 0)
                thickness = cmd.get("thickness", 1)
                draw.line([(x1, y1), (x2, y2)],fill=fill,width=thickness)
            # Draws a circle at a location
            elif cmd["type"] == "circle":
                cx, cy = cmd["center"]
                r = cmd["radius"]
                fill = cmd.get("fill", 0)
                thickness = cmd.get("thickness", 1)
                # -1 draw filled circle
                if thickness <= 0:  draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], fill=fill)
                else: draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], outline=fill, width=thickness)

        # Clear commands after render
        self.commands = []
        image = self.image
        self.image = Image.new("1", (self.width, self.height), color=self.background) # Base image color
        return image