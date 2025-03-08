from random import shuffle

import questionary
from loguru import logger

from src.manager.manager import Manager
from .utils import select_profiles, custom_style


def run_manager_scripts_on_multiple_profiles(profiles=None, scripts=None, shuffle_scripts=False, gui_mode=False):
    """
    Запускает выбранные скрипты менеджера для выбранных профилей
    
    Args:
        profiles (list, optional): Список профилей для запуска. Если None, будет запрошен выбор через консоль.
        scripts (list, optional): Список скриптов для запуска. Если None, будет запрошен выбор через консоль.
        shuffle_scripts (bool, optional): Перемешать порядок скриптов. По умолчанию False.
        gui_mode (bool, optional): Режим работы через GUI. По умолчанию False.
        
    Returns:
        bool: True, если все скрипты выполнены успешно, иначе False
    """
    # Если не указаны профили, запрашиваем их через консоль
    if profiles is None:
        selected_profiles = select_profiles()
        if not selected_profiles:
            return False
    else:
        selected_profiles = profiles
    
    manager = Manager()
    
    # Если не указаны скрипты, запрашиваем их через консоль
    if scripts is None:
        scripts_dict = {
            value['human_name']: key
            for key, value in manager.scripts.items()
        }

        chosen_scripts_human_names = questionary.checkbox(
            "Выбери скрипты",
            choices=list(scripts_dict.keys()),
            style=custom_style
        ).ask()

        chosen_scripts = [scripts_dict[name] for name in chosen_scripts_human_names]
    else:
        chosen_scripts = scripts
    
    if not chosen_scripts:
        logger.warning('⚠️ Скрипты не выбраны')
        return False
    
    # Если не указано, перемешивать ли скрипты, и не в GUI-режиме, запрашиваем через консоль
    if len(chosen_scripts) > 1 and not gui_mode and shuffle_scripts is None:
        shuffle_choice = questionary.select(
            "Рандомить порядок выполнения скриптов?",
            choices=[
                '✅  да',
                '❌  нет'
            ],
            style=custom_style
        ).ask()

        shuffle_scripts = 'да' in shuffle_choice
    
    # Перемешиваем скрипты, если нужно
    if shuffle_scripts and len(chosen_scripts) > 1:
        shuffle(chosen_scripts)
    
    success = True
    
    # Запускаем скрипты для каждого профиля
    for name in selected_profiles:
        try:
            result = manager.run_scripts(
                str(name),
                chosen_scripts
            )
            if not result:
                success = False
        except Exception as e:
            logger.error(f"Ошибка при выполнении скриптов для профиля {name}: {e}")
            success = False
    
    return success
