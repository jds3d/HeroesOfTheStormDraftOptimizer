import os
import logging
import re
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

BATTLETAG_PATTERN = re.compile(r'([A-Za-z0-9]+#\d{4,6})')


class LiveMonitor:
    def __init__(self):
        self.battle_lobby_temp_path = os.getenv("TEMP")

        # Check multiple locations for Storm Save path
        default_storm_save_path = os.path.join(os.path.expanduser("~"), "Documents", "Heroes of the Storm", "Accounts")
        onedrive_storm_save_path = os.path.join(os.path.expanduser("~"), "OneDrive", "Documents", "Heroes of the Storm")

        self.storm_save_path = default_storm_save_path if os.path.exists(default_storm_save_path) else onedrive_storm_save_path

        self.battle_lobby_observer = None
        self.storm_save_observer = None

    def wait_for_file(self, file_path, timeout=5):
        """Waits for the file to be fully written before reading it."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                try:
                    with open(file_path, 'rb') as f:
                        f.read(1)  # Try to read a byte to check access
                    return True
                except PermissionError:
                    logger.warning(f"File is locked: {file_path}. Retrying...")
            time.sleep(0.5)
        return False

    def extract_battletags(self, file_path):
        """Extracts BattleTags from a given file."""
        if not self.wait_for_file(file_path):
            logger.error(f"File not available or locked: {file_path}")
            return

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                battletags = BATTLETAG_PATTERN.findall(content)
                if battletags:
                    logger.info(f"Extracted BattleTags from {file_path}: {battletags}")
                else:
                    logger.info(f"No BattleTags found in {file_path}")
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")

    def on_battle_lobby_added(self, event):
        if event.is_directory:
            return
        logger.debug(f"Detected new temp live replay: {event.src_path}")
        self.extract_battletags(event.src_path)

    def on_storm_save_added(self, event):
        if event.is_directory:
            return
        logger.debug(f"Detected new StormSave replay: {event.src_path}")
        self.extract_battletags(event.src_path)

    def start_battle_lobby(self):
        if not os.path.exists(self.battle_lobby_temp_path):
            logger.warning(f"Battle Lobby directory does not exist: {self.battle_lobby_temp_path}")
            return

        if not self.battle_lobby_observer:
            event_handler = FileSystemEventHandler()

            event_handler.on_created = self.on_battle_lobby_added

            self.battle_lobby_observer = Observer()
            self.battle_lobby_observer.schedule(event_handler, self.battle_lobby_temp_path, recursive=True)

            event_handler.event_handler.patterns = ['*.battlelobby']
            self.battle_lobby_observer.start()
            logger.debug("Started watching for new battlelobby")

    def start_storm_save(self):
        if not os.path.exists(self.storm_save_path):
            logger.warning(f"Storm Save directory does not exist: {self.storm_save_path}")
            return

        if not self.storm_save_observer:
            event_handler = FileSystemEventHandler()

            event_handler.on_created = self.on_storm_save_added

            self.storm_save_observer = Observer()
            self.storm_save_observer.schedule(event_handler, self.storm_save_path, recursive=True)

            event_handler.event_handler.patterns = ['*.StormSave']
            self.storm_save_observer.start()
            logger.debug("Started watching for new storm save")

    def stop_battle_lobby_watcher(self):
        if self.battle_lobby_observer:
            self.battle_lobby_observer.stop()
            self.battle_lobby_observer.join()
            self.battle_lobby_observer = None
            logger.debug("Stopped watching for new replays")

    def stop_storm_save_watcher(self):
        if self.storm_save_observer:
            self.storm_save_observer.stop()
            self.storm_save_observer.join()
            self.storm_save_observer = None
            logger.debug("Stopped watching for new storm save files")

    def is_battle_lobby_running(self):
        return self.battle_lobby_observer is not None

    def is_storm_save_running(self):
        return self.storm_save_observer is not None


if __name__ == "__main__":
    monitor = LiveMonitor()
    monitor.start_battle_lobby()
    monitor.start_storm_save()

    try:
        while True:
            pass
    except KeyboardInterrupt:
        monitor.stop_battle_lobby_watcher()
        monitor.stop_storm_save_watcher()
