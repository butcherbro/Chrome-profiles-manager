from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QPushButton, QListWidget, QLabel,
    QMessageBox, QFileDialog
)
from loguru import logger

from src.utils.zenno_profile_importer import ZennoProfileImporter


class ZennoImportWindow(QDialog):
    """Окно импорта профилей из ZennoPoster"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Импорт профилей из ZennoPoster")
        self.setMinimumSize(800, 500)
        
        # Инициализируем импортер
        self.importer = ZennoProfileImporter()
        
        # Основной layout
        layout = QVBoxLayout(self)
        
        # Кнопка выбора папки
        select_folder_layout = QHBoxLayout()
        self.folder_label = QLabel("Папка с профилями не выбрана")
        select_folder_layout.addWidget(self.folder_label)
        
        select_folder_button = QPushButton("Выбрать папку")
        select_folder_button.clicked.connect(self.select_folder)
        select_folder_layout.addWidget(select_folder_button)
        
        layout.addLayout(select_folder_layout)
        
        # Список профилей
        layout.addWidget(QLabel("Доступные профили:"))
        self.profiles_list = QListWidget()
        self.profiles_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        layout.addWidget(self.profiles_list)
        
        # Кнопки управления
        buttons_layout = QHBoxLayout()
        
        import_button = QPushButton("Импортировать выбранные")
        import_button.clicked.connect(self.import_selected_profiles)
        buttons_layout.addWidget(import_button)
        
        close_button = QPushButton("Закрыть")
        close_button.clicked.connect(self.reject)
        buttons_layout.addWidget(close_button)
        
        layout.addLayout(buttons_layout)
    
    def select_folder(self):
        """Выбор папки с профилями ZennoPoster"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Выберите папку с профилями ZennoPoster"
        )
        
        if folder:
            self.importer.set_profiles_path(folder)
            self.folder_label.setText(f"Выбрана папка: {folder}")
            self.load_profiles()
    
    def load_profiles(self):
        """Загрузка списка доступных профилей"""
        self.profiles_list.clear()
        
        profiles = self.importer.list_zenno_profiles()
        if not profiles:
            QMessageBox.warning(
                self,
                "Предупреждение",
                "В выбранной папке не найдены профили ZennoPoster"
            )
            return
        
        for profile in profiles:
            self.profiles_list.addItem(profile)
    
    def import_selected_profiles(self):
        """Импорт выбранных профилей"""
        selected_items = self.profiles_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Предупреждение", "Выберите хотя бы один профиль")
            return
        
        success_count = 0
        for item in selected_items:
            profile_path = item.text()
            if self.importer.import_profile(profile_path):
                success_count += 1
        
        if success_count > 0:
            QMessageBox.information(
                self,
                "Успех",
                f"Успешно импортировано профилей: {success_count}"
            )
            self.accept()
        else:
            QMessageBox.warning(
                self,
                "Предупреждение",
                "Не удалось импортировать профили. Проверьте логи."
            ) 