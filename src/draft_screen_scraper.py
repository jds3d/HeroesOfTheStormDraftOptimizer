import time
import pyautogui
import pytesseract
from PIL import ImageGrab


def get_screen_size():
    """Returns the screen width and height."""
    return pyautogui.size()


def convert_percentage_to_position(x_percent, y_percent):
    """Converts percentage-based coordinates to absolute screen positions."""
    screen_width, screen_height = get_screen_size()
    return int(screen_width * x_percent), int(screen_height * y_percent)


def capture_screen_text():
    """Captures the screen and extracts text using OCR."""
    screen_image = ImageGrab.grab()
    return pytesseract.image_to_string(screen_image)


def right_click_view_profile(player_position):
    """Right-clicks on a player’s hexagon and selects 'View Profile'."""
    pyautogui.moveTo(player_position)
    pyautogui.rightClick()
    time.sleep(0.5)  # Wait for the menu to open
    pyautogui.moveRel(0, 50)  # Move to 'View Profile' (assumed position)
    pyautogui.click()
    time.sleep(1.5)  # Wait for profile window to open


def extract_battletag():
    """Extracts the BattleTag from the profile window using OCR."""
    time.sleep(0.5)
    screen_width, screen_height = get_screen_size()
    bbox = (int(screen_width * 0.35), int(screen_height * 0.15), int(screen_width * 0.65), int(screen_height * 0.2))
    profile_image = ImageGrab.grab(bbox=bbox)  # Adjusted to percentage-based location
    battletag = pytesseract.image_to_string(profile_image).strip()
    if "#" in battletag:
        return battletag
    return None


def get_battletags():
    """Extracts BattleTags for all 10 players using accurate percentage-based positions."""
    player_positions = [
        convert_percentage_to_position(0.0633, 0.1368),  # Blue team player 1 (top-left)
        convert_percentage_to_position(0.1141, 0.2993),
        convert_percentage_to_position(0.0656, 0.4528),
        convert_percentage_to_position(0.1242, 0.6250),
        convert_percentage_to_position(0.0586, 0.7639),  # Blue team player 5 (bottom-left)
        convert_percentage_to_position(0.9375, 0.1389),  # Red team player 1 (top-right)
        convert_percentage_to_position(0.8398, 0.2993),
        convert_percentage_to_position(0.9375, 0.4528),
        convert_percentage_to_position(0.8398, 0.6250),
        convert_percentage_to_position(0.9375, 0.7639)  # Red team player 5 (bottom-right)
    ]

    battletags = []
    for pos in player_positions:
        right_click_view_profile(pos)
        tag = extract_battletag()
        if tag:
            battletags.append(tag)
        pyautogui.press('esc')  # Close the profile window
        time.sleep(0.5)
    return battletags[:5], battletags[5:]


def main():
    print("Extracting BattleTags...")
    team_1, team_2 = get_battletags()
    print(f"Team 1 BattleTags: {team_1}")
    print(f"Team 2 BattleTags: {team_2}")
    # Now you can pass these lists to draft.py


if __name__ == "__main__":
    main()
