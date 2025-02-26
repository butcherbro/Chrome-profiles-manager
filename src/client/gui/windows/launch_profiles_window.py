from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QPushButton, QListWidget, QLabel,
    QMessageBox, QRadioButton, QButtonGroup
)
from loguru import logger

from src.client.menu.utils import get_all_sorted_profiles
from src.utils.helpers import get_comments_for_profiles


class LaunchProfilesWindow(QDialog):
    """Окно запуска профилей"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Запуск профилей")
        self.setMinimumSize(800, 500)
        
        # Основной layout
        layout = QVBoxLayout(self)
        
        # Инициализация компонентов
        self.init_components()
        
        # Создание UI
        self.create_selection_methods(layout)
        self.create_profiles_list(layout)
        self.create_input_field(layout)
        self.create_comment_search(layout)
        self.create_control_buttons(layout)
        
        # Изначально показываем только список
        self.show_list_selection()
    
    def init_components(self):
        """Инициализация компонентов"""
        # Списки
        self.profiles_list = QListWidget()
        self.profiles_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        
        self.names_input = QListWidget()
        self.names_input.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        
        self.comment_list = QListWidget()
        self.comment_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        
        # Радио-кнопки
        self.list_radio = QRadioButton("📋 Выбрать из списка")
        self.names_radio = QRadioButton("📝 Вписать названия")
        self.comment_radio = QRadioButton("📒 Выбрать по комментарию")
        self.all_radio = QRadioButton("📦 Выбрать все")
    
    def create_selection_methods(self, layout):
        """Создание радио-кнопок для выбора способа"""
        methods_group = QButtonGroup(self)
        
        # Добавляем в группу
        methods_group.addButton(self.list_radio)
        methods_group.addButton(self.names_radio)
        methods_group.addButton(self.comment_radio)
        methods_group.addButton(self.all_radio)
        
        # Подключаем обработчики
        self.list_radio.toggled.connect(lambda: self.show_list_selection() if self.list_radio.isChecked() else None)
        self.names_radio.toggled.connect(lambda: self.show_names_input() if self.names_radio.isChecked() else None)
        self.comment_radio.toggled.connect(lambda: self.show_comment_search() if self.comment_radio.isChecked() else None)
        self.all_radio.toggled.connect(lambda: self.select_all_profiles() if self.all_radio.isChecked() else None)
        
        # Добавляем на форму
        layout.addWidget(self.list_radio)
        layout.addWidget(self.names_radio)
        layout.addWidget(self.comment_radio)
        layout.addWidget(self.all_radio)
        
        # По умолчанию выбираем список
        self.list_radio.setChecked(True)
    
    def create_profiles_list(self, layout):
        """Создание списка профилей"""
        self.load_profiles()
        layout.addWidget(self.profiles_list)
        self.profiles_list.hide()
    
    def create_input_field(self, layout):
        """Создание поля для ввода названий"""
        layout.addWidget(self.names_input)
        self.names_input.hide()
    
    def create_comment_search(self, layout):
        """Создание поля для поиска по комментарию"""
        layout.addWidget(self.comment_list)
        self.comment_list.hide()
    
    def create_control_buttons(self, layout):
        """Создание кнопок управления"""
        buttons_layout = QHBoxLayout()
        
        launch_button = QPushButton("Запустить")
        launch_button.clicked.connect(self.launch_selected_profiles)
        buttons_layout.addWidget(launch_button)
        
        cancel_button = QPushButton("Отмена")
        cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_button)
        
        layout.addLayout(buttons_layout)
    
    def load_profiles(self):
        """Загрузка списка профилей"""
        profiles_list = get_all_sorted_profiles()
        if not profiles_list:
            logger.error("⛔  Профили отсутствуют")
            return
        
        self.profiles_list.addItems(profiles_list)
    
    def show_list_selection(self):
        """Показ выбора из списка"""
        self.profiles_list.show()
        self.names_input.hide()
        self.comment_list.hide()
    
    def show_names_input(self):
        """Показ ввода названий"""
        self.profiles_list.hide()
        self.names_input.show()
        self.comment_list.hide()
    
    def show_comment_search(self):
        """Показ поиска по комментарию"""
        self.profiles_list.hide()
        self.names_input.hide()
        self.comment_list.show()
        
        # Загружаем профили с комментариями
        self.comment_list.clear()
        profiles_list = get_all_sorted_profiles()
        if not profiles_list:
            return
        
        result = get_comments_for_profiles()
        if result["success"]:
            comments = result["comments"]
        else:
            logger.warning(f"⚠️ Не удалось загрузить комментарии, причина: {result.get('description')}")
            comments = {}
        
        for profile in profiles_list:
            comment = comments.get(profile, '')
            display_text = f"{profile} - {comment}" if comment else profile
            self.comment_list.addItem(display_text)
    
    def select_all_profiles(self):
        """Выбор всех профилей"""
        self.profiles_list.hide()
        self.names_input.hide()
        self.comment_list.hide()
        
        profiles_list = get_all_sorted_profiles()
        if not profiles_list:
            return
        
        # Очищаем и добавляем все профили
        self.names_input.clear()
        self.names_input.addItems(profiles_list)
        # Выбираем все
        for i in range(self.names_input.count()):
            self.names_input.item(i).setSelected(True)
        self.names_input.show()
    
    def get_selected_profiles(self):
        """Получение выбранных профилей"""
        if self.list_radio.isChecked():
            return [item.text() for item in self.profiles_list.selectedItems()]
        elif self.names_radio.isChecked() or self.all_radio.isChecked():
            return [item.text() for item in self.names_input.selectedItems()]
        elif self.comment_radio.isChecked():
            return [item.text().split(' - ')[0] for item in self.comment_list.selectedItems()]
        return []
    
    def launch_selected_profiles(self):
        """Запуск выбранных профилей"""
        selected_profiles = self.get_selected_profiles()
        if not selected_profiles:
            QMessageBox.warning(self, "Предупреждение", "Выберите хотя бы один профиль")
            return
        
        self.selected_profiles = selected_profiles
        self.accept() 