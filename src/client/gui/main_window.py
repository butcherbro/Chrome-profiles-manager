from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, 
    QPushButton, QApplication, QMessageBox
)
from PyQt6.QtCore import Qt
from loguru import logger
import os

from src.client.menu import (
    launch_multiple_profiles,
    create_multiple_profiles,
    kill_chrome_processes
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
from .windows.create_profiles_window import CreateProfilesWindow
from src.manager.extensions.downloader import ExtensionDownloader
from src.utils.constants import DEFAULT_EXTENSIONS_PATH
from .windows.playwright_scripts_window import PlaywrightScriptsWindow


class MainWindow(QMainWindow):
    """Главное окно приложения"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chrome Profiles Manager")
        self.setMinimumSize(400, 600)
        
        # Загружаем расширения по умолчанию если их нет
        self.download_default_extensions()
        
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Основной layout
        layout = QVBoxLayout(central_widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Создаем кнопки
        self.create_buttons(layout)
        
    def download_default_extensions(self):
        """Загружает необходимые расширения из Chrome Web Store или локальных файлов"""
        try:
            downloader = ExtensionDownloader()
            
            # Проверяем наличие SwitchyOmega
            if not (DEFAULT_EXTENSIONS_PATH / "padekgcemlokbadohgkifijomclgjgif").exists():
                logger.info("⏳ Добавление SwitchyOmega...")
                # Сначала пробуем загрузить из магазина
                if not downloader.download_from_store("padekgcemlokbadohgkifijomclgjgif"):
                    # Если не получилось, ищем локальную версию
                    local_path = DEFAULT_EXTENSIONS_PATH / "Proxy-SwitchyOmega"
                    if local_path.exists():
                        if downloader.add_extension(str(local_path)):
                            logger.success("✅ SwitchyOmega успешно добавлен из локальной папки")
                        else:
                            logger.error("❌ Не удалось добавить SwitchyOmega из локальной папки")
                    else:
                        logger.error("❌ SwitchyOmega не найден ни в магазине, ни локально")
            
            # Проверяем наличие MetaMask
            if not (DEFAULT_EXTENSIONS_PATH / "nkbihfbeogaeaoehlefnkodbefgpgknn").exists():
                logger.info("⏳ Загрузка MetaMask...")
                if downloader.download_from_store("nkbihfbeogaeaoehlefnkodbefgpgknn"):
                    logger.success("✅ MetaMask успешно загружен")
                else:
                    logger.error("❌ Не удалось загрузить MetaMask")
                    
        except Exception as e:
            logger.error("❌ Ошибка при загрузке расширений")
            logger.debug(f"Причина: {str(e)}")
        
    def create_buttons(self, layout):
        """Создание кнопок главного меню"""
        buttons_data = {
            '🚀 Запуск профилей': self.launch_profiles,
            '📖 Просмотр профилей': self.show_profiles,
            '📝 Задать комментарии': self.update_comments,
            '🤖 Скрипты [Selenium]': self.run_chrome_scripts,
            '🚀 Скрипты [Playwright]': self.run_playwright_scripts,
            '🧩 Работа с расширениями': self.manage_extensions,
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
    
    def run_playwright_scripts(self):
        """Открытие окна скриптов Playwright"""
        try:
            scripts_window = PlaywrightScriptsWindow(self)
            scripts_window.exec()
        except Exception as e:
            self.show_error(f"Ошибка при запуске скриптов: {str(e)}")
    
    def manage_extensions(self):
        """Открытие окна управления расширениями"""
        extensions_window = ExtensionsWindow(self)
        extensions_window.show()
    
    def create_profiles(self):
        """Создание профилей"""
        try:
            create_window = CreateProfilesWindow(self)
            create_window.exec()
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
    
    def show_success(self, message):
        """Показ сообщения об успехе"""
        QMessageBox.information(self, "Успех", message)
    
    def show_error(self, message):
        """Показ сообщения об ошибке"""
        logger.error(message)
        QMessageBox.critical(self, "Ошибка", message) 