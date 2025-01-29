from sys import stderr

import questionary
from loguru import logger

import src.client.menu as menu
from config import general_config

logger.remove()
logger_level = "DEBUG" if general_config['show_debug_logs'] else "INFO"
log_format = "<white>{time:HH:mm:ss}</white> | <level>{level: <8}</level> | <white>{message}</white>"
logger.add(stderr, level=logger_level, format=log_format)
logger.add("data/debug_log.log", level="DEBUG", format=log_format)


def main():
    main_activities_list = {
        '📖 просмотр профилей': menu.show_all_profiles,
        '🚀 запуск профилей': menu.launch_multiple_profiles,
        '🤖 прогон chrome скриптов': menu.run_chrome_scripts_on_multiple_profiles,
        '🤖 прогон manager скриптов': menu.run_manager_scripts_on_multiple_profiles,
        '🆕 создание профилей': menu.create_multiple_profiles,
        '🧩 работа с расширениями': menu.manage_extensions,
        '🖊 задать комментарии': menu.update_comments,
        '🚪 выход': None
    }

    while True:
        main_activity = questionary.select(
            "Выбери действие",
            choices=list(main_activities_list.keys()),
            style=menu.custom_style
        ).ask()

        if not main_activity or main_activity == '🚪 выход':
            logger.info("Работа завершена")
            exit(0)

        else:
            main_activities_list[main_activity]()  # TODO: pass arguments using mapping
            continue


if __name__ == '__main__':
    main()
