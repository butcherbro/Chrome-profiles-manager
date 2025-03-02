"""
Модуль для работы с браузером Chrome
"""
import os
import time
import json
import subprocess
from typing import List, Optional
from pathlib import Path
from loguru import logger

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

from src.utils.constants import (
    CHROME_DATA_PATH,
    CHROME_PATH,
    CHROME_DRIVER_PATH,
    PROFILE_WELCOME_PAGES_OUTPUT_PATH
)
from src.utils.helpers import register_chrome_process

class Browser:
    """Класс для работы с браузером Chrome"""
    
    def __init__(self):
        """Инициализация браузера"""
        self.chrome_path = CHROME_PATH
        self.profiles_path = CHROME_DATA_PATH
        self.welcome_pages_path = PROFILE_WELCOME_PAGES_OUTPUT_PATH
        self.driver_path = CHROME_DRIVER_PATH
        
    def create_new_profile(self, profile_name: str) -> None:
        """
        Создает новый профиль Chrome
        
        Args:
            profile_name: имя профиля
        """
        try:
            # Создаем папку профиля
            profile_path = os.path.join(self.profiles_path, f"Profile {profile_name}")
            os.makedirs(profile_path, exist_ok=True)
            
            # Инициализируем настройки профиля
            self.init_profile_preferences(profile_name)
            
            logger.success(f'✅  {profile_name} - профиль успешно создан')
            
        except Exception as e:
            logger.error(f'⛔  {profile_name} - не удалось создать профиль')
            logger.debug(f'{profile_name} - не удалось создать профиль, причина: {e}')
    
    def init_profile_preferences(self, profile_name: str) -> bool:
        """
        Инициализирует настройки профиля
        
        Args:
            profile_name: имя профиля
            
        Returns:
            bool: True если настройки успешно инициализированы
        """
        initialized = False
        
        try:
            launch_args = self.__create_launch_flags(profile_name, False, False, False)
            
            with open(os.devnull, 'w') as devnull:  # to avoid Chrome log spam
                chrome_process = subprocess.Popen([self.chrome_path, *launch_args], stdout=devnull, stderr=devnull)
                register_chrome_process(chrome_process)  # Регистрируем процесс
            
            logger.info(f'✅  {profile_name} - профиль запущен')
            initialized = True
            
        except Exception as e:
            logger.error(f'⛔  {profile_name} - не удалось запустить профиль для инициализации настроек')
            logger.debug(f'{profile_name} - не удалось запустить профиль для инициализации настроек, причина: {e}')
            return initialized
        
        time.sleep(2)
        
        try:
            chrome_process.terminate()
            chrome_process.wait()
            logger.debug(f'{profile_name} - профиль закрыт')
        except Exception as e:
            logger.error(f'⛔  {profile_name} - не удалось закрыть профиль')
            logger.debug(f'{profile_name} - не удалось закрыть профиль, причина: {e}')
        
        return initialized
    
    def launch_profile(self, profile_name: str, debug: bool = False, headless: bool = False, maximized: bool = False) -> subprocess.Popen | None:
        """
        Запускает профиль Chrome
        
        Args:
            profile_name: имя профиля
            debug: режим отладки
            headless: безголовый режим
            maximized: запуск в полноэкранном режиме
            
        Returns:
            subprocess.Popen | None: процесс Chrome или None в случае ошибки
        """
        try:
            launch_args = self.__create_launch_flags(profile_name, debug, headless, maximized)
            
            with open(os.devnull, 'w') as devnull:  # to avoid Chrome log spam
                chrome_process = subprocess.Popen([self.chrome_path, *launch_args], stdout=devnull, stderr=devnull)
                register_chrome_process(chrome_process)  # Регистрируем процесс
            
            logger.success(f'✅  {profile_name} - профиль успешно запущен')
            return chrome_process
            
        except Exception as e:
            logger.error(f'⛔  {profile_name} - не удалось запустить профиль')
            logger.debug(f'{profile_name} - не удалось запустить профиль, причина: {e}')
            return None
    
    def run_scripts(self, profile_name: str, scripts_list: list[str], headless: bool = False) -> None:
        """
        Запускает скрипты для профиля
        
        Args:
            profile_name: имя профиля
            scripts_list: список скриптов для запуска
            headless: безголовый режим
        """
        try:
            # Запускаем профиль в режиме отладки
            process = self.launch_profile(profile_name, debug=True, headless=headless)
            if not process:
                return
                
            time.sleep(2)  # Даем время на запуск
            
            # Подключаемся к профилю через selenium
            driver = self.__establish_debug_port_connection(profile_name)
            if not driver:
                return
                
            try:
                # Запускаем скрипты
                for script in scripts_list:
                    try:
                        logger.info(f'⏳  {profile_name} - запуск скрипта {script}')
                        script_module = __import__(f'src.chrome.scripts.{script}', fromlist=[script])
                        script_func = getattr(script_module, script)
                        script_func(profile_name, driver)
                        logger.success(f'✅  {profile_name} - скрипт {script} успешно выполнен')
                    except Exception as e:
                        logger.error(f'⛔  {profile_name} - ошибка при выполнении скрипта {script}')
                        logger.debug(f'{profile_name} - ошибка при выполнении скрипта {script}, причина: {e}')
                        
            finally:
                # Закрываем драйвер
                try:
                    driver.quit()
                except:
                    pass
                    
        except Exception as e:
            logger.error(f'⛔  {profile_name} - ошибка при запуске скриптов')
            logger.debug(f'{profile_name} - ошибка при запуске скриптов, причина: {e}')
    
    def __establish_debug_port_connection(self, profile_name) -> webdriver.Chrome:
        """
        Устанавливает соединение с профилем через selenium
        
        Args:
            profile_name: имя профиля
            
        Returns:
            webdriver.Chrome: драйвер Chrome или None в случае ошибки
        """
        try:
            options = Options()
            options.debugger_address = "127.0.0.1:9222"
            service = Service(executable_path=self.driver_path)
            driver = webdriver.Chrome(service=service, options=options)
            return driver
        except Exception as e:
            logger.error(f'⛔  {profile_name} - не удалось подключиться к профилю')
            logger.debug(f'{profile_name} - не удалось подключиться к профилю, причина: {e}')
            return None
    
    def __create_launch_flags(self,
                          profile_name: str,
                          debug: bool = False,
                          headless: bool = False,
                          maximized: bool = False) -> list[str]:
        """
        Создает список аргументов запуска Chrome
        
        Args:
            profile_name: имя профиля
            debug: режим отладки
            headless: безголовый режим
            maximized: запуск в полноэкранном режиме
            
        Returns:
            list[str]: список аргументов запуска
        """
        # Базовые аргументы
        args = [
            f"--user-data-dir={self.__get_profile_path(profile_name)}",
            "--no-default-browser-check",
            "--no-first-run",
            "--disable-default-apps",
            "--disable-gpu",
            f"--start-maximized" if maximized else "",
            f"--headless=new" if headless else "",
            f"--remote-debugging-port=9222" if debug else "",
        ]
        
        # Добавляем стартовую страницу
        welcome_page = self.__get_profile_welcome_page(profile_name)
        if welcome_page:
            args.append(welcome_page)
            
        # Фильтруем пустые аргументы
        return [arg for arg in args if arg]
    
    @staticmethod
    def __get_profile_path(profile_name: str) -> str:
        """Возвращает путь к папке профиля"""
        return os.path.join(CHROME_DATA_PATH, f"Profile {profile_name}")
    
    @staticmethod
    def __get_profile_welcome_page(profile_name: str) -> str:
        """Возвращает путь к стартовой странице профиля"""
        welcome_page = os.path.join(PROFILE_WELCOME_PAGES_OUTPUT_PATH, f"{profile_name}.html")
        if os.path.exists(welcome_page):
            return f"file://{welcome_page}"
        return "" 