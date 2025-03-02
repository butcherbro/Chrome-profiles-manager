"""
Модуль для установки расширений Chrome в профили.
Поддерживает установку как во все профили, так и в выбранные.
"""

import os
import json
import shutil
from pathlib import Path
from loguru import logger
from typing import List, Optional, Dict, Any

from src.utils.constants import DEFAULT_EXTENSIONS_PATH, PROFILES_PATH

class ExtensionInstaller:
    """Класс для установки расширений в профили Chrome"""
    
    def __init__(self):
        """Инициализация установщика расширений"""
        self.extensions_path = DEFAULT_EXTENSIONS_PATH
        self.profiles_path = PROFILES_PATH
        
    def install_to_profile(self, extension_id: str, profile_id: str) -> bool:
        """
        Устанавливает расширение в конкретный профиль
        
        Args:
            extension_id: ID расширения
            profile_id: ID профиля
            
        Returns:
            bool: True если установка успешна
        """
        try:
            # Проверяем наличие расширения
            source_path = self.extensions_path / extension_id
            if not source_path.exists():
                logger.error(f"⛔ Расширение {extension_id} не найдено")
                return False
                
            # Путь к папке расширений в профиле
            profile_extensions_path = self.profiles_path / f"Profile {profile_id}" / "Extensions"
            profile_extensions_path.mkdir(parents=True, exist_ok=True)
            
            # Путь для установки расширения
            target_path = profile_extensions_path / extension_id
            
            # Если расширение уже установлено, удаляем его
            if target_path.exists():
                shutil.rmtree(target_path)
                
            # Копируем расширение
            shutil.copytree(source_path, target_path)
            
            logger.info(f"✅ Расширение {extension_id} установлено в профиль {profile_id}")
            return True
            
        except Exception as e:
            logger.error(f"⛔ Ошибка при установке расширения {extension_id} в профиль {profile_id}")
            logger.debug(f"Причина: {str(e)}")
            return False
            
    def install_to_all_profiles(self, extension_id: str) -> Dict[str, bool]:
        """
        Устанавливает расширение во все профили
        
        Args:
            extension_id: ID расширения
            
        Returns:
            Dict[str, bool]: Словарь с результатами установки для каждого профиля
        """
        results = {}
        
        # Получаем список всех профилей
        for profile_path in self.profiles_path.glob("Profile *"):
            profile_id = profile_path.name.split(" ")[1]
            results[profile_id] = self.install_to_profile(extension_id, profile_id)
            
        return results
        
    def install_to_selected_profiles(self, extension_id: str, profile_ids: List[str]) -> Dict[str, bool]:
        """
        Устанавливает расширение в выбранные профили
        
        Args:
            extension_id: ID расширения
            profile_ids: Список ID профилей
            
        Returns:
            Dict[str, bool]: Словарь с результатами установки для каждого профиля
        """
        results = {}
        
        for profile_id in profile_ids:
            results[profile_id] = self.install_to_profile(extension_id, profile_id)
            
        return results
        
    def get_installed_extensions(self, profile_id: str) -> List[str]:
        """
        Получает список установленных расширений в профиле
        
        Args:
            profile_id: ID профиля
            
        Returns:
            List[str]: Список ID установленных расширений
        """
        try:
            extensions_path = self.profiles_path / f"Profile {profile_id}" / "Extensions"
            if not extensions_path.exists():
                return []
                
            return [d.name for d in extensions_path.iterdir() if d.is_dir()]
            
        except Exception as e:
            logger.error(f"⛔ Ошибка при получении списка расширений профиля {profile_id}")
            logger.debug(f"Причина: {str(e)}")
            return [] 