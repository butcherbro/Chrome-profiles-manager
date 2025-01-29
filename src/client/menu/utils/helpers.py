import json

from loguru import logger
import questionary


custom_style = questionary.Style([
    ('question', 'bold'),
    ('answer', 'fg:#ff9900 bold'),
    ('pointer', 'fg:#ff9900 bold'),
    ('text', 'fg:#4d4d4d'),
    ('disabled', 'fg:#858585 italic')
])


def get_comments_for_profiles() -> dict:
    comments = {}
    try:
        with open('data/comments_for_profiles.json', 'r', encoding="utf-8") as f:
            comments = json.load(f)
    except FileNotFoundError:
        logger.warning("⚠️ Файл с комментариями не найден, комментарии не будут загружены.")
    except json.JSONDecodeError:
        logger.warning("⚠️ Не удалось прочитать файл с комментариями. Комментарии не будут загружены.")

    return comments
