import questionary
from loguru import logger

from src.utils.helpers import get_profiles_list
from src.client.menu.utils.helpers import custom_style, get_comments_for_profiles


def select_profiles() -> list[str] | None:
    profiles_list_sorted = get_all_sorted_profiles()
    if not profiles_list_sorted:
        logger.error("❌  Профиля отсутствуют")
        return

    select_options = [
        '📋 выбрать из списка',
        '🖐 вписать названия',
        '📒 выбрать по комментарию',
        '📦 выбрать все',
        '⬅️ назад'
    ]

    select_method = questionary.select(
        "Способ выбора профилей",
        choices=select_options,
        style=custom_style
    ).ask()

    if select_method == '⬅️ назад':
        return

    selected_profiles = []
    if select_method == '📋 выбрать из списка':
        selected_profiles = paginate_profiles(profiles_list_sorted)

    elif select_method == '🖐 вписать названия':
        names_raw = questionary.text(
            "Впиши названия профилей через запятую\n",
            style=custom_style
        ).ask()

        names = list(set(i.strip() for i in names_raw.split(',') if i.strip()))
        existing_profile_names = get_profiles_list()
        names_to_skip = [name for name in names if name not in existing_profile_names]

        if names_to_skip:
            logger.warning(f'⚠️ Пропускаем профиля {names_to_skip}, профиля не найдены')

        selected_profiles = [name for name in names if name not in names_to_skip]

    elif select_method == '📒 выбрать по комментарию':
        comment_substring = questionary.text(
            "Впиши текст, который должен содержать комментарий\n",
            style=custom_style
        ).ask()

        for profile in profiles_list_sorted:
            comments = get_comments_for_profiles()
            comment = comments.get(profile, '')
            if comment_substring.lower() in comment.lower():
                selected_profiles.append(profile)

    elif select_method == '📦 выбрать все':
        selected_profiles = profiles_list_sorted

    if not selected_profiles:
        logger.warning("⚠️ Профиля не выбраны")
        return

    return selected_profiles


def paginate_profiles(profiles, items_per_page=10):
    total_pages = (len(profiles) + items_per_page - 1) // items_per_page
    current_page = 0
    selected_profiles = []

    while current_page < total_pages:
        start = current_page * items_per_page
        end = min(start + items_per_page, len(profiles))
        page_profiles = profiles[start:end]

        selected_profiles_on_page = questionary.checkbox(
            f"Выбери профиля для запуска (страница {current_page + 1} из {total_pages})",
            choices=page_profiles,
            style=custom_style,
        ).ask()

        selected_profiles.extend(selected_profiles_on_page)

        current_page += 1

    return selected_profiles


def get_all_sorted_profiles() -> list[str] | None:
    profiles_list = get_profiles_list()
    if not profiles_list:
        return

    numeric_profiles = [profile for profile in profiles_list if profile.isdigit()]
    non_numeric_profiles = [profile for profile in profiles_list if not any(char.isdigit() for char in profile)]
    numeric_profiles.sort(key=int)
    non_numeric_profiles.sort()

    profiles_list_sorted = numeric_profiles + non_numeric_profiles
    return profiles_list_sorted
