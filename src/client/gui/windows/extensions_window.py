from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QPushButton, QListWidget, QLabel,
    QMessageBox
)
from loguru import logger
import os

from src.utils.helpers import (
    get_all_default_extensions_info,
    get_profiles_extensions_info,
    copy_extension,
    remove_extensions,
    kill_chrome_processes
)
from src.client.menu.utils import get_all_sorted_profiles
from src.utils.constants import DEFAULT_EXTENSIONS_PATH, CHROME_DATA_PATH


class ExtensionsWindow(QDialog):
    """Окно работы с расширениями"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Работа с расширениями")
        self.setMinimumSize(1000, 600)
        
        # Основной layout
        layout = QHBoxLayout(self)
        
        # Левая часть - профили
        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("Выберите профили:"))
        
        self.profiles_list = QListWidget()
        self.profiles_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.load_profiles()
        left_layout.addWidget(self.profiles_list)
        
        layout.addLayout(left_layout)
        
        # Центральная часть - установленные расширения
        center_layout = QVBoxLayout()
        center_layout.addWidget(QLabel("Установленные расширения:"))
        
        self.installed_extensions = QListWidget()
        self.installed_extensions.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        center_layout.addWidget(self.installed_extensions)
        
        remove_button = QPushButton("Удалить выбранные")
        remove_button.clicked.connect(self.remove_selected_extensions)
        center_layout.addWidget(remove_button)
        
        layout.addLayout(center_layout)
        
        # Правая часть - доступные расширения
        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("Доступные расширения:"))
        
        self.available_extensions = QListWidget()
        self.available_extensions.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.load_available_extensions()
        right_layout.addWidget(self.available_extensions)
        
        install_button = QPushButton("Установить выбранные")
        install_button.clicked.connect(self.install_selected_extensions)
        right_layout.addWidget(install_button)
        
        layout.addLayout(right_layout)
        
        # Кнопки внизу
        buttons_layout = QHBoxLayout()
        
        close_button = QPushButton("Закрыть")
        close_button.clicked.connect(self.accept)
        buttons_layout.addWidget(close_button)
        
        layout.addLayout(buttons_layout)
        
        # Подключаем обновление списка установленных расширений
        self.profiles_list.itemSelectionChanged.connect(self.update_installed_extensions)
    
    def load_profiles(self):
        """Загрузка списка профилей"""
        profiles_list = get_all_sorted_profiles()
        if not profiles_list:
            logger.error("⛔  Профили отсутствуют")
            return
        
        self.profiles_list.addItems(profiles_list)
    
    def load_available_extensions(self):
        """Загрузка списка доступных расширений"""
        extensions = get_all_default_extensions_info()
        for ext_id, name in extensions.items():
            display_text = f"{name} ({ext_id})" if name else ext_id
            self.available_extensions.addItem(display_text)
    
    def update_installed_extensions(self):
        """Обновление списка установленных расширений"""
        self.installed_extensions.clear()
        
        selected_items = self.profiles_list.selectedItems()
        if not selected_items:
            return
        
        selected_profiles = [item.text() for item in selected_items]
        extensions = get_profiles_extensions_info(selected_profiles)
        
        for ext_id, name in extensions.items():
            display_text = f"{name} ({ext_id})" if name else ext_id
            self.installed_extensions.addItem(display_text)
    
    def install_selected_extensions(self):
        """Установка выбранных расширений"""
        selected_profiles = [item.text() for item in self.profiles_list.selectedItems()]
        if not selected_profiles:
            QMessageBox.warning(self, "Предупреждение", "Выберите хотя бы один профиль")
            return
        
        selected_extensions = self.available_extensions.selectedItems()
        if not selected_extensions:
            QMessageBox.warning(self, "Предупреждение", "Выберите расширения для установки")
            return
        
        # Закрываем Chrome перед установкой
        kill_chrome_processes()
        
        success_count = 0
        for profile in selected_profiles:
            for ext_item in selected_extensions:
                ext_id = ext_item.text().split('(')[-1].strip(')')
                src_path = os.path.join(DEFAULT_EXTENSIONS_PATH, ext_id)
                dest_path = os.path.join(CHROME_DATA_PATH, f"Profile {profile}", "Extensions", ext_id)
                
                # Проверяем существование исходной папки
                if not os.path.exists(src_path):
                    logger.error(f"⛔ Исходная папка расширения не найдена: {src_path}")
                    continue
                    
                # Создаем папку Extensions если её нет
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                
                # Пробуем установить с заменой существующего
                if copy_extension(src_path, dest_path, profile, ext_id, replace=True):
                    success_count += 1
        
        if success_count > 0:
            QMessageBox.information(self, "Успех", f"Установлено расширений: {success_count}")
            self.update_installed_extensions()
        else:
            QMessageBox.warning(self, "Предупреждение", "Не удалось установить расширения. Проверьте логи.")
    
    def remove_selected_extensions(self):
        """Удаление выбранных расширений"""
        selected_profiles = [item.text() for item in self.profiles_list.selectedItems()]
        if not selected_profiles:
            QMessageBox.warning(self, "Предупреждение", "Выберите хотя бы один профиль")
            return
        
        selected_extensions = self.installed_extensions.selectedItems()
        if not selected_extensions:
            QMessageBox.warning(self, "Предупреждение", "Выберите расширения для удаления")
            return
        
        ext_ids = [item.text().split('(')[-1].strip(')') for item in selected_extensions]
        
        for profile in selected_profiles:
            remove_extensions(profile, ext_ids)
        
        QMessageBox.information(self, "Успех", "Расширения удалены")
        self.update_installed_extensions() 