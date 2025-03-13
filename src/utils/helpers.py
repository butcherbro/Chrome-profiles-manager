import os
import json
import shutil
import sys

from loguru import logger

from src.utils.constants import *


def get_profiles_list() -> list[str]:
    profiles = []
    for item in os.listdir(CHROME_DATA_PATH):
        item_path = os.path.join(CHROME_DATA_PATH, item)

        if os.path.isdir(item_path) and item.startswith("Profile"):
            # Возвращаем полное имя профиля, включая префикс "Profile "
            profiles.append(item)

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
        logger.warning(f"⚠️ Не удалось загрузить комментарии, причина: {result.get('description')}")
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
    """
    Копирует расширение из папки default_extensions в папку Extensions профиля Chrome
    
    Args:
        src_path: Путь к исходной папке расширения
        dest_path: Путь к папке назначения (Extensions/ext_id)
        profile: Имя или номер профиля
        ext_id: ID расширения
        replace: Заменять ли существующее расширение
        
    Returns:
        bool: True, если расширение успешно скопировано, иначе False
    """
    try:
        logger.debug(f"copy_extension: src_path={src_path}, type={type(src_path)}")
        logger.debug(f"copy_extension: dest_path={dest_path}, type={type(dest_path)}")
        logger.debug(f"copy_extension: profile={profile}, type={type(profile)}")
        logger.debug(f"copy_extension: ext_id={ext_id}, type={type(ext_id)}")
        logger.debug(f"copy_extension: replace={replace}, type={type(replace)}")
        
        # Проверяем, содержит ли имя профиля префикс "Profile "
        if isinstance(profile, str) and profile.startswith("Profile "):
            profile_path = profile
        else:
            profile_path = f"Profile {profile}"
            
        # Путь к файлу Preferences
        preferences_path = os.path.join(CHROME_DATA_PATH, profile_path, "Preferences")
        
        # Создаем резервную копию Preferences если он существует
        if os.path.exists(preferences_path):
            backup_path = preferences_path + ".backup"
            shutil.copy2(preferences_path, backup_path)
            logger.debug(f'Создана резервная копия Preferences для профиля {profile}')
            
            # Читаем текущие настройки
            with open(preferences_path, 'r', encoding='utf-8') as f:
                preferences = json.load(f)
                
            # Инициализируем структуру если её нет
            if 'extensions' not in preferences:
                preferences['extensions'] = {}
            if 'pinned_extensions' not in preferences['extensions']:
                preferences['extensions']['pinned_extensions'] = []
        else:
            # Создаем новый файл Preferences если его нет
            preferences = {
                'extensions': {
                    'pinned_extensions': []
                }
            }
        
        # Проверяем, содержит ли src_path уже версию расширения
        # Если в src_path есть папки и в одной из них есть manifest.json, 
        # то это значит, что src_path содержит версию расширения
        version_folders = []
        for item in os.listdir(src_path):
            item_path = os.path.join(src_path, item)
            if os.path.isdir(item_path) and os.path.isfile(os.path.join(item_path, "manifest.json")):
                version_folders.append(item)
        
        logger.debug(f"copy_extension: version_folders={version_folders}")
        
        if replace:
            if os.path.exists(dest_path):
                logger.debug(f"copy_extension: удаляем существующее расширение: {dest_path}")
                shutil.rmtree(dest_path)
            
            # Создаем директорию для ID расширения
            logger.debug(f"copy_extension: создаем директорию: {dest_path}")
            os.makedirs(dest_path, exist_ok=True)
            
            if version_folders:
                # Если в src_path уже есть версии, копируем их напрямую
                for version in version_folders:
                    version_src_path = os.path.join(src_path, version)
                    version_dest_path = os.path.join(dest_path, version)
                    logger.debug(f"copy_extension: копируем версию {version} из {version_src_path} в {version_dest_path}")
                    shutil.copytree(version_src_path, version_dest_path)
                logger.info(f'✅  {profile} - добавлено/заменено расширение {ext_id} (версии: {", ".join(version_folders)})')
            else:
                # Если в src_path нет версий, получаем версию из manifest.json
                version = get_extension_version(src_path)
                if not version:
                    version = "1.0.0"  # Используем дефолтную версию, если не удалось получить
                
                # Создаем папку с версией и копируем туда файлы
                version_dest_path = os.path.join(dest_path, version)
                logger.debug(f"copy_extension: копируем расширение из {src_path} в {version_dest_path}")
                shutil.copytree(src_path, version_dest_path)
                logger.info(f'✅  {profile} - добавлено/заменено расширение {ext_id} (версия {version})')
            
            # Добавляем расширение в pinned_extensions если его там нет
            if ext_id not in preferences['extensions']['pinned_extensions']:
                preferences['extensions']['pinned_extensions'].append(ext_id)
                logger.debug(f'{profile} - расширение {ext_id} добавлено в pinned_extensions')
            
            # Сохраняем обновленные настройки
            with open(preferences_path, 'w', encoding='utf-8') as f:
                json.dump(preferences, f, indent=4)
                
            return True
        else:
            if os.path.exists(dest_path):
                # Проверяем, есть ли уже установленные версии
                existing_versions = []
                for item in os.listdir(dest_path):
                    item_path = os.path.join(dest_path, item)
                    if os.path.isdir(item_path) and os.path.isfile(os.path.join(item_path, "manifest.json")):
                        existing_versions.append(item)
                
                if version_folders:
                    # Проверяем, есть ли новые версии для установки
                    new_versions = [v for v in version_folders if v not in existing_versions]
                    if not new_versions:
                        logger.debug(f'{profile} - расширение {ext_id} уже установлено со всеми версиями, пропущено')
                        return False
                    
                    # Устанавливаем только новые версии
                    for version in new_versions:
                        version_src_path = os.path.join(src_path, version)
                        version_dest_path = os.path.join(dest_path, version)
                        shutil.copytree(version_src_path, version_dest_path)
                    
                    logger.info(f'✅  {profile} - добавлены новые версии расширения {ext_id}: {", ".join(new_versions)}')
                    
                    # Добавляем расширение в pinned_extensions если его там нет
                    if ext_id not in preferences['extensions']['pinned_extensions']:
                        preferences['extensions']['pinned_extensions'].append(ext_id)
                        logger.debug(f'{profile} - расширение {ext_id} добавлено в pinned_extensions')
                    
                    # Сохраняем обновленные настройки
                    with open(preferences_path, 'w', encoding='utf-8') as f:
                        json.dump(preferences, f, indent=4)
                        
                    return True
                else:
                    logger.debug(f'{profile} - расширение {ext_id} уже существует, пропущено')
                    return False
            else:
                # Создаем директорию для ID расширения
                os.makedirs(dest_path, exist_ok=True)
                
                if version_folders:
                    # Если в src_path уже есть версии, копируем их напрямую
                    for version in version_folders:
                        version_src_path = os.path.join(src_path, version)
                        version_dest_path = os.path.join(dest_path, version)
                        shutil.copytree(version_src_path, version_dest_path)
                    logger.info(f'✅  {profile} - добавлено расширение {ext_id} (версии: {", ".join(version_folders)})')
                else:
                    # Если в src_path нет версий, получаем версию из manifest.json
                    version = get_extension_version(src_path)
                    if not version:
                        version = "1.0.0"  # Используем дефолтную версию, если не удалось получить
                    
                    # Создаем папку с версией и копируем туда файлы
                    version_dest_path = os.path.join(dest_path, version)
                    shutil.copytree(src_path, version_dest_path)
                    logger.info(f'✅  {profile} - добавлено расширение {ext_id} (версия {version})')
                
                # Добавляем расширение в pinned_extensions если его там нет
                if ext_id not in preferences['extensions']['pinned_extensions']:
                    preferences['extensions']['pinned_extensions'].append(ext_id)
                    logger.debug(f'{profile} - расширение {ext_id} добавлено в pinned_extensions')
                
                # Сохраняем обновленные настройки
                with open(preferences_path, 'w', encoding='utf-8') as f:
                    json.dump(preferences, f, indent=4)
                
                return True
    except Exception as e:
        logger.error(f'⛔  {profile} - не удалось добавить расширение {ext_id}')
        logger.debug(f'{profile} - не удалось добавить расширение {ext_id}, причина: {e}')
        return False


