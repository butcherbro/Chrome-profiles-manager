import os
from sys import platform
from pathlib import Path

current_file = Path(__file__).resolve()
current_dir = os.path.dirname(current_file)
PROJECT_PATH = os.path.abspath(os.path.join(current_dir, "..", ".."))  # TODO: should be better way
DATA_PATH = os.path.join(PROJECT_PATH, "data")
CHROME_DATA_PATH = os.path.join(DATA_PATH, "profiles")
DEFAULT_EXTENSIONS_PATH = os.path.join(PROJECT_PATH, "data", "default_extensions")
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe" if platform == "win32" else "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

chrome_driver_name = "chromedriver.exe" if platform == "win32" else "chromedriver"
CHROME_DRIVER_PATH = os.path.join(PROJECT_PATH, "src", "chrome", "scripts", chrome_driver_name)

PROFILE_WELCOME_PAGE_TEMPLATE_PATH = os.path.join(PROJECT_PATH, "src", "client", "template.html")
PROFILE_WELCOME_PAGES_OUTPUT_PATH = os.path.join(CHROME_DATA_PATH, "WelcomePages")