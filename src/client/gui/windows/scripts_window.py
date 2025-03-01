from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QPushButton, QListWidget, QLabel,
    QMessageBox, QRadioButton, QButtonGroup,
    QCheckBox, QGroupBox
)
from PyQt6.QtCore import Qt
from loguru import logger
from random import shuffle
import psutil

from src.client.menu.utils import get_all_sorted_profiles
from src.utils.helpers import get_comments_for_profiles
from src.chrome.chrome import Chrome
from src.manager.manager import Manager
from src.manager.extensions.downloader import ExtensionDownloader
from src.utils.constants import DEFAULT_EXTENSIONS_PATH


class ScriptsWindow(QDialog):
    """Окно запуска скриптов"""
    def __init__(self, parent=None, script_type="chrome"):
        super().__init__(parent)
        self.script_type = script_type
        self.setWindowTitle(f"Запуск скриптов [{script_type}]")
        self.setMinimumSize(1000, 600)
        
        # Основной layout
        layout = QVBoxLayout(self)
        
        # Инициализация компонентов
        self.init_components()
        
        # Создание UI
        self.create_selection_methods(layout)
        self.create_profiles_list(layout)
        self.create_input_field(layout)
        self.create_comment_search(layout)
        self.create_scripts_selection(layout)
        self.create_additional_options(layout)
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
        
        # Список скриптов
        self.scripts_list = QListWidget()
        self.scripts_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        
        # Дополнительные опции
        self.shuffle_checkbox = QCheckBox("Рандомизировать порядок выполнения скриптов")
        if self.script_type == "chrome":
            self.headless_checkbox = QCheckBox("Использовать Headless Mode")
        
        # Загружаем доступные скрипты
        if self.script_type == "chrome":
            self.scripts = Chrome().scripts
        else:
            self.scripts = Manager().scripts
    
    def create_selection_methods(self, layout):
        """Создание радио-кнопок для выбора способа"""
        group_box = QGroupBox("Выбор профилей")
        group_layout = QVBoxLayout()
        
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
        group_layout.addWidget(self.list_radio)
        group_layout.addWidget(self.names_radio)
        group_layout.addWidget(self.comment_radio)
        group_layout.addWidget(self.all_radio)
        
        group_box.setLayout(group_layout)
        layout.addWidget(group_box)
        
        # По умолчанию выбираем список
        self.list_radio.setChecked(True)
    
    def create_scripts_selection(self, layout):
        """Создание списка выбора скриптов"""
        group_box = QGroupBox("Выбор скриптов")
        group_layout = QVBoxLayout()
        
        # Добавляем скрипты в список
        for script_id, script_info in self.scripts.items():
            self.scripts_list.addItem(script_info['human_name'])
        
        group_layout.addWidget(self.scripts_list)
        group_box.setLayout(group_layout)
        layout.addWidget(group_box)
    
    def create_additional_options(self, layout):
        """Создание дополнительных опций"""
        group_box = QGroupBox("Дополнительные опции")
        group_layout = QVBoxLayout()
        
        group_layout.addWidget(self.shuffle_checkbox)
        if self.script_type == "chrome":
            group_layout.addWidget(self.headless_checkbox)
        
        group_box.setLayout(group_layout)
        layout.addWidget(group_box)
    
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
        
        run_button = QPushButton("Запустить")
        run_button.clicked.connect(self.run_scripts)
        buttons_layout.addWidget(run_button)
        
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
    
    def get_selected_scripts(self):
        """Получение выбранных скриптов"""
        selected_names = [item.text() for item in self.scripts_list.selectedItems()]
        selected_scripts = []
        
        for script_id, script_info in self.scripts.items():
            if script_info['human_name'] in selected_names:
                selected_scripts.append(script_id)
        
        return selected_scripts
    
    def run_scripts(self):
        """Запуск скриптов для выбранных профилей"""
        # Проверяем выбранные профили
        selected_profiles = self.get_selected_profiles()
        if not selected_profiles:
            QMessageBox.warning(self, "Предупреждение", "Выберите хотя бы один профиль")
            return
        
        # Проверяем выбранные скрипты
        selected_scripts = self.get_selected_scripts()
        if not selected_scripts:
            QMessageBox.warning(self, "Предупреждение", "Выберите хотя бы один скрипт")
            return
        
        # Рандомизируем порядок если нужно
        if self.shuffle_checkbox.isChecked() and len(selected_scripts) > 1:
            shuffle(selected_scripts)
        
        # Сохраняем выбранные параметры
        self.selected_profiles = selected_profiles
        self.selected_scripts = selected_scripts
        if self.script_type == "chrome":
            self.use_headless = self.headless_checkbox.isChecked()
        
        self.accept()

    def create_buttons(self):
        """Создает кнопки для запуска скриптов"""
        self.buttons_data = {
            '🌐 Настройка Chrome': self.chrome_initial_setup,
            '🔄 Смена User-Agent': self.agent_switcher,
            '🦊 Импорт кошелька Rabby': self.rabby_import,
            '🧪 Тест профиля': self.test_profile,
            '🔁 Тест Uniswap': self.test_uniswap,
            '🔧 Настройка SwitchyOmega': self.setup_switchyomega,
        }

        for text, callback in self.buttons_data.items():
            button = QPushButton(text)
            button.clicked.connect(callback)
            self.layout().addWidget(button)

    def setup_switchyomega(self):
        """Настройка SwitchyOmega для выбранных профилей"""
        try:
            # Получаем выбранные профили
            selected_profiles = self.get_selected_profiles()
            if not selected_profiles:
                QMessageBox.warning(self, "Предупреждение", "Выберите хотя бы один профиль")
                return
            
            # Проверяем наличие расширения
            extension_path = DEFAULT_EXTENSIONS_PATH / "padekgcemlokbadohgkifijomclgjgif"
            if not extension_path.exists():
                reply = QMessageBox.question(
                    self,
                    "Расширение не найдено",
                    "Расширение SwitchyOmega не установлено.\n"
                    "Хотите установить его сейчас?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    try:
                        downloader = ExtensionDownloader()
                        if downloader.download_from_store("padekgcemlokbadohgkifijomclgjgif"):
                            logger.success("✅ SwitchyOmega успешно установлен")
                        else:
                            # Пробуем установить из локальной папки
                            local_path = DEFAULT_EXTENSIONS_PATH / "Proxy-SwitchyOmega"
                            if local_path.exists():
                                if downloader.add_extension(str(local_path)):
                                    logger.success("✅ SwitchyOmega успешно добавлен из локальной папки")
                                else:
                                    QMessageBox.critical(
                                        self,
                                        "Ошибка",
                                        "Не удалось установить SwitchyOmega.\n"
                                        "Проверьте логи для деталей."
                                    )
                                    return
                            else:
                                QMessageBox.critical(
                                    self,
                                    "Ошибка",
                                    "Не удалось установить SwitchyOmega.\n"
                                    "Расширение не найдено ни в магазине, ни локально."
                                )
                                return
                    except Exception as e:
                        logger.error("❌ Ошибка при установке SwitchyOmega")
                        logger.debug(f"Причина: {str(e)}")
                        QMessageBox.critical(
                            self,
                            "Ошибка",
                            f"Произошла ошибка при установке расширения: {str(e)}"
                        )
                        return
                else:
                    return
            
            # Подтверждение действия
            reply = QMessageBox.question(
                self,
                "Подтверждение",
                "Это действие настроит прокси в SwitchyOmega для выбранных профилей.\n"
                "Убедитесь, что:\n"
                "1. В файле .env настроены параметры прокси\n"
                "2. Если расширение отключено Chrome, оно будет автоматически включено\n\n"
                "Продолжить?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # Закрываем Chrome перед настройкой
                self.kill_chrome_processes()
                
                success_count = 0
                failed_profiles = []
                
                # Настраиваем каждый профиль
                for profile in selected_profiles:
                    logger.info(f"⚙️ Настройка SwitchyOmega для профиля {profile}...")
                    try:
                        if setup_switchyomega(profile):
                            success_count += 1
                            logger.success(f"✅ Профиль {profile} успешно настроен")
                        else:
                            failed_profiles.append(profile)
                            logger.error(f"❌ Не удалось настроить профиль {profile}")
                    except Exception as e:
                        failed_profiles.append(profile)
                        logger.error(f"❌ Ошибка при настройке профиля {profile}")
                        logger.debug(f"Причина: {str(e)}")
                
                # Показываем результат
                if success_count > 0:
                    message = f"Успешно настроено профилей: {success_count}"
                    if failed_profiles:
                        message += f"\nНе удалось настроить профили: {', '.join(failed_profiles)}"
                    QMessageBox.information(self, "Результат", message)
                else:
                    QMessageBox.critical(
                        self,
                        "Ошибка",
                        f"Не удалось настроить ни один профиль.\nПроверьте:\n"
                        f"1. Корректность настроек прокси в .env\n"
                        f"2. Логи для деталей ошибок"
                    )
                
        except Exception as e:
            logger.error("❌ Ошибка при настройке SwitchyOmega")
            logger.debug(f"Причина: {str(e)}")
            QMessageBox.critical(self, "Ошибка", f"Произошла ошибка: {str(e)}")

    def kill_chrome_processes(self):
        """Закрывает все процессы Chrome"""
        try:
            for proc in psutil.process_iter(['name']):
                if proc.info['name'] and 'chrome' in proc.info['name'].lower():
                    try:
                        proc.kill()
                    except:
                        pass
            logger.info("✅ Все процессы Chrome успешно закрыты")
        except Exception as e:
            logger.error("❌ Ошибка при закрытии процессов Chrome")
            logger.debug(f"Причина: {str(e)}") 