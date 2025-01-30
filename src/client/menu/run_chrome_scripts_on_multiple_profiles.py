from random import shuffle

import questionary
from loguru import logger

from src.chrome.chrome import Chrome
from .utils import select_profiles, custom_style


def run_chrome_scripts_on_multiple_profiles():
    selected_profiles = select_profiles()
    if not selected_profiles:
        return

    chrome = Chrome()
    scripts = {
        value['human_name']: key
        for key, value in chrome.scripts.items()
    }

    chosen_scripts_human_names = questionary.checkbox(
        "Выбери скрипты",
        choices=list(scripts.keys()),
        style=custom_style
    ).ask()

    chosen_scripts = [scripts[name] for name in chosen_scripts_human_names]

    if not chosen_scripts:
        logger.warning('⚠️ Скрипты не выбраны')
        return

    if len(chosen_scripts) > 1:
        shuffle_choice = questionary.select(
            "Рандомить порядок выполнения скриптов?",
            choices=[
                '✅  да',
                '❌  нет'
            ],
            style=custom_style
        ).ask()

        if 'да' in shuffle_choice:
            shuffle(chosen_scripts)

    for name in selected_profiles:
        chrome.run_scripts(
            str(name),
            chosen_scripts
        )
