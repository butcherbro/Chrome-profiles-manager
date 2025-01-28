import os
import shutil
import subprocess
from sys import platform
import time
import socket

from loguru import logger

from .automation.establish_connection import establish_connection
from .automation.initial_setup import initial_setup
from .automation.omega_proxy_setup import omega_proxy_setup
from config import automation_config


class Chrome:
    def __init__(self, root_path: str):
        self.root_path = root_path
        self.debug_ports = {}
        self.chosen_debug_ports = []
        Chrome.init_class_variables(self.root_path)

        self.automation_scripts = {
            'run_initial_setup': {
                'human_name': 'Первичная настройка Chrome',
                'method': initial_setup
            },
            'run_omega_proxy_setup': {
                'human_name': 'Настройка Omega Proxy',
                'method': omega_proxy_setup
            }
        }

    @classmethod
    def init_class_variables(cls, root_path):
        cls.PROJECT_PATH = root_path
        cls.CHROME_DATA_PATH = os.path.join(cls.PROJECT_PATH, "data", "profiles")
        cls.DEFAULT_EXTENSIONS_PATH = os.path.join(cls.PROJECT_PATH, "data", "default_extensions")
        cls.CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe" if platform == "win32" else "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

        chrome_driver_name = "chromedriver.exe" if platform == "win32" else "chromedriver"
        cls.CHROME_DRIVER_PATH = os.path.join(cls.PROJECT_PATH, "src", "chrome", "automation", chrome_driver_name)

        cls.PROFILE_WELCOME_PAGE_TEMPLATE_PATH = os.path.join(cls.PROJECT_PATH, "src", "client", "template.html")
        cls.PROFILE_WELCOME_PAGES_OUTPUT_PATH = os.path.join(cls.CHROME_DATA_PATH, "WelcomePages")

    def create_new_profile(self, profile_name: str) -> None:
        try:
            profile_path = self.__get_profile_path(profile_name)
            profile_extensions_path = os.path.join(profile_path, "Extensions")

            os.makedirs(profile_path)  # can trigger FileExistsError
            os.makedirs(profile_extensions_path, exist_ok=True)

            logger.info(f'✅ {profile_name} - профиль создан')
        except FileExistsError:
            logger.warning(f'⚠️ {profile_name} - профиль уже существует')
        except Exception as e:
            logger.error(f'❌️  {profile_name} - не удалось создать профиль')
            logger.debug(f'{profile_name} - не удалось создать профиль, причина: {e}')

    def launch_profile(self, profile_name: str) -> None:
        try:
            launch_args = self.__create_launch_flags(profile_name)

            with open(os.devnull, 'w') as devnull:  # to avoid Chrome log spam
                subprocess.Popen([Chrome.CHROME_PATH, *launch_args], stdout=devnull, stderr=devnull)

            logger.info(f'✅ {profile_name} - профиль запущен')
        except Exception as e:
            logger.error(f'❌  {profile_name} - не удалось запустить профиль')
            logger.debug(f'{profile_name} - не удалось запустить профиль, причина: {e}')

    def run_scripts(self, profile_name: str, startup_scripts) -> None:
        try:
            launch_args = self.__create_launch_flags(profile_name, True)

            with open(os.devnull, 'w') as devnull:
                chrome_process = subprocess.Popen([Chrome.CHROME_PATH, *launch_args], stdout=devnull, stderr=devnull)

            logger.debug(f'{profile_name} - профиль запущен')
            time.sleep(1)

            logger.debug(f'{profile_name} - подключаюсь к порту {self.debug_ports[profile_name]}')
            driver = establish_connection(self.debug_ports[profile_name], Chrome.CHROME_DRIVER_PATH)
            logger.debug(f'{profile_name} - соединение установлено')

            for script in startup_scripts:
                try:
                    human_name = self.automation_scripts[script]['human_name']
                    logger.info(f'ℹ️ {profile_name} - запускаю скрипт "{human_name}"')
                    self.automation_scripts[script]['method'](profile_name, driver)
                    logger.info(f'✅ {profile_name} - скрипт "{human_name}" выполнен')
                except Exception as e:
                    human_name = self.automation_scripts[script]['human_name']
                    logger.error(f'❌  {profile_name} - скрипт "{human_name}" завершен с ошибкой')
                    logger.debug(f'{profile_name} - скрипт "{human_name}" завершен с ошибкой, причина: {e}')
                    time.sleep(1000)

        except Exception as e:
            logger.error(f'❌  {profile_name} - не удалось запустить профиль, выполнение скриптов прервано')
            logger.debug(f'{profile_name} - не удалось запустить профиль, причина: {e}')
            return

        time.sleep(1)

        try:
            chrome_process.terminate()
            chrome_process.wait()
            logger.debug(f'{profile_name} - профиль закрыт')
        except Exception as e:
            logger.error(f'❌  {profile_name} - не удалось закрыть профиль')
            logger.debug(f'{profile_name} - не удалось закрыть профиль, причина: {e}')

    @staticmethod
    def get_profiles_list() -> list[str]:
        profiles = []
        for item in os.listdir(Chrome.CHROME_DATA_PATH):
            item_path = os.path.join(Chrome.CHROME_DATA_PATH, item)

            if os.path.isdir(item_path) and item.startswith("Profile"):
                profiles.append(item.replace('Profile ', ''))

        return profiles

    def __create_launch_flags(self, profile_name: str, debug: bool = False) -> list[str]:
        profile_path = self.__get_profile_path(profile_name)
        profile_extensions_path = os.path.join(profile_path, "Extensions")
        profile_html_path = self.__get_profile_welcome_page(profile_name)

        all_extensions = []
        for ext_id in os.listdir(profile_extensions_path):
            versions_dir = os.path.join(profile_extensions_path, ext_id)
            if os.path.isdir(versions_dir):
                for version in os.listdir(versions_dir):
                    version_path = os.path.join(versions_dir, version)
                    if os.path.isfile(os.path.join(version_path, "manifest.json")):
                        all_extensions.append(version_path)

        load_arg = ",".join(all_extensions)

        flags = [
            f"--user-data-dir={Chrome.CHROME_DATA_PATH}",
            f"--profile-directory={f'Profile {profile_name}'}",
            "--no-first-run",
            f"--load-extension={load_arg}",
            f"file:///{profile_html_path}",
            "--no-sync",
            "--disable-features=IdentityConsistency",
            "--disable-accounts-receiver"
        ]

        if debug:
            free_port = self.__find_free_port()
            if free_port:
                self.debug_ports[profile_name] = free_port
                flags.append(f'--remote-debugging-port={free_port}')
            else:
                logger.warning(f'⚠️ {profile_name} - отсутствуют свободные порты для подключения')

        return flags

    @staticmethod
    def __get_profile_path(profile_name: str) -> str:
        return os.path.join(Chrome.CHROME_DATA_PATH, f'Profile {profile_name}')

    @staticmethod
    def __get_profile_welcome_page(profile_name: str):
        os.makedirs(Chrome.PROFILE_WELCOME_PAGES_OUTPUT_PATH, exist_ok=True)
        profile_welcome_page_path = os.path.join(Chrome.PROFILE_WELCOME_PAGES_OUTPUT_PATH, f"{profile_name}.html")

        # USE CACHE
        # if os.path.exists(profile_welcome_page_path):
        #     return profile_welcome_page_path

        with open(Chrome.PROFILE_WELCOME_PAGE_TEMPLATE_PATH, 'r') as template_file:
            template_content = template_file.read()

        profile_page_content = template_content.replace("{{ profile_name }}", profile_name)

        with open(profile_welcome_page_path, 'w') as profile_page_file:
            profile_page_file.write(profile_page_content)

        return profile_welcome_page_path

    def __find_free_port(self, start_port=9222, max_port=9300) -> int | None:
        for port in range(start_port, max_port):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                result = s.connect_ex(('127.0.0.1', port))
                if result != 0 and port not in self.chosen_debug_ports:
                    self.chosen_debug_ports.append(port)
                    return port

        return None