def copy_extension_from_profile_to_default(profile: str | int, ext_id: str) -> bool:
    """
    Копирует расширение из профиля Chrome в папку дефолтных расширений
    
    Args:
        profile: Имя или номер профиля
        ext_id: ID расширения
        
    Returns:
        bool: True, если расширение успешно скопировано, иначе False
    """
    try:
        # Путь к расширению в профиле
        profile_extensions_path = os.path.join(CHROME_DATA_PATH, f"Profile {profile}", "Extensions", ext_id)
        
        # Путь к дефолтному расширению
        default_extension_path = os.path.join(DEFAULT_EXTENSIONS_PATH, ext_id)
        
        # Проверяем, существует ли расширение в профиле
        if not os.path.exists(profile_extensions_path):
            logger.error(f'⛔ Расширение {ext_id} не найдено в профиле {profile}')
            return False
            
        # Проверяем, есть ли версии расширения
        version_folders = []
        for item in os.listdir(profile_extensions_path):
            item_path = os.path.join(profile_extensions_path, item)
            if os.path.isdir(item_path) and os.path.isfile(os.path.join(item_path, "manifest.json")):
                version_folders.append(item)
                
        if not version_folders:
            logger.error(f'⛔ Не найдены версии расширения {ext_id} в профиле {profile}')
            return False
            
        # Удаляем существующее дефолтное расширение, если оно есть
        if os.path.exists(default_extension_path):
            shutil.rmtree(default_extension_path)
            
        # Создаем директорию для дефолтного расширения
        os.makedirs(default_extension_path, exist_ok=True)
        
        # Копируем все версии расширения
        for version in version_folders:
            version_src_path = os.path.join(profile_extensions_path, version)
            version_dest_path = os.path.join(default_extension_path, version)
            shutil.copytree(version_src_path, version_dest_path)
            
        logger.info(f'✅ Расширение {ext_id} успешно скопировано из профиля {profile} в папку дефолтных расширений')
        logger.info(f'✅ Скопированы версии: {", ".join(version_folders)}')
        return True
    except Exception as e:
        logger.error(f'⛔ Не удалось скопировать расширение {ext_id} из профиля {profile}')
        logger.debug(f'Не удалось скопировать расширение {ext_id} из профиля {profile}, причина: {e}')
        return False


