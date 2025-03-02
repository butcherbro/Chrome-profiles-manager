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
from src.utils.copy_extensions import copy_extensions_to_all_profiles


class ExtensionsWindow(QDialog):
    """Окно работы с расширениями"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Работа с расширениями")
        self.setMinimumSize(1000, 600)
        
        # Основной layout
        main_layout = QVBoxLayout(self)
        
        # Верхняя кнопка для быстрого копирования
        top_button_layout = QHBoxLayout()
        
        copy_all_button = QPushButton("📋 Копировать все расширения из профиля 03")
        copy_all_button.setMinimumHeight(40)
        copy_all_button.clicked.connect(self.copy_all_extensions)
        top_button_layout.addWidget(copy_all_button)
        
        main_layout.addLayout(top_button_layout)
        
        # Разделительная линия
        line = QLabel()
        line.setStyleSheet("background-color: #cccccc;")
        line.setFixedHeight(1)
        main_layout.addWidget(line)
        
        # Контейнер для основного содержимого
        content_layout = QHBoxLayout()
        
        # Левая часть - профили
        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("Выберите профили:"))
        
        self.profiles_list = QListWidget()
        self.profiles_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.load_profiles()
        left_layout.addWidget(self.profiles_list)
        
        content_layout.addLayout(left_layout)
        
        # Центральная часть - установленные расширения
        center_layout = QVBoxLayout()
        center_layout.addWidget(QLabel("Установленные расширения:"))
        
        self.installed_extensions = QListWidget()
        self.installed_extensions.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        center_layout.addWidget(self.installed_extensions)
        
        remove_button = QPushButton("🗑️ Удалить выбранные")
        remove_button.clicked.connect(self.remove_selected_extensions)
        center_layout.addWidget(remove_button)
        
        content_layout.addLayout(center_layout)
        
        # Правая часть - доступные расширения
        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("Доступные расширения:"))
        
        self.available_extensions = QListWidget()
        self.available_extensions.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.load_available_extensions()
        right_layout.addWidget(self.available_extensions)
        
        install_button = QPushButton("➕ Установить выбранные")
        install_button.clicked.connect(self.install_selected_extensions)
        right_layout.addWidget(install_button)
        
        content_layout.addLayout(right_layout)
        
        main_layout.addLayout(content_layout)
        
        # Кнопки внизу
        buttons_layout = QHBoxLayout()
        
        close_button = QPushButton("Закрыть")
        close_button.clicked.connect(self.accept)
        buttons_layout.addWidget(close_button)
        
        main_layout.addLayout(buttons_layout)
        
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
            # Добавляем известные названия расширений
            known_names = {
                "padekgcemlokbadohgkifijomclgjgif": "Proxy SwitchyOmega",
                "nkbihfbeogaeaoehlefnkodbefgpgknn": "MetaMask",
                "nmmhkkegccagdldgiimedpiccmgmieda": "Google Payments"
            }
            display_name = known_names.get(ext_id, name) or ext_id
            display_text = f"{display_name} ({ext_id})"
            self.available_extensions.addItem(display_text)
    
    def update_installed_extensions(self):
        """Обновление списка установленных расширений"""
        self.installed_extensions.clear()
        
        # Получаем выбранные профили
        selected_profiles = [item.text() for item in self.profiles_list.selectedItems()]
        if not selected_profiles:
            return
            
        # Получаем установленные расширения
        extensions = get_profiles_extensions_info(selected_profiles)
        
        # Добавляем известные названия расширений
        known_names = {
            "padekgcemlokbadohgkifijomclgjgif": "Proxy SwitchyOmega",
            "nkbihfbeogaeaoehlefnkodbefgpgknn": "MetaMask",
            "nmmhkkegccagdldgiimedpiccmgmieda": "Google Payments"
        }
        
        for ext_id, name in extensions.items():
            display_name = known_names.get(ext_id, name) or ext_id
            display_text = f"{display_name} ({ext_id})"
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
    
    def copy_all_extensions(self):
        """Копирование всех расширений из профиля 03"""
        try:
            reply = QMessageBox.question(
                self,
                "Подтверждение",
                "Это действие скопирует все расширения из профиля 03 во все остальные профили.\n"
                "Для криптокошельков будут сохранены существующие настройки в профилях.\n\n"
                "Продолжить?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # Закрываем Chrome перед копированием
                kill_chrome_processes()
                
                if copy_extensions_to_all_profiles():
                    QMessageBox.information(self, "Успех", "Расширения успешно скопированы во все профили")
                    # Обновляем список установленных расширений
                    self.update_installed_extensions()
                else:
                    QMessageBox.warning(self, "Ошибка", "Не удалось скопировать расширения. Проверьте логи.")
                    
        except Exception as e:
            logger.error(f"⛔ Ошибка при копировании расширений: {str(e)}")
            QMessageBox.critical(self, "Ошибка", f"Произошла ошибка: {str(e)}") 