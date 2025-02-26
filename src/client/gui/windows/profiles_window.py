from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, 
    QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt
from loguru import logger

from src.utils.helpers import get_comments_for_profiles
from src.client.menu.utils import get_all_sorted_profiles


class ProfilesWindow(QDialog):
    """Окно просмотра профилей"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Просмотр профилей")
        self.setMinimumSize(600, 400)
        
        # Основной layout
        layout = QVBoxLayout(self)
        
        # Создаем таблицу
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Название", "Комментарий"])
        
        # Растягиваем колонки
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(self.table)
        
        # Заполняем данными
        self.load_profiles()
    
    def load_profiles(self):
        """Загрузка профилей в таблицу"""
        profiles_list = get_all_sorted_profiles()
        if not profiles_list:
            logger.error("⛔  Профили отсутствуют")
            return
        
        # Получаем комментарии
        result = get_comments_for_profiles()
        if result["success"]:
            comments = result["comments"]
        else:
            logger.warning(f"⚠️ Не удалось загрузить комментарии, причина: {result.get('description')}")
            comments = {}
        
        # Заполняем таблицу
        self.table.setRowCount(len(profiles_list))
        for row, profile in enumerate(profiles_list):
            # Название профиля
            name_item = QTableWidgetItem(profile)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 0, name_item)
            
            # Комментарий
            comment = comments.get(profile, '')
            comment_item = QTableWidgetItem(comment)
            comment_item.setFlags(comment_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 1, comment_item) 