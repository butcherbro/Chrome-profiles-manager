import os
import shutil
import subprocess
from sys import stderr, platform, exit
import time
import socket
import threading
import re
import concurrent.futures
import json
from random import shuffle

from rich.table import Table
from rich.console import Console
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

        current_page += 1

    return selected_profiles


def get_all_sorted_profiles() -> list[str] | None:
    profiles_list = chrome.get_profiles_list()
    if not profiles_list:
        return

    numeric_profiles = [profile for profile in profiles_list if profile.isdigit()]
    non_numeric_profiles = [profile for profile in profiles_list if not any(char.isdigit() for char in profile)]
    numeric_profiles.sort(key=int)
    non_numeric_profiles.sort()

    profiles_list_sorted = numeric_profiles + non_numeric_profiles
    return profiles_list_sorted


def get_all_default_extensions_info() -> dict[str, str]:
    extensions_info = {}
    default_extensions_path = os.path.join(chrome.PROJECT_PATH, "data", "default_extensions")
    for extension_id in os.listdir(default_extensions_path):
        extension_path = os.path.join(default_extensions_path, extension_id)
        if os.path.isdir(extension_path):
            name = get_extension_name(extension_path)
            extensions_info[extension_id] = name

    return extensions_info


def get_profiles_extensions_info(profiles_list) -> dict[str, str]:
    extensions_info = {}
    for profile in profiles_list:
        profile_path = os.path.join(chrome.PROJECT_PATH, "data", "profiles", f"Profile {profile}")
        extensions_path = os.path.join(profile_path, "Extensions")
        if not os.path.isdir(extensions_path):
            continue

        for extension_id in os.listdir(extensions_path):
            extension_path = os.path.join(extensions_path, extension_id)
            if os.path.isdir(extension_path):
                name = get_extension_name(extension_path)
                extensions_info[extension_id] = name

    return extensions_info


def get_extension_name(extension_path: str) -> str:
    manifest_path = os.path.join(extension_path, "manifest.json")
    if os.path.isfile(manifest_path):
        return read_manifest_name(manifest_path)

    for subdir in os.listdir(extension_path):
        version_path = os.path.join(extension_path, subdir)
        if os.path.isdir(version_path):
            manifest_path = os.path.join(version_path, "manifest.json")
            if os.path.isfile(manifest_path):
                return read_manifest_name(manifest_path)

    return ''


def read_manifest_name(manifest_path: str) -> str:
    try:
        with open(manifest_path, 'r', encoding='utf-8') as file:
            manifest = json.load(file)

        return manifest.get("action", {}).get("default_title", "")
    except (json.JSONDecodeError, OSError) as e:
        return ''


def select_profiles() -> list[str] | None:
    profiles_list_sorted = get_all_sorted_profiles()
    if not profiles_list_sorted:
        logger.error("❌  Профиля отсутствуют")
        return

    select_options = [
        '📋 выбрать из списка',
        '🖐 вписать названия',
        '📒 выбрать по комментарию',
        '📦 выбрать все',
        '⬅️ назад'
    ]

    select_method = questionary.select(
        "Способ выбора профилей",
        choices=select_options,
        style=custom_style
    ).ask()

    if select_method == '⬅️ назад':
        return

    selected_profiles = []
    if select_method == '📋 выбрать из списка':
        selected_profiles = paginate_profiles(profiles_list_sorted)

    elif select_method == '🖐 вписать названия':
        names_raw = questionary.text(
            "Впиши названия профилей через запятую\n",
            style=custom_style
        ).ask()

        names = list(set(i.strip() for i in names_raw.split(',') if i.strip()))
        existing_profile_names = chrome.get_profiles_list()
        names_to_skip = [name for name in names if name not in existing_profile_names]

        if names_to_skip:
            logger.warning(f'⚠️ Пропускаем профиля {names_to_skip}, профиля не найдены')

        selected_profiles = [name for name in names if name not in names_to_skip]

    elif select_method == '📒 выбрать по комментарию':
        comment_substring = questionary.text(
            "Впиши текст, который должен содержать комментарий\n",
            style=custom_style
        ).ask()

        for profile in profiles_list_sorted:
            comments = get_comments_for_profiles()
            comment = comments.get(profile, '')
            if comment_substring.lower() in comment.lower() :
                selected_profiles.append(profile)

    elif select_method == '📦 выбрать все':
        selected_profiles = profiles_list_sorted

    if not selected_profiles:
        logger.warning("⚠️ Профиля не выбраны")
        return

    return selected_profiles


