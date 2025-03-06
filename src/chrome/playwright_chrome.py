"""
Модуль для работы с профилями Chrome через Playwright

Этот модуль предоставляет класс PlaywrightChrome, который позволяет управлять
профилями Chrome с использованием библиотеки Playwright вместо Selenium.
"""

import os
import time
import subprocess
from pathlib import Path

from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
from loguru import logger

from src.utils.helpers import set_comments_for_profiles, get_profiles_list
from src.utils.constants import *


class PlaywrightChrome:
    """
    Класс для работы с профилями Chrome через Playwright
    
    Этот класс предоставляет методы для запуска, управления и автоматизации
    действий в профилях Chrome с использованием библиотеки Playwright.
    """
    
    def __init__(self):
        """
        Инициализация класса PlaywrightChrome
        """
        self.debug_ports = {}
        self.chosen_debug_ports = []
        self.playwright = None
        self.browser = None
        self.context = None
        
        # Словарь доступных скриптов
        self.scripts = {}
        
    def get_profiles(self) -> list[str]:
        """
        Получает список всех профилей Chrome
        
        Returns:
            list[str]: Список имен профилей
        """
        return get_profiles_list()
    
    def create_new_profile(self, profile_name: str) -> None:
        """
        Создает новый профиль Chrome
        
        Args:
            profile_name: Имя нового профиля
        """
        try:
            profile_path = self.__get_profile_path(profile_name)
            profile_extensions_path = os.path.join(profile_path, "Extensions")

            os.makedirs(profile_path)  # может вызвать FileExistsError
            os.makedirs(profile_extensions_path, exist_ok=True)

            set_comments_for_profiles(profile_name, "")  # сбросить комментарий

            logger.info(f'✅  {profile_name} - профиль создан')
        except FileExistsError:
            logger.warning(f'⚠️ {profile_name} - профиль уже существует')
        except Exception as e:
            logger.error(f'⛔  {profile_name} - не удалось создать профиль')
            logger.debug(f'{profile_name} - не удалось создать профиль, причина: {e}')
    
    def launch_profile(self, 
                      profile_name: str, 
                      headless: bool = False, 
                      maximized: bool = False) -> Browser:
        """
        Запускает профиль Chrome с использованием Playwright
        
        Args:
            profile_name: Имя профиля
            headless: Запускать ли браузер в фоновом режиме
            maximized: Запускать ли браузер в полноэкранном режиме
            
        Returns:
            Browser: Объект браузера Playwright или None в случае ошибки
        """
        try:
            logger.debug(f"launch_profile: profile_name={profile_name}, headless={headless}, maximized={maximized}")
            
            # Находим свободный порт для отладки
            free_port = self.__find_free_port()
            if free_port:
                self.debug_ports[profile_name] = free_port
            else:
                logger.warning(f'⚠️ {profile_name} - отсутствуют свободные порты для подключения')
                return None
            
            # Формируем путь к профилю
            profile_path = self.__get_profile_path(profile_name)
            
            # Запускаем Chrome с нужными параметрами через subprocess
            # Это необходимо, так как Playwright не поддерживает напрямую запуск с указанием профиля
            launch_args = [
                f"--user-data-dir={CHROME_DATA_PATH}",
                f"--profile-directory={f'Profile {profile_name}'}",
                "--no-first-run",
                "--no-sync",
                "--disable-features=IdentityConsistency",
                "--disable-accounts-receiver",
                f"--remote-debugging-port={free_port}",
                "--headless" if headless else None,
                "--start-maximized" if maximized else None
            ]
            
            launch_args = [i for i in launch_args if i is not None]
            logger.debug(f"Флаги запуска Chrome: {launch_args}")
            
            with open(os.devnull, 'w') as devnull:  # чтобы избежать спама логов Chrome
                chrome_process = subprocess.Popen([CHROME_PATH, *launch_args], stdout=devnull, stderr=devnull)
            
            # Даем браузеру время на запуск
            time.sleep(2)
            
            # Подключаемся к запущенному браузеру через CDP
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.connect_over_cdp(f"http://localhost:{free_port}")
            
            logger.info(f'✅  {profile_name} - профиль запущен через Playwright')
            
            return self.browser
            
        except Exception as e:
            logger.error(f'⛔  {profile_name} - не удалось запустить профиль через Playwright')
            logger.debug(f'{profile_name} - не удалось запустить профиль через Playwright, причина: {e}')
            return None
    
    def run_scripts(self, profile_name: str, scripts_list: list[str], headless: bool = False) -> None:
        """
        Запускает скрипты для профиля Chrome
        
        Args:
            profile_name: Имя профиля
            scripts_list: Список скриптов для запуска
            headless: Запускать ли браузер в фоновом режиме
        """
        try:
            browser = self.launch_profile(profile_name, headless)
            if not browser:
                raise Exception('не удалось запустить браузер')
            
            # Получаем контекст и страницу
            context = browser.contexts[0]  # Используем существующий контекст
            page = context.pages[0]  # Используем существующую страницу
            
            logger.debug(f'{profile_name} - подключение установлено')
            
            logger.debug(f'{profile_name} - скрипты для прогона: {scripts_list}')
            for script in scripts_list:
                try:
                    human_name = self.scripts[script]['human_name']
                    logger.info(f'ℹ️ {profile_name} - запускаю скрипт "{human_name}"')
                    script_data_path = os.path.join(DATA_PATH, 'scripts', "playwright", script)
                    self.scripts[script]['method'](
                        profile_name,
                        script_data_path,
                        page
                    )
                    logger.info(f'✅  {profile_name} - скрипт "{human_name}" выполнен')
                except Exception as e:
                    human_name = self.scripts[script]['human_name']
                    logger.error(f'⛔  {profile_name} - скрипт "{human_name}" завершен с ошибкой')
                    logger.debug(f'{profile_name} - скрипт "{human_name}" завершен с ошибкой, причина: {e}')
            
        except Exception as e:
            logger.error(f'⛔  {profile_name} - не удалось запустить профиль, выполнение скриптов прервано')
            logger.debug(f'{profile_name} - не удалось запустить профиль, причина: {e}')
            return
        
        finally:
            # Закрываем браузер и playwright
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
            logger.debug(f'{profile_name} - профиль закрыт')
    
    @staticmethod
    def __get_profile_path(profile_name: str) -> str:
        """
        Получает путь к профилю Chrome
        
        Args:
            profile_name: Имя профиля
            
        Returns:
            str: Путь к профилю
        """
        return os.path.join(CHROME_DATA_PATH, f'Profile {profile_name}')
    
    def __find_free_port(self, start_port=9222, max_port=9300) -> int | None:
        """
        Находит свободный порт для подключения к Chrome
        
        Args:
            start_port: Начальный порт для поиска
            max_port: Максимальный порт для поиска
            
        Returns:
            int | None: Номер свободного порта или None, если свободный порт не найден
        """
        import socket
        for port in range(start_port, max_port):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                result = s.connect_ex(('127.0.0.1', port))
                if result != 0 and port not in self.chosen_debug_ports:
                    self.chosen_debug_ports.append(port)
                    return port

        return None 