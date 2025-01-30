import os
import json
import shutil

from loguru import logger

from src.utils.constants import *


def get_profiles_list() -> list[str]:
    profiles = []
    for item in os.listdir(CHROME_DATA_PATH):
        item_path = os.path.join(CHROME_DATA_PATH, item)

        if os.path.isdir(item_path) and item.startswith("Profile"):
            profiles.append(item.replace('Profile ', ''))

    return profiles


def get_comments_for_profiles() -> dict:
    try:
        comments_file_path = DATA_PATH / "comments_for_profiles.json"
        with open(comments_file_path, 'r', encoding="utf-8") as f:
            comments = json.load(f)
    except FileNotFoundError:
        return {
            "success": False,
            "description": "файл с комментариями не найден"
        }

    except json.JSONDecodeError:
        return {
            "success": False,
            "description": "не удалось прочитать файл с комментариями"
        }

    return {
        "success": True,
        "comments": comments
    }


def set_comments_for_profiles(profile_names: list[str | int], comment: str | int | float) -> dict:
    result = get_comments_for_profiles()
    if result["success"]:
        comments = result["comments"]
    else:
        logger.warning(f"⚠️ Не удалось загрузить комментарии, причина: {result["description"]}")
        return result

    for profile_name in profile_names:
        comments[profile_name] = comment

    comments_file_path = DATA_PATH / "comments_for_profiles.json"
    with open(comments_file_path, 'w', encoding="utf-8") as f:
        json.dump(comments, f, indent=4, ensure_ascii=False)

    return {
        "success": True
    }


def copy_extension(src_path: str, dest_path: str, profile: str | int, ext_id: str, replace: bool = False):
    if replace:
        if os.path.exists(dest_path):
            shutil.rmtree(dest_path)
        try:
            shutil.copytree(src_path, dest_path)
            logger.info(f'✅  {profile} - добавлено/заменено расширение {ext_id}')
            return True
        except Exception as e:
            logger.error(f'⛔  {profile} - не удалось добавить расширение {ext_id}')
            logger.debug(f'{profile} - не удалось добавить расширение {ext_id}, причина: {e}')
            return False
    else:
        if os.path.exists(dest_path):
            logger.debug(f'{profile} - расширение {ext_id} уже существует, пропущено')
            return False
        else:
            try:
                shutil.copytree(src_path, dest_path)
                logger.info(f'✅  {profile} - добавлено расширение {ext_id}')
                return True
            except Exception as e:
                logger.error(f'⛔  {profile} - не удалось добавить расширение {ext_id}')
                logger.debug(f'{profile} - не удалось добавить расширение {ext_id}, причина: {e}')
                return False


def get_all_default_extensions_info() -> dict:
    extensions_info = {}
    default_extensions_path = os.path.join(PROJECT_PATH, "data", "default_extensions")
    for extension_id in os.listdir(default_extensions_path):
        extension_path = os.path.join(default_extensions_path, extension_id)
        if os.path.isdir(extension_path):
            name = get_extension_name(extension_path)
            extensions_info[extension_id] = name

    return extensions_info


def get_profiles_extensions_info(profiles_list) -> dict[str, str]:
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