def remove_extensions(profile: str | int, ext_ids: list[str]) -> None:
    # Проверяем, содержит ли имя профиля префикс "Profile "
    if isinstance(profile, str) and profile.startswith("Profile "):
        profile_path = profile
    else:
        profile_path = f"Profile {profile}"
        
    extensions_path = os.path.join(CHROME_DATA_PATH, profile_path, "Extensions")
    extensions_settings_path = os.path.join(CHROME_DATA_PATH, profile_path, "Local Extension Settings")
    preferences_path = os.path.join(CHROME_DATA_PATH, profile_path, "Preferences")

    for ext_id in ext_ids:
        ext_path = os.path.join(extensions_path, ext_id)
        ext_settings_path = os.path.join(extensions_settings_path, ext_id)

        try:
            if os.path.isdir(ext_path):
                shutil.rmtree(ext_path)
                logger.info(f'{profile} - расширение {ext_id} удалено')
        except Exception as e:
            logger.error(f'⛔  {profile} - не удалоcь удалить расширение {ext_id}')
            logger.debug(f'{profile} - не удалоcь удалить  расширение {ext_id}, причина: {e}')

        try:
            if os.path.isdir(ext_settings_path):
                shutil.rmtree(ext_settings_path)
                logger.info(f'{profile} - локальные настройки расширения {ext_id} удалены')
        except Exception as e:
            logger.error(f'⛔  {profile} - не удалоcь удалить локальные настройки расширения {ext_id}')
            logger.debug(f'{profile} - не удалоcь удалить локальные настройки расширения {ext_id}, причина: {e}')

    # Обновляем файл Preferences
    try:
        if os.path.exists(preferences_path):
            with open(preferences_path, 'r', encoding='utf-8') as f:
                preferences = json.load(f)

            # Удаляем информацию об удаленных расширениях
            if 'extensions' in preferences:
                for ext_id in ext_ids:
                    # Удаляем из chrome_url_overrides
                    if 'chrome_url_overrides' in preferences['extensions']:
                        preferences['extensions']['chrome_url_overrides'] = {}

                    # Удаляем из settings
                    if 'settings' in preferences['extensions']:
                        if ext_id in preferences['extensions']['settings']:
                            del preferences['extensions']['settings'][ext_id]

                    # Удаляем из pinned_extensions
                    if 'pinned_extensions' in preferences['extensions']:
                        if ext_id in preferences['extensions']['pinned_extensions']:
                            preferences['extensions']['pinned_extensions'].remove(ext_id)

            # Сохраняем обновленные настройки
            with open(preferences_path, 'w', encoding='utf-8') as f:
                json.dump(preferences, f, indent=4)

            logger.info(f'{profile} - файл Preferences обновлен')
        else:
            logger.warning(f'{profile} - файл Preferences не найден')
    except Exception as e:
        logger.error(f'⛔  {profile} - не удалось обновить файл Preferences')
        logger.debug(f'{profile} - не удалось обновить файл Preferences, причина: {e}')


def get_all_default_extensions_info() -> dict:
    extensions_info = {}
    default_extensions_path = DEFAULT_EXTENSIONS_PATH
    for extension_id in os.listdir(default_extensions_path):
        extension_path = os.path.join(default_extensions_path, extension_id)
        if os.path.isdir(extension_path):
            name = get_extension_name(extension_path)
            extensions_info[extension_id] = name

    return extensions_info


