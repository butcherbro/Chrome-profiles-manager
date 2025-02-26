from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, 
    QPushButton, QApplication, QMessageBox
)
from PyQt6.QtCore import Qt
from loguru import logger

from src.client.menu import (
    launch_multiple_profiles,
    create_multiple_profiles,
    kill_chrome_processes,
    copy_extensions_to_all_profiles
)
from src.chrome.chrome import Chrome
from src.manager.manager import Manager
from .windows.profiles_window import ProfilesWindow
from .windows.comments_window import CommentsWindow
from .windows.extensions_window import ExtensionsWindow
from .windows.launch_profiles_window import LaunchProfilesWindow
from .windows.scripts_window import ScriptsWindow
from .windows.zenno_import_window import ZennoImportWindow
from .windows.cache_cleanup_window import CacheCleanupWindow


class MainWindow(QMainWindow):
    """Главное окно приложения"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chrome Profiles Manager")
        self.setMinimumSize(400, 600)
        
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Основной layout
        layout = QVBoxLayout(central_widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Создаем кнопки
        self.create_buttons(layout)
        
    def create_buttons(self, layout):
        """Создание кнопок главного меню"""
        buttons_data = {
            '🚀 Запуск профилей': self.launch_profiles,
            '📖 Просмотр профилей': self.show_profiles,
            '📝 Задать комментарии': self.update_comments,
            '🤖 Прогон скриптов [chrome]': self.run_chrome_scripts,
            '🤖 Прогон скриптов [manager]': self.run_manager_scripts,
            '🧩 Работа с расширениями': self.manage_extensions,
            '🔄 Копировать расширения': self.copy_extensions,
            '🗑️ Очистка кэша': self.cleanup_cache,
            '➕ Создание профилей': self.create_profiles,
            '📥 Импорт из ZennoPoster': self.import_from_zenno,
            '💀 Убить процессы Chrome': self.kill_chrome
        }
        
        for text, handler in buttons_data.items():
            button = QPushButton(text)
            button.setMinimumHeight(40)
            button.clicked.connect(handler)
            layout.addWidget(button)
    
    def launch_profiles(self):
        """Запуск профилей"""
        try:
            # Открываем окно выбора профилей
            launch_window = LaunchProfilesWindow(self)
            if launch_window.exec():
                # Если пользователь нажал "Запустить"
                selected_profiles = launch_window.selected_profiles
                if selected_profiles:
                    # Запускаем выбранные профили через существующую функцию
                    launch_multiple_profiles(selected_profiles)
                    self.show_success("Профили успешно запущены")
        except Exception as e:
            self.show_error(f"Ошибка при запуске профилей: {str(e)}")
    
    def show_profiles(self):
        """Открытие окна просмотра профилей"""
        profiles_window = ProfilesWindow(self)
        profiles_window.show()
    
    def update_comments(self):
        """Открытие окна обновления комментариев"""
        comments_window = CommentsWindow(self)
        comments_window.show()
    
    def run_chrome_scripts(self):
        """Запуск скриптов для Chrome"""
        try:
            scripts_window = ScriptsWindow(self, script_type="chrome")
            if scripts_window.exec():
                selected_profiles = scripts_window.selected_profiles
                selected_scripts = scripts_window.selected_scripts
                use_headless = scripts_window.use_headless
                
                if selected_profiles and selected_scripts:
                    chrome = Chrome()
                    for name in selected_profiles:
                        chrome.run_scripts(str(name), selected_scripts, use_headless)
                    self.show_success("Скрипты успешно выполнены")
        except Exception as e:
            self.show_error(f"Ошибка при запуске скриптов: {str(e)}")
    
    def run_manager_scripts(self):
        """Запуск скриптов для менеджера"""
        try:
            scripts_window = ScriptsWindow(self, script_type="manager")
            if scripts_window.exec():
                selected_profiles = scripts_window.selected_profiles
                selected_scripts = scripts_window.selected_scripts
                
                if selected_profiles and selected_scripts:
                    manager = Manager()
                    for name in selected_profiles:
                        manager.run_scripts(str(name), selected_scripts)
                    self.show_success("Скрипты успешно выполнены")
        except Exception as e:
            self.show_error(f"Ошибка при запуске скриптов: {str(e)}")
    
    def manage_extensions(self):
        """Открытие окна управления расширениями"""
        extensions_window = ExtensionsWindow(self)
        extensions_window.show()
    
    def create_profiles(self):
        """Создание профилей"""
        try:
            create_multiple_profiles()
            self.show_success("Профили успешно созданы")
        except Exception as e:
            self.show_error(f"Ошибка при создании профилей: {str(e)}")
    
    def import_from_zenno(self):
        """Импорт профилей из ZennoPoster"""
        try:
            import_window = ZennoImportWindow(self)
            import_window.exec()
        except Exception as e:
            self.show_error(f"Ошибка при импорте профилей: {str(e)}")
    
    def kill_chrome(self):
        """Завершение процессов Chrome"""
        try:
            kill_chrome_processes()
            self.show_success("Процессы Chrome успешно завершены")
        except Exception as e:
            self.show_error(f"Ошибка при завершении процессов: {str(e)}")
    
    def cleanup_cache(self):
        """Открытие окна очистки кэша"""
        cleanup_window = CacheCleanupWindow(self)
        cleanup_window.show()
    
    def copy_extensions(self):
        """Копирование расширений во все профили"""
        try:
            if copy_extensions_to_all_profiles():
                self.show_success("Расширения успешно скопированы во все профили")
            else:
                self.show_error("Не удалось скопировать расширения")
        except Exception as e:
            self.show_error(f"Ошибка при копировании расширений: {str(e)}")
    
    def show_success(self, message):
        """Показ сообщения об успехе"""
        QMessageBox.information(self, "Успех", message)
    
    def show_error(self, message):
        """Показ сообщения об ошибке"""
        logger.error(message)
        QMessageBox.critical(self, "Ошибка", message) 