import questionary
from loguru import logger

from src.utils.helpers import get_profiles_list
from src.chrome.chrome import Chrome
from .utils import custom_style

def create_multiple_profiles(chrome: Chrome) -> None:
    create_methods = [
        '🖐 задать вручную',
        '🤖 задать автоматически',
        '⬅️ назад'
    ]

    create_method = questionary.select(
        "Выбери способ создания имен",
        choices=create_methods,
        style=custom_style
    ).ask()

    if not create_method:
        logger.warning("⚠️ Активность не выбрана")
        return

    if create_method == '⬅️ назад':
        return

    existing_profile_names = get_profiles_list()

    profiles_to_create = []

    if create_method == '🖐 задать вручную':
        selected_names = questionary.text(
            "Впиши названия профилей через запятую\n",
            style=custom_style
        ).ask()
        selected_names = list(set(i.strip() for i in selected_names.split(',') if i.strip()))
        names_to_skip = list(set(existing_profile_names) & set(selected_names))

        if names_to_skip:
            logger.warning(f'⚠️ Пропускаем профиля {names_to_skip}, имена уже заняты')

        profiles_to_create = [item for item in selected_names if item not in names_to_skip]

    elif create_method == '🤖 задать автоматически':
        amount = questionary.text(
            "Впиши количество профилей для создания\n",
            style=custom_style
        ).ask()

        try:
            amount = int(amount)
        except ValueError:
            logger.warning('⚠️ Неверное количество')
            return

        highest_existing_numeric_name = 0

        for name in existing_profile_names:
            try:
                num = int(name)
                if num > highest_existing_numeric_name:
                    highest_existing_numeric_name = num
            except ValueError:
                continue

        start = highest_existing_numeric_name + 1
        profiles_to_create = list(range(start, start + amount))

    for name in profiles_to_create:
        chrome.create_new_profile(str(name))