def get_comments_for_profiles() -> dict[str, str]:
    comments = {}
    try:
        with open('data/comments_for_profiles.json', 'r', encoding="utf-8") as f:
            comments = json.load(f)
    except FileNotFoundError:
        logger.warning("⚠️ Файл с комментариями не найден, комментарии не будут загружены.")
    except json.JSONDecodeError:
        logger.warning("⚠️ Не удалось прочитать файл с комментариями. Комментарии не будут загружены.")

    return comments


def launch_multiple_profiles():
    selected_profiles = select_profiles()
    if not selected_profiles:
        return

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for name in selected_profiles:
            futures.append(executor.submit(
                chrome.launch_profile,
                str(name),
            ))

        for future in concurrent.futures.as_completed(futures):
            future.result()


def run_scripts_on_multiple_profiles():
    selected_profiles = select_profiles()
    if not selected_profiles:
        return

    startup_scripts = {
        value['human_name']: key
        for key, value in chrome.automation_scripts.items()
    }

    chosen_startup_script_human_names = questionary.checkbox(
        "Выбери стартап скрипты",
        choices=list(startup_scripts.keys()),
        style=custom_style
    ).ask()

    chosen_startup_scripts = [startup_scripts[name] for name in chosen_startup_script_human_names]

    if not chosen_startup_scripts:
        logger.warning('⚠️ Скрипты не выбраны')
        return

    to_shuffle = False
    if len(chosen_startup_scripts) > 1:
        shuffle_choice = questionary.select(
            "Рандомить порядок выполнения скриптов?",
            choices=[
                '✅ да',
                '❌ нет'
            ],
            style=custom_style
        ).ask()

        to_shuffle = shuffle_choice == '✅ да'

    for name in selected_profiles:
        chrome.run_scripts(
            str(name),
            shuffle(chosen_startup_scripts) if to_shuffle else chosen_startup_scripts,
        )


def show_all_profiles():
    profiles_list_sorted = get_all_sorted_profiles()
    if not profiles_list_sorted:
        logger.error("❌  Профиля отсутствуют")
        return

    console = Console()
    table = Table(style="cyan")
    table.add_column("Название", style="magenta")
    table.add_column("Комментарии", style="green")

    comments = get_comments_for_profiles()
    for profile in profiles_list_sorted:
        comment = comments.get(profile, '')
        table.add_row(profile, comment)

    console.print(table)


def create_multiple_profiles():
    create_methods = [
        '🖐 задать вручную',
        '🤖 задать автоматически',
        '⬅️ назад'
    ]

    create_method = questionary.select(
        "Выбери способ создания имен",
        choices=create_methods,
        style=custom_style
    ).ask()

    if not create_method:
        logger.warning("⚠️ Активность не выбрана")
        return

    if create_method == '⬅️ назад':
        return

    existing_profile_names = chrome.get_profiles_list()

    profiles_to_create = []

    if create_method == '🖐 задать вручную':
        selected_names = questionary.text(
            "Впиши названия профилей через запятую\n",
            style=custom_style
        ).ask()
        selected_names = list(set(i.strip() for i in selected_names.split(',') if i.strip()))
        names_to_skip = list(set(existing_profile_names) & set(selected_names))

        if names_to_skip:
            logger.warning(f'⚠️ Пропускаем профиля {names_to_skip}, имена уже заняты')

        profiles_to_create = [item for item in selected_names if item not in names_to_skip]

    elif create_method == '🤖 задать автоматически':
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


def update_comments():
    selected_profiles = select_profiles()
    if not selected_profiles:
        return

    new_comment = questionary.text(
        "Впиши комментарий\n",
        style=custom_style
    ).ask()

    comments = get_comments_for_profiles()

    for profile in selected_profiles:
        comments[profile] = new_comment

    with open('data/comments_for_profiles.json', 'w', encoding="utf-8") as f:
        json.dump(comments, f, indent=4, ensure_ascii=False)


def manage_extensions():
    selected_profiles = select_profiles()
    if not selected_profiles:
        return

    extension_activity = questionary.select(
        "Выбери действие с расширениями",
        choices=[
            '🔸 добавить дефолтные без замены',
            '🔸 добавить дефолтные с заменой',
            '🔸 удалить расширения',
            '⬅️ назад'
        ],
        style=custom_style
    ).ask()

    if extension_activity == '⬅️ назад':
        return

    if 'добавить дефолтные без замены' in extension_activity:
        add_default_extensions(selected_profiles, False)
    elif 'добавить дефолтные с заменой' in extension_activity:
        add_default_extensions(selected_profiles, True)
    elif 'удалить расширения' in extension_activity:
        remove_extensions(selected_profiles)
    else:
        logger.warning('⚠️ Действие с расширениями не выбрано')
        return
    

def add_default_extensions(selected_profiles: list[str], replace=False) -> None:
    default_extensions_info = get_all_default_extensions_info()
    if not default_extensions_info:
        logger.warning('⚠️ Дефолтные расширения не найдены')
        return

    choices = [
        f"{ext_id} ({name})" if name else ext_id
        for ext_id, name in default_extensions_info.items()
    ]

    selected_extensions = questionary.checkbox(
        "Выбери расширения",
        choices=choices,
        style=custom_style
    ).ask()

    selected_ids = [choice.split(" ")[0] for choice in selected_extensions]

    if not selected_ids:
        logger.warning('⚠️ Расширения не выбраны')
        return

    for profile in selected_profiles:
        added_something = False
        profile_extensions_path = os.path.join(chrome.CHROME_DATA_PATH, f"Profile {profile}", "Extensions")
        os.makedirs(profile_extensions_path, exist_ok=True)

        for ext_id in selected_ids:
            src_path = os.path.join(chrome.DEFAULT_EXTENSIONS_PATH, ext_id)
            dest_path = os.path.join(profile_extensions_path, ext_id)

            if replace:
                if os.path.exists(dest_path):
                    shutil.rmtree(dest_path)
                    logger.debug(f'{profile} - заменено расширение {ext_id}')
                try:
                    shutil.copytree(src_path, dest_path)
                    logger.debug(f'{profile} - добавлено расширение {ext_id}')
                    added_something = True
                except Exception as e:
                    logger.error(f'❌ {profile} - не удалось добавить расширение {ext_id}')
                    logger.debug(f'{profile} - не удалось добавить расширение {ext_id}, причина: {e}')
            else:
                if os.path.exists(dest_path):
                    logger.debug(f'{profile} - расширение {ext_id} уже существует, пропущено')
                else:
                    try:
                        shutil.copytree(src_path, dest_path)
                        logger.debug(f'{profile} - добавлено расширение {ext_id}')
                        added_something = True
                    except Exception as e:
                        logger.error(f'❌ {profile} - не удалось добавить расширение {ext_id}')
                        logger.debug(f'{profile} - не удалось добавить расширение {ext_id}, причина: {e}')

        if added_something:
            logger.info(f'✅ {profile} - расширения добавлены')


def remove_extensions(selected_profiles: list[str]) -> None:
    profiles_extension_info = get_profiles_extensions_info(selected_profiles)
    if not profiles_extension_info:
        logger.warning('⚠️ Расширения в профилях не найдены')
        return

    choices = [
        f"{ext_id} ({name})" if name else ext_id
        for ext_id, name in profiles_extension_info.items()
    ]

    selected_extensions = questionary.checkbox(
        "Выбери расширения",
        choices=choices,
        style=custom_style
    ).ask()

    selected_ids = [choice.split(" ")[0] for choice in selected_extensions]

    if not selected_ids:
        logger.warning('⚠️ Расширения не выбраны')
        return

    for profile in selected_profiles:
        removed_something = False

        extensions_path = os.path.join(chrome.PROJECT_PATH, "data", "profiles", f"Profile {profile}", "Extensions")
        for ext_id in selected_ids:
            try:
                ext_path = os.path.join(extensions_path, ext_id)
                if os.path.isdir(ext_path):
                    shutil.rmtree(ext_path)
                    logger.debug(f'{profile} - расширение {ext_id} удалено')
                    removed_something = True
            except Exception as e:
                logger.error(f'❌ {profile} - не удалоcь удалить расширение {ext_id}')
                logger.debug(f'{profile} - не удалоcь удалить расширение {ext_id}, причина: {e}')

        if removed_something:
            logger.info(f'✅ {profile} - расширения удалены')


def quit_program():
    logger.info("Работа завершена")
    exit(0)


def main():
    main_activities_list = {
        '📖 просмотр профилей': show_all_profiles,
        '🚀 запуск профилей': launch_multiple_profiles,
        '🤖 прогнать скрипты': run_scripts_on_multiple_profiles,
        '🆕 создание профилей': create_multiple_profiles,
        '🧩 менеджер расширений': manage_extensions,
        '🖊 задать комментарии': update_comments,
        '🚪 выход': quit_program
    }

    while True:  # Infinite loop to keep menu open
        main_activity = questionary.select(
            "Выбери действие",
            choices=list(main_activities_list.keys()),
            style=custom_style
        ).ask()

        if not main_activity:
            quit_program()

        else:
            main_activities_list[main_activity]()
            continue


def main_test():
    chrome.run_scripts('1', ['run_omega_proxy_setup'])


if __name__ == '__main__':
    root_path = os.getcwd()
    chrome = Chrome(root_path)
    main()
    # main_test()
