import pytesseract
from PIL import ImageGrab

def capture_screen_text():
    # Capture screen image and use OCR to interpret locked heroes
    screen_image = ImageGrab.grab()
    text = pytesseract.image_to_string(screen_image)
    return text
