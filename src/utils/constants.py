from sys import platform
from pathlib import Path
import os

# Определяем базовый путь в зависимости от ОС
if platform == "win32":
    BASE_PATH = Path(os.path.expandvars(r"%USERPROFILE%\Cursor\Chrome-profiles-manager"))
else:
    BASE_PATH = Path(os.path.expanduser("~/Python/Chrome-profiles-manager"))

DATA_PATH = BASE_PATH / "data"
CHROME_DATA_PATH = DATA_PATH / "profiles"
DEFAULT_EXTENSIONS_PATH = DATA_PATH / "default_extensions"
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe" if platform == "win32" else "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

chrome_driver_name = "chromedriver.exe" if platform == "win32" else "chromedriver"
CHROME_DRIVER_PATH = BASE_PATH / "src" / "chrome" / "scripts" / "drivers" / chrome_driver_name
PROFILE_WELCOME_PAGE_TEMPLATE_PATH = BASE_PATH / "src" / "client" / "template.html"
PROFILE_WELCOME_PAGES_OUTPUT_PATH = CHROME_DATA_PATH / "WelcomePages"

# Создаем директории, если они не существуют
DATA_PATH.mkdir(parents=True, exist_ok=True)
CHROME_DATA_PATH.mkdir(parents=True, exist_ok=True)
CHROME_DRIVER_PATH.parent.mkdir(parents=True, exist_ok=True)