def get_profiles_extensions_info(profiles_list) -> dict[str, str]:
    """
    Получает информацию о расширениях для списка профилей
    
    Args:
        profiles_list: Список профилей
        
    Returns:
        dict: Словарь с информацией о расширениях в формате {ext_id: name}
    """
    extensions_info = {}
    for profile in profiles_list:
        # Проверяем, содержит ли имя профиля префикс "Profile "
        if profile.startswith("Profile "):
            profile_path = os.path.join(CHROME_DATA_PATH, profile)
        else:
            profile_path = os.path.join(CHROME_DATA_PATH, f"Profile {profile}")
            
        extensions_path = os.path.join(profile_path, "Extensions")
        extensions_settings_path = os.path.join(profile_path, "Local Extension Settings")
        if not os.path.isdir(extensions_path) and not os.path.isdir(extensions_settings_path):
            continue

        if os.path.exists(extensions_path):
            for extension_id in os.listdir(extensions_path):
                extension_path = os.path.join(extensions_path, extension_id)
                if os.path.isdir(extension_path):
                    name = get_extension_name(extension_path)
                    extensions_info[extension_id] = name

        if os.path.exists(extensions_settings_path):
            for extension_id in os.listdir(extensions_settings_path):
                extension_settings_path = os.path.join(extensions_settings_path, extension_id)
                if os.path.isdir(extension_settings_path):
                    if extensions_info.get(extension_id) is None:
                        extensions_info[extension_id] = ''

    return extensions_info


def get_extension_name(extension_path: str) -> str:
    """
    Получает имя расширения из manifest.json
    
    Args:
        extension_path: Путь к папке расширения
        
    Returns:
        str: Имя расширения или пустая строка в случае ошибки
    """
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


def get_extension_version(extension_path: str) -> str:
    """
    Получает версию расширения из manifest.json
    
    Args:
        extension_path: Путь к папке расширения
        
    Returns:
        str: Версия расширения или "Неизвестно" в случае ошибки
    """
    try:
        # Сначала проверяем, есть ли manifest.json в корне папки расширения
        manifest_path = os.path.join(extension_path, "manifest.json")
        if os.path.exists(manifest_path):
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
                return manifest.get("version", "Неизвестно")
        
        # Если нет, ищем папки версий и проверяем manifest.json в них
        for item in os.listdir(extension_path):
            item_path = os.path.join(extension_path, item)
            if os.path.isdir(item_path):
                manifest_path = os.path.join(item_path, "manifest.json")
                if os.path.isfile(manifest_path):
                    with open(manifest_path, 'r', encoding='utf-8') as f:
                        manifest = json.load(f)
                        return manifest.get("version", "Неизвестно")
        
        # Если не нашли версию, возвращаем "Неизвестно"
        return "Неизвестно"
    except Exception as e:
        logger.error(f"Error getting extension version: {e}")
        return "Неизвестно"


