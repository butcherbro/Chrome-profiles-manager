from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QListWidget,
    QLabel, QMessageBox
)
from loguru import logger

from src.utils.helpers import set_comments_for_profiles
from src.client.menu.utils import get_all_sorted_profiles


class CommentsWindow(QDialog):
    """Окно работы с комментариями"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Задать комментарии")
        self.setMinimumSize(800, 500)
        
        # Основной layout
        layout = QHBoxLayout(self)
        
        # Левая часть - список профилей
        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("Выберите профили:"))
        
        self.profiles_list = QListWidget()
        self.profiles_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.load_profiles()
        left_layout.addWidget(self.profiles_list)
        
        layout.addLayout(left_layout)
        
        # Правая часть - комментарий и кнопки
        right_layout = QVBoxLayout()
        
        right_layout.addWidget(QLabel("Введите комментарий:"))
        self.comment_edit = QTextEdit()
        right_layout.addWidget(self.comment_edit)
        
        # Кнопки
        buttons_layout = QHBoxLayout()
        
        save_button = QPushButton("Сохранить")
        save_button.clicked.connect(self.save_comments)
        buttons_layout.addWidget(save_button)
        
        cancel_button = QPushButton("Отмена")
        cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_button)
        
        right_layout.addLayout(buttons_layout)
        layout.addLayout(right_layout)
    
    def load_profiles(self):
        """Загрузка списка профилей"""
        profiles_list = get_all_sorted_profiles()
        if not profiles_list:
            logger.error("⛔  Профили отсутствуют")
            return
        
        self.profiles_list.addItems(profiles_list)
    
    def save_comments(self):
        """Сохранение комментариев"""
        selected_items = self.profiles_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Предупреждение", "Выберите хотя бы один профиль")
            return
        
        selected_profiles = [item.text() for item in selected_items]
        comment = self.comment_edit.toPlainText()
        
        result = set_comments_for_profiles(selected_profiles, comment)
        
        if result["success"]:
            QMessageBox.information(self, "Успех", "Комментарии успешно обновлены")
            self.accept()
        else:
            QMessageBox.critical(
                self, 
                "Ошибка", 
                f"Не удалось обновить комментарии: {result.get('description')}"
            ) 