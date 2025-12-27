import spidev
import RPi.GPIO as GPIO
import time

# Epaper display class for displaying data to the display
class EpaperDisplay(): 
    def __init__(self):
        # Screen size
        self.width=800
        self.height=480   
        self.buffer_length = self.width * self.height // 8   # screen buffer size 

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
        self.data(0x00)
    
    # Clear display by changing it to white
    def clear_display(self):
        self.cmd(0x13)
        for i in range(self.buffer_length): # Set every pixel to white
            self.data(0xFF)
        self.cmd(0x12)                      # send display refresh command
        self.wait_busy()

    # Send image to display and then render whole image to display
    def display_image(self, img):
        self.clear_display()                                        # Clear old images off display first
        img = img.convert("L").resize((self.width, self.height))    # Convert image to grayscale 
        img = img.point(lambda x: 0 if x > 128 else 255, mode="1")  # Fit image to screen
        pixels = img.load()                                         # Load image data and write image data into bytes then send to screen to display image
        self.cmd(0x13)
        for y in range(self.height):
            for x in range(0, self.width, 8):
                byte = 0xFF
                for bit in range(8):
                    if pixels[x + bit, y] == 0:
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