def get_extension_icon_path(extension_path: str) -> str:
    """
    Находит путь к иконке расширения
    
    Args:
        extension_path: Путь к папке расширения
        
    Returns:
        str: Путь к иконке или пустая строка в случае ошибки
    """
    try:
        # Проверяем, существует ли путь
        if not os.path.exists(extension_path):
            logger.warning(f"Путь к расширению не существует: {extension_path}")
            return ""
            
        # Сначала проверяем, есть ли manifest.json в корне папки расширения
        manifest_path = os.path.join(extension_path, "manifest.json")
        if os.path.exists(manifest_path):
            try:
                with open(manifest_path, 'r', encoding='utf-8') as f:
                    manifest = json.load(f)
                    
                # Проверяем разные варианты расположения иконки
                icons = manifest.get("icons", {})
                if icons:
                    # Предпочитаем иконки в порядке убывания размера
                    for size in ["128", "64", "48", "32", "16"]:
                        if size in icons:
                            icon_path = icons[size]
                            full_path = os.path.join(extension_path, icon_path)
                            if os.path.exists(full_path):
                                logger.debug(f"Найдена иконка размера {size} для расширения: {full_path}")
                                return full_path
                        
                        # Если не нашли по предпочтительным размерам, берем первую доступную
                        icon_path = next(iter(icons.values()))
                        full_path = os.path.join(extension_path, icon_path)
                        if os.path.exists(full_path):
                            logger.debug(f"Найдена иконка для расширения: {full_path}")
                            return full_path
                    
                    # Проверяем поле browser_action или action (для новых версий)
                    browser_action = manifest.get("browser_action", {}) or manifest.get("action", {})
                    if browser_action:
                        # Проверяем default_icon
                        default_icon = browser_action.get("default_icon", "")
                        if isinstance(default_icon, str) and default_icon:
                            full_path = os.path.join(extension_path, default_icon)
                            if os.path.exists(full_path):
                                logger.debug(f"Найдена иконка browser_action для расширения: {full_path}")
                                return full_path
                        elif isinstance(default_icon, dict):
                            # Если default_icon - словарь с размерами
                            for size in ["128", "64", "48", "32", "16"]:
                                if size in default_icon:
                                    icon_path = default_icon[size]
                                    full_path = os.path.join(extension_path, icon_path)
                                    if os.path.exists(full_path):
                                        logger.debug(f"Найдена иконка browser_action размера {size} для расширения: {full_path}")
                                        return full_path
                            # Берем первую доступную
                            if default_icon:
                                icon_path = next(iter(default_icon.values()))
                                full_path = os.path.join(extension_path, icon_path)
                                if os.path.exists(full_path):
                                    logger.debug(f"Найдена иконка browser_action для расширения: {full_path}")
                                    return full_path
                    
                    # Проверяем альтернативные пути
                    for icon_name in ["icon.png", "icon.jpg", "icon.svg", "logo.png", "logo.jpg", "logo.svg"]:
                        potential_path = os.path.join(extension_path, icon_name)
                        if os.path.exists(potential_path):
                            logger.debug(f"Найдена стандартная иконка для расширения: {potential_path}")
                            return potential_path
            except Exception as manifest_error:
                logger.warning(f"Ошибка при чтении manifest.json: {manifest_error}")
        
        # Если нет, ищем папки версий и проверяем manifest.json в них
        for item in os.listdir(extension_path):
            item_path = os.path.join(extension_path, item)
            if os.path.isdir(item_path):
                manifest_path = os.path.join(item_path, "manifest.json")
                if os.path.isfile(manifest_path):
                    try:
                        with open(manifest_path, 'r', encoding='utf-8') as f:
                            manifest = json.load(f)
                            
                            # Проверяем разные варианты расположения иконки
                            icons = manifest.get("icons", {})
                            if icons:
                                # Предпочитаем иконки в порядке убывания размера
                                for size in ["128", "64", "48", "32", "16"]:
                                    if size in icons:
                                        icon_path = icons[size]
                                        full_path = os.path.join(item_path, icon_path)
                                        if os.path.exists(full_path):
                                            logger.debug(f"Найдена иконка размера {size} для расширения в подпапке: {full_path}")
                                            return full_path
                                
                                # Если не нашли по предпочтительным размерам, берем первую доступную
                                icon_path = next(iter(icons.values()))
                                full_path = os.path.join(item_path, icon_path)
                                if os.path.exists(full_path):
                                    logger.debug(f"Найдена иконка для расширения в подпапке: {full_path}")
                                    return full_path
                            
                            # Проверяем поле browser_action или action (для новых версий)
                            browser_action = manifest.get("browser_action", {}) or manifest.get("action", {})
                            if browser_action:
                                # Проверяем default_icon
                                default_icon = browser_action.get("default_icon", "")
                                if isinstance(default_icon, str) and default_icon:
                                    full_path = os.path.join(item_path, default_icon)
                                    if os.path.exists(full_path):
                                        logger.debug(f"Найдена иконка browser_action для расширения в подпапке: {full_path}")
                                        return full_path
                                elif isinstance(default_icon, dict):
                                    # Если default_icon - словарь с размерами
                                    for size in ["128", "64", "48", "32", "16"]:
                                        if size in default_icon:
                                            icon_path = default_icon[size]
                                            full_path = os.path.join(item_path, icon_path)
                                            if os.path.exists(full_path):
                                                logger.debug(f"Найдена иконка browser_action размера {size} для расширения в подпапке: {full_path}")
                                                return full_path
                                    # Берем первую доступную
                                    if default_icon:
                                        icon_path = next(iter(default_icon.values()))
                                        full_path = os.path.join(item_path, icon_path)
                                        if os.path.exists(full_path):
                                            logger.debug(f"Найдена иконка browser_action для расширения в подпапке: {full_path}")
                                            return full_path
                            
                            # Проверяем альтернативные пути
                            for icon_name in ["icon.png", "icon.jpg", "icon.svg", "logo.png", "logo.jpg", "logo.svg"]:
                                potential_path = os.path.join(item_path, icon_name)
                                if os.path.exists(potential_path):
                                    logger.debug(f"Найдена стандартная иконка для расширения в подпапке: {potential_path}")
                                    return potential_path
                                    
                            # Ищем иконки в подпапках
                            for subdir in ["_metadata", "images", "img", "icons", "assets"]:
                                subdir_path = os.path.join(item_path, subdir)
                                if os.path.isdir(subdir_path):
                                    for icon_name in ["icon.png", "icon.jpg", "icon.svg", "logo.png", "logo.jpg", "logo.svg", "icon_128.png", "icon_48.png", "icon_32.png"]:
                                        potential_path = os.path.join(subdir_path, icon_name)
                                        if os.path.exists(potential_path):
                                            logger.debug(f"Найдена иконка в подпапке {subdir}: {potential_path}")
                                            return potential_path
                    except Exception as manifest_error:
                        logger.warning(f"Ошибка при чтении manifest.json в подпапке: {manifest_error}")
                        
                # Если manifest.json не найден, ищем иконки напрямую
                for icon_name in ["icon.png", "icon.jpg", "icon.svg", "logo.png", "logo.jpg", "logo.svg"]:
                    potential_path = os.path.join(item_path, icon_name)
                    if os.path.exists(potential_path):
                        logger.debug(f"Найдена стандартная иконка для расширения в подпапке без manifest: {potential_path}")
                        return potential_path
                
                # Ищем иконки в подпапках
                for subdir in ["_metadata", "images", "img", "icons", "assets"]:
                    subdir_path = os.path.join(item_path, subdir)
                    if os.path.isdir(subdir_path):
                        for icon_name in ["icon.png", "icon.jpg", "icon.svg", "logo.png", "logo.jpg", "logo.svg", "icon_128.png", "icon_48.png", "icon_32.png"]:
                            potential_path = os.path.join(subdir_path, icon_name)
                            if os.path.exists(potential_path):
                                logger.debug(f"Найдена иконка в подпапке {subdir} без manifest: {potential_path}")
                                return potential_path
        
        logger.warning(f"Иконка для расширения не найдена: {extension_path}")
        return ""
    except Exception as e:
        logger.error(f"Ошибка при поиске иконки расширения: {e}")
        return ""


