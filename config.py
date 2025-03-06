import os

general_config = {
    'show_debug_logs': False,                   # Показывать DEBUG логи в консоли (True / False)
    'max_workers': 10,                          # Максимальное количество потоков для многопоточных процессов (1+)
    'chrome_data_path': os.path.expanduser('~/Library/Application Support/Google/Chrome/Profile *'),  # Путь к профилям Chrome
    'install_default_extensions_on_launch': True  # Устанавливать расширения из папки по умолчанию при запуске профилей (True / False)
}
