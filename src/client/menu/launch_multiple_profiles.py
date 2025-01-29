import concurrent.futures

from src.chrome.chrome import Chrome
from .utils import select_profiles


def launch_multiple_profiles():
    selected_profiles = select_profiles()
    if not selected_profiles:
        return

    chrome = Chrome()
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for name in selected_profiles:
            futures.append(executor.submit(
                chrome.launch_profile,
                str(name),
                False
            ))

        for future in concurrent.futures.as_completed(futures):
            future.result()