def read_manifest_name(manifest_path: str) -> str:
    """
    Читает имя расширения из manifest.json
    
    Args:
        manifest_path: Путь к файлу manifest.json
        
    Returns:
        str: Имя расширения или пустая строка в случае ошибки
    """
    try:
        with open(manifest_path, 'r', encoding='utf-8') as file:
            manifest = json.load(file)

        return manifest.get("action", {}).get("default_title", "")
    except (json.JSONDecodeError, OSError):
        return ''


def kill_chrome_processes() -> None:
    try:
        if sys.platform == 'win32':
            os.system('taskkill /F /IM chrome.exe')
        else:
            os.system('pkill chrome')
        logger.info(f'✅  Все процессы Chrome завершены')
    except Exception as e:
        logger.error(f'⛔  Не удалоcь завершить процессы Chrome')
        logger.error(f'⛔  Не удалоcь завершить процессы Chrome, причина: {e}')


def get_profile_comments() -> dict:
    """
    Получает словарь комментариев для профилей
    
    Returns:
        dict: Словарь с комментариями, где ключ - имя профиля, значение - комментарий
    """
    result = get_comments_for_profiles()
    if result["success"]:
        return result["comments"]
    else:
        logger.warning(f"⚠️ Не удалось загрузить комментарии, причина: {result.get('description')}")
        return {}


def delete_profile(profile: str | int) -> bool:
    """
    Полностью удаляет профиль Chrome с диска
    
    Args:
        profile: Имя профиля (с префиксом "Profile " или без)
        
    Returns:
        bool: True если профиль успешно удален, False в случае ошибки
    """
    try:
        # Проверяем, содержит ли имя профиля префикс "Profile "
        if isinstance(profile, str) and profile.startswith("Profile "):
            profile_path = profile
        else:
            profile_path = f"Profile {profile}"
        
        # Полный путь к папке профиля
        full_profile_path = os.path.join(CHROME_DATA_PATH, profile_path)
        
        # Проверяем существование папки профиля
        if not os.path.isdir(full_profile_path):
            logger.warning(f"Профиль {profile_path} не существует")
            return False
        
        # Удаляем папку профиля
        shutil.rmtree(full_profile_path)
        logger.info(f"Профиль {profile_path} успешно удален")
        return True
    except Exception as e:
        logger.error(f"⛔ Не удалось удалить профиль {profile}")
        logger.debug(f"Не удалось удалить профиль {profile}, причина: {e}")
        return False


def restore_default_extensions(profile: str | int) -> None:
    """
    Восстанавливает все расширения из папки default_extensions в указанный профиль
    
    Args:
        profile: Имя или номер профиля
    """
    try:
        # Получаем список всех расширений в папке default_extensions
        default_extensions = os.listdir(DEFAULT_EXTENSIONS_PATH)
        
        # Проверяем, содержит ли имя профиля префикс "Profile "
        if isinstance(profile, str) and profile.startswith("Profile "):
            profile_path = profile
        else:
            profile_path = f"Profile {profile}"
            
        # Путь к папке расширений профиля
        profile_extensions_path = os.path.join(CHROME_DATA_PATH, profile_path, "Extensions")
        preferences_path = os.path.join(CHROME_DATA_PATH, profile_path, "Preferences")
        
        # Создаем папку расширений, если она не существует
        os.makedirs(profile_extensions_path, exist_ok=True)
        
        # Создаем резервную копию Preferences если он существует
        if os.path.exists(preferences_path):
            backup_path = preferences_path + ".backup"
            shutil.copy2(preferences_path, backup_path)
            logger.debug(f'Создана резервная копия Preferences для профиля {profile}')
            
            # Читаем текущие настройки
            with open(preferences_path, 'r', encoding='utf-8') as f:
                preferences = json.load(f)
                
            # Инициализируем структуру если её нет
            if 'extensions' not in preferences:
                preferences['extensions'] = {}
            if 'pinned_extensions' not in preferences['extensions']:
                preferences['extensions']['pinned_extensions'] = []
        else:
            # Создаем новый файл Preferences если его нет
            preferences = {
                'extensions': {
                    'pinned_extensions': []
                }
            }
        
        # Копируем каждое расширение и обновляем Preferences
        for ext_id in default_extensions:
            src_path = os.path.join(DEFAULT_EXTENSIONS_PATH, ext_id)
            if os.path.isdir(src_path):
                dest_path = os.path.join(profile_extensions_path, ext_id)
                if copy_extension(src_path, dest_path, profile, ext_id, replace=True):
                    # Добавляем расширение в pinned_extensions если его там нет
                    if ext_id not in preferences['extensions']['pinned_extensions']:
                        preferences['extensions']['pinned_extensions'].append(ext_id)
                        logger.debug(f'{profile} - расширение {ext_id} добавлено в pinned_extensions')
        
        # Сохраняем обновленные настройки
        with open(preferences_path, 'w', encoding='utf-8') as f:
            json.dump(preferences, f, indent=4)
            
        logger.info(f'✅  {profile} - все расширения восстановлены из папки default_extensions')
    except Exception as e:
        logger.error(f'⛔  {profile} - не удалось восстановить расширения')
        logger.debug(f'{profile} - не удалось восстановить расширения, причина: {e}')


