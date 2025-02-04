from time import sleep
import concurrent.futures

from src.chrome.chrome import Chrome
from .utils import select_profiles


def launch_multiple_profiles():
    selected_profiles = select_profiles()
    if not selected_profiles:
        return

    chrome = Chrome()

    for name in selected_profiles:
        chrome.launch_profile(
            str(name),
            debug=False,
            headless=False,
            maximized=False
        )

        sleep(0.5)

