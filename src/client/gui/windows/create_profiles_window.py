"""
Окно создания профилей Chrome
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QRadioButton, 
    QPushButton, QLineEdit, QMessageBox, QButtonGroup,
    QLabel, QWidget
)
from PyQt6.QtCore import Qt
from loguru import logger

from src.utils.helpers import get_profiles_list
from src.chrome.chrome import Chrome


class CreateProfilesWindow(QDialog):
    """Окно создания профилей"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Создание профилей")
        self.setMinimumWidth(400)
        
        # Инициализация компонентов
        self.manual_radio = QRadioButton("📝 Задать вручную")
        self.auto_radio = QRadioButton("🤖 Задать автоматически")
        
        self.manual_input = QLineEdit()
        self.manual_input.setPlaceholderText("Введите названия профилей через запятую")
        
        self.auto_input = QLineEdit()
        self.auto_input.setPlaceholderText("Введите количество профилей")
        
        # Создаем layout
        layout = QVBoxLayout(self)
        
        # Добавляем компоненты
        self.create_radio_buttons(layout)
        self.create_input_fields(layout)
        self.create_control_buttons(layout)
        
        # По умолчанию выбираем ручной ввод
        self.manual_radio.setChecked(True)
        self.show_manual_input()
        
    def create_radio_buttons(self, layout):
        """Создание радио-кнопок"""
        methods_group = QButtonGroup(self)
        methods_group.addButton(self.manual_radio)
        methods_group.addButton(self.auto_radio)
        
        self.manual_radio.toggled.connect(lambda: self.show_manual_input() if self.manual_radio.isChecked() else None)
        self.auto_radio.toggled.connect(lambda: self.show_auto_input() if self.auto_radio.isChecked() else None)
        
        layout.addWidget(self.manual_radio)
        layout.addWidget(self.auto_radio)
        
    def create_input_fields(self, layout):
        """Создание полей ввода"""
        self.manual_widget = QWidget()
        manual_layout = QVBoxLayout(self.manual_widget)
        manual_layout.addWidget(QLabel("Впиши названия профилей через запятую:"))
        manual_layout.addWidget(self.manual_input)
        layout.addWidget(self.manual_widget)
        
        self.auto_widget = QWidget()
        auto_layout = QVBoxLayout(self.auto_widget)
        auto_layout.addWidget(QLabel("Впиши количество профилей для создания:"))
        auto_layout.addWidget(self.auto_input)
        layout.addWidget(self.auto_widget)
        self.auto_widget.hide()
        
    def create_control_buttons(self, layout):
        """Создание кнопок управления"""
        buttons_layout = QHBoxLayout()
        
        create_button = QPushButton("Создать")
        create_button.clicked.connect(self.create_profiles)
        buttons_layout.addWidget(create_button)
        
        cancel_button = QPushButton("Отмена")
        cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_button)
        
        layout.addLayout(buttons_layout)
        
    def show_manual_input(self):
        """Показ поля для ручного ввода"""
        self.manual_widget.show()
        self.auto_widget.hide()
        
    def show_auto_input(self):
        """Показ поля для автоматического ввода"""
        self.manual_widget.hide()
        self.auto_widget.show()
        
    def create_profiles(self):
        """Создание профилей"""
        try:
            existing_profile_names = get_profiles_list()
            profiles_to_create = []
            
            if self.manual_radio.isChecked():
                # Ручной ввод
                selected_names = self.manual_input.text()
                if not selected_names:
                    QMessageBox.warning(self, "Предупреждение", "Введите названия профилей")
                    return
                    
                selected_names = list(set(i.strip() for i in selected_names.split(',') if i.strip()))
                names_to_skip = list(set(existing_profile_names) & set(selected_names))
                
                if names_to_skip:
                    logger.warning(f'⚠️ Пропускаем профили {names_to_skip}, имена уже заняты')
                
                profiles_to_create = [item for item in selected_names if item not in names_to_skip]
                
            else:
                # Автоматический ввод
                try:
                    amount = int(self.auto_input.text())
                    if amount <= 0:
                        QMessageBox.warning(self, "Предупреждение", "Введите положительное число")
                        return
                except ValueError:
                    QMessageBox.warning(self, "Предупреждение", "Введите корректное число")
                    return
                
                highest_existing_numeric_name = 0
                for name in existing_profile_names:
                    try:
                        num = int(name)
                        if num > highest_existing_numeric_name:
                            highest_existing_numeric_name = num
                    except ValueError:
                        continue
                
                start = highest_existing_numeric_name + 1
                profiles_to_create = list(range(start, start + amount))
            
            if not profiles_to_create:
                QMessageBox.warning(self, "Предупреждение", "Нет профилей для создания")
                return
            
            chrome = Chrome()
            for name in profiles_to_create:
                chrome.create_new_profile(str(name))
            
            QMessageBox.information(self, "Успех", "Профили успешно созданы")
            self.accept()
            
        except Exception as e:
            logger.error(f"⛔ Ошибка при создании профилей: {str(e)}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать профили: {str(e)}") 