def safe_remove_extensions(profile: str | int, ext_ids: list[str]) -> bool:
    """
    Безопасно удаляет расширения только из указанного профиля
    
    Args:
        profile: Имя или номер профиля
        ext_ids: Список ID расширений для удаления
        
    Returns:
        bool: True если операция успешна, False в случае ошибки
    """
    try:
        # Проверяем, содержит ли имя профиля префикс "Profile "
        if isinstance(profile, str) and profile.startswith("Profile "):
            profile_path = profile
        else:
            profile_path = f"Profile {profile}"
            
        # Формируем пути
        profile_dir = os.path.join(CHROME_DATA_PATH, profile_path)
        extensions_path = os.path.join(profile_dir, "Extensions")
        extensions_settings_path = os.path.join(profile_dir, "Local Extension Settings")
        preferences_path = os.path.join(profile_dir, "Preferences")
        
        # Проверяем существование профиля
        if not os.path.exists(profile_dir):
            logger.error(f'⛔ Профиль {profile} не существует')
            return False
            
        # Создаем резервную копию Preferences
        if os.path.exists(preferences_path):
            backup_path = preferences_path + ".backup"
            shutil.copy2(preferences_path, backup_path)
            logger.debug(f'Создана резервная копия Preferences для профиля {profile}')
        
        success = True
        for ext_id in ext_ids:
            try:
                # Удаляем файлы расширения
                ext_path = os.path.join(extensions_path, ext_id)
                if os.path.exists(ext_path):
                    shutil.rmtree(ext_path)
                    logger.info(f'✅ {profile} - расширение {ext_id} удалено')
                
                # Удаляем настройки расширения
                ext_settings_path = os.path.join(extensions_settings_path, ext_id)
                if os.path.exists(ext_settings_path):
                    shutil.rmtree(ext_settings_path)
                    logger.info(f'✅ {profile} - настройки расширения {ext_id} удалены')
                    
                # Обновляем Preferences
                if os.path.exists(preferences_path):
                    try:
                        with open(preferences_path, 'r', encoding='utf-8') as f:
                            preferences = json.load(f)
                        
                        if 'extensions' in preferences:
                            # Удаляем из chrome_url_overrides
                            if 'chrome_url_overrides' in preferences['extensions']:
                                preferences['extensions']['chrome_url_overrides'] = {}
                            
                            # Удаляем из settings
                            if 'settings' in preferences['extensions']:
                                if ext_id in preferences['extensions']['settings']:
                                    del preferences['extensions']['settings'][ext_id]
                            
                            # Удаляем из pinned_extensions
                            if 'pinned_extensions' in preferences['extensions']:
                                if ext_id in preferences['extensions']['pinned_extensions']:
                                    preferences['extensions']['pinned_extensions'].remove(ext_id)
                        
                        # Сохраняем обновленные настройки
                        with open(preferences_path, 'w', encoding='utf-8') as f:
                            json.dump(preferences, f, indent=4)
                            
                        logger.info(f'✅ {profile} - настройки расширения {ext_id} обновлены в Preferences')
                    except Exception as e:
                        logger.error(f'⛔ {profile} - ошибка при обновлении Preferences: {e}')
                        success = False
                        
            except Exception as e:
                logger.error(f'⛔ {profile} - ошибка при удалении расширения {ext_id}: {e}')
                success = False
        
        return success
    except Exception as e:
        logger.error(f'⛔ Ошибка при удалении расширений из профиля {profile}: {e}')
        return False


