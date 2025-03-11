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


def get_all_default_extensions_info() -> dict:
    extensions_info = {}
    default_extensions_path = DEFAULT_EXTENSIONS_PATH
    for extension_id in os.listdir(default_extensions_path):
        extension_path = os.path.join(default_extensions_path, extension_id)
        if os.path.isdir(extension_path):
            name = get_extension_name(extension_path)
            extensions_info[extension_id] = name

    return extensions_info


def get_profiles_extensions_info(profiles_list) -> dict:
    """
    Получает информацию о расширениях для списка профилей
    
    Args:
        profiles_list: Список профилей
        
    Returns:
        dict: Словарь с информацией о расширениях в формате {ext_id: {profile_name: ext_path, ...}, ...}
    """
    extensions_info = {}
    for profile in profiles_list:
        # Проверяем, содержит ли имя профиля префикс "Profile "
        if profile.startswith("Profile "):
            profile_path = CHROME_DATA_PATH / profile
            profile_name = profile
        else:
            profile_path = CHROME_DATA_PATH / f"Profile {profile}"
            profile_name = f"Profile {profile}"
            
        # Проверяем основной путь к расширениям
        extensions_path = profile_path / "Extensions"
        if os.path.exists(extensions_path):
            logger.debug(f"Найдена директория расширений: {extensions_path}")
            for extension_id in os.listdir(extensions_path):
                extension_dir = extensions_path / extension_id
                if os.path.isdir(extension_dir):
                    # Находим последнюю версию расширения
                    versions = [v for v in os.listdir(extension_dir) if os.path.isdir(extension_dir / v)]
                    if not versions:
                        continue
                        
                    # Берем последнюю версию (обычно самую новую)
                    latest_version = sorted(versions)[-1]
                    extension_path = str(extension_dir / latest_version)
                    
                    # Получаем информацию о расширении из манифеста
                    manifest_path = os.path.join(extension_path, "manifest.json")
                    extension_name = extension_id
                    
                    if os.path.exists(manifest_path):
                        try:
                            with open(manifest_path, 'r', encoding='utf-8') as f:
                                manifest = json.load(f)
                                extension_name = manifest.get('name', extension_id)
                        except Exception as e:
                            logger.error(f"Ошибка при чтении манифеста расширения {extension_id}: {e}")
                    
                    # Добавляем информацию о расширении
                    if extension_id not in extensions_info:
                        extensions_info[extension_id] = {}
                    
                    # Добавляем информацию о профиле
                    extensions_info[extension_id][profile_name] = extension_path
        else:
            logger.debug(f"Директория расширений не найдена: {extensions_path}")
            
        # Проверяем альтернативные пути к расширениям
        # 1. Проверяем путь к расширениям в Local State
        local_state_path = profile_path / "Local State"
        if os.path.exists(local_state_path):
            try:
                with open(local_state_path, 'r', encoding='utf-8') as f:
                    local_state = json.load(f)
                    extensions_settings = local_state.get('extensions', {}).get('settings', {})
                    for ext_id, ext_data in extensions_settings.items():
                        if ext_id not in extensions_info and ext_id != 'ahfgeienlihckogmohjhadlkjgocpleb':  # Исключаем Chrome Web Store
                            # Проверяем, есть ли расширение в default_extensions
                            default_ext_path = os.path.join(DEFAULT_EXTENSIONS_PATH, ext_id)
                            if os.path.exists(default_ext_path):
                                # Находим последнюю версию расширения
                                versions = [v for v in os.listdir(default_ext_path) if os.path.isdir(os.path.join(default_ext_path, v))]
                                if versions:
                                    latest_version = sorted(versions)[-1]
                                    extension_path = os.path.join(default_ext_path, latest_version)
                                    
                                    # Добавляем информацию о расширении
                                    if ext_id not in extensions_info:
                                        extensions_info[ext_id] = {}
                                    
                                    # Добавляем информацию о профиле
                                    extensions_info[ext_id][profile_name] = extension_path
            except Exception as e:
                logger.error(f"Ошибка при чтении Local State для профиля {profile}: {e}")
                
        # 2. Проверяем путь к расширениям в Preferences
        preferences_path = profile_path / "Preferences"
        if os.path.exists(preferences_path):
            try:
                with open(preferences_path, 'r', encoding='utf-8') as f:
                    preferences = json.load(f)
                    extensions_prefs = preferences.get('extensions', {}).get('settings', {})
                    for ext_id, ext_data in extensions_prefs.items():
                        if ext_id not in extensions_info and ext_id != 'ahfgeienlihckogmohjhadlkjgocpleb':  # Исключаем Chrome Web Store
                            # Проверяем, есть ли расширение в default_extensions
                            default_ext_path = os.path.join(DEFAULT_EXTENSIONS_PATH, ext_id)
                            if os.path.exists(default_ext_path):
                                # Находим последнюю версию расширения
                                versions = [v for v in os.listdir(default_ext_path) if os.path.isdir(os.path.join(default_ext_path, v))]
                                if versions:
                                    latest_version = sorted(versions)[-1]
                                    extension_path = os.path.join(default_ext_path, latest_version)
                                    
                                    # Добавляем информацию о расширении
                                    if ext_id not in extensions_info:
                                        extensions_info[ext_id] = {}
                                    
                                    # Добавляем информацию о профиле
                                    extensions_info[ext_id][profile_name] = extension_path
            except Exception as e:
                logger.error(f"Ошибка при чтении Preferences для профиля {profile}: {e}")

    return extensions_info


def get_extension_name(extension_path: str) -> str:
    """
    Получает имя расширения из manifest.json
    
    Args:
        extension_path: Путь к папке расширения
        
    Returns:
        str: Имя расширения или ID расширения в случае ошибки
    """
    try:
        extension_id = os.path.basename(extension_path)
        
        # Сначала проверяем, есть ли manifest.json в корне папки расширения
        manifest_path = os.path.join(extension_path, "manifest.json")
        if os.path.exists(manifest_path):
            return read_manifest_name(manifest_path)
        
        # Если нет, ищем папки версий и проверяем manifest.json в них
        version_folders = []
        for item in os.listdir(extension_path):
            item_path = os.path.join(extension_path, item)
            if os.path.isdir(item_path):
                manifest_path = os.path.join(item_path, "manifest.json")
                if os.path.isfile(manifest_path):
                    version_folders.append(item)
                    name = read_manifest_name(manifest_path)
                    if name:
                        return name
        
        # Если не нашли имя, возвращаем ID расширения
        return extension_id
    except Exception as e:
        logger.error(f"Error getting extension name: {e}")
        return os.path.basename(extension_path)


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

        # Проверяем различные поля, где может быть указано имя расширения
        # Сначала проверяем основное поле name
        name = manifest.get("name", "")
        if name:
            return name
            
        # Проверяем поле action.default_title (для новых манифестов v3)
        action_title = manifest.get("action", {}).get("default_title", "")
        if action_title:
            return action_title
            
        # Проверяем поле browser_action.default_title (для старых манифестов v2)
        browser_action_title = manifest.get("browser_action", {}).get("default_title", "")
        if browser_action_title:
            return browser_action_title
            
        # Если ничего не нашли, возвращаем пустую строку
        return ""
    except (json.JSONDecodeError, OSError) as e:
        logger.error(f"Ошибка при чтении manifest.json: {e}")
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
