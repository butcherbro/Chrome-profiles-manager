import sys
import os
from PyQt6.QtWidgets import QApplication
from src.client.gui.main_window import MainWindow
from src.utils.constants import DATA_PATH
from loguru import logger

def is_app_running():
    """Проверяет, запущено ли уже приложение"""
    lock_file = DATA_PATH / "app.lock"
    
    if lock_file.exists():
        # Проверяем валидность PID в файле
        try:
            with open(lock_file, 'r') as f:
                pid = int(f.read().strip())
            # Проверяем, существует ли процесс с таким PID
            os.kill(pid, 0)  # Не убивает процесс, а только проверяет его существование
            return True
        except (OSError, ValueError):
            # Если процесс не существует или файл поврежден
            try:
                os.remove(lock_file)
            except:
                pass
    return False

def create_lock_file():
    """Создает файл-блокировку с текущим PID"""
    lock_file = DATA_PATH / "app.lock"
    with open(lock_file, 'w') as f:
        f.write(str(os.getpid()))

def remove_lock_file():
    """Удаляет файл-блокировку при выходе"""
    try:
        lock_file = DATA_PATH / "app.lock"
        if lock_file.exists():
            os.remove(lock_file)
    except:
        pass

if __name__ == "__main__":
    # Проверяем, не запущено ли уже приложение
    if is_app_running():
        logger.warning("⚠️ Приложение уже запущено")
        sys.exit(1)
        
    # Создаем файл-блокировку
    create_lock_file()
    
    try:
        app = QApplication(sys.argv)
        
        # Удаляем lock-файл при выходе
        app.aboutToQuit.connect(remove_lock_file)
        
        window = MainWindow()
        window.show()
        
        sys.exit(app.exec())
        
    except Exception as e:
        logger.error(f"⛔ Ошибка при запуске приложения: {str(e)}")
        remove_lock_file()
        sys.exit(1) 