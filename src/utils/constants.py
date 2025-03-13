from sys import platform
from pathlib import Path


current_file = Path(__file__).resolve()
current_dir = current_file.parent
chrome_driver_name = "chromedriver.exe" if platform == "win32" else "chromedriver"

PROJECT_PATH = current_dir.parents[1]
DATA_PATH = PROJECT_PATH / "data"
CHROME_DATA_PATH = DATA_PATH / "profiles"
DEFAULT_EXTENSIONS_PATH = DATA_PATH / "default_extensions"
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe" if platform == "win32" else "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
CHROME_DRIVER_PATH = PROJECT_PATH / "src" / "chrome" / "scripts" / chrome_driver_name
PROFILE_WELCOME_PAGE_TEMPLATE_PATH = PROJECT_PATH / "src" / "client" / "template.html"
PROFILE_WELCOME_PAGES_OUTPUT_PATH = CHROME_DATA_PATH / "WelcomePages"

# ID расширений
METAMASK_ID = "nkbihfbeogaeaoehlefnkodbefgpgknn"
