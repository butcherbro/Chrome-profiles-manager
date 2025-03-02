"""
Модуль для загрузки расширений Chrome из Web Store или локальных файлов.
Поддерживает два способа загрузки:
1. Прямая загрузка из Chrome Web Store по ID расширения
2. Импорт локального .crx файла или распакованного расширения
"""

import os
import json
import shutil
import requests
import zipfile
from pathlib import Path
from loguru import logger
from typing import Optional, Dict, Any

from src.utils.constants import DEFAULT_EXTENSIONS_PATH

class ExtensionDownloader:
    """Класс для загрузки и добавления расширений Chrome"""
    
    def __init__(self):
        """Инициализация загрузчика расширений"""
        self.extensions_path = DEFAULT_EXTENSIONS_PATH
        self.extensions_path.mkdir(parents=True, exist_ok=True)
        
        # Известные версии расширений
        self.known_versions = {
            "padekgcemlokbadohgkifijomclgjgif": "2.5.21",  # SwitchyOmega
            "nkbihfbeogaeaoehlefnkodbefgpgknn": "10.34.1",  # MetaMask
        }
        
        # Известные имена расширений
        self.known_names = {
            "padekgcemlokbadohgkifijomclgjgif": "Proxy SwitchyOmega",
            "nkbihfbeogaeaoehlefnkodbefgpgknn": "MetaMask",
        }
    
    def add_extension(self, source: str) -> bool:
        """
        Универсальный метод добавления расширения.
        
        Args:
            source: Может быть:
                   - ID расширения из Chrome Web Store
                   - Путь к .crx файлу
                   - Путь к распакованной папке расширения
                   
        Returns:
            bool: True если добавление успешно
        """
        try:
            # Определяем тип источника
            if len(source) == 32 and all(c in "abcdefghijklmnopqrstuvwxyz0123456789" for c in source):
                # Это похоже на ID расширения
                return self.download_from_store(source)
                
            source_path = Path(source)
            if not source_path.exists():
                logger.error(f"⛔ Источник не найден: {source}")
                return False
                
            if source_path.is_file() and source_path.suffix == '.crx':
                # Это .crx файл
                return self._process_crx_file(source_path)
            elif source_path.is_dir():
                # Это распакованное расширение
                return self._process_unpacked_extension(source_path)
            else:
                logger.error(f"⛔ Неподдерживаемый тип источника: {source}")
                return False
                
        except Exception as e:
            logger.error(f"⛔ Ошибка при добавлении расширения: {str(e)}")
            return False
    
    def _process_crx_file(self, crx_path: Path) -> bool:
        """Обработка .crx файла"""
        try:
            # Читаем manifest.json из .crx
            with zipfile.ZipFile(crx_path, 'r') as zip_ref:
                try:
                    manifest_data = json.loads(zip_ref.read('manifest.json').decode('utf-8'))
                except:
                    logger.error("⛔ Не удалось прочитать manifest.json из .crx файла")
                    return False
            
            # Получаем ID и версию
            extension_id = manifest_data.get('key', crx_path.stem)
            version = manifest_data.get('version', '1.0.0')
            
            # Создаем структуру папок
            extension_path = self.extensions_path / extension_id
            version_path = extension_path / f"{version}_0"
            
            # Удаляем старую версию если есть
            if version_path.exists():
                shutil.rmtree(version_path)
            version_path.mkdir(parents=True, exist_ok=True)
            
            # Распаковываем содержимое
            with zipfile.ZipFile(crx_path, 'r') as zip_ref:
                zip_ref.extractall(version_path)
            
            logger.success(f"✅ Расширение {extension_id} успешно добавлено из .crx файла")
            return True
            
        except Exception as e:
            logger.error(f"⛔ Ошибка при обработке .crx файла: {str(e)}")
            return False
    
    def _process_unpacked_extension(self, source_path: Path) -> bool:
        """Обработка распакованного расширения"""
        try:
            # Ищем manifest.json
            manifest_path = source_path / "manifest.json"
            if not manifest_path.exists():
                logger.error(f"⛔ manifest.json не найден в {source_path}")
                return False
            
            # Читаем manifest.json
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest_data = json.load(f)
            
            # Получаем ID и версию
            extension_id = manifest_data.get('key', source_path.name)
            version = manifest_data.get('version', '1.0.0')
            
            # Создаем структуру папок
            extension_path = self.extensions_path / extension_id
            version_path = extension_path / f"{version}_0"
            
            # Удаляем старую версию если есть
            if version_path.exists():
                shutil.rmtree(version_path)
            
            # Копируем файлы
            shutil.copytree(source_path, version_path)
            
            logger.success(f"✅ Расширение {extension_id} успешно добавлено из папки")
            return True
            
        except Exception as e:
            logger.error(f"⛔ Ошибка при обработке распакованного расширения: {str(e)}")
            return False
    
    def download_from_store(self, extension_id: str) -> bool:
        """
        Загружает расширение из Chrome Web Store
        
        Args:
            extension_id: ID расширения в Chrome Web Store
            
        Returns:
            bool: True если загрузка успешна
        """
        try:
            # URL для загрузки расширения
            download_url = f"https://clients2.google.com/service/update2/crx?response=redirect&acceptformat=crx2,crx3&prodversion=32&x=id%3D{extension_id}%26installsource%3Dondemand%26uc"
            
            # Создаем папку для расширения
            extension_path = self.extensions_path / extension_id
            extension_path.mkdir(parents=True, exist_ok=True)
            
            # Загружаем расширение
            response = requests.get(download_url, stream=True)
            if response.status_code == 200:
                # Сохраняем .crx файл
                crx_path = extension_path / "extension.crx"
                with open(crx_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                # Создаем папку для версии
                version = self.known_versions.get(extension_id, "1.0.0")
                version_path = extension_path / f"{version}_0"
                version_path.mkdir(parents=True, exist_ok=True)
                
                try:
                    # Пробуем распаковать как zip
                    with zipfile.ZipFile(crx_path, 'r') as zip_ref:
                        zip_ref.extractall(version_path)
                    logger.info(f"✅ Расширение {extension_id} распаковано")
                    
                    # Удаляем .crx файл после успешной распаковки
                    os.remove(crx_path)
                except:
                    logger.error(f"❌ Не удалось распаковать {extension_id}")
                    return False
                
                # Проверяем наличие manifest.json
                manifest_path = version_path / "manifest.json"
                if not manifest_path.exists():
                    manifest_data = {
                        "name": self._get_extension_name(extension_id),
                        "version": version,
                        "manifest_version": 3,
                        "description": "Downloaded from Chrome Web Store"
                    }
                    with open(manifest_path, 'w', encoding='utf-8') as f:
                        json.dump(manifest_data, f, indent=2)
                
                logger.info(f"✅ Расширение {extension_id} успешно загружено")
                return True
            else:
                logger.error(f"❌ Ошибка загрузки расширения {extension_id}: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка при загрузке расширения {extension_id}")
            logger.debug(f"Причина: {str(e)}")
            return False
    
    def _get_extension_name(self, extension_id: str) -> str:
        """Возвращает название расширения по его ID"""
        return self.known_names.get(extension_id, extension_id) 