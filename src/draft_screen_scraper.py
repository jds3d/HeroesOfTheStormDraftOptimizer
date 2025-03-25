import time
import pyautogui
import pytesseract
from PIL import ImageGrab
import re

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


def right_click_view_profile(player_position, menu_offset):
    """Right-clicks on a player’s hexagon and selects 'View Profile' with specific offsets."""
    pyautogui.moveTo(player_position)
    pyautogui.rightClick()
    time.sleep(0.2)  # Wait for the menu to open
    pyautogui.moveRel(*menu_offset)  # Move to 'View Profile' with specific offset
    pyautogui.click()
    time.sleep(1.0)  # Wait for profile window to open


def extract_battletag():
    """Extracts the BattleTag from the profile window using OCR."""
    time.sleep(0.5)
    text = capture_screen_text()
    matches = re.findall(r'([A-Za-z0-9]+#\d{4,6})', text)  # Extracts text matching a BattleTag format
    print(matches[0])
    return matches[0] if matches else None

def get_battletags():
    """Extracts BattleTags for all 10 players using accurate percentage-based positions."""
    player_positions = [
        convert_percentage_to_position(0.0633, 0.1368),  # Blue team player 1 (top-left)
        convert_percentage_to_position(0.1141, 0.2993),
        convert_percentage_to_position(0.0656, 0.4528),
        convert_percentage_to_position(0.1242, 0.6250),
        convert_percentage_to_position(0.0586, 0.7639),  # Blue team player 5 (bottom-left)
        # convert_percentage_to_position(0.9375, 0.1389),  # Red team player 1 (top-right)
        # convert_percentage_to_position(0.8398, 0.2993),
        # convert_percentage_to_position(0.9375, 0.4528),
        # convert_percentage_to_position(0.8398, 0.6250),
        # convert_percentage_to_position(0.9375, 0.7639)  # Red team player 5 (bottom-right)
    ]

    menu_offsets = [
        (90, 170), (90, 160), (90, 160), (90, 170), (90, 10),  # Offsets for blue team
        # (-90, 120), (-90, 160), (-90, 160), (-90, 170), (-90, -10)  # Offsets for red team
    ]

    battletags = []
    for pos, offset in zip(player_positions, menu_offsets):
        right_click_view_profile(pos, offset)
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