def safe_install_extension(profile: str | int, ext_id: str, replace: bool = False) -> bool:
    """
    Безопасно устанавливает расширение в указанный профиль
    
    Args:
        profile: Имя или номер профиля
        ext_id: ID расширения
        replace: Заменять ли существующее расширение
        
    Returns:
        bool: True если операция успешна, False в случае ошибки
    """
    try:
        # Проверяем, содержит ли имя профиля префикс "Profile "
        if isinstance(profile, str) and profile.startswith("Profile "):
            profile_path = profile
            profile_name = profile.replace("Profile ", "")
        else:
            profile_path = f"Profile {profile}"
            profile_name = str(profile)
            
        # Формируем пути
        profile_dir = os.path.join(CHROME_DATA_PATH, profile_path)
        extensions_path = os.path.join(profile_dir, "Extensions")
        preferences_path = os.path.join(profile_dir, "Preferences")
        
        # Проверяем существование профиля
        if not os.path.exists(profile_dir):
            logger.error(f'⛔ Профиль {profile} не существует')
            return False
            
        # Проверяем наличие расширения в default_extensions
        src_path = os.path.join(DEFAULT_EXTENSIONS_PATH, ext_id)
        if not os.path.exists(src_path):
            logger.error(f'⛔ Расширение {ext_id} не найдено в папке default_extensions')
            return False
            
        # Создаем папку Extensions, если она не существует
        os.makedirs(extensions_path, exist_ok=True)
        
        # Создаем резервную копию Preferences
        if os.path.exists(preferences_path):
            backup_path = preferences_path + ".backup"
            shutil.copy2(preferences_path, backup_path)
            logger.debug(f'Создана резервная копия Preferences для профиля {profile}')
        
        # Устанавливаем расширение
        dest_path = os.path.join(extensions_path, ext_id)
        result = copy_extension(src_path, dest_path, profile_name, ext_id, replace)
        
        if result:
            # Обновляем Preferences
            if os.path.exists(preferences_path):
                try:
                    with open(preferences_path, 'r', encoding='utf-8') as f:
                        preferences = json.load(f)
                    
                    # Создаем структуру extensions если её нет
                    if 'extensions' not in preferences:
                        preferences['extensions'] = {}
                    
                    # Добавляем расширение в pinned_extensions
                    if 'pinned_extensions' not in preferences['extensions']:
                        preferences['extensions']['pinned_extensions'] = []
                    
                    if ext_id not in preferences['extensions']['pinned_extensions']:
                        preferences['extensions']['pinned_extensions'].append(ext_id)
                        
                    # Сохраняем обновленные настройки
                    with open(preferences_path, 'w', encoding='utf-8') as f:
                        json.dump(preferences, f, indent=4)
                        
                    logger.info(f'✅ {profile} - расширение {ext_id} добавлено в Preferences')
                except Exception as e:
                    logger.error(f'⛔ {profile} - ошибка при обновлении Preferences: {e}')
                    return False
            
            logger.info(f'✅ {profile} - расширение {ext_id} успешно установлено')
            return True
        else:
            logger.error(f'⛔ {profile} - не удалось установить расширение {ext_id}')
            return False
            
    except Exception as e:
        logger.error(f'⛔ Ошибка при установке расширения {ext_id} в профиль {profile}: {e}')
        return False


def safe_restore_profile_extensions(profile: str | int) -> bool:
    """
    Безопасно восстанавливает все расширения из default_extensions в указанный профиль
    
    Args:
        profile: Имя или номер профиля
        
    Returns:
        bool: True если операция успешна, False в случае ошибки
    """
    try:
        # Проверяем, содержит ли имя профиля префикс "Profile "
        if isinstance(profile, str) and profile.startswith("Profile "):
            profile_path = profile
            profile_name = profile.replace("Profile ", "")
        else:
            profile_path = f"Profile {profile}"
            profile_name = str(profile)
            
        # Формируем пути
        profile_dir = os.path.join(CHROME_DATA_PATH, profile_path)
        extensions_path = os.path.join(profile_dir, "Extensions")
        
        # Проверяем существование профиля
        if not os.path.exists(profile_dir):
            logger.error(f'⛔ Профиль {profile} не существует')
            return False
            
        # Создаем папку Extensions, если она не существует
        os.makedirs(extensions_path, exist_ok=True)
        
        # Получаем список расширений из default_extensions
        success = True
        for ext_id in os.listdir(DEFAULT_EXTENSIONS_PATH):
            src_path = os.path.join(DEFAULT_EXTENSIONS_PATH, ext_id)
            if os.path.isdir(src_path):
                dest_path = os.path.join(extensions_path, ext_id)
                if not copy_extension(src_path, dest_path, profile_name, ext_id, True):
                    success = False
                    
        if success:
            logger.info(f'✅ {profile} - все расширения успешно восстановлены')
        else:
            logger.warning(f'⚠️ {profile} - некоторые расширения не удалось восстановить')
            
        return success
            
    except Exception as e:
        logger.error(f'⛔ Ошибка при восстановлении расширений в профиль {profile}: {e}')
        return False
