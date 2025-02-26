from .create_multiple_profiles import create_multiple_profiles
from .launch_multiple_profiles import launch_multiple_profiles
from .manage_extensions import manage_extensions
from .run_chrome_scripts_on_multiple_profiles import run_chrome_scripts_on_multiple_profiles
from .run_manager_scripts_on_multiple_profiles import run_manager_scripts_on_multiple_profiles
from .show_all_profiles import show_all_profiles
from .update_comments import update_comments
from .run_scripts import (
    run_chrome_scripts,
    run_manager_scripts,
    run_chrome_scripts_on_multiple_profiles,
    run_manager_scripts_on_multiple_profiles
)
from src.utils.helpers import kill_chrome_processes
from src.utils.copy_extensions import copy_extensions_to_all_profiles

__all__ = [
    'launch_multiple_profiles',
    'create_multiple_profiles',
    'run_chrome_scripts',
    'run_manager_scripts',
    'run_chrome_scripts_on_multiple_profiles',
    'run_manager_scripts_on_multiple_profiles',
    'kill_chrome_processes',
    'copy_extensions_to_all_profiles'
]
