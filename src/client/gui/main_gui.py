class ProfileManager(QObject):
    # Сигналы для работы с менеджер-скриптами
    managerScriptsListChanged = Signal()
    managerScriptOperationStatusChanged = Signal(bool, str)
    ManagerScriptOperationStatusChanged = Signal(bool, str)
    
    @Slot()
    def update_manager_scripts_list(self):
        """Обновляет список доступных менеджер-скриптов"""
        try:
            # Получаем список скриптов из директории manager_scripts
            scripts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'manager_scripts')
            self._manager_scripts_list = []
            
            if os.path.exists(scripts_dir):
                for file in os.listdir(scripts_dir):
                    if file.endswith('.py') and not file.startswith('__'):
                        script_name = file[:-3]  # Убираем расширение .py
                        self._manager_scripts_list.append(script_name)
            
            # Сортируем список скриптов
            self._manager_scripts_list.sort()
            
            # Уведомляем об изменении списка скриптов
            self.managerScriptsListChanged.emit()
            
        except Exception as e:
            logger.error(f"Ошибка при обновлении списка менеджер-скриптов: {e}")
    
    @Property(list, notify=managerScriptsListChanged)
    def managerScriptsList(self):
        """Возвращает список доступных менеджер-скриптов"""
        return self._manager_scripts_list
    
    def get_manager_scripts_list(self):
        """Получает список доступных менеджер-скриптов"""
        try:
            from src.manager.manager import Manager
            manager = Manager()
            
            # Получаем список скриптов из менеджера
            scripts_list = []
            for script_id, script_info in manager.scripts.items():
                scripts_list.append(script_id)
            
            # Сортируем список скриптов
            scripts_list.sort()
            
            return scripts_list
        except Exception as e:
            logger.error(f"Ошибка при получении списка менеджер-скриптов: {e}")
            return ["test_script"]
    
    @Slot(list, list, bool)
    def runManagerScripts(self, profiles, scripts, shuffle_scripts=False):
        """Запускает выбранные менеджер-скрипты для выбранных профилей
        
        Args:
            profiles (list): Список профилей для запуска
            scripts (list): Список скриптов для запуска
            shuffle_scripts (bool): Перемешать порядок скриптов
        """
        logger.info(f"Вызван метод runManagerScripts с параметрами: profiles={profiles}, scripts={scripts}, shuffle_scripts={shuffle_scripts}")
        try:
            # Запускаем скрипты в отдельном потоке
            logger.info("Создаем поток для выполнения скриптов")
            thread = threading.Thread(
                target=self._run_manager_scripts_thread,
                args=(profiles, scripts, shuffle_scripts)
            )
            thread.daemon = True
            logger.info("Запускаем поток")
            thread.start()
            logger.info("Поток запущен успешно")
        except Exception as e:
            logger.error(f"Ошибка при запуске менеджер-скриптов: {e}")
            self.managerScriptOperationStatusChanged.emit(False, f"Ошибка при запуске скриптов: {e}")
            # Дублируем вызов для нового сигнала
            self.ManagerScriptOperationStatusChanged.emit(False, f"Ошибка при запуске скриптов: {e}")
    
    def _run_manager_scripts_thread(self, profiles, scripts, shuffle_scripts=False):
        """Выполняет менеджер-скрипты в отдельном потоке
        
        Args:
            profiles (list): Список профилей для запуска
            scripts (list): Список скриптов для запуска
            shuffle_scripts (bool): Перемешать порядок скриптов
        """
        logger.info(f"Запущен поток _run_manager_scripts_thread с параметрами: profiles={profiles}, scripts={scripts}, shuffle_scripts={shuffle_scripts}")
        try:
            from src.client.menu.run_manager_scripts_on_multiple_profiles import run_manager_scripts_on_multiple_profiles
            logger.info("Импортирован модуль run_manager_scripts_on_multiple_profiles")
            
            # Запускаем скрипты
            logger.info("Вызываем функцию run_manager_scripts_on_multiple_profiles")
            success = run_manager_scripts_on_multiple_profiles(
                profiles=profiles,
                scripts=scripts,
                shuffle_scripts=shuffle_scripts,
                gui_mode=True
            )
            logger.info(f"Функция run_manager_scripts_on_multiple_profiles выполнена с результатом: {success}")
            
            # Отправляем сигнал о завершении операции
            if success:
                logger.info(f"Отправляем сигнал об успешном выполнении скриптов для {len(profiles)} профилей")
                self.managerScriptOperationStatusChanged.emit(True, f"Скрипты успешно выполнены для всех профилей ({len(profiles)})")
                # Дублируем вызов для нового сигнала
                self.ManagerScriptOperationStatusChanged.emit(True, f"Скрипты успешно выполнены для всех профилей ({len(profiles)})")
            else:
                logger.info("Отправляем сигнал об ошибке при выполнении скриптов")
                self.managerScriptOperationStatusChanged.emit(False, "Произошла ошибка при выполнении скриптов")
                # Дублируем вызов для нового сигнала
                self.ManagerScriptOperationStatusChanged.emit(False, "Произошла ошибка при выполнении скриптов")
                
        except Exception as e:
            logger.error(f"Ошибка при выполнении менеджер-скриптов: {e}")
            logger.info("Отправляем сигнал об ошибке при выполнении скриптов")
            self.managerScriptOperationStatusChanged.emit(False, f"Ошибка при выполнении скриптов: {e}")
            # Дублируем вызов для нового сигнала
            self.ManagerScriptOperationStatusChanged.emit(False, f"Ошибка при выполнении скриптов: {e}")
    
    @Slot()
    def run_manager_scripts(self):
        """Открывает окно для запуска менеджер-скриптов"""
        try:
            logger.info("Запуск метода run_manager_scripts")
            # Выводим список доступных сигналов
            logger.info(f"Доступные сигналы в ProfileManager: {[attr for attr in dir(self) if isinstance(getattr(self, attr), Signal)]}")
            
            # Находим окно для запуска скриптов
            manager_scripts_runner = self.engine.rootObjects()[0].findChild(QObject, "managerScriptsRunner")
            
            if manager_scripts_runner:
                logger.info("Найден компонент managerScriptsRunner")
                try:
                    # Получаем список скриптов менеджера
                    scripts_list = self.get_manager_scripts_list()
                    logger.info(f"Получен список скриптов менеджера: {scripts_list}")
                    
                    # Устанавливаем список скриптов в QML
                    manager_scripts_runner.setProperty("managerScriptsList", scripts_list)
                    logger.info("Установлен список скриптов в QML")
                    
                    # Показываем окно
                    logger.info("Вызываем метод show() для компонента managerScriptsRunner")
                    manager_scripts_runner.show()
                    logger.info("Метод show() выполнен успешно")
                    return
                except Exception as e:
                    logger.error(f"Ошибка при настройке окна для запуска менеджер-скриптов: {e}")
            else:
                logger.warning("Окно для запуска менеджер-скриптов не найдено")
            
            # Если не удалось открыть окно, запускаем терминальную версию
            logger.info("Запускаем терминальную версию")
            from src.client.menu.run_manager_scripts_on_multiple_profiles import run_manager_scripts_on_multiple_profiles
            run_manager_scripts_on_multiple_profiles()
        except Exception as e:
            logger.error(f"Ошибка при открытии окна для запуска менеджер-скриптов: {e}")
            # Если не удалось открыть окно, запускаем терминальную версию
            logger.info("Запускаем терминальную версию")
            from src.client.menu.run_manager_scripts_on_multiple_profiles import run_manager_scripts_on_multiple_profiles
            run_manager_scripts_on_multiple_profiles()
    
    def __init__(self, engine, parent=None):
        super().__init__(parent)
        self.engine = engine
        self._profiles_list = []
        self._selected_profiles = []
        self._chrome_scripts_list = []
        self._manager_scripts_list = []
        # ... rest of the initialization ... 