import json
import shutil
import os
from concurrent.futures import ThreadPoolExecutor

import questionary
from loguru import logger

from config import general_config
from src.utils.helpers import get_all_default_extensions_info, get_profiles_extensions_info, copy_extension
from src.utils.constants import *
from .utils import select_profiles, custom_style


def manage_extensions():
    selected_profiles = select_profiles()
    if not selected_profiles:
        return

    extension_activity = questionary.select(
        "Выбери действие с расширениями",
        choices=[
            '🟢 добавить дефолтные без замены',
            '🔴 добавить дефолтные с заменой',
            '❌  удалить расширения',
            '🏠 назад в меню'
        ],
        style=custom_style
    ).ask()

    if 'назад в меню' in extension_activity:
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

    selected_ids = [str(choice.split(" ")[0]) for choice in selected_extensions]

    if not selected_ids:
        logger.warning('⚠️ Расширения не выбраны')
        return

    with ThreadPoolExecutor(max_workers=general_config['max_workers']) as executor:
        futures = []
        for profile in selected_profiles:
            profile_extensions_path = CHROME_DATA_PATH / f"Profile {profile}" / "Extensions"
            os.makedirs(profile_extensions_path, exist_ok=True)

            for ext_id in selected_ids:
                src_path = os.path.join(DEFAULT_EXTENSIONS_PATH, ext_id)
                dest_path = os.path.join(profile_extensions_path, ext_id)
                futures.append(executor.submit(copy_extension, src_path, dest_path, profile, ext_id, replace))


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

        extensions_path = os.path.join(PROJECT_PATH, "data", "profiles", f"Profile {profile}", "Extensions")
        for ext_id in selected_ids:
            try:
                ext_path = os.path.join(extensions_path, ext_id)
                if os.path.isdir(ext_path):
                    shutil.rmtree(ext_path)
                    logger.debug(f'{profile} - расширение {ext_id} удалено')
                    removed_something = True
            except Exception as e:
                logger.error(f'⛔  {profile} - не удалоcь удалить расширение {ext_id}')
                logger.debug(f'{profile} - не удалоcь удалить расширение {ext_id}, причина: {e}')

        if removed_something:
            logger.info(f'✅  {profile} - расширения удалены')
