import json
import os

import questionary
from loguru import logger

from src.utils.helpers import set_comments_for_profiles
from .utils import select_profiles, custom_style


def update_comments():
    selected_profiles = select_profiles()
    if not selected_profiles:
        return

    new_comment = questionary.text(
        "Впиши комментарий\n",
        style=custom_style
    ).ask()

    result = set_comments_for_profiles(selected_profiles, new_comment)

    if result["success"]:
        logger.info("✅ Комментарии обновлены")
    else:
        logger.warning(f"⚠️ Не удалось обновить комментарии, причина: {result["description"]}")



