from src.chrome.chrome import Chrome
from src.scripts.chrome_scripts import run_scripts as run_chrome_scripts_impl
from src.scripts.manager_scripts import run_scripts as run_manager_scripts_impl
from .utils import select_profiles


def run_chrome_scripts_on_multiple_profiles():
    """Запуск Chrome скриптов на нескольких профилях"""
    selected_profiles = select_profiles()
    if not selected_profiles:
        return
    
    run_chrome_scripts(selected_profiles)


def run_manager_scripts_on_multiple_profiles():
    """Запуск скриптов менеджера на нескольких профилях"""
    selected_profiles = select_profiles()
    if not selected_profiles:
        return
    
    run_manager_scripts(selected_profiles)


def run_chrome_scripts(profiles):
    """Запуск Chrome скриптов на выбранных профилях"""
    chrome = Chrome()
    for name in profiles:
        run_chrome_scripts_impl(chrome, str(name))


def run_manager_scripts(profiles):
    """Запуск скриптов менеджера на выбранных профилях"""
    chrome = Chrome()
    for name in profiles:
        run_manager_scripts_impl(chrome, str(name)) 