import spidev
import RPi.GPIO as GPIO
import time
from PIL import Image

# Setup used pins, screen size, and buffer size
DC, RST, BUSY = 25, 17, 24
WIDTH, HEIGHT = 800, 480
BUF_LEN = WIDTH * HEIGHT // 8

# Startup display
spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 2_000_000
spi.mode = 0b00

# Set screen settings
GPIO.setmode(GPIO.BCM)
GPIO.setup(DC, GPIO.OUT)
GPIO.setup(RST, GPIO.OUT)
GPIO.setup(BUSY, GPIO.IN)

# Send command to display
def cmd(data):
    GPIO.output(DC, GPIO.LOW)
    spi.writebytes([data])

# Send data to the display
def data(data):
    GPIO.output(DC, GPIO.HIGH)
    spi.writebytes([data])

# Busy pin detector, to delay code
def wait_busy():
    while GPIO.input(BUSY) == 1:
        time.sleep(0.05)

# Initilize display and reset it
def init_display():
    GPIO.output(RST, GPIO.LOW)
    time.sleep(0.2)
    GPIO.output(RST, GPIO.HIGH)
    time.sleep(0.2)

    cmd(0x01); data(0x07); data(0x07); data(0x3F); data(0x3F)
    cmd(0x04); wait_busy()
    cmd(0x00); data(0x1F)
    cmd(0x61); data(0x03); data(0x20); data(0x01); data(0xE0)
    cmd(0x15); data(0x00)

# Clear whole display
def clear_display():
    cmd(0x13)
    for i in range(BUF_LEN):
        data(0xFF)
    cmd(0x12)
    wait_busy()

# Write image to display
def display_image(img: Image.Image):
    img = img.convert("L").resize((WIDTH, HEIGHT))
    img = img.point(lambda x: 0 if x > 128 else 255, mode="1")
    pixels = img.load()
    cmd(0x13)
    for y in range(HEIGHT):
        for x in range(0, WIDTH, 8):
            byte = 0xFF
            for bit in range(8):
                if pixels[x + bit, y] == 0:
                    byte &= ~(1 << (7 - bit))
            data(byte)
    cmd(0x12)
    wait_busy()

# Shutdown display power while not in use
def sleep_display():
    cmd(0x02); wait_busy()
    cmd(0x07); data(0xA5)
    spi.close()
    GPIO.cleanup()