"""
Модуль для работы с профилями Chrome через Playwright

Этот модуль предоставляет класс PlaywrightChrome, который позволяет управлять
профилями Chrome с использованием библиотеки Playwright вместо Selenium.
"""

import os
import time
import subprocess
import json
from pathlib import Path

from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext, TimeoutError as PlaywrightTimeoutError
from loguru import logger
import requests

from src.utils.helpers import set_comments_for_profiles, get_profiles_list, kill_chrome_processes
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
        self.page = None
        self.chrome_process = None
        
        # Словарь доступных скриптов
        self.scripts = {}
        
        # Загружаем конфигурацию
        config_path = os.path.join(os.path.dirname(__file__), "config", "chrome_launch_config.json")
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
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
    
    def launch_profile(self, profile_name, headless=False, debug_port=None, timeout=None):
        """
        Запускает профиль Chrome с использованием Playwright
        
        Args:
            profile_name: Имя профиля для запуска
            headless: Запускать ли в безголовом режиме
            debug_port: Порт для отладки (если None, будет использован порт из конфигурации)
            timeout: Таймаут для запуска Chrome (если None, будет использован таймаут из конфигурации)
            
        Returns:
            bool: True если профиль успешно запущен, иначе False
        """
        try:
            # Убиваем все процессы Chrome перед запуском
            logger.info(f"🔫 {profile_name} - убиваем все процессы Chrome...")
            kill_chrome_processes()
            
            # Определяем путь к профилю
            if profile_name.isdigit():
                profile_dir = f"Profile {profile_name}"
            else:
                profile_dir = profile_name
                
            profile_path = os.path.join(CHROME_DATA_PATH, profile_dir)
            logger.info(f"📂 {profile_name} - путь к профилю: {profile_path}")
            
            # Проверяем существование профиля
            if not os.path.exists(profile_path):
                logger.error(f"❌ {profile_name} - профиль не найден по пути: {profile_path}")
                return False
                
            # Получаем список расширений для профиля
            profile_extensions = []
            extensions_path = os.path.join(profile_path, "Extensions")
            
            if os.path.exists(extensions_path):
                for ext_id in os.listdir(extensions_path):
                    ext_path = os.path.join(extensions_path, ext_id)
                    if os.path.isdir(ext_path):
                        for version in os.listdir(ext_path):
                            version_path = os.path.join(ext_path, version)
                            if os.path.isdir(version_path):
                                logger.info(f"📦 {profile_name} - найдено расширение {ext_id} версии {version}")
                                profile_extensions.append(f"{version_path}")
                                break
            
            # Запускаем Chrome
            logger.info(f"🚀 {profile_name} - запускаем Chrome...")
            
            # Используем порт из конфигурации, если не указан
            if debug_port is None:
                debug_port = self.config.get("debug_port", 9222)
                
            # Используем таймаут из конфигурации, если не указан
            if timeout is None:
                timeout = self.config.get("timeouts", {}).get("chrome_startup", 30)
                
            # Формируем аргументы запуска
            launch_args = [
                CHROME_PATH,
                f"--user-data-dir={CHROME_DATA_PATH}",
                f"--profile-directory={profile_dir}",
                f"--remote-debugging-port={debug_port}",
            ]
            
            # Добавляем обязательные флаги из конфигурации
            for flag in self.config.get("launch_flags", {}).get("required", []):
                if flag == "--user-data-dir={CHROME_DATA_PATH}":
                    continue  # Пропускаем, так как уже добавили
                if flag == "--profile-directory=Profile {profile_name}":
                    continue  # Пропускаем, так как уже добавили
                if flag == "--remote-debugging-port={debug_port}":
                    continue  # Пропускаем, так как уже добавили
                # Заменяем переменные в шаблонах
                flag = flag.replace("{CHROME_DATA_PATH}", str(CHROME_DATA_PATH))
                flag = flag.replace("{profile_name}", str(profile_name))
                flag = flag.replace("{debug_port}", str(debug_port))
                launch_args.append(flag)
                
            logger.info(f"🔌 {profile_name} - будет использован порт {debug_port} для отладки")
            
            # Добавляем расширения, если они есть
            if profile_extensions:
                extensions_arg = ",".join(profile_extensions)
                launch_args.append(f"--load-extension={extensions_arg}")
                
            # Добавляем опциональные флаги из конфигурации
            for flag_name, flag_value in self.config.get("launch_flags", {}).get("optional", {}).items():
                if flag_name == "headless" and not headless:
                    continue  # Пропускаем флаг --headless, если headless=False
                # Заменяем переменные в шаблонах
                flag_value = flag_value.replace("{CHROME_DATA_PATH}", str(CHROME_DATA_PATH))
                flag_value = flag_value.replace("{profile_name}", str(profile_name))
                flag_value = flag_value.replace("{debug_port}", str(debug_port))
                launch_args.append(flag_value)
            
            # Выводим команду запуска для отладки
            logger.debug(f"Команда запуска Chrome: {' '.join(launch_args)}")
            
            # Запускаем Chrome
            self.chrome_process = subprocess.Popen(
                launch_args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            logger.info(f"✅ {profile_name} - процесс Chrome запущен с PID: {self.chrome_process.pid}")
            
            # Ждем указанное время для запуска Chrome
            time.sleep(5)
            
            # Проверяем доступность порта отладки
            logger.info(f"🔍 {profile_name} - проверяем доступность порта отладки {debug_port}...")
            
            # Получаем URL для подключения к Chrome DevTools
            debug_url = self.config.get("debug_endpoint", f"http://localhost:{debug_port}")
            
            # Проверяем доступность порта отладки с повторными попытками
            max_attempts = 30
            for attempt in range(1, max_attempts + 1):
                try:
                    logger.debug(f"Попытка {attempt}/{max_attempts} подключения к {debug_url}/json/version")
                    response = requests.get(f"{debug_url}/json/version", timeout=1)
                    if response.status_code == 200:
                        logger.debug(f"Ответ от Chrome DevTools: {response.json()}")
                        logger.info(f"✅ {profile_name} - порт отладки доступен")
                        break
                except requests.exceptions.RequestException:
                    if attempt == max_attempts:
                        logger.error(f"❌ {profile_name} - не удалось подключиться к порту отладки после {max_attempts} попыток")
                        return False
                    time.sleep(1)
            
            # Подключаемся к Chrome через CDP
            try:
                logger.info(f"🔌 {profile_name} - подключаемся к Chrome через CDP...")
                
                # Запускаем Playwright
                self.playwright = sync_playwright().start()
                
                # Подключаемся к запущенному Chrome через CDP
                self.browser = self.playwright.chromium.connect_over_cdp(debug_url)
                
                # Получаем список доступных браузеров
                logger.debug(f"Получаем список браузеров: {debug_url}/json/list")
                response = requests.get(f"{debug_url}/json/list")
                logger.debug(f"Доступные браузеры: {response.json()}")
                
                # Получаем контекст браузера
                contexts = self.browser.contexts
                if not contexts:
                    logger.error(f"❌ {profile_name} - не найден контекст браузера")
                    return False
                    
                self.context = contexts[0]
                logger.info(f"✅ {profile_name} - получен контекст браузера")
                
                # Получаем существующую страницу или создаем новую
                if self.context.pages:
                    self.page = self.context.pages[0]
                    logger.info(f"✅ {profile_name} - использована существующая страница")
                else:
                    self.page = self.context.new_page()
                    logger.info(f"✅ {profile_name} - создана новая страница")
                
                # Открываем простую страницу с именем профиля в заголовке
                try:
                    # Создаем HTML-страницу с именем профиля в заголовке
                    html_content = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <title>{profile_name}</title>
                        <style>
                            body {{
                                font-family: Arial, sans-serif;
                                background: linear-gradient(135deg, #1e2a38, #3a414a);
                                color: #f0f0f0;
                                margin: 0;
                                padding: 0;
                                display: flex;
                                justify-content: center;
                                align-items: center;
                                height: 100vh;
                                overflow: hidden;
                            }}
                            .profile-info {{
                                background: rgba(255, 255, 255, 0.1);
                                padding: 30px;
                                border-radius: 10px;
                                text-align: center;
                                box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
                            }}
                            h1 {{
                                font-size: 2.5em;
                                margin-bottom: 10px;
                                color: #ffcc00;
                            }}
                            p {{
                                font-size: 1.2em;
                                color: #ddd;
                            }}
                        </style>
                    </head>
                    <body>
                        <div class="profile-info">
                            <h1>{profile_name}</h1>
                            <p>Вы успешно запустили профиль Chrome</p>
                        </div>
                    </body>
                    </html>
                    """
                    
                    # Открываем страницу с этим HTML-содержимым в первой вкладке
                    # Сначала проверяем, что страница загружена и готова
                    try:
                        # Ждем, пока страница загрузится
                        self.page.wait_for_load_state("domcontentloaded", timeout=5000)
                        
                        # Заменяем содержимое первой вкладки нашей страницей
                        self.page.set_content(html_content)
                        logger.info(f"✅ {profile_name} - открыта страница с информацией о профиле в первой вкладке")
                    except Exception as e:
                        logger.warning(f"⚠️ {profile_name} - не удалось изменить содержимое первой вкладки: {str(e)}")
                        
                        # Если не удалось изменить содержимое первой вкладки, пробуем перейти на пустую страницу и затем установить содержимое
                        try:
                            self.page.goto("about:blank", timeout=5000)
                            self.page.set_content(html_content)
                            logger.info(f"✅ {profile_name} - открыта страница с информацией о профиле после перехода на about:blank")
                        except Exception as e2:
                            logger.error(f"❌ {profile_name} - не удалось открыть страницу с информацией о профиле после перехода на about:blank: {str(e2)}")
                            
                            # Если и это не сработало, пробуем создать новую вкладку
                            try:
                                # Закрываем текущую вкладку
                                self.page.close()
                                
                                # Создаем новую вкладку
                                self.page = self.context.new_page()
                                self.page.set_content(html_content)
                                logger.info(f"✅ {profile_name} - открыта страница с информацией о профиле в новой вкладке")
                            except Exception as e3:
                                logger.error(f"❌ {profile_name} - не удалось открыть страницу с информацией о профиле в новой вкладке: {str(e3)}")
                    
                    # Закрываем все лишние вкладки, кроме нашей и вкладок расширений
                    try:
                        # Получаем все вкладки
                        all_pages = self.context.pages
                        
                        # Закрываем только стандартные вкладки Chrome (New Tab, пустые страницы и т.д.)
                        for page in all_pages:
                            if page != self.page:
                                try:
                                    # Получаем URL вкладки для логирования
                                    page_url = page.url
                                    
                                    # Проверяем, является ли это стандартной вкладкой Chrome
                                    # Не закрываем вкладки расширений (chrome-extension://)
                                    if (page_url.startswith("chrome://") or 
                                        page_url.startswith("about:") or 
                                        "new-tab-page" in page_url or 
                                        page_url == "about:blank"):
                                        # Закрываем стандартную вкладку
                                        page.close()
                                        logger.debug(f"🔒 {profile_name} - закрыта стандартная вкладка: {page_url}")
                                except Exception as e:
                                    logger.warning(f"⚠️ {profile_name} - не удалось закрыть вкладку: {str(e)}")
                        
                        logger.info(f"✅ {profile_name} - закрыты все стандартные вкладки Chrome")
                    except Exception as e:
                        logger.error(f"❌ {profile_name} - ошибка при закрытии лишних вкладок: {str(e)}")
                    
                    logger.success(f"✅ {profile_name} - профиль успешно запущен")
                    return True
                    
                except Exception as e:
                    logger.error(f"❌ {profile_name} - ошибка при открытии страницы с информацией о профиле: {str(e)}")
                
                logger.success(f"✅ {profile_name} - профиль успешно запущен")
                return True
                
            except Exception as e:
                logger.error(f"❌ {profile_name} - ошибка при подключении к Chrome через CDP: {str(e)}")
                return False
                
        except Exception as e:
            logger.error(f"❌ {profile_name} - ошибка при запуске профиля: {str(e)}")
            return False
    
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
    
    def close(self) -> None:
        """
        Закрывает браузер и освобождает ресурсы
        """
        try:
            if self.browser:
                self.browser.close()
                self.browser = None
                
            if self.playwright:
                self.playwright.stop()
                self.playwright = None
                
            if self.chrome_process:
                try:
                    self.chrome_process.terminate()
                    self.chrome_process.wait(timeout=5)
                except:
                    try:
                        self.chrome_process.kill()
                    except:
                        pass
                self.chrome_process = None
                
            logger.info("🔒 Браузер закрыт")
        except Exception as e:
            logger.error(f"⛔ Ошибка при закрытии браузера: {str(e)}")
    
    def __find_free_port(self, start_port: int, end_port: int) -> int:
        """
        Находит свободный порт в указанном диапазоне
        
        Args:
            start_port: Начальный порт диапазона
            end_port: Конечный порт диапазона
            
        Returns:
            int: Свободный порт или None, если не найден
        """
        import socket
        
        for port in range(start_port, end_port + 1):
            if port in self.chosen_debug_ports:
                continue
                
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.bind(('localhost', port))
                    self.chosen_debug_ports.append(port)
                    return port
                except:
                    continue
        
        return None
    
    def __get_profile_path(self, profile_name: str) -> str:
        """
        Получает путь к профилю Chrome
        
        Args:
            profile_name: Имя профиля
            
        Returns:
            str: Путь к профилю
        """
        return os.path.join(CHROME_DATA_PATH, f"Profile {profile_name}") 