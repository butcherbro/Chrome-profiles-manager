import json
import shutil

import questionary
from loguru import logger

from src.utils.constants import *
from src.chrome.chrome import Chrome
from .utils import select_profiles, custom_style


def manage_extensions(chrome: Chrome):
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
        add_default_extensions(chrome, selected_profiles, False)
    elif 'добавить дефолтные с заменой' in extension_activity:
        add_default_extensions(chrome, selected_profiles, True)
    elif 'удалить расширения' in extension_activity:
        remove_extensions(chrome, selected_profiles)
    else:
        logger.warning('⚠️ Действие с расширениями не выбрано')
        return


def get_profiles_extensions_info(chrome: Chrome, profiles_list) -> dict[str, str]:
    extensions_info = {}
    for profile in profiles_list:
        profile_path = os.path.join(PROJECT_PATH, "data", "profiles", f"Profile {profile}")
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
    except (json.JSONDecodeError, OSError):
        return ''

def remove_extensions(chrome: Chrome, selected_profiles: list[str]) -> None:
    profiles_extension_info = get_profiles_extensions_info(chrome, selected_profiles)
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

        extensions_path = os.path.join(PROJECT_PATH, "data", "profiles", f"Profile {profile}", "Extensions")
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


def add_default_extensions(chrome: Chrome, selected_profiles: list[str], replace=False) -> None:
    default_extensions_info = get_all_default_extensions_info(chrome)
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

    selected_ids = [str(choice.split(" ")[0]) for choice in selected_extensions]

    if not selected_ids:
        logger.warning('⚠️ Расширения не выбраны')
        return

    for profile in selected_profiles:
        added_something = False
        profile_extensions_path = os.path.join(CHROME_DATA_PATH, f"Profile {profile}", "Extensions")
        os.makedirs(profile_extensions_path, exist_ok=True)

        for ext_id in selected_ids:
            src_path = os.path.join(DEFAULT_EXTENSIONS_PATH, ext_id)
            dest_path = os.path.join(profile_extensions_path, ext_id)

            if replace:
                is_replaced = False
                if os.path.exists(dest_path):
                    shutil.rmtree(dest_path)
                    is_replaced = True
                try:
                    shutil.copytree(src_path, dest_path)

                    if is_replaced:
                        logger.debug(f'{profile} - заменено расширение {ext_id}')
                    else:
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


def get_all_default_extensions_info(chrome: Chrome) -> dict[str, str]:
    extensions_info = {}
    default_extensions_path = os.path.join(PROJECT_PATH, "data", "default_extensions")
    for extension_id in os.listdir(default_extensions_path):
        extension_path = os.path.join(default_extensions_path, extension_id)
        if os.path.isdir(extension_path):
            name = get_extension_name(extension_path)
            extensions_info[extension_id] = name

    return extensions_info

