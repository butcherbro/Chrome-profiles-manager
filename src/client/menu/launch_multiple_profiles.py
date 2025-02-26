from time import sleep

from src.chrome.chrome import Chrome
from .utils import select_profiles


def launch_multiple_profiles(profiles=None):
    """
    Запуск нескольких профилей Chrome
    
    Args:
        profiles: Список профилей для запуска. Если None, будет показано меню выбора.
    """
    if profiles is None:
        profiles = select_profiles()
        if not profiles:
            return
    
    launch_profiles(profiles)


def launch_profiles(profiles):
    """Запуск выбранных профилей Chrome"""
    chrome = Chrome()

    for name in profiles:
        chrome.launch_profile(
            str(name),
            debug=False,
            headless=False,
            maximized=False
        )
        sleep(0.5)

