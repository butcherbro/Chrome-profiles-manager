"""
Модуль для автоматизации Chrome через Playwright
"""
import os
import time
import subprocess
from pathlib import Path
from typing import Optional, List
from loguru import logger
from playwright.sync_api import sync_playwright, Page, BrowserContext
import asyncio
import shutil
import json
import socket
from urllib.request import urlopen
from urllib.error import URLError

from src.utils.constants import (
    CHROME_DATA_PATH,
    PROFILE_WELCOME_PAGES_OUTPUT_PATH,
    DEFAULT_EXTENSIONS_PATH,
    CHROME_PATH
)
from src.utils.helpers import kill_chrome_processes

class PlaywrightAutomation:
    """Класс для автоматизации действий в Chrome через Playwright"""
    
    def __init__(self):
        """Инициализация"""
        self.playwright = None
        self.browser = None
        self.context = None
        self.chrome_process = None
        
    def _find_free_port(self) -> int:
        """Находит свободный порт"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            s.listen(1)
            port = s.getsockname()[1]
        return port
        
    def _get_profile_extensions(self, profile_path: str) -> List[str]:
        """
        Получает пути ко всем расширениям профиля
        
        Args:
            profile_path: Путь к папке профиля
            
        Returns:
            List[str]: Список путей к расширениям
        """
        extensions = []
        extensions_path = os.path.join(profile_path, "Extensions")
        
        if os.path.exists(extensions_path):
            for ext_id in os.listdir(extensions_path):
                ext_path = os.path.join(extensions_path, ext_id)
                if os.path.isdir(ext_path):
                    # Получаем последнюю версию расширения
                    versions = [v for v in os.listdir(ext_path) 
                              if os.path.isdir(os.path.join(ext_path, v))]
                    if versions:
                        latest = sorted(versions)[-1]
                        ext_version_path = os.path.join(ext_path, latest)
                        extensions.append(ext_version_path)
                        logger.info(f"✓ Найдено расширение: {ext_id} (версия {latest})")
        
        return extensions
        
    def launch_profile(self, profile_name: str) -> bool:
        """
        Запускает профиль Chrome с полным функционалом
        
        Args:
            profile_name: Имя профиля
            
        Returns:
            bool: True если запуск успешен
        """
        try:
            # Закрываем Chrome если запущен
            logger.info("Закрываю все процессы Chrome...")
            kill_chrome_processes()
            time.sleep(2)
            
            # Формируем пути
            profile_path = os.path.join(CHROME_DATA_PATH, f"Profile {profile_name}")
            welcome_page = f"file://{PROFILE_WELCOME_PAGES_OUTPUT_PATH}/{profile_name}.html"
            
            # Проверяем существование профиля
            if not os.path.exists(profile_path):
                logger.error(f"❌ Профиль {profile_name} не найден")
                return False
            
            # Получаем все расширения профиля
            profile_extensions = self._get_profile_extensions(profile_path)
            
            # Добавляем MetaMask если его нет
            metamask_path = os.path.join(DEFAULT_EXTENSIONS_PATH, "nkbihfbeogaeaoehlefnkodbefgpgknn")
            if os.path.exists(metamask_path):
                metamask_profile_path = os.path.join(profile_path, "Extensions", "nkbihfbeogaeaoehlefnkodbefgpgknn")
                if not os.path.exists(metamask_profile_path):
                    # Создаем директорию если нужно
                    os.makedirs(os.path.dirname(metamask_profile_path), exist_ok=True)
                    # Копируем расширение
                    shutil.copytree(metamask_path, metamask_profile_path, dirs_exist_ok=True)
                    logger.info("✓ MetaMask скопирован в профиль")
                    profile_extensions.append(metamask_profile_path)
            
            # Находим свободный порт для отладки
            debug_port = self._find_free_port()
            
            # Формируем список аргументов запуска
            launch_args = [
                CHROME_PATH,
                f"--user-data-dir={CHROME_DATA_PATH}",
                f"--profile-directory=Profile {profile_name}",
                f"--remote-debugging-port={debug_port}",
                "--no-first-run",
                "--no-default-browser-check",
                "--enable-extensions",
                "--disable-background-timer-throttling",
                "--disable-backgrounding-occluded-windows",
                "--disable-renderer-backgrounding",
                "--disable-features=TranslateUI",
                "--disable-translate",
                "--disable-notifications",
                "--disable-save-password-bubble",
                welcome_page
            ]
            
            # Добавляем расширения если есть
            if profile_extensions:
                extensions_arg = ",".join(profile_extensions)
                launch_args.append(f"--load-extension={extensions_arg}")
            
            # Запускаем Chrome
            logger.info(f"Запускаю Chrome с портом отладки {debug_port}...")
            self.chrome_process = subprocess.Popen(
                launch_args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Ждем пока порт станет доступен
            logger.info("Жду подключения к порту отладки...")
            max_attempts = 30
            attempt = 0
            while attempt < max_attempts:
                try:
                    response = urlopen(f"http://localhost:{debug_port}/json/version")
                    data = json.loads(response.read())
                    if "webSocketDebuggerUrl" in data:
                        websocket_url = data["webSocketDebuggerUrl"]
                        logger.info(f"Chrome запущен, websocket URL: {websocket_url}")
                        break
                except URLError:
                    attempt += 1
                    time.sleep(1)
                    continue
                    
            if attempt >= max_attempts:
                raise Exception("Не удалось подключиться к Chrome DevTools")
            
            # Подключаемся через CDP
            logger.info("Подключаюсь через CDP...")
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.connect_over_cdp(
                f"http://localhost:{debug_port}"
            )
            
            # Получаем существующий контекст
            contexts = self.browser.contexts
            if not contexts:
                raise Exception("Не найден контекст браузера")
            
            self.context = contexts[0]
            
            # Ждем загрузки расширений
            logger.info("⏳ Жду загрузки расширений...")
            time.sleep(5)
            
            logger.success(f"✅ Профиль {profile_name} успешно запущен")
            return True
                
        except Exception as e:
            logger.error(f"❌ Ошибка при запуске профиля {profile_name}")
            logger.debug(f"Причина: {str(e)}")
            self.close()
            return False

    def run_script(self, script_function) -> bool:
        """
        Запуск скрипта Playwright
        
        Args:
            script_function: Функция скрипта для выполнения
            
        Returns:
            bool: True если скрипт успешно выполнен
        """
        try:
            if not self.context:
                raise Exception("Браузер не запущен")
                
            # Запускаем скрипт
            return script_function(self.context)
            
        except Exception as e:
            logger.error(f"❌ Ошибка при выполнении скрипта: {str(e)}")
            return False
            
    def close(self):
        """Закрытие браузера"""
        try:
            if self.chrome_process:
                self.chrome_process.terminate()
                self.chrome_process.wait()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
        except Exception as e:
            logger.error(f"❌ Ошибка при закрытии браузера: {str(e)}") 