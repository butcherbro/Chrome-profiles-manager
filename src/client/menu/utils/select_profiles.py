import re
import questionary
from loguru import logger

from src.utils.helpers import get_profiles_list, get_comments_for_profiles
from src.client.menu.utils.helpers import custom_style


def select_profiles() -> list[str] | None:
    profiles_list_sorted = get_all_sorted_profiles()
    if not profiles_list_sorted:
        logger.error("⛔  Профили отсутствуют")
        return

    select_options = [
        '📋 выбрать из списка',
        '📝 вписать названия',
        '📒 выбрать по комментарию',
        '📦 выбрать все',
        '🏠 назад в меню'
    ]

    select_method = questionary.select(
        "Способ выбора профилей",
        choices=select_options,
        style=custom_style
    ).ask()

    if 'назад в меню' in select_method:
        return

    selected_profiles = []
    if 'выбрать из списка' in select_method:
        selected_profiles = paginate_profiles(profiles_list_sorted)

    elif 'вписать названия' in select_method:
        names_raw = questionary.text(
            "Впиши названия профилей через запятую\n",
            style=custom_style
        ).ask()

        names = list(set(i.strip() for i in re.split(r'[\n,]+', names_raw) if i.strip()))
        existing_profile_names = get_profiles_list()
        names_to_skip = [name for name in names if name not in existing_profile_names]

        if names_to_skip:
            logger.warning(f'⚠️ Пропускаем профили {names_to_skip}, профили не найдены')

        selected_profiles = [name for name in names if name not in names_to_skip]

    elif 'выбрать по комментарию' in select_method:
        comment_substring = questionary.text(
            "Впиши текст, который должен содержать комментарий\n",
            style=custom_style
        ).ask()

        for profile in profiles_list_sorted:
            result = get_comments_for_profiles()
            if result["success"]:
                comments = result["comments"]
            else:
                logger.warning(f"⚠️ Не удалось загрузить комментарии, причина: {result.get('description')}")
                comments = {}

            comment = comments.get(profile, '')
            if comment_substring.lower() in comment.lower():
                selected_profiles.append(profile)

    elif 'выбрать все' in select_method:
        selected_profiles = profiles_list_sorted

    if not selected_profiles:
        logger.warning("⚠️ Профили не выбраны")
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
            f"Выбери профили для запуска (страница {current_page + 1} из {total_pages})",
            choices=page_profiles,
            style=custom_style,
        ).ask()

        selected_profiles.extend(selected_profiles_on_page)

        current_page += 1

    return selected_profiles


def get_all_sorted_profiles() -> list[str] | None:
    """
    Получает отсортированный список профилей.
    Числовые профили (созданные в программе) идут первыми, отсортированные по номеру.
    Именованные профили (импортированные из ZennoPoster) идут вторыми, отсортированные по алфавиту.
    """
    profiles_list = get_profiles_list()
    if not profiles_list:
        return

    # Разделяем профили на числовые (созданные в программе) и именованные (из ZennoPoster)
    numeric_profiles = [profile for profile in profiles_list if profile.isdigit()]
    named_profiles = [profile for profile in profiles_list if not profile.isdigit()]
    
    # Сортируем числовые профили как числа
    numeric_profiles.sort(key=int)
    # Сортируем именованные профили по алфавиту
    named_profiles.sort()

    # Объединяем отсортированные списки: сначала числовые, потом именованные
    profiles_list_sorted = numeric_profiles + named_profiles
    return profiles_list_sorted
