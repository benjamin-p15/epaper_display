# modules/image_display/main.py
from PIL import Image
import threading

_uploaded_image = None
_lock = threading.Lock()

def set_image(img):
    global _uploaded_image
    with _lock:
        _uploaded_image = img.copy()

def render():
    with _lock:
        if _uploaded_image is None:
            return None, False
        return _uploaded_image, True
