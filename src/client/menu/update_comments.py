import json
import os

import questionary

from src.chrome.chrome import Chrome
from .utils import select_profiles, custom_style, get_comments_for_profiles


def update_comments(chrome: Chrome):
    selected_profiles = select_profiles(chrome)
    if not selected_profiles:
        return

    new_comment = questionary.text(
        "Впиши комментарий\n",
        style=custom_style
    ).ask()

    comments = get_comments_for_profiles()

    for profile in selected_profiles:
        comments[profile] = new_comment

    comments_path = os.path.join('data', 'comments_for_profiles.json')
    with open(comments_path, 'w', encoding="utf-8") as f:
        json.dump(comments, f, indent=4, ensure_ascii=False)