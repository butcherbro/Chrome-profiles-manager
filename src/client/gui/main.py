from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtCore import QObject, Slot, Signal, Property
from PySide6.QtGui import QGuiApplication
import sys
import os
import shutil
from src.chrome.chrome import Chrome
from config import general_config
import src.client.menu as menu
from src.utils.helpers import kill_chrome_processes

class ProfileManager(QObject):
    profilesChanged = Signal()
    
    def __init__(self):
        super().__init__()
        self._profiles = []
        self.chrome = Chrome()
        self.load_profiles()
    
    def load_profiles(self):
        from src.utils.helpers import get_profiles_list
        self._profiles = get_profiles_list()
        self.profilesChanged.emit()
    
    @Property(list, notify=profilesChanged)
    def profiles(self):
        return self._profiles

    # Повторяем структуру консольного меню
    @Slot(result=bool)
    def launch_multiple_profiles(self):
        try:
            menu.launch_multiple_profiles()
            self.load_profiles()
            return True
        except Exception as e:
            print(f"Error launching profiles: {e}")
            return False

    @Slot(result=bool)
    def show_all_profiles(self):
        try:
            menu.show_all_profiles()
            return True
        except Exception as e:
            print(f"Error showing profiles: {e}")
            return False

    @Slot(result=bool)
    def update_comments(self):
        try:
            menu.update_comments()
            self.load_profiles()
            return True
        except Exception as e:
            print(f"Error updating comments: {e}")
            return False

    @Slot(result=bool)
    def run_chrome_scripts(self):
        try:
            menu.run_chrome_scripts_on_multiple_profiles()
            return True
        except Exception as e:
            print(f"Error running chrome scripts: {e}")
            return False

    @Slot(result=bool)
    def run_manager_scripts(self):
        try:
            menu.run_manager_scripts_on_multiple_profiles()
            return True
        except Exception as e:
            print(f"Error running manager scripts: {e}")
            return False

    @Slot(result=bool)
    def manage_extensions(self):
        try:
            menu.manage_extensions()
            self.load_profiles()
            return True
        except Exception as e:
            print(f"Error managing extensions: {e}")
            return False

    @Slot(result=bool)
    def create_multiple_profiles(self):
        try:
            menu.create_multiple_profiles()
            self.load_profiles()
            return True
        except Exception as e:
            print(f"Error creating profiles: {e}")
            return False

    @Slot(result=bool)
    def kill_chrome_processes(self):
        try:
            kill_chrome_processes()
            return True
        except Exception as e:
            print(f"Error killing chrome processes: {e}")
            return False

def main():
    app = QGuiApplication(sys.argv)
    engine = QQmlApplicationEngine()
    
    profile_manager = ProfileManager()
    engine.rootContext().setContextProperty("profileManager", profile_manager)
    
    # Загружаем основной QML файл
    engine.load("src/client/gui/qml/main.qml")
    
    if not engine.rootObjects():
        return -1
    
    return app.exec() 