from loguru import logger
from rich.table import Table
from rich.console import Console

from src.utils.helpers import get_comments_for_profiles
from .utils import get_all_sorted_profiles


def show_all_profiles():
    profiles_list_sorted = get_all_sorted_profiles()
    if not profiles_list_sorted:
        logger.error("⛔  Профили отсутствуют")
        return

    console = Console()
    table = Table(style="cyan")
    table.add_column("Название", style="magenta")
    table.add_column("Комментарии", style="green")

    result = get_comments_for_profiles()
    if result["success"]:
        comments = result["comments"]
    else:
        logger.warning(f"⚠️ Не удалось загрузить комментарии, причина: {result["description"]}")
        comments = {}

    for profile in profiles_list_sorted:
        comment = comments.get(profile, '')
        table.add_row(profile, comment)

    console.print(table)
