import pytesseract
from PIL import ImageGrab


## This is for future functionality of live, on-screen suggestions.
def capture_screen_text():
    # Capture screen image and use OCR to interpret locked heroes
    screen_image = ImageGrab.grab()
    text = pytesseract.image_to_string(screen_image)
    return text
