"""
Модуль для импорта профилей из ZennoPoster
"""
import os
import shutil
import json
from pathlib import Path
from loguru import logger
import time

from .constants import CHROME_DATA_PATH
from .helpers import (
    set_comments_for_profiles,
    copy_default_extensions
)


class ZennoProfileImporter:
    """Класс для импорта профилей из ZennoPoster"""
    
    def __init__(self):
        # Путь к папке с профилями ZennoPoster
        self.zenno_profiles_path = None
        
    def set_profiles_path(self, path: str) -> None:
        """
        Устанавливает путь к папке с профилями ZennoPoster
        
        Args:
            path: Путь к папке с профилями
        """
        self.zenno_profiles_path = path
        
    def import_profile(self, profile_folder: str) -> bool:
        """
        Импортирует профиль из ZennoPoster
        
        Args:
            profile_folder: Путь к папке профиля ZennoPoster
            
        Returns:
            bool: Успешность импорта
        """
        try:
            # Проверяем существование папки профиля
            if not os.path.exists(profile_folder):
                logger.error(f"⛔ Папка профиля ZennoPoster не найдена: {profile_folder}")
                return False
                
            # Получаем оригинальное имя профиля из имени папки
            profile_name = os.path.basename(profile_folder)
            
            # Создаем папку для нового профиля с префиксом "Profile "
            new_profile_path = os.path.join(CHROME_DATA_PATH, f"Profile {profile_name}")
            
            # Если папка существует - удаляем ее
            if os.path.exists(new_profile_path):
                shutil.rmtree(new_profile_path)
                logger.debug(f"{profile_name} - удалена существующая папка профиля")
            
            # Создаем основные папки
            os.makedirs(new_profile_path)
            logger.debug(f"{profile_name} - создана папка профиля")
            
            # Создаем необходимые папки
            required_folders = [
                "Extensions",
                "Local Extension Settings",
                "Sync Extension Settings",
                "Extension Rules",
                "Extension Scripts",
                "Extension State",
                "Local Storage",
                "IndexedDB",
                "Session Storage",
                "Network",
                "Cache",
                "Code Cache",
                "GPUCache"
            ]
            
            for folder in required_folders:
                folder_path = os.path.join(new_profile_path, folder)
                os.makedirs(folder_path, exist_ok=True)
                logger.debug(f"{profile_name} - создана папка {folder}")
            
            # Копируем содержимое из Default
            src_default = os.path.join(profile_folder, "Default")
            if os.path.exists(src_default):
                for item in os.listdir(src_default):
                    src = os.path.join(src_default, item)
                    dst = os.path.join(new_profile_path, item)
                    if os.path.isfile(src):
                        shutil.copy2(src, dst)
                        logger.debug(f"{profile_name} - скопирован файл Default/{item}")
                    else:
                        shutil.copytree(src, dst, dirs_exist_ok=True)
                        logger.debug(f"{profile_name} - скопирована папка Default/{item}")
            
            # Копируем остальные папки и файлы из корня профиля
            for item in os.listdir(profile_folder):
                if item != "Default":  # Пропускаем Default, так как уже скопировали
                    src = os.path.join(profile_folder, item)
                    dst = os.path.join(new_profile_path, item)
                    if os.path.isfile(src):
                        shutil.copy2(src, dst)
                        logger.debug(f"{profile_name} - скопирован файл {item}")
                    else:
                        shutil.copytree(src, dst, dirs_exist_ok=True)
                        logger.debug(f"{profile_name} - скопирована папка {item}")
            
            # Копируем расширения по умолчанию
            copy_default_extensions(profile_name)
            
            # Добавляем комментарий о происхождении профиля
            set_comments_for_profiles([profile_name], f"Импортирован из ZennoPoster")
            
            logger.info(f"✅ Профиль {profile_name} успешно импортирован из ZennoPoster")
            return True
            
        except Exception as e:
            logger.error(f"⛔ Ошибка при импорте профиля: {e}")
            logger.debug(f"{profile_name} - ошибка импорта, причина: {str(e)}")
            return False
            
    def list_zenno_profiles(self) -> list[str]:
        """
        Получает список доступных профилей ZennoPoster
        
        Returns:
            list[str]: Список путей к профилям
        """
        profiles = []
        
        if not self.zenno_profiles_path or not os.path.exists(self.zenno_profiles_path):
            return profiles
            
        # Ищем папки профилей
        for item in os.listdir(self.zenno_profiles_path):
            profile_path = os.path.join(self.zenno_profiles_path, item)
            if os.path.isdir(profile_path):
                profiles.append(profile_path)
                    
        return profiles 