from random import shuffle

import questionary
from loguru import logger

from src.chrome.playwright_chrome import PlaywrightChrome
from src.scripts import register_all_scripts
from .utils import select_profiles, custom_style


def run_playwright_scripts_on_multiple_profiles():
    """
    Запускает выбранные скрипты Playwright для выбранных профилей
    """
    selected_profiles = select_profiles()
    if not selected_profiles:
        return

    # Создаем экземпляр PlaywrightChrome
    pw = PlaywrightChrome()
    
    # Регистрируем все доступные скрипты
    register_all_scripts(pw)
    
    # Получаем список скриптов для выбора
    scripts = {
        value['human_name']: key
        for key, value in pw.scripts.items()
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

    headless_choice = questionary.select(
        "Использовать Headless Mode?",
        choices=[
            '✅  да',
            '❌  нет'
        ],
        style=custom_style
    ).ask()

    headless = True if 'да' in headless_choice else False

    # Запускаем скрипты для каждого профиля
    for name in selected_profiles:
        try:
            logger.info(f"🚀 Запускаем скрипты для профиля {name}")
            pw.run_scripts(
                str(name),
                chosen_scripts,
                headless
            )
            logger.success(f"✅ Скрипты для профиля {name} выполнены")
        except Exception as e:
            logger.error(f"❌ Ошибка при выполнении скриптов для профиля {name}: {e}") 