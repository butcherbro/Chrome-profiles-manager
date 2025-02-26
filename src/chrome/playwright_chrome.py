import os
import time
import subprocess
import json
from loguru import logger
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

from src.utils.constants import CHROME_DATA_PATH, CHROME_PATH
from src.utils.helpers import kill_chrome_processes


class PlaywrightChrome:
    def __init__(self):
        """Инициализация класса для работы с Chrome через Playwright"""
        self.playwright = None
        self.browser = None
        self.page = None
        self.chrome_process = None
        
        # Загружаем конфигурацию
        config_path = os.path.join(os.path.dirname(__file__), "config", "chrome_launch_config.json")
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
    
    def launch_profile(self, profile_name: str, headless: bool = False) -> bool:
        """
        Запуск профиля Chrome с помощью Playwright
        
        Args:
            profile_name: Имя профиля для запуска
            headless: Запускать ли браузер в headless режиме
        Returns:
            bool: True если профиль успешно запущен, False в противном случае
        """
        try:
            # Проверяем существование профиля
            profile_path = os.path.join(CHROME_DATA_PATH, f"Profile {profile_name}")
            if not os.path.exists(profile_path):
                logger.error(f"⛔ {profile_name} - профиль не найден")
                return False
            
            logger.info(f"📂 {profile_name} - путь к профилю: {profile_path}")
            
            # Проверяем и собираем пути к расширениям
            extensions_path = os.path.join(profile_path, "Extensions")
            if not os.path.exists(extensions_path):
                logger.warning(f"⚠️ {profile_name} - папка с расширениями не найдена")
                return False
            
            # Собираем пути ко всем установленным расширениям
            extension_paths = []
            for ext_id in os.listdir(extensions_path):
                ext_dir = os.path.join(extensions_path, ext_id)
                if os.path.isdir(ext_dir):
                    # Находим последнюю версию расширения
                    versions = [v for v in os.listdir(ext_dir) if os.path.isdir(os.path.join(ext_dir, v))]
                    if versions:
                        latest_version = sorted(versions)[-1]
                        ext_path = os.path.join(ext_dir, latest_version)
                        extension_paths.append(ext_path)
                        logger.info(f"📦 {profile_name} - найдено расширение {ext_id} версии {latest_version}")
            
            if not extension_paths:
                logger.warning(f"⚠️ {profile_name} - расширения не найдены")
                return False
            
            # Проверяем наличие обязательных расширений
            required_extensions = self.config["extensions"]["required"]
            installed_extensions = [os.path.basename(os.path.dirname(os.path.dirname(p))) for p in extension_paths]
            missing_extensions = [ext for ext in required_extensions if ext not in installed_extensions]
            
            if missing_extensions:
                logger.error(f"⛔ {profile_name} - отсутствуют обязательные расширения: {', '.join(missing_extensions)}")
                return False
            
            # Запускаем Chrome с нужными параметрами
            logger.info(f"🚀 {profile_name} - запускаем Chrome...")
            
            # Формируем строку с путями к расширениям
            extensions_arg = ",".join(extension_paths)
            
            # Подготавливаем аргументы запуска
            chrome_cmd = [CHROME_PATH]
            
            # Добавляем обязательные флаги
            for flag in self.config["launch_flags"]["required"]:
                formatted_flag = flag.format(
                    CHROME_DATA_PATH=CHROME_DATA_PATH,
                    profile_name=profile_name,
                    debug_port=self.config["debug_port"],
                    extensions_arg=extensions_arg
                )
                chrome_cmd.append(formatted_flag)
            
            # Добавляем опциональные флаги
            if headless and "headless" in self.config["launch_flags"]["optional"]:
                chrome_cmd.append(self.config["launch_flags"]["optional"]["headless"])
            
            # Запускаем Chrome
            self.chrome_process = subprocess.Popen(
                chrome_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            # Проверяем доступность порта отладки
            max_attempts = self.config["timeouts"]["chrome_startup"]
            attempt = 0
            
            while attempt < max_attempts:
                try:
                    import urllib.request
                    import urllib.error
                    
                    url = self.config["urls"]["debug_endpoint"].format(debug_port=self.config["debug_port"])
                    try:
                        response = urllib.request.urlopen(url)
                        break
                    except urllib.error.URLError:
                        attempt += 1
                        time.sleep(1)
                        continue
                        
                except Exception as e:
                    attempt += 1
                    time.sleep(1)
                    continue
            
            if attempt >= max_attempts:
                raise Exception("Не удалось подключиться к Chrome DevTools")
            
            # Подключаемся через CDP
            logger.info(f"🔌 {profile_name} - подключаемся к Chrome через CDP...")
            self.playwright = sync_playwright().start()
            
            try:
                self.browser = self.playwright.chromium.connect_over_cdp(
                    f"http://localhost:{self.config['debug_port']}"
                )
            except Exception as e:
                logger.error(f"⛔ {profile_name} - ошибка подключения через CDP: {str(e)}")
                return False
            
            # Получаем существующий контекст
            contexts = self.browser.contexts
            if not contexts:
                logger.error(f"⛔ {profile_name} - не найден контекст браузера")
                return False
            
            context = contexts[0]
            
            # Создаем новую страницу
            logger.info(f"📄 {profile_name} - создаем новую страницу...")
            self.page = self.browser.new_page()
            
            # Устанавливаем таймауты
            self.page.set_default_navigation_timeout(self.config["timeouts"]["page_navigation"])
            self.page.set_default_timeout(self.config["timeouts"]["element_search"])
            
            logger.success(f"✅ {profile_name} - профиль успешно запущен")
            return True
            
        except Exception as e:
            logger.error(f"⛔ {profile_name} - не удалось запустить профиль")
            logger.debug(f"{profile_name} - не удалось запустить профиль, причина: {str(e)}")
            self.close()
            return False
    
    def close(self) -> None:
        """Закрытие браузера и освобождение ресурсов"""
        try:
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
            if self.chrome_process:
                self.chrome_process.terminate()
                self.chrome_process.wait()
        except Exception as e:
            logger.error(f"Ошибка при закрытии браузера: {str(e)}") 