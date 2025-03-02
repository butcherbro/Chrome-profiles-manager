import os
import shutil
from pathlib import Path
from loguru import logger

from src.utils.constants import CHROME_DATA_PATH, DEFAULT_EXTENSIONS_PATH
from src.utils.helpers import get_profiles_list

def copy_extensions_to_all_profiles(source_profile: str = "03"):
    """
    Копирует расширения из профиля 03 во все остальные профили.
    При копировании также сохраняет расширения в папку default_extensions.
    
    Для криптокошельков:
    - Если в целевом профиле уже есть настройки кошелька - они сохраняются
    - Если в целевом профиле нет настроек - копируется только расширение без настроек
    
    Args:
        source_profile: Номер профиля-источника (по умолчанию "03")
    """
    try:
        # Путь к папкам исходного профиля
        source_profile_path = CHROME_DATA_PATH / f"Profile {source_profile}"
        source_extensions_path = source_profile_path / "Extensions"
        
        # ID расширений-кошельков, для которых нужно сохранять существующие настройки
        WALLET_EXTENSIONS = [
            "nkbihfbeogaeaoehlefnkodbefgpgknn",  # MetaMask
            "fhbohimaelbohpjbbldcnglifacahlip",  # Rabby Wallet
            "bfnaelmomeimhlpmgjnjophhpkkoljpa",  # Phantom Wallet
            "nanjmdknhkinifnkgdcggcfnhdaammmj"   # Backpack Wallet
        ]
        
        # Папки с настройками расширений
        extension_data_folders = [
            "Local Extension Settings",    # Локальные настройки
            "Sync Extension Settings",     # Синхронизированные настройки
            "Extension State",             # Состояние расширений
            "Extension Rules",             # Правила расширений
            "Extension Scripts",           # Скрипты расширений
            "Local Storage",               # Локальное хранилище
            "Session Storage",             # Сессионное хранилище
            "IndexedDB",                   # База данных IndexedDB
            "Service Worker"               # Данные Service Worker
        ]
        
        if not source_extensions_path.exists():
            logger.error(f"❌ Папка Extensions в профиле {source_profile} не найдена")
            return False
            
        # Получаем список всех профилей
        profiles = get_profiles_list()
        
        # Сначала копируем расширения в default_extensions
        logger.info("Сохраняем расширения в default_extensions...")
        DEFAULT_EXTENSIONS_PATH.mkdir(parents=True, exist_ok=True)
        
        for ext_id in os.listdir(source_extensions_path):
            if ext_id == '.gitkeep':
                continue
                
            src_ext_path = source_extensions_path / ext_id
            default_ext_path = DEFAULT_EXTENSIONS_PATH / ext_id
            
            # Удаляем старую версию если есть
            if default_ext_path.exists():
                shutil.rmtree(default_ext_path)
            
            # Копируем расширение с сохранением структуры
            shutil.copytree(src_ext_path, default_ext_path, symlinks=True)
            logger.info(f"✅ Расширение {ext_id} сохранено в default_extensions")
        
        # Копируем расширения в каждый профиль
        for profile in profiles:
            if profile == source_profile:
                continue
                
            target_profile_path = CHROME_DATA_PATH / f"Profile {profile}"
            target_extensions_path = target_profile_path / "Extensions"
            
            # Создаем папки для настроек если их нет
            for folder in extension_data_folders:
                (target_profile_path / folder).mkdir(parents=True, exist_ok=True)
            
            # Удаляем старую папку Extensions если она существует
            if target_extensions_path.exists():
                shutil.rmtree(target_extensions_path)
            
            # Копируем папку Extensions с сохранением прав доступа
            shutil.copytree(source_extensions_path, target_extensions_path, symlinks=True)
            
            # Копируем права доступа с исходной папки Extensions
            source_stat = os.stat(source_extensions_path)
            os.chmod(target_extensions_path, source_stat.st_mode)
            
            # Копируем права доступа для всех подпапок и файлов Extensions
            for root, dirs, files in os.walk(source_extensions_path):
                relative_path = os.path.relpath(root, source_extensions_path)
                target_root = os.path.join(target_extensions_path, relative_path)
                
                # Копируем права для директорий
                for d in dirs:
                    source_path = os.path.join(root, d)
                    target_path = os.path.join(target_root, d)
                    if os.path.exists(target_path):  # Проверяем существование
                        source_stat = os.stat(source_path)
                        os.chmod(target_path, source_stat.st_mode)
                
                # Копируем права для файлов
                for f in files:
                    source_path = os.path.join(root, f)
                    target_path = os.path.join(target_root, f)
                    if os.path.exists(target_path):  # Проверяем существование
                        source_stat = os.stat(source_path)
                        os.chmod(target_path, source_stat.st_mode)
            
            # Копируем все папки с настройками расширений
            for folder in extension_data_folders:
                source_folder = source_profile_path / folder
                target_folder = target_profile_path / folder
                
                if source_folder.exists():
                    # Для каждого расширения в папке
                    for ext_id in os.listdir(source_folder):
                        source_ext_path = source_folder / ext_id
                        target_ext_path = target_folder / ext_id
                        
                        # Для кошельков проверяем наличие настроек
                        if ext_id in WALLET_EXTENSIONS:
                            if target_ext_path.exists():
                                logger.info(f"ℹ️ {profile} - найдены существующие настройки кошелька {ext_id}, пропускаем копирование настроек")
                                continue
                            else:
                                logger.info(f"ℹ️ {profile} - настройки кошелька {ext_id} не найдены, расширение установлено без настроек")
                                continue
                        
                        if source_ext_path.is_dir():
                            # Удаляем старые настройки если они есть
                            if target_ext_path.exists():
                                shutil.rmtree(target_ext_path)
                            
                            # Копируем папку с настройками
                            shutil.copytree(source_ext_path, target_ext_path, symlinks=True)
                            
                            # Копируем права доступа
                            source_stat = os.stat(source_ext_path)
                            os.chmod(target_ext_path, source_stat.st_mode)
                            
                            # Копируем права для содержимого
                            for root, dirs, files in os.walk(source_ext_path):
                                relative_path = os.path.relpath(root, source_ext_path)
                                target_root = os.path.join(target_ext_path, relative_path)
                                
                                for d in dirs:
                                    source_path = os.path.join(root, d)
                                    target_path = os.path.join(target_root, d)
                                    if os.path.exists(target_path):
                                        source_stat = os.stat(source_path)
                                        os.chmod(target_path, source_stat.st_mode)
                                
                                for f in files:
                                    source_path = os.path.join(root, f)
                                    target_path = os.path.join(target_root, f)
                                    if os.path.exists(target_path):
                                        source_stat = os.stat(source_path)
                                        os.chmod(target_path, source_stat.st_mode)
            
            logger.success(f"✅ Profile {profile} - расширения и все настройки успешно скопированы")
            
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка при копировании расширений: {str(e)}")
        return False 