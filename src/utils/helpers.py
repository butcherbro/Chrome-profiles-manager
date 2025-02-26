import os
import json
import shutil
import sys
import psutil
from pathlib import Path

from loguru import logger

from src.utils.constants import *

# Глобальный список для хранения PID процессов Chrome
chrome_processes = []

def register_chrome_process(process):
    """Регистрирует процесс Chrome в глобальном списке"""
    if process and process.pid:
        chrome_processes.append(process.pid)
        logger.debug(f'Зарегистрирован процесс Chrome с PID {process.pid}')

def kill_chrome_processes() -> None:
    """Завершает только процессы Chrome, запущенные нашей программой"""
    try:
        killed = 0
        for pid in chrome_processes[:]:  # Создаем копию списка для безопасного удаления
            try:
                process = psutil.Process(pid)
                if process.is_running():
                    process.terminate()  # Сначала пробуем мягкое завершение
                    process.wait(timeout=3)  # Ждем 3 секунды
                    if process.is_running():  # Если процесс все еще жив
                        process.kill()  # Принудительное завершение
                    killed += 1
                chrome_processes.remove(pid)
            except psutil.NoSuchProcess:
                chrome_processes.remove(pid)  # Процесс уже не существует
            except Exception as e:
                logger.debug(f'Ошибка при завершении процесса {pid}: {str(e)}')
                
        if killed > 0:
            logger.info(f'✅ Завершено процессов Chrome: {killed}')
        else:
            logger.info('ℹ️ Нет активных процессов Chrome для завершения')
            
    except Exception as e:
        logger.error(f'⛔ Ошибка при завершении процессов Chrome: {str(e)}')


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
    try:
        # Сначала проверяем manifest.json в корне (как у Backpack)
        root_manifest_path = os.path.join(src_path, "manifest.json")
        if os.path.isfile(root_manifest_path):
            # Если manifest.json в корне - копируем всю папку целиком
            if replace and os.path.exists(dest_path):
                shutil.rmtree(dest_path)
            
            # Копируем все файлы из корня расширения
            os.makedirs(dest_path, exist_ok=True)
            for item in os.listdir(src_path):
                s = os.path.join(src_path, item)
                d = os.path.join(dest_path, item)
                if os.path.isfile(s):
                    shutil.copy2(s, d)
                else:
                    shutil.copytree(s, d, dirs_exist_ok=True)
                    
            logger.info(f'✅  {profile} - добавлено/заменено расширение {ext_id} (root structure)')
            return True
            
        # Если manifest.json не в корне - ищем в подпапках версий
        version_folders = [f for f in os.listdir(src_path) if os.path.isdir(os.path.join(src_path, f))]
        if not version_folders:
            logger.error(f'⛔  {profile} - не найдена папка с версией расширения в {src_path}')
            return False
            
        # Берем последнюю версию
        version = sorted(version_folders)[-1]
        version_src_path = os.path.join(src_path, version)
            
        # Проверяем наличие manifest.json в папке версии
        manifest_path = os.path.join(version_src_path, "manifest.json")
        if not os.path.isfile(manifest_path):
            logger.error(f'⛔  {profile} - manifest.json не найден в {version_src_path}')
            return False
            
        # Создаем структуру папок: Extensions/ext_id/version/
        version_dest_path = os.path.join(dest_path, version)
        
        if replace and os.path.exists(dest_path):
            shutil.rmtree(dest_path)
                
        # Создаем папку с версией
        os.makedirs(version_dest_path, exist_ok=True)
        
        # Копируем файлы расширения в папку с версией
        for item in os.listdir(version_src_path):
            s = os.path.join(version_src_path, item)
            d = os.path.join(version_dest_path, item)
            if os.path.isfile(s):
                shutil.copy2(s, d)
            else:
                shutil.copytree(s, d, dirs_exist_ok=True)
                
        logger.info(f'✅  {profile} - добавлено/заменено расширение {ext_id} версии {version}')
        return True
        
    except Exception as e:
        logger.error(f'⛔  {profile} - не удалось добавить расширение {ext_id}')
        logger.debug(f'{profile} - не удалось добавить расширение {ext_id}, причина: {e}')
        return False


def remove_extensions(profile: str | int, ext_ids: list[str]) -> None:
    extensions_path = os.path.join(CHROME_DATA_PATH, f"Profile {profile}", "Extensions")
    extensions_settings_path = os.path.join(CHROME_DATA_PATH, f"Profile {profile}", "Local Extension Settings")

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


def copy_default_extensions(profile_name: str | int) -> bool:
    """
    Копирует расширения из папки default_extensions в профиль
    
    Args:
        profile_name: Имя профиля
        
    Returns:
        bool: True если все расширения успешно скопированы
    """
    try:
        # Получаем пути
        profile_extensions_path = os.path.join(CHROME_DATA_PATH, f"Profile {profile_name}", "Extensions")
        
        # Проверяем наличие папки default_extensions
        if not os.path.exists(DEFAULT_EXTENSIONS_PATH):
            logger.error(f"⛔ Папка default_extensions не найдена")
            return False
            
        # Получаем список расширений
        extensions = os.listdir(DEFAULT_EXTENSIONS_PATH)
        if not extensions:
            logger.warning(f"⚠️ В папке default_extensions нет расширений")
            return False
            
        success_count = 0
        for ext_id in extensions:
            if ext_id == '.gitkeep':
                continue
                
            src_path = os.path.join(DEFAULT_EXTENSIONS_PATH, ext_id)
            dest_path = os.path.join(profile_extensions_path, ext_id)
            
            if copy_extension(src_path, dest_path, profile_name, ext_id, replace=True):
                success_count += 1
                
        if success_count > 0:
            logger.info(f"✅ {profile_name} - скопировано расширений: {success_count}")
            return True
        else:
            logger.warning(f"⚠️ {profile_name} - не удалось скопировать расширения")
            return False
            
    except Exception as e:
        logger.error(f"⛔ {profile_name} - ошибка при копировании расширений")
        logger.debug(f"{profile_name} - ошибка при копировании расширений, причина: {str(e)}")
        return False


def analyze_profile_cache(profile_name: str | int) -> dict:
    """
    Анализирует кэш профиля и возвращает информацию о размерах и расположении
    
    Args:
        profile_name: Имя профиля
        
    Returns:
        dict: Информация о кэше профиля
    """
    profile_path = os.path.join(CHROME_DATA_PATH, f"Profile {profile_name}")
    
    # Анализируем все файлы и папки в профиле для отладки
    logger.debug(f"Анализ всех файлов и папок в профиле {profile_name}:")
    total_profile_size = 0
    
    # Анализ корневых файлов
    root_files_size = 0
    for item in os.listdir(profile_path):
        item_path = os.path.join(profile_path, item)
        if os.path.isfile(item_path):
            size = os.path.getsize(item_path)
            root_files_size += size
            logger.debug(f"Файл: {item}: {format_size(size)}")
        elif os.path.isdir(item_path):
            size = get_directory_size(item_path)
            total_profile_size += size
            logger.debug(f"Папка: {item}: {format_size(size)}")
    
    total_profile_size += root_files_size
    logger.debug(f"Размер корневых файлов: {format_size(root_files_size)}")
    logger.debug(f"Общий размер профиля: {format_size(total_profile_size)}")
    
    cache_info = {
        "browser": {
            "name": "Кэш веб-страниц",
            "description": "Кэш веб-страниц (HTML, CSS, картинки)",
            "impact": "Временно медленная загрузка сайтов",
            "paths": ["Cache"],  # Упрощаем пути для точности
            "size": 0
        },
        "code": {
            "name": "JavaScript кэш",
            "description": "Скомпилированный JavaScript",
            "impact": "Временно медленная работа сайтов",
            "paths": ["Code Cache"],  # Берем всю папку Code Cache
            "size": 0
        },
        "gpu": {
            "name": "Кэш графики",
            "description": "Кэш графических элементов",
            "impact": "Временно медленная отрисовка",
            "paths": ["GPUCache"],  # Упрощаем пути для точности
            "size": 0
        },
        "service_worker": {
            "name": "Кэш уведомлений",
            "description": "Кэш сервис-воркеров",
            "impact": "Временно не будут работать уведомления",
            "paths": ["Service Worker"],  # Берем всю папку Service Worker
            "size": 0
        },
        "media": {
            "name": "Кэш медиа",
            "description": "Кэш медиа файлов",
            "impact": "Повторная загрузка медиа",
            "paths": ["Media Cache"],
            "size": 0
        },
        "system": {
            "name": "Системный кэш",
            "description": "Системные временные файлы",
            "impact": "Не влияет на работу",
            "paths": ["System Cache"],
            "size": 0
        },
        "network": {
            "name": "Сетевой кэш",
            "description": "Кэш сетевых запросов",
            "impact": "Временно медленная работа сети",
            "paths": ["Network"],
            "size": 0
        }
    }
    
    # Анализ пользовательских данных
    user_data = {
        "indexeddb": {
            "name": "IndexedDB",
            "description": "База данных сайтов",
            "paths": ["IndexedDB", "Sync IndexedDB", "LevelDB"],  # Добавляем LevelDB
            "size": 0,
            "items": {}
        },
        "local_storage": {
            "name": "Local Storage",
            "description": "Локальное хранилище",
            "paths": ["Local Storage", "Session Storage", "WebStorage", "File System"],  # Добавляем File System
            "size": 0,
            "items": {}
        },
        "extension_settings": {
            "name": "Extension Settings",
            "description": "Настройки расширений",
            "paths": [
                "Local Extension Settings",
                "Sync Extension Settings",
                "Extension State",
                "Extension Rules",
                "Extension Scripts",
                "Extensions"
            ],
            "size": 0,
            "items": {}
        },
        "databases": {
            "name": "Databases",
            "description": "Базы данных браузера",
            "paths": [
                "databases",
                "Database",
                "Sync Data",
                "QuotaManager",
                "QuotaManager-journal",
                "Shortcuts",
                "Shortcuts-journal",
                "WebRTC",
                "blob_storage"
            ],
            "size": 0,
            "items": {}
        }
    }
    
    # Подсчет размеров кэша
    for cache_type in cache_info.values():
        for path in cache_type["paths"]:
            full_path = os.path.join(profile_path, path)
            if os.path.exists(full_path):
                cache_type["size"] += get_directory_size(full_path)
    
    # Подсчет размеров и анализ пользовательских данных
    for data_type, data in user_data.items():
        for path in data["paths"]:
            full_path = os.path.join(profile_path, path)
            if os.path.exists(full_path):
                # Общий размер
                path_size = get_directory_size(full_path)
                data["size"] += path_size
                logger.debug(f"{data_type} - {path}: {format_size(path_size)}")
                
                # Анализ отдельных элементов
                try:
                    for item in os.listdir(full_path):
                        item_path = os.path.join(full_path, item)
                        if os.path.isdir(item_path):
                            item_size = get_directory_size(item_path)
                            if item_size > 0:  # Показываем только непустые элементы
                                data["items"][f"{path}/{item}"] = {
                                    "size": item_size,
                                    "path": item_path
                                }
                except Exception as e:
                    logger.debug(f"Ошибка при анализе {path}: {str(e)}")
    
    return {
        "cache": cache_info,
        "user_data": user_data,
        "total_size": total_profile_size  # Возвращаем реальный размер профиля
    }


def clean_profile_cache(profile_name: str | int, cache_types: list[str]) -> dict:
    """
    Очищает выбранные типы кэша профиля
    
    Args:
        profile_name: Имя профиля
        cache_types: Список типов кэша для очистки
        
    Returns:
        dict: Результат очистки
    """
    try:
        profile_path = os.path.join(CHROME_DATA_PATH, f"Profile {profile_name}")
        
        cache_paths = {
            "browser": ["Cache"],
            "code": ["Code Cache/js"],
            "gpu": ["GPUCache"],
            "service_worker": ["Service Worker"],
            "media": ["Media Cache"],
            "system": ["System Cache"],
            "network": ["Network"]
        }
        
        cleaned_size = 0
        for cache_type in cache_types:
            if cache_type in cache_paths:
                for path in cache_paths[cache_type]:
                    full_path = os.path.join(profile_path, path)
                    if os.path.exists(full_path):
                        try:
                            size = get_directory_size(full_path)
                            # Сначала пробуем очистить содержимое
                            for root, dirs, files in os.walk(full_path, topdown=False):
                                for name in files:
                                    try:
                                        file_path = os.path.join(root, name)
                                        if not os.path.islink(file_path):  # Пропускаем символические ссылки
                                            os.remove(file_path)
                                    except:
                                        pass
                                for name in dirs:
                                    try:
                                        dir_path = os.path.join(root, name)
                                        if not os.path.islink(dir_path):  # Пропускаем символические ссылки
                                            os.rmdir(dir_path)
                                    except:
                                        pass
                            cleaned_size += size
                            logger.info(f"✅ {profile_name} - очищен кэш {path}")
                        except Exception as e:
                            logger.warning(f"⚠️ {profile_name} - не удалось полностью очистить {path}: {str(e)}")
                        
        return {
            "success": True,
            "cleaned_size": cleaned_size
        }
        
    except Exception as e:
        logger.error(f"⛔ {profile_name} - ошибка при очистке кэша")
        logger.debug(f"{profile_name} - ошибка при очистке кэша, причина: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


def get_directory_size(path: str) -> int:
    """
    Получает размер директории в байтах
    
    Args:
        path: Путь к директории
        
    Returns:
        int: Размер в байтах
    """
    total_size = 0
    try:
        # Используем os.scandir вместо os.walk для лучшей производительности
        with os.scandir(path) as it:
            for entry in it:
                if entry.is_file() and not entry.is_symlink():
                    total_size += entry.stat().st_size
                elif entry.is_dir() and not entry.is_symlink():
                    total_size += get_directory_size(entry.path)
    except Exception as e:
        logger.debug(f"Ошибка при подсчете размера {path}: {str(e)}")
    return total_size


def clean_user_data_items(profile_name: str | int, data_type: str, items: list[str]) -> dict:
    """
    Очищает выбранные элементы пользовательских данных
    
    Args:
        profile_name: Имя профиля
        data_type: Тип данных ('indexeddb', 'local_storage', 'extension_settings')
        items: Список элементов для очистки
        
    Returns:
        dict: Результат очистки
    """
    try:
        profile_path = os.path.join(CHROME_DATA_PATH, f"Profile {profile_name}")
        
        # Маппинг типов данных к путям
        data_paths = {
            "indexeddb": ["IndexedDB", "Sync IndexedDB", "LevelDB"],
            "local_storage": ["Local Storage", "Session Storage", "WebStorage", "File System"],
            "extension_settings": ["Local Extension Settings", "Sync Extension Settings", "Extension State"],
            "databases": ["databases", "Database", "Sync Data"]
        }
        
        if data_type not in data_paths:
            return {
                "success": False,
                "error": f"Неизвестный тип данных: {data_type}"
            }
            
        cleaned_size = 0
        cleaned_items = []
        
        # Перебираем все возможные пути для данного типа данных
        for base_path_name in data_paths[data_type]:
            base_path = os.path.join(profile_path, base_path_name)
            if not os.path.exists(base_path):
                continue
                
            # Для каждого элемента
            for item in items:
                # Извлекаем имя файла/папки из полного пути
                item_name = os.path.basename(item.split("/")[-1])
                item_path = os.path.join(base_path, item_name)
                
                if os.path.exists(item_path):
                    try:
                        # Получаем размер перед удалением
                        size = get_directory_size(item_path) if os.path.isdir(item_path) else os.path.getsize(item_path)
                        
                        # Удаляем файл или директорию
                        if os.path.isdir(item_path):
                            shutil.rmtree(item_path)
                        else:
                            os.remove(item_path)
                            
                        cleaned_size += size
                        cleaned_items.append(item_name)
                        logger.info(f"✅ {profile_name} - удален элемент {data_type}/{item_name} ({format_size(size)})")
                        
                        # Также удаляем связанные файлы (например, для IndexedDB)
                        if data_type == "indexeddb":
                            # Удаляем .blob файлы
                            blob_path = f"{item_path}.blob"
                            if os.path.exists(blob_path):
                                if os.path.isdir(blob_path):
                                    shutil.rmtree(blob_path)
                                else:
                                    os.remove(blob_path)
                            
                            # Удаляем .files файлы
                            files_path = f"{item_path}.files"
                            if os.path.exists(files_path):
                                if os.path.isdir(files_path):
                                    shutil.rmtree(files_path)
                                else:
                                    os.remove(files_path)
                            
                            # Удаляем .journal файлы
                            journal_path = f"{item_path}-journal"
                            if os.path.exists(journal_path):
                                if os.path.isdir(journal_path):
                                    shutil.rmtree(journal_path)
                                else:
                                    os.remove(journal_path)
                            
                    except Exception as e:
                        logger.warning(f"⚠️ {profile_name} - не удалось удалить {data_type}/{item_name}: {str(e)}")
        
        return {
            "success": True,
            "cleaned_size": cleaned_size,
            "cleaned_items": cleaned_items
        }
        
    except Exception as e:
        logger.error(f"⛔ {profile_name} - ошибка при очистке {data_type}")
        logger.debug(f"{profile_name} - ошибка при очистке {data_type}, причина: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


def format_size(size_bytes: int) -> str:
    """
    Форматирует размер в байтах в человекочитаемый вид
    
    Args:
        size_bytes: Размер в байтах
        
    Returns:
        str: Отформатированный размер
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"
