import spidev
import RPi.GPIO as GPIO
import time
import sys

print("===== WAVESHARE 7.5\" DEBUG START =====", flush=True)

# ================= GPIO (BCM) =================
DC   = 25
RST  = 17
BUSY = 24

# ================= DISPLAY =================
WIDTH  = 800
HEIGHT = 480
BUF_LEN = WIDTH * HEIGHT // 8  # 48000

# ================= SPI =================
print("[1] SPI INIT", flush=True)
spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 2_000_000
spi.mode = 0b00
print("    SPI OK", flush=True)

# ================= GPIO =================
print("[2] GPIO INIT", flush=True)
GPIO.setmode(GPIO.BCM)
GPIO.setup(DC, GPIO.OUT)
GPIO.setup(RST, GPIO.OUT)
GPIO.setup(BUSY, GPIO.IN)
print("    GPIO OK", flush=True)

# ================= LOW LEVEL =================
def cmd(c):
    GPIO.output(DC, GPIO.LOW)
    spi.writebytes([c])
    print(f"CMD 0x{c:02X}", flush=True)

def data(d):
    GPIO.output(DC, GPIO.HIGH)
    spi.writebytes([d])

def wait_busy(tag=""):
    print(f"[BUSY] {tag}", flush=True)
    t0 = time.time()
    while GPIO.input(BUSY) == 1:
        if time.time() - t0 > 30:
            print("    BUSY TIMEOUT", flush=True)
            sys.exit(1)
        time.sleep(0.05)
    print("    BUSY RELEASED", flush=True)

# ================= RESET =================
print("[3] HARD RESET", flush=True)
GPIO.output(RST, GPIO.LOW)
time.sleep(0.2)
GPIO.output(RST, GPIO.HIGH)
time.sleep(0.2)
print("    RESET DONE", flush=True)

# ================= INIT (UC8179 / SSD1677) =================
print("[4] INIT SEQUENCE", flush=True)

cmd(0x01)          # POWER SETTING
data(0x07)
data(0x07)
data(0x3F)
data(0x3F)

cmd(0x04)          # POWER ON
wait_busy("POWER ON")

cmd(0x00)          # PANEL SETTING
data(0x1F)         # LUT from OTP, 480x800

cmd(0x61)          # RESOLUTION
data(0x03)         # 800 >> 8
data(0x20)         # 800 & 0xFF
data(0x01)         # 480 >> 8
data(0xE0)         # 480 & 0xFF

cmd(0x15)          # VCOM
data(0x00)

print("    INIT OK", flush=True)

# ================= FULL CLEAR =================
print("[5] FULL CLEAR (WHITE)", flush=True)

cmd(0x13)          # WRITE RAM
for i in range(BUF_LEN):
    if i % 4000 == 0:
        print(f"    DATA {i}/{BUF_LEN}", flush=True)
    data(0xFF)     # WHITE

cmd(0x12)          # DISPLAY REFRESH
wait_busy("REFRESH")

print("    CLEAR DONE", flush=True)

# ================= SLEEP =================
print("[6] SLEEP", flush=True)
cmd(0x02)          # POWER OFF
wait_busy("POWER OFF")
cmd(0x07)
data(0xA5)

# ================= CLEANUP =================
print("[7] CLEANUP", flush=True)
spi.close()
GPIO.cleanup()

print("===== DONE =====", flush=True)
