"""
Окно для запуска скриптов через Playwright
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QListWidget,
    QCheckBox, QLineEdit, QMessageBox,
    QRadioButton, QButtonGroup
)
from PyQt6.QtCore import Qt
from loguru import logger

from src.chrome.automation import PlaywrightAutomation
from src.utils.helpers import get_profiles_list, get_comments_for_profiles
from src.scripts.metamask_import import metamask_import_wallet

class PlaywrightScriptsWindow(QDialog):
    """Окно для запуска скриптов через Playwright"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Скрипты [Playwright]")
        self.setMinimumSize(600, 400)
        
        # Доступные скрипты
        self.available_scripts = {
            "🦊 Импорт кошелька MetaMask": metamask_import_wallet,
            # Здесь можно добавить другие скрипты
        }
        
        # Инициализация UI
        layout = QVBoxLayout(self)
        
        # Методы выбора профилей
        self.create_selection_methods(layout)
        
        # Список профилей
        self.create_profiles_list(layout)
        
        # Поле для ввода номеров
        self.create_input_field(layout)
        
        # Поиск по комментарию
        self.create_comment_search(layout)
        
        # Список скриптов
        self.create_scripts_list(layout)
        
        # Кнопки управления
        self.create_control_buttons(layout)
        
        # Загружаем профили
        self.load_profiles()
        
        # По умолчанию показываем список
        self.show_list_selection()
    
    def create_scripts_list(self, layout):
        """Создание списка скриптов"""
        layout.addWidget(QLabel("Доступные скрипты:"))
        self.scripts_list = QListWidget()
        self.scripts_list.addItems(self.available_scripts.keys())
        self.scripts_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        layout.addWidget(self.scripts_list)
        
        # Выбираем первый скрипт по умолчанию
        if self.scripts_list.count() > 0:
            self.scripts_list.setCurrentRow(0)
    
    def create_selection_methods(self, layout):
        """Создание методов выбора профилей"""
        group_box = QHBoxLayout()
        
        # Радио кнопки
        self.selection_group = QButtonGroup()
        
        # Выбор из списка
        self.list_radio = QRadioButton("Выбор из списка")
        self.list_radio.setChecked(True)
        self.selection_group.addButton(self.list_radio)
        group_box.addWidget(self.list_radio)
        
        # Ввод номеров
        self.input_radio = QRadioButton("Ввод номеров")
        self.selection_group.addButton(self.input_radio)
        group_box.addWidget(self.input_radio)
        
        # Поиск по комментарию
        self.comment_radio = QRadioButton("Поиск по комментарию")
        self.selection_group.addButton(self.comment_radio)
        group_box.addWidget(self.comment_radio)
        
        # Подключаем обработчики
        self.list_radio.toggled.connect(lambda: self.show_list_selection() if self.list_radio.isChecked() else None)
        self.input_radio.toggled.connect(lambda: self.show_names_input() if self.input_radio.isChecked() else None)
        self.comment_radio.toggled.connect(lambda: self.show_comment_search() if self.comment_radio.isChecked() else None)
        
        layout.addLayout(group_box)
    
    def create_profiles_list(self, layout):
        """Создание списка профилей"""
        self.profiles_list = QListWidget()
        self.profiles_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        layout.addWidget(self.profiles_list)
        self.profiles_list.hide()
    
    def create_input_field(self, layout):
        """Создание поля для ввода номеров"""
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Введите номера профилей через запятую")
        layout.addWidget(self.input_field)
        self.input_field.hide()
    
    def create_comment_search(self, layout):
        """Создание поля для поиска по комментарию"""
        self.comment_field = QLineEdit()
        self.comment_field.setPlaceholderText("Введите комментарий для поиска")
        layout.addWidget(self.comment_field)
        self.comment_field.hide()
    
    def create_control_buttons(self, layout):
        """Создание кнопок управления"""
        buttons_layout = QHBoxLayout()
        
        # Кнопка выбора всех профилей
        self.select_all_btn = QPushButton("Выбрать все")
        self.select_all_btn.clicked.connect(self.select_all_profiles)
        buttons_layout.addWidget(self.select_all_btn)
        
        # Кнопка запуска
        self.run_btn = QPushButton("Запустить")
        self.run_btn.clicked.connect(self.run_scripts)
        buttons_layout.addWidget(self.run_btn)
        
        layout.addLayout(buttons_layout)
    
    def load_profiles(self):
        """Загрузка списка профилей"""
        try:
            self.profiles = get_profiles_list()
            self.comments = get_comments_for_profiles()
            
            self.profiles_list.clear()
            
            # Сортируем профили: сначала числовые, потом остальные
            def sort_key(profile):
                try:
                    return (0, int(profile))  # Числовые профили идут первыми
                except ValueError:
                    return (1, profile)  # Нечисловые профили идут после
                    
            sorted_profiles = sorted(self.profiles, key=sort_key)
            
            for profile in sorted_profiles:
                comment = self.comments.get(profile, "")
                item_text = f"{profile} - {comment}" if comment else profile
                self.profiles_list.addItem(item_text)
                
        except Exception as e:
            logger.error(f"❌ Ошибка при загрузке профилей: {str(e)}")
    
    def show_list_selection(self):
        """Показать выбор из списка"""
        self.profiles_list.show()
        self.input_field.hide()
        self.comment_field.hide()
        self.select_all_btn.setEnabled(True)
    
    def show_names_input(self):
        """Показать поле ввода номеров"""
        self.profiles_list.hide()
        self.input_field.show()
        self.comment_field.hide()
        self.select_all_btn.setEnabled(False)
    
    def show_comment_search(self):
        """Показать поиск по комментарию"""
        self.profiles_list.hide()
        self.input_field.hide()
        self.comment_field.show()
        self.select_all_btn.setEnabled(False)
    
    def select_all_profiles(self):
        """Выбрать все профили"""
        for i in range(self.profiles_list.count()):
            self.profiles_list.item(i).setSelected(True)
    
    def get_selected_profiles(self) -> list[str]:
        """Получить список выбранных профилей"""
        selected = []
        
        if self.list_radio.isChecked():
            # Получаем выбранные из списка
            for item in self.profiles_list.selectedItems():
                profile = item.text().split(" - ")[0]  # Отделяем имя от комментария
                selected.append(profile)
                
        elif self.input_radio.isChecked():
            # Парсим введенные имена профилей
            text = self.input_field.text().strip()
            if text:
                names = [n.strip() for n in text.split(",")]
                selected = [n for n in names if n in self.profiles]
                
        elif self.comment_radio.isChecked():
            # Ищем по комментарию
            search = self.comment_field.text().lower().strip()
            if search:
                for profile, comment in self.comments.items():
                    if search in str(comment).lower():
                        selected.append(profile)
        
        return selected
    
    def run_scripts(self):
        """Запуск скриптов"""
        try:
            selected_profiles = self.get_selected_profiles()
            
            if not selected_profiles:
                QMessageBox.warning(self, "Внимание", "Не выбрано ни одного профиля")
                return
                
            # Получаем выбранный скрипт
            selected_script_items = self.scripts_list.selectedItems()
            if not selected_script_items:
                QMessageBox.warning(self, "Внимание", "Не выбран скрипт для запуска")
                return
                
            selected_script_name = selected_script_items[0].text()
            script_function = self.available_scripts[selected_script_name]
            
            automation = PlaywrightAutomation()
            
            for profile in selected_profiles:
                logger.info(f"🚀 Запускаю скрипт {selected_script_name} для профиля {profile}")
                if automation.launch_profile(profile):
                    # Запускаем выбранный скрипт
                    try:
                        automation.run_script(script_function)
                        logger.success(f"✅ Скрипт успешно выполнен для профиля {profile}")
                    except Exception as e:
                        logger.error(f"❌ Ошибка при выполнении скрипта для профиля {profile}: {str(e)}")
                else:
                    logger.error(f"❌ Ошибка при запуске профиля {profile}")
            
            self.accept()
            
        except Exception as e:
            logger.error("❌ Ошибка при запуске скриптов")
            logger.debug(f"Причина: {str(e)}")
            QMessageBox.critical(self, "Ошибка", f"Ошибка при запуске скриптов: {str(e)}") 