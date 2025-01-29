from loguru import logger
from rich.table import Table
from rich.console import Console

from src.chrome.chrome import Chrome
from .utils import get_all_sorted_profiles, get_comments_for_profiles


def show_all_profiles(chrome: Chrome):
    profiles_list_sorted = get_all_sorted_profiles(chrome)
    if not profiles_list_sorted:
        logger.error("❌  Профиля отсутствуют")
        return

    console = Console()
    table = Table(style="cyan")
    table.add_column("Название", style="magenta")
    table.add_column("Комментарии", style="green")

    comments = get_comments_for_profiles()
    for profile in profiles_list_sorted:
        comment = comments.get(profile, '')
        table.add_row(profile, comment)

    console.print(table)