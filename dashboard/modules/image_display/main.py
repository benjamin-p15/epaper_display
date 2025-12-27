from PIL import Image
import threading

_uploaded_image = None
_lock = threading.Lock()

def set_image(img: Image.Image):
    global _uploaded_image
    with _lock:
        _uploaded_image = img.copy()

def render():
    with _lock:
        if _uploaded_image is None:
            return None, False

        # Always return the current image
        return _uploaded_image, True
