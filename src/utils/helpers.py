from src.utils.constants import *


def get_profiles_list() -> list[str]:
    profiles = []
    for item in os.listdir(CHROME_DATA_PATH):
        item_path = os.path.join(CHROME_DATA_PATH, item)

        if os.path.isdir(item_path) and item.startswith("Profile"):
            profiles.append(item.replace('Profile ', ''))

    return profiles