import os

from loguru import logger

from src.utils.constants import *
from .scripts import *


class Manager:
    def __init__(self):

        self.scripts = {
            'test_script': {
                'human_name': 'Тестовый скрипт',
                'method': test_script,
            }
        }

    def run_scripts(self, profile_name: str, scripts_list: list[str]) -> None:
        for script in scripts_list:
            try:
                human_name = self.scripts[script]['human_name']
                logger.info(f'ℹ️ {profile_name} - запускаю скрипт "{human_name}"')
                script_data_path = os.path.join(DATA_PATH, 'scripts', "manager", script)
                self.scripts[script]['method'](
                    profile_name,
                    script_data_path
                )
                logger.info(f'✅ {profile_name} - скрипт "{human_name}" выполнен')
            except Exception as e:
                human_name = self.scripts[script]['human_name']
                logger.error(f'⛔ {profile_name} - скрипт "{human_name}" завершен с ошибкой')
                logger.debug(f'{profile_name} - скрипт "{human_name}" завершен с ошибкой, причина: {e}')
