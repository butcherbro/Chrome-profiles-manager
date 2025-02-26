from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QPushButton, QListWidget, QLabel,
    QMessageBox, QCheckBox, QGroupBox,
    QTextEdit, QWidget, QScrollArea,
    QTreeWidget, QTreeWidgetItem,
    QMenu
)
from PyQt6.QtCore import Qt
from loguru import logger

from src.utils.helpers import (
    analyze_profile_cache,
    clean_profile_cache,
    clean_user_data_items,
    format_size
)
from src.client.menu.utils import get_all_sorted_profiles


class CacheCleanupWindow(QDialog):
    """Окно очистки кэша профилей"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Очистка профилей Chrome")
        self.setMinimumSize(1200, 700)  # Увеличим размер окна
        
        # Основной layout
        layout = QHBoxLayout(self)
        
        # Левая часть - список профилей
        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("Выберите профили для очистки:"))
        
        self.profiles_list = QListWidget()
        self.profiles_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.load_profiles()
        left_layout.addWidget(self.profiles_list)
        
        # Добавляем метку для общего размера выбранного кэша
        self.selected_cache_size_label = QLabel("Размер выбранного кэша: 0 B")
        left_layout.addWidget(self.selected_cache_size_label)
        
        # Добавляем метку для общего размера профиля
        self.total_size_label = QLabel("Общий размер профиля: 0 B")
        left_layout.addWidget(self.total_size_label)
        
        layout.addLayout(left_layout, stretch=1)
        
        # Центральная часть - кэш
        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        
        # Информация о кэше
        info_label = QLabel("Типы кэша:")
        center_layout.addWidget(info_label)
        
        # Создаем область прокрутки для информации о кэше
        cache_scroll = QScrollArea()
        cache_scroll.setWidgetResizable(True)
        cache_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Контейнер для информации о кэше
        cache_widget = QWidget()
        cache_layout = QVBoxLayout(cache_widget)
        
        # Группы кэша
        self.cache_groups = {
            "browser": {
                "icon": "🌐",
                "name": "Кэш веб-страниц",
                "description": "Кэш веб-страниц (HTML, CSS, картинки)",
                "impact": "Временно медленная загрузка сайтов",
                "checkbox": QCheckBox()
            },
            "code": {
                "icon": "📜",
                "name": "JavaScript кэш",
                "description": "Скомпилированный JavaScript",
                "impact": "Временно медленная работа сайтов",
                "checkbox": QCheckBox()
            },
            "gpu": {
                "icon": "🎮",
                "name": "Кэш графики",
                "description": "Кэш графических элементов",
                "impact": "Временно медленная отрисовка",
                "checkbox": QCheckBox()
            },
            "service_worker": {
                "icon": "🔔",
                "name": "Кэш уведомлений",
                "description": "Кэш сервис-воркеров",
                "impact": "Временно не будут работать уведомления",
                "checkbox": QCheckBox()
            },
            "media": {
                "icon": "🎥",
                "name": "Кэш медиа",
                "description": "Кэш медиа файлов",
                "impact": "Повторная загрузка медиа",
                "checkbox": QCheckBox()
            },
            "system": {
                "icon": "⚙️",
                "name": "Системный кэш",
                "description": "Системные временные файлы",
                "impact": "Не влияет на работу",
                "checkbox": QCheckBox()
            },
            "network": {
                "icon": "🌍",
                "name": "Сетевой кэш",
                "description": "Кэш сетевых запросов",
                "impact": "Временно медленная работа сети",
                "checkbox": QCheckBox()
            }
        }
        
        # Создаем группы для каждого типа кэша
        for cache_type, info in self.cache_groups.items():
            group = QGroupBox()
            group_layout = QVBoxLayout(group)
            
            # Заголовок с иконкой
            header = QHBoxLayout()
            header.addWidget(info["checkbox"])
            # Устанавливаем галочку по умолчанию
            info["checkbox"].setChecked(True)
            header.addWidget(QLabel(f"{info['icon']} {info['name']}"))
            header.addStretch()
            group_layout.addLayout(header)
            
            # Описание
            desc = QLabel(f"Описание: {info['description']}")
            desc.setWordWrap(True)
            group_layout.addWidget(desc)
            
            # Влияние при очистке
            impact = QLabel(f"Влияние при очистке: {info['impact']}")
            impact.setWordWrap(True)
            group_layout.addWidget(impact)
            
            # Текущий размер (будет обновляться)
            info["size_label"] = QLabel("Текущий размер: 0 B")
            group_layout.addWidget(info["size_label"])
            
            cache_layout.addWidget(group)
        
        # Кнопка очистки кэша
        clean_cache_button = QPushButton("Очистить выбранный кэш")
        clean_cache_button.clicked.connect(self.clean_selected_cache)
        cache_layout.addWidget(clean_cache_button)
        
        cache_scroll.setWidget(cache_widget)
        center_layout.addWidget(cache_scroll)
        
        layout.addWidget(center_widget, stretch=2)
        
        # Правая часть - пользовательские данные
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # Добавляем секцию пользовательских данных
        user_data_section = self.create_user_data_section()
        right_layout.addWidget(user_data_section)
        
        layout.addWidget(right_widget, stretch=2)
        
        # Кнопка закрытия
        close_button = QPushButton("Закрыть")
        close_button.clicked.connect(self.reject)
        right_layout.addWidget(close_button)
        
        # Подключаем обновление информации при выборе профилей
        self.profiles_list.itemSelectionChanged.connect(self.analyze_selected_profiles)
    
    def load_profiles(self):
        """Загрузка списка профилей"""
        profiles_list = get_all_sorted_profiles()
        if not profiles_list:
            logger.error("⛔  Профили отсутствуют")
            return
        
        self.profiles_list.addItems(profiles_list)
    
    def format_size(self, size_bytes: int) -> str:
        """Форматирование размера в человекочитаемый вид"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"
    
    def analyze_selected_profiles(self):
        """Анализ выбранных профилей"""
        MIN_SIZE_MB = 10  # Минимальный размер для отображения в МБ
        
        selected_profiles = [item.text() for item in self.profiles_list.selectedItems()]
        if not selected_profiles:
            # Очищаем информацию
            for info in self.cache_groups.values():
                info["size_label"].setText("Текущий размер: 0 B")
            self.total_size_label.setText("Общий размер профиля: 0 B")
            self.selected_cache_size_label.setText("Размер выбранного кэша: 0 B")
            self.user_data_tree.clear()
            return
        
        total_cache = {type: 0 for type in self.cache_groups.keys()}
        total_size = 0
        
        # Очищаем старые данные
        self.user_data_tree.clear()
        
        for profile in selected_profiles:
            cache_data = analyze_profile_cache(profile)
            total_size += cache_data["total_size"]
            
            # Обновляем размеры кэша
            for cache_type, data in cache_data["cache"].items():
                total_cache[cache_type] += data["size"]
            
            # Собираем информацию о пользовательских данных
            for data_type, data in cache_data["user_data"].items():
                if data["size"] > 0:
                    # Фильтруем элементы по размеру для IndexedDB
                    filtered_items = {}
                    if data_type == "indexeddb":
                        for item_name, item_info in data["items"].items():
                            if item_info["size"] >= MIN_SIZE_MB * 1024 * 1024:  # Конвертируем МБ в байты
                                filtered_items[item_name] = item_info
                    else:
                        filtered_items = data["items"]
                    
                    if filtered_items:  # Показываем только если есть элементы после фильтрации
                        # Добавляем заголовок типа данных
                        type_item = QTreeWidgetItem([f"{data['name']} ({format_size(data['size'])})"])
                        self.user_data_tree.addTopLevelItem(type_item)
                        
                        # Добавляем отдельные элементы
                        for item_name, item_info in filtered_items.items():
                            item = QTreeWidgetItem([
                                f"{item_name} ({format_size(item_info['size'])})"
                            ])
                            item.setData(0, Qt.ItemDataRole.UserRole, {
                                "profile": profile,
                                "type": data_type,
                                "name": item_name,
                                "size": item_info["size"]
                            })
                            type_item.addChild(item)
                            
                        # Сворачиваем узел по умолчанию
                        type_item.setExpanded(False)
        
        # Обновляем отображение размеров кэша
        for cache_type, total_size in total_cache.items():
            self.cache_groups[cache_type]["size_label"].setText(
                f"Текущий размер: {format_size(total_size)}"
            )
            
        # Обновляем общий размер профиля
        self.total_size_label.setText(f"Общий размер профиля: {format_size(total_size)}")
        
        # Обновляем размер выбранного кэша
        self.update_selected_cache_size()
    
    def update_selected_cache_size(self):
        """Обновление размера выбранного кэша"""
        total_selected_size = 0
        for cache_type, info in self.cache_groups.items():
            if info["checkbox"].isChecked():
                # Извлекаем текущий размер из метки
                size_text = info["size_label"].text()
                size_str = size_text.split(": ")[1].split(" ")[0]
                try:
                    size = float(size_str)
                    unit = size_text.split(" ")[-1]
                    # Конвертируем в байты
                    multiplier = {
                        'B': 1,
                        'KB': 1024,
                        'MB': 1024*1024,
                        'GB': 1024*1024*1024,
                        'TB': 1024*1024*1024*1024
                    }
                    total_selected_size += size * multiplier[unit]
                except (ValueError, IndexError):
                    continue
        
        self.selected_cache_size_label.setText(f"Размер выбранного кэша: {format_size(total_selected_size)}")
    
    def clean_selected_cache(self):
        """Очистка выбранного кэша"""
        selected_profiles = [item.text() for item in self.profiles_list.selectedItems()]
        if not selected_profiles:
            QMessageBox.warning(self, "Предупреждение", "Выберите хотя бы один профиль")
            return
        
        selected_cache_types = [
            cache_type for cache_type, info in self.cache_groups.items()
            if info["checkbox"].isChecked()
        ]
        
        if not selected_cache_types:
            QMessageBox.warning(self, "Предупреждение", "Выберите типы кэша для очистки")
            return
        
        # Подтверждение очистки
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setText("Очистка кэша")
        msg.setInformativeText("Вы уверены, что хотите очистить выбранный кэш?\nЭто может временно замедлить работу браузера.")
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.setDefaultButton(QMessageBox.StandardButton.No)
        
        if msg.exec() == QMessageBox.StandardButton.Yes:
            total_cleaned = 0
            for profile in selected_profiles:
                result = clean_profile_cache(profile, selected_cache_types)
                if result["success"]:
                    total_cleaned += result["cleaned_size"]
            
            QMessageBox.information(
                self,
                "Успех",
                f"Очищено: {self.format_size(total_cleaned)}"
            )
            
            # Обновляем информацию
            self.analyze_selected_profiles()
    
    def clean_selected_items(self):
        """Очистка выбранных элементов пользовательских данных"""
        # Получаем выбранные элементы
        selected_items = []
        root = self.user_data_tree.invisibleRootItem()
        for i in range(root.childCount()):
            type_item = root.child(i)
            for j in range(type_item.childCount()):
                item = type_item.child(j)
                if item.isSelected():
                    data = item.data(0, Qt.ItemDataRole.UserRole)
                    if data:
                        selected_items.append(data)
        
        if not selected_items:
            return
            
        # Группируем элементы по профилям и типам
        grouped_items = {}
        for item in selected_items:
            key = (item["profile"], item["type"])
            if key not in grouped_items:
                grouped_items[key] = []
            grouped_items[key].append(item["name"])
        
        # Подтверждение очистки
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setText("Очистка данных")
        msg.setInformativeText(
            "Вы уверены, что хотите удалить выбранные элементы?\n"
            "Это действие нельзя отменить."
        )
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.setDefaultButton(QMessageBox.StandardButton.No)
        
        if msg.exec() == QMessageBox.StandardButton.Yes:
            total_cleaned = 0
            for (profile, data_type), items in grouped_items.items():
                result = clean_user_data_items(profile, data_type, items)
                if result["success"]:
                    total_cleaned += result["cleaned_size"]
            
            QMessageBox.information(
                self,
                "Успех",
                f"Очищено: {format_size(total_cleaned)}"
            )
            
            # Обновляем информацию
            self.analyze_selected_profiles()
    
    def create_user_data_section(self):
        """Создание секции пользовательских данных"""
        group = QGroupBox("Пользовательские данные")
        layout = QVBoxLayout(group)
        
        # Создаем дерево для отображения данных
        self.user_data_tree = QTreeWidget()
        self.user_data_tree.setHeaderHidden(True)
        self.user_data_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.user_data_tree.customContextMenuRequested.connect(self.show_context_menu)
        layout.addWidget(self.user_data_tree)
        
        # Кнопка очистки выбранных элементов
        clean_button = QPushButton("Очистить выбранное")
        clean_button.clicked.connect(self.clean_selected_items)
        layout.addWidget(clean_button)
        
        return group

    def show_context_menu(self, position):
        """Показ контекстного меню для элемента дерева"""
        item = self.user_data_tree.itemAt(position)
        if not item:
            return
        
        # Получаем данные элемента
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data:
            return
        
        menu = QMenu()
        delete_everywhere_action = menu.addAction("Удалить этот элемент у всех выбранных профилей")
        action = menu.exec(self.user_data_tree.viewport().mapToGlobal(position))
        
        if action == delete_everywhere_action:
            self.delete_item_from_all_profiles(data)

    def delete_item_from_all_profiles(self, item_data):
        """Удаление конкретного элемента у всех выбранных профилей"""
        selected_profiles = [item.text() for item in self.profiles_list.selectedItems()]
        if not selected_profiles:
            QMessageBox.warning(self, "Предупреждение", "Выберите хотя бы один профиль")
            return
        
        # Получаем имя элемента для удаления
        item_name = item_data["name"]
        item_type = item_data["type"]
        
        # Подтверждение удаления
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setText("Удаление элемента у всех профилей")
        msg.setInformativeText(
            f"Вы уверены, что хотите удалить элемент\n{item_name}\n"
            f"у всех выбранных профилей ({len(selected_profiles)} шт.)?\n"
            "Это действие нельзя отменить."
        )
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.setDefaultButton(QMessageBox.StandardButton.No)
        
        if msg.exec() == QMessageBox.StandardButton.Yes:
            total_cleaned = 0
            success_count = 0
            
            for profile in selected_profiles:
                # Проверяем наличие элемента в профиле через анализ
                cache_data = analyze_profile_cache(profile)
                if item_type in cache_data["user_data"]:
                    if item_name in cache_data["user_data"][item_type]["items"]:
                        # Удаляем элемент
                        result = clean_user_data_items(profile, item_type, [item_name])
                        if result["success"]:
                            total_cleaned += result["cleaned_size"]
                            success_count += 1
            
            if success_count > 0:
                QMessageBox.information(
                    self,
                    "Успех",
                    f"Элемент удален у {success_count} профилей\n"
                    f"Очищено: {format_size(total_cleaned)}"
                )
            else:
                QMessageBox.warning(
                    self,
                    "Предупреждение",
                    "Не удалось удалить элемент ни у одного профиля"
                )
            
            # Обновляем информацию
            self.analyze_selected_profiles() 