import os
import shutil
import subprocess
from sys import stderr, platform, exit
import time
import socket
import threading
import re

import questionary
from loguru import logger

from config import general_config
from src.chrome.chrome import Chrome

logger.remove()
logger_level = "DEBUG" if general_config['show_debug_logs'] else "INFO"
log_format = "<white>{time:HH:mm:ss}</white> | <level>{level: <8}</level> | <white>{message}</white>"
logger.add(stderr, level=logger_level, format=log_format)
logger.add("data/debug_log.log", level="DEBUG", format=log_format)

custom_style = questionary.Style([
    # ('qmark', 'fg:#00ff00 bold'),
    ('question', 'bold'),
    ('answer', 'fg:#ff9900 bold'),
    ('pointer', 'fg:#ff9900 bold'),
    ('text', 'fg:#4d4d4d'),
    ('disabled', 'fg:#858585 italic')
])


def paginate_profiles(profiles, items_per_page=10):
    total_pages = (len(profiles) + items_per_page - 1) // items_per_page
    current_page = 0
    selected_profiles = []

    while current_page < total_pages:
        start = current_page * items_per_page
        end = min(start + items_per_page, len(profiles))
        page_profiles = profiles[start:end]

        selected_profiles_on_page = questionary.checkbox(
            f"Выбери профиля для запуска (страница {current_page + 1} из {total_pages})",
            choices=page_profiles,
            style=custom_style,
        ).ask()

        selected_profiles.extend(selected_profiles_on_page)

        # Добавляем выбранные на текущей странице профили

        current_page += 1

    return selected_profiles


def launch_multiple_profiles():
    profiles_list = chrome.get_profiles_list()
    if not profiles_list:
        logger.error("❌  Профиля отсутствуют")
        return

    numeric_profiles = [profile for profile in profiles_list if profile.isdigit()]
    non_numeric_profiles = [profile for profile in profiles_list if not any(char.isdigit() for char in profile)]
    numeric_profiles.sort(key=int)
    non_numeric_profiles.sort()

    profiles_list_sorted = numeric_profiles + non_numeric_profiles

    selected_profiles = paginate_profiles(profiles_list_sorted)

    if not selected_profiles:
        logger.warning("⚠️ Профиля не выбраны")
        return

    # TODO: get them from chrome object
    startup_scripts = {
        'Первичная настройка Chrome': 'run_initial_setup',
        # 'Настройка Omega Proxy': 'run_omega_proxy_setup',
    }

    chosen_startup_script_human_names = questionary.checkbox(
        "Выбери стартап скрипты",
        choices=list(startup_scripts.keys()),
        style=custom_style
    ).ask()

    chosen_startup_scripts = [startup_scripts[name] for name in chosen_startup_script_human_names]

    for name in selected_profiles:
        chrome.launch_profile(
            str(name),
            chosen_startup_scripts,
            True if len(chosen_startup_scripts) > 0 else False
        )


def create_multiple_profiles():
    create_methods = [
        'ручные имена',
        'автоматические имена',
        '<- назад'
    ]

    create_method = questionary.select(
        "Выбери способ создания имен",
        choices=create_methods,
        style=custom_style
    ).ask()

    if not create_method:
        logger.warning("⚠️ Активность не выбрана")
        return

    if create_method == '<- назад':
        return

    existing_profile_names = chrome.get_profiles_list()

    profiles_to_create = []

    if create_method == 'ручные имена':
        selected_names = questionary.text(
            "Впиши названия профилей через запятую\n",
            style=custom_style
        ).ask()
        selected_names = list(set(i.strip() for i in selected_names.split(',') if i.strip()))
        names_to_skip = list(set(existing_profile_names) & set(selected_names))

        if names_to_skip:
            logger.warning(f'⚠️ Пропускаем профиля {names_to_skip}, имена уже заняты')

        profiles_to_create = [item for item in selected_names if item not in names_to_skip]

    elif create_method == 'автоматические имена':
        amount = questionary.text(
            "Впиши количество профилей для создания\n",
            style=custom_style
        ).ask()

        try:
            amount = int(amount)
        except ValueError:
            logger.warning('⚠️ Неверное количество')
            return

        highest_existing_numeric_name = 0

        for name in existing_profile_names:
            try:
                num = int(name)
                if num > highest_existing_numeric_name:
                    highest_existing_numeric_name = num
            except ValueError:
                continue

        start = highest_existing_numeric_name + 1
        profiles_to_create = list(range(start, start + amount))

    for name in profiles_to_create:
        chrome.create_new_profile(str(name))


def quit_program():
    logger.info("Работа завершена")
    exit(0)


def main():
    main_activities_list = {
        '🚀 запуск профилей': launch_multiple_profiles,
        '🤖 создание профилей': create_multiple_profiles,
        '🚪 выход': quit_program
    }

    while True:  # Infinite loop to keep menu open
        main_activity = questionary.select(
            "🔧 Выбери действие",
            choices=list(main_activities_list.keys()),
            style=custom_style
        ).ask()

        if not main_activity:
            logger.warning("⚠️ Активность не выбрана")
            continue

        else:
            main_activities_list[main_activity]()
            continue


if __name__ == '__main__':
    root_path = os.getcwd()
    chrome = Chrome(root_path)
    main()
