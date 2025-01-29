import subprocess
import time
import socket
import os

from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from loguru import logger

from src.utils.helpers import set_comments_for_profiles
from src.utils.constants import *
from .scripts import *


class Chrome:
    def __init__(self):
        self.debug_ports = {}
        self.chosen_debug_ports = []

        self.scripts = {
            'chrome_initial_setup': {
                'human_name': 'Первичная настройка Chrome',
                'method': chrome_initial_setup,
            },
            'omega_proxy_setup': {
                'human_name': 'Настройка Omega Proxy',
                'method': omega_proxy_setup
            },
            'agent_switcher': {
                'human_name': 'Настройка Agent Switcher',
                'method': agent_switcher
            }
        }

    def create_new_profile(self, profile_name: str) -> None:
        try:
            profile_path = self.__get_profile_path(profile_name)
            profile_extensions_path = os.path.join(profile_path, "Extensions")

            os.makedirs(profile_path)  # can trigger FileExistsError
            os.makedirs(profile_extensions_path, exist_ok=True)

            set_comments_for_profiles(profile_name, "")  # reset comment

            logger.info(f'✅ {profile_name} - профиль создан')
        except FileExistsError:
            logger.warning(f'⚠️ {profile_name} - профиль уже существует')
        except Exception as e:
            logger.error(f'❌️ {profile_name} - не удалось создать профиль')
            logger.debug(f'{profile_name} - не удалось создать профиль, причина: {e}')

    def init_profile_preferences(self, profile_name: str) -> bool:
        initialized = False

        try:
            launch_args = self.__create_launch_flags(profile_name, False)

            with open(os.devnull, 'w') as devnull:  # to avoid Chrome log spam
                chrome_process = subprocess.Popen([CHROME_PATH, *launch_args], stdout=devnull, stderr=devnull)

            logger.info(f'✅ {profile_name} - профиль запущен')
        except Exception as e:
            logger.error(f'❌ {profile_name} - не удалось запустить профиль для инициализации настроек')
            logger.debug(f'{profile_name} - не удалось запустить профиль для инициализации настроек, причина: {e}')
            return initialized

        time.sleep(2)

        try:
            chrome_process.terminate()
            chrome_process.wait()
            logger.debug(f'{profile_name} - профиль закрыт')
        except Exception as e:
            logger.error(f'❌ {profile_name} - не удалось закрыть профиль')
            logger.debug(f'{profile_name} - не удалось закрыть профиль, причина: {e}')

        return initialized

    def launch_profile(self, profile_name: str, debug=False) -> subprocess.Popen | None:
        try:
            launch_args = self.__create_launch_flags(profile_name, debug)

            with open(os.devnull, 'w') as devnull:  # to avoid Chrome log spam
                chrome_process = subprocess.Popen([CHROME_PATH, *launch_args], stdout=devnull, stderr=devnull)

            logger.info(f'✅ {profile_name} - профиль запущен')

            return chrome_process
        except Exception as e:
            logger.error(f'❌ {profile_name} - не удалось запустить профиль')
            logger.debug(f'{profile_name} - не удалось запустить профиль, причина: {e}')

    def run_scripts(self, profile_name: str, scripts_list: list[str]) -> None:
        try:
            chrome_process = self.launch_profile(profile_name, True)
            if not chrome_process:
                raise Exception('не удалось запустить браузер')

            time.sleep(1)

            logger.debug(f'{profile_name} - подключаюсь к порту {self.debug_ports[profile_name]}')
            driver = self.__establish_debug_port_connection(profile_name)
            logger.debug(f'{profile_name} - соединение установлено')

            logger.debug(f'{profile_name} - скрипты для прогона: {scripts_list}')
            for script in scripts_list:
                try:
                    human_name = self.scripts[script]['human_name']
                    logger.info(f'ℹ️ {profile_name} - запускаю скрипт "{human_name}"')
                    script_data_path = os.path.join(DATA_PATH, 'scripts', "chrome", script)
                    self.scripts[script]['method'](
                        profile_name,
                        script_data_path,
                        driver
                    )
                    logger.info(f'✅ {profile_name} - скрипт "{human_name}" выполнен')
                except Exception as e:
                    human_name = self.scripts[script]['human_name']
                    logger.error(f'❌ {profile_name} - скрипт "{human_name}" завершен с ошибкой')
                    logger.debug(f'{profile_name} - скрипт "{human_name}" завершен с ошибкой, причина: {e}')

        except Exception as e:
            logger.error(f'❌ {profile_name} - не удалось запустить профиль, выполнение скриптов прервано')
            logger.debug(f'{profile_name} - не удалось запустить профиль, причина: {e}')
            return

        time.sleep(1)

        try:
            driver.quit()
            chrome_process.terminate()
            chrome_process.wait()
            logger.debug(f'{profile_name} - профиль закрыт')
        except Exception as e:
            logger.error(f'❌ {profile_name} - не удалось закрыть профиль')
            logger.debug(f'{profile_name} - не удалось закрыть профиль, причина: {e}')

    def __establish_debug_port_connection(self, profile_name) -> webdriver.Chrome:
        debug_port = self.debug_ports[profile_name]

        chrome_options = Options()
        chrome_options.add_experimental_option("debuggerAddress", f"127.0.0.1:{debug_port}")
        service = Service(CHROME_DRIVER_PATH)
        driver = webdriver.Chrome(service=service, options=chrome_options)

        return driver

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
            f"--user-data-dir={CHROME_DATA_PATH}",
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
        return os.path.join(CHROME_DATA_PATH, f'Profile {profile_name}')

    @staticmethod
    def __get_profile_welcome_page(profile_name: str):
        os.makedirs(PROFILE_WELCOME_PAGES_OUTPUT_PATH, exist_ok=True)
        profile_welcome_page_path = os.path.join(PROFILE_WELCOME_PAGES_OUTPUT_PATH, f"{profile_name}.html")

        # USE CACHE
        # if os.path.exists(profile_welcome_page_path):
        #     return profile_welcome_page_path

        with open(PROFILE_WELCOME_PAGE_TEMPLATE_PATH, 'r') as template_file:
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
