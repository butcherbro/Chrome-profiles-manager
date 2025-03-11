from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtCore import QObject, Slot, Signal, Property, QStringListModel
from PySide6.QtGui import QGuiApplication
import sys
from pathlib import Path
from src.chrome.chrome import Chrome
from src.utils.helpers import (
    kill_chrome_processes, get_profiles_list, set_comments_for_profiles, 
    get_comments_for_profiles, copy_extension, remove_extensions, 
    get_profiles_extensions_info, get_all_default_extensions_info,
    get_extension_version, get_extension_icon_path, get_extension_name,
    copy_extension_from_profile_to_default, delete_profile
)
from src.utils.constants import PROJECT_PATH, CHROME_DATA_PATH, DEFAULT_EXTENSIONS_PATH, CHROME_DRIVER_PATH
from src.client.menu import manage_extensions, run_chrome_scripts_on_multiple_profiles, run_manager_scripts_on_multiple_profiles, update_comments, create_multiple_profiles
from loguru import logger
from config import general_config
import os
from concurrent.futures import ThreadPoolExecutor
import time
import shutil
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from PySide6.QtCore import QUrl
import json
import threading
import signal
import importlib.util
import random
import subprocess
import re
import csv
from datetime import datetime
import uuid

class ProfileManager(QObject):
    profilesListChanged = Signal()
    selectedProfilesChanged = Signal()
    filteredProfilesListChanged = Signal()
    commentSaveStatusChanged = Signal(bool, str)  # Сигнал для уведомления о статусе сохранения (успех/неудача, сообщение)
    profileCreationStatusChanged = Signal(bool, str)  # Сигнал для уведомления о статусе создания профилей (успех/неудача, сообщение)
    extensionOperationStatusChanged = Signal(bool, str)  # Сигнал для уведомления о статусе операций с расширениями (успех/неудача, сообщение)
    extensionsListChanged = Signal('QVariantList')  # Сигнал для уведомления об изменении списка расширений
    scriptOperationStatusChanged = Signal(bool, str)  # Сигнал для уведомления о статусе операций со скриптами (успех/неудача, сообщение)
    # Сигналы для работы с менеджер-скриптами
    managerScriptsListChanged = Signal()
    managerScriptOperationStatusChanged = Signal(bool, str)
    # Сигналы для работы со списками профилей
    profileListsChanged = Signal()
    profileListOperationStatusChanged = Signal(bool, str)  # Сигнал для уведомления о статусе операций со списками профилей

    def __init__(self):
        super().__init__()
        self.chrome = Chrome()
        self._profiles_list = []
        self._selected_profiles = set()
        self._filtered_profiles = []
        self._manager_scripts_list = []  # Список доступных менеджер-скриптов
        self._profile_lists = []  # Список доступных списков профилей
        self._current_list_id = ""  # Текущий выбранный список профилей
        self.update_profiles_list()
        self.updateProfileLists()  # Загружаем списки профилей
        self.engine = None  # Будет установлено позже
        
    @Slot()
    def update_profiles_list(self):
        try:
            self._profiles_list = get_profiles_list()
            logger.debug(f"Загружено профилей: {len(self._profiles_list)}")
            logger.debug(f"Список профилей: {self._profiles_list}")
            self.profilesListChanged.emit()
            # Очищаем выбранные профили при обновлении списка
            self._selected_profiles.clear()
            self.selectedProfilesChanged.emit()
            
            # Инициализируем _filtered_profiles всеми профилями
            self.searchProfilesByName("")
        except Exception as e:
            logger.error(f"Error updating profiles list: {e}")
            
    @Property('QVariantList', notify=profilesListChanged)
    def profilesList(self):
        """
        Возвращает список профилей без префикса "Profile " для отображения в интерфейсе
        """
        try:
            # Удаляем префикс "Profile " из имен профилей для отображения
            display_profiles = [profile.replace('Profile ', '') for profile in self._profiles_list]
            return display_profiles
        except Exception as e:
            logger.error(f"Ошибка при получении списка профилей: {e}")
            return []

    @Property('QVariantList', notify=filteredProfilesListChanged)
    def filteredProfilesList(self):
        return self._filtered_profiles

    @Property(bool, notify=selectedProfilesChanged)
    def hasSelectedProfiles(self):
        """
        Возвращает True, если есть выбранные профили, иначе False
        
        Returns:
            bool: True, если есть выбранные профили, иначе False
        """
        return len(self._selected_profiles) > 0
        
    @Slot(str, result=bool)
    def isProfileSelected(self, profile_name):
        """
        Проверяет, выбран ли профиль
        
        Args:
            profile_name: Имя профиля (без префикса "Profile ")
            
        Returns:
            bool: True, если профиль выбран, иначе False
        """
        # Проверяем, есть ли профиль в списке выбранных
        return profile_name in self._selected_profiles
        
    @Slot(str, bool)
    def toggleProfileSelection(self, profile_name, is_selected):
        """
        Переключает выбор профиля
        
        Args:
            profile_name: Имя профиля (без префикса "Profile ")
            is_selected: True, если профиль выбран, иначе False
        """
        try:
            logger.debug(f"toggleProfileSelection вызван для {profile_name}, is_selected={is_selected}")
            logger.debug(f"Текущие выбранные профили: {self._selected_profiles}")
            
            if is_selected and profile_name not in self._selected_profiles:
                self._selected_profiles.add(profile_name)
                self.selectedProfilesChanged.emit()
                logger.debug(f"Profile {profile_name} selected")
                logger.debug(f"Обновленные выбранные профили: {self._selected_profiles}")
            elif not is_selected and profile_name in self._selected_profiles:
                self._selected_profiles.remove(profile_name)
                self.selectedProfilesChanged.emit()
                logger.debug(f"Profile {profile_name} deselected")
                logger.debug(f"Обновленные выбранные профили: {self._selected_profiles}")
        except Exception as e:
            logger.error(f"Error toggling profile selection: {e}")

    @Slot(str)
    def searchProfilesByComment(self, search_text):
        try:
            from src.utils.helpers import get_profile_comments
            comments = get_profile_comments()
            search_text = search_text.lower()
            
            filtered_profiles = []
            for profile in self._profiles_list:
                comment = comments.get(profile, "").lower()
                if search_text in comment:
                    filtered_profiles.append({
                        "name": profile,
                        "comment": comments.get(profile, "")
                    })
            
            self._filtered_profiles = filtered_profiles
            self.filteredProfilesListChanged.emit()
            logger.debug(f"Found {len(filtered_profiles)} profiles matching '{search_text}'")
        except Exception as e:
            logger.error(f"Error searching profiles by comment: {e}")
            
    @Slot()
    def selectAllProfiles(self):
        try:
            # Просто выбираем все профили, но не запускаем их
            self._selected_profiles = set(self._profiles_list)
            self.selectedProfilesChanged.emit()
            logger.debug(f"Selected all profiles: {self._selected_profiles}")
        except Exception as e:
            logger.error(f"Error selecting all profiles: {e}")
        
    @Slot()
    def deselectAllProfiles(self):
        """
        Снимает выбор со всех профилей
        """
        self._selected_profiles.clear()
        self.selectedProfilesChanged.emit()
        logger.debug("Все профили сняты с выбора")
        
    @Slot('QVariantList')
    def setSelectedProfiles(self, profiles):
        """
        Устанавливает список выбранных профилей
        
        Args:
            profiles: Список профилей для выбора
        """
        logger.debug(f"setSelectedProfiles вызван с параметрами: profiles={profiles}")
        self._selected_profiles.clear()
        for profile in profiles:
            self._selected_profiles.add(profile)
        self.selectedProfilesChanged.emit()
        logger.debug(f"Установлены выбранные профили: {self._selected_profiles}")
        
    @Slot()
    def launchSelectedProfiles(self):
        if not self._selected_profiles:
            logger.warning("No profiles selected to launch")
            return
            
        logger.info(f"Launching selected profiles: {self._selected_profiles}")
        
        # Создаем копию выбранных профилей, чтобы избежать изменения во время итерации
        profiles_to_launch = list(self._selected_profiles)
        
        # Запускаем профили по одному
        for profile in profiles_to_launch:
            try:
                # Если профиль содержит префикс "Profile ", удаляем его перед запуском
                if isinstance(profile, str) and profile.startswith("Profile "):
                    profile_name = profile.replace("Profile ", "")
                else:
                    profile_name = profile
                
                # Запускаем профиль
                self.chrome.launch_profile(profile_name)
                logger.info(f"✅  {profile} - профиль запущен")
            except Exception as e:
                logger.error(f"❌  {profile} - ошибка запуска: {e}")
        
        # Очищаем выбранные профили после запуска
        self._selected_profiles.clear()
        self.selectedProfilesChanged.emit()

    @Slot('QVariantList')
    def launchProfilesByNames(self, profile_names):
        if not profile_names:
            logger.warning("No profile names provided")
            return
            
        logger.info(f"Launching profiles by names: {profile_names}")
        all_profiles = set(self._profiles_list)
        
        for name in profile_names:
            try:
                if name in all_profiles:
                    # Если профиль содержит префикс "Profile ", удаляем его перед запуском
                    if isinstance(name, str) and name.startswith("Profile "):
                        profile_name = name.replace("Profile ", "")
                    else:
                        profile_name = name
                    
                    # Используем те же параметры, что и в терминальном интерфейсе
                    self.chrome.launch_profile(
                        str(profile_name),
                        debug=False,
                        headless=False,
                        maximized=False
                    )
                    logger.info(f"✅  {name} - профиль запущен")
                else:
                    logger.warning(f"⚠️  {name} - профиль не найден")
            except Exception as e:
                logger.error(f"❌  {name} - ошибка запуска: {e}")
    
    @Slot(str)
    def updateProfileComments(self, comment):
        if not self._selected_profiles:
            logger.warning("No profiles selected to update comments")
            self.commentSaveStatusChanged.emit(False, "Не выбраны профили для обновления комментариев")
            return
            
        logger.info(f"Updating comments for profiles: {self._selected_profiles}")
        
        try:
            # Создаем копию выбранных профилей
            profiles_to_update = list(self._selected_profiles)
            
            # Обновляем комментарии
            result = set_comments_for_profiles(profiles_to_update, comment)
            
            if result["success"]:
                logger.info("✅  Комментарии обновлены")
                # Обновляем список профилей, чтобы отобразить изменения
                self.update_profiles_list()
                self.commentSaveStatusChanged.emit(True, "Комментарии успешно сохранены")
            else:
                error_message = f"Не удалось обновить комментарии: {result.get('description')}"
                logger.warning(f"⚠️ {error_message}")
                self.commentSaveStatusChanged.emit(False, error_message)
                
            # Очищаем выбранные профили после обновления
            self._selected_profiles.clear()
            self.selectedProfilesChanged.emit()
        except Exception as e:
            error_message = f"Ошибка при обновлении комментариев: {e}"
            logger.error(error_message)
            self.commentSaveStatusChanged.emit(False, error_message)
    
    @Slot(str, result=str)
    def getProfileComment(self, profile_name):
        """
        Получает комментарий для указанного профиля
        
        Args:
            profile_name: Имя профиля
            
        Returns:
            str: Комментарий к профилю или пустая строка, если комментария нет
        """
        try:
            result = get_comments_for_profiles()
            if result["success"]:
                comments = result["comments"]
                return comments.get(profile_name, "")
            return ""
        except Exception as e:
            logger.error(f"Error getting profile comment: {e}")
            return ""
            
    # Методы для подменю выбора профилей
    @Slot()
    def selectFromList(self):
        try:
            self.update_profiles_list()
            stackView = self.parent().findChild(QObject, "stackView")
            if stackView:
                stackView.push("qrc:/components/ProfileListSelection.qml")
        except Exception as e:
            logger.error(f"Error selecting from list: {e}")
            
    @Slot()
    def enterNames(self):
        try:
            # Показать диалог ввода имен
            print("Ввод названий")
        except Exception as e:
            logger.error(f"Error entering names: {e}")
            
    @Slot()
    def selectByComment(self):
        try:
            # Показать диалог выбора по комментарию
            print("Выбор по комментарию")
        except Exception as e:
            logger.error(f"Error selecting by comment: {e}")
            
    @Slot()
    def selectAll(self):
        try:
            self.update_profiles_list()
            
            # Получаем список всех профилей
            profiles = self._profiles_list
            logger.info(f"Launching all profiles: {profiles}")
            
            # Добавляем все профили в выбранные
            self._selected_profiles = set(profiles)
            
            # Запускаем выбранные профили через существующий метод
            self.launchSelectedProfiles()
        except Exception as e:
            logger.error(f"Error selecting all profiles: {e}")
    
    # Основные действия главного меню
    @Slot()
    def show_profiles(self):
        """
        Обновляет список профилей перед показом экрана просмотра профилей
        """
        self.update_profiles_list()
        logger.info("Просмотр профилей")
        
    @Slot()
    def update_comments(self):
        update_comments()
        
    @Slot()
    def run_chrome_scripts(self):
        """
        Открывает окно для прогона Chrome скриптов
        """
        # Находим объект ChromeScriptsRunner в QML
        engine = QQmlApplicationEngine.contextForObject(self).engine()
        root_objects = engine.rootObjects()
        
        for obj in root_objects:
            chrome_scripts_runner = obj.findChild(QObject, "chromeScriptsRunner")
            if chrome_scripts_runner:
                chrome_scripts_runner.show()
                return
                
        logger.warning("Не удалось найти окно ChromeScriptsRunner")
        
    @Slot()
    def run_manager_scripts(self):
        """Открывает окно для запуска менеджер-скриптов"""
        try:
            logger.info("Запуск метода run_manager_scripts")
            
            if not self.engine:
                logger.error("Engine не инициализирован")
                return
                
            # Находим окно для запуска скриптов
            manager_scripts_runner = self.engine.rootObjects()[0].findChild(QObject, "managerScriptsRunner")
            
            if manager_scripts_runner:
                logger.info("Найден компонент managerScriptsRunner")
                try:
                    # Обновляем список скриптов
                    self.update_manager_scripts_list()
                    logger.info(f"Обновлен список скриптов: {self._manager_scripts_list}")
                    
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
    
    @Slot()
    def manage_extensions(self):
        manage_extensions()
        
    @Slot(str)
    def createProfilesManually(self, profile_names_text):
        """
        Создает профили с указанными именами
        
        Args:
            profile_names_text: Строка с именами профилей, разделенными запятыми
        """
        try:
            # Разбиваем строку на имена профилей
            profile_names = [name.strip() for name in profile_names_text.split(',') if name.strip()]
            
            if not profile_names:
                self.profileCreationStatusChanged.emit(False, "Не указаны имена профилей")
                return
                
            logger.info(f"Создание профилей вручную: {profile_names}")
            
            # Получаем существующие профили для проверки дубликатов
            existing_profile_names = get_profiles_list()
            
            # Создаем профили
            created_profiles = []
            for name in profile_names:
                try:
                    # Проверяем, существует ли уже профиль с таким именем
                    if name in existing_profile_names:
                        logger.warning(f"Профиль с именем {name} уже существует, пропускаем")
                        continue
                        
                    # Создаем профиль
                    logger.info(f"Создание профиля: {name}")
                    self.chrome.create_new_profile(str(name))
                    created_profiles.append(name)
                except Exception as e:
                    logger.error(f"Ошибка при создании профиля {name}: {e}")
            
            # Обновляем список профилей
            self.update_profiles_list()
            
            if created_profiles:
                self.profileCreationStatusChanged.emit(True, f"Успешно созданы профили: {', '.join(created_profiles)}")
            else:
                self.profileCreationStatusChanged.emit(False, "Не удалось создать ни одного профиля")
                
        except Exception as e:
            logger.error(f"Ошибка при создании профилей: {e}")
            self.profileCreationStatusChanged.emit(False, f"Ошибка при создании профилей: {e}")
    
    @Slot(int, str)
    def createProfilesAutomatically(self, count, prefix=""):
        """
        Создает указанное количество профилей с автоматически сгенерированными именами
        
        Args:
            count: Количество профилей для создания
            prefix: Префикс для имен профилей (необязательно)
        """
        try:
            if count <= 0:
                self.profileCreationStatusChanged.emit(False, "Количество профилей должно быть больше 0")
                return
                
            logger.info(f"Автоматическое создание {count} профилей с префиксом '{prefix}'")
            
            # Получаем существующие профили
            existing_profile_names = get_profiles_list()
            
            # Находим наибольший числовой индекс среди существующих профилей
            highest_existing_numeric_name = 0
            
            for name in existing_profile_names:
                # Если используется префикс, проверяем только профили с этим префиксом
                if prefix and not name.startswith(prefix):
                    continue
                    
                # Извлекаем числовую часть имени
                try:
                    if prefix:
                        # Удаляем префикс и пытаемся преобразовать остаток в число
                        num_part = name[len(prefix):]
                        num = int(num_part)
                    else:
                        # Пытаемся преобразовать все имя в число
                        num = int(name)
                        
                    if num > highest_existing_numeric_name:
                        highest_existing_numeric_name = num
                except ValueError:
                    continue
            
            # Создаем профили
            created_profiles = []
            start = highest_existing_numeric_name + 1
            
            for i in range(count):
                try:
                    # Генерируем имя профиля
                    profile_name = f"{prefix}{start + i}"
                    
                    # Создаем профиль
                    logger.info(f"Создание профиля: {profile_name}")
                    self.chrome.create_new_profile(str(profile_name))
                    created_profiles.append(profile_name)
                except Exception as e:
                    logger.error(f"Ошибка при создании профиля {start + i}: {e}")
            
            # Обновляем список профилей
            self.update_profiles_list()
            
            if created_profiles:
                self.profileCreationStatusChanged.emit(True, f"Успешно созданы профили: {', '.join(created_profiles)}")
            else:
                self.profileCreationStatusChanged.emit(False, "Не удалось создать ни одного профиля")
                
        except Exception as e:
            logger.error(f"Ошибка при создании профилей: {e}")
            self.profileCreationStatusChanged.emit(False, f"Ошибка при создании профилей: {e}")
            
    @Slot()
    def create_profiles(self):
        create_multiple_profiles()
        
    @Slot()
    def kill_chrome(self):
        """
        Убивает все процессы Chrome
        """
        kill_chrome_processes()
        
    @Slot()
    def quit_application(self):
        """
        Корректно завершает работу приложения
        """
        logger.info("Завершение работы приложения...")
        QGuiApplication.quit()
        
    @Slot(str)
    def installExtensionForAllProfiles(self, extension_id):
        """
        Устанавливает расширение для всех профилей
        
        Args:
            extension_id: ID расширения в Chrome Web Store
        """
        # Запускаем операцию в отдельном потоке, чтобы не блокировать интерфейс
        def install_task():
            try:
                logger.info(f"Установка расширения {extension_id} для всех профилей")
                
                # Проверяем наличие расширения в папке default_extensions
                default_extensions_path = DEFAULT_EXTENSIONS_PATH
                extension_path = os.path.join(default_extensions_path, extension_id)
                
                if not os.path.exists(extension_path):
                    self.extensionOperationStatusChanged.emit(False, f"Расширение {extension_id} не найдено в папке default_extensions")
                    return
                    
                # Получаем список всех профилей
                profiles = self.chrome.get_profiles()
                if not profiles:
                    self.extensionOperationStatusChanged.emit(False, "Не найдено ни одного профиля")
                    return
                    
                # Устанавливаем расширение для каждого профиля
                success_count = 0
                for profile in profiles:
                    # Проверяем, содержит ли имя профиля префикс "Profile "
                    if isinstance(profile, str) and profile.startswith("Profile "):
                        profile_path = profile
                        # Для передачи в copy_extension нужно убрать префикс
                        profile_name = profile.replace("Profile ", "")
                    else:
                        profile_path = f"Profile {profile}"
                        profile_name = profile
                    
                    # Используем тот же способ формирования путей, что и в терминальном интерфейсе
                    profile_extensions_path = CHROME_DATA_PATH / profile_path / "Extensions"
                    os.makedirs(profile_extensions_path, exist_ok=True)
                    
                    dest_path = str(profile_extensions_path / extension_id)
                    if copy_extension(extension_path, dest_path, profile_name, extension_id, True):
                        success_count += 1
                        
                if success_count > 0:
                    self.extensionOperationStatusChanged.emit(True, f"Расширение установлено для {success_count} из {len(profiles)} профилей")
                else:
                    self.extensionOperationStatusChanged.emit(False, "Не удалось установить расширение ни для одного профиля")
                
                # Обновляем список установленных расширений
                self.getInstalledExtensionsList()
                    
            except Exception as e:
                logger.error(f"Ошибка при установке расширения: {e}")
                self.extensionOperationStatusChanged.emit(False, f"Ошибка при установке расширения: {e}")
        
        # Запускаем задачу в отдельном потоке
        executor = ThreadPoolExecutor(max_workers=1)
        executor.submit(install_task)
        executor.shutdown(wait=False)  # Не блокируем основной поток
    
    @Slot(str, bool)
    def installExtensionForAllProfilesWithReplace(self, extension_id, replace):
        """
        Устанавливает расширение для всех профилей с возможностью замены существующего
        
        Args:
            extension_id: ID расширения в Chrome Web Store
            replace: Заменять ли существующее расширение
        """
        # Запускаем операцию в отдельном потоке, чтобы не блокировать интерфейс
        def install_task():
            try:
                logger.info(f"Установка расширения {extension_id} для всех профилей (replace={replace})")
                
                # Проверяем наличие расширения в папке default_extensions
                default_extensions_path = DEFAULT_EXTENSIONS_PATH
                extension_path = os.path.join(default_extensions_path, extension_id)
                
                if not os.path.exists(extension_path):
                    self.extensionOperationStatusChanged.emit(False, f"Расширение {extension_id} не найдено в папке default_extensions")
                    return
                    
                # Получаем список всех профилей
                profiles = self.chrome.get_profiles()
                if not profiles:
                    self.extensionOperationStatusChanged.emit(False, "Не найдено ни одного профиля")
                    return
                    
                # Устанавливаем расширение для каждого профиля
                success_count = 0
                for profile in profiles:
                    # Проверяем, содержит ли имя профиля префикс "Profile "
                    if isinstance(profile, str) and profile.startswith("Profile "):
                        profile_path = profile
                        # Для передачи в copy_extension нужно убрать префикс
                        profile_name = profile.replace("Profile ", "")
                    else:
                        profile_path = f"Profile {profile}"
                        profile_name = profile
                    
                    # Используем тот же способ формирования путей, что и в терминальном интерфейсе
                    profile_extensions_path = CHROME_DATA_PATH / profile_path / "Extensions"
                    os.makedirs(profile_extensions_path, exist_ok=True)
                    
                    dest_path = str(profile_extensions_path / extension_id)
                    if copy_extension(extension_path, dest_path, profile_name, extension_id, replace):
                        success_count += 1
                        
                if success_count > 0:
                    self.extensionOperationStatusChanged.emit(True, f"Расширение установлено для {success_count} из {len(profiles)} профилей")
                else:
                    self.extensionOperationStatusChanged.emit(False, "Не удалось установить расширение ни для одного профиля")
                
                # Обновляем список установленных расширений
                self.getInstalledExtensionsList()
                    
            except Exception as e:
                logger.error(f"Ошибка при установке расширения: {e}")
                self.extensionOperationStatusChanged.emit(False, f"Ошибка при установке расширения: {e}")
        
        # Запускаем задачу в отдельном потоке
        executor = ThreadPoolExecutor(max_workers=1)
        executor.submit(install_task)
        executor.shutdown(wait=False)  # Не блокируем основной поток
    
    @Slot(str, bool)
    def installExtensionForSelectedProfilesWithReplace(self, extension_id, replace):
        """
        Устанавливает расширение для выбранных профилей с возможностью замены существующего
        
        Args:
            extension_id: ID расширения в Chrome Web Store
            replace: Заменять ли существующее расширение
        """
        # Запускаем операцию в отдельном потоке, чтобы не блокировать интерфейс
        def install_task():
            try:
                if not self._selected_profiles:
                    self.extensionOperationStatusChanged.emit(False, "Не выбрано ни одного профиля")
                    return
                    
                logger.info(f"Установка расширения {extension_id} для выбранных профилей: {self._selected_profiles} (replace={replace})")
                
                # Проверяем наличие расширения в папке default_extensions
                default_extensions_path = DEFAULT_EXTENSIONS_PATH
                extension_path = os.path.join(default_extensions_path, extension_id)
                
                if not os.path.exists(extension_path):
                    self.extensionOperationStatusChanged.emit(False, f"Расширение {extension_id} не найдено в папке default_extensions")
                    return
                    
                # Устанавливаем расширение для каждого выбранного профиля
                success_count = 0
                for profile in self._selected_profiles:
                    # Проверяем, содержит ли имя профиля префикс "Profile "
                    if isinstance(profile, str) and profile.startswith("Profile "):
                        profile_path = profile
                        # Для передачи в copy_extension нужно убрать префикс
                        profile_name = profile.replace("Profile ", "")
                    else:
                        profile_path = f"Profile {profile}"
                        profile_name = profile
                    
                    # Используем тот же способ формирования путей, что и в терминальном интерфейсе
                    profile_extensions_path = CHROME_DATA_PATH / profile_path / "Extensions"
                    os.makedirs(profile_extensions_path, exist_ok=True)
                    
                    dest_path = str(profile_extensions_path / extension_id)
                    if copy_extension(extension_path, dest_path, profile_name, extension_id, replace):
                        success_count += 1
                        
                if success_count > 0:
                    self.extensionOperationStatusChanged.emit(True, f"Расширение установлено для {success_count} из {len(self._selected_profiles)} профилей")
                else:
                    self.extensionOperationStatusChanged.emit(False, "Не удалось установить расширение ни для одного профиля")
                    
                # Очищаем выбранные профили
                # self._selected_profiles.clear()
                # self.selectedProfilesChanged.emit()
                
                # Обновляем список установленных расширений
                self.getInstalledExtensionsList()
                    
            except Exception as e:
                logger.error(f"Ошибка при установке расширения: {e}")
                self.extensionOperationStatusChanged.emit(False, f"Ошибка при установке расширения: {e}")
        
        # Запускаем задачу в отдельном потоке
        executor = ThreadPoolExecutor(max_workers=1)
        executor.submit(install_task)
    
    @Slot(str)
    def installExtensionForSelectedProfiles(self, extension_id):
        """
        Устанавливает расширение для выбранных профилей
        
        Args:
            extension_id: ID расширения в Chrome Web Store
        """
        # Запускаем операцию в отдельном потоке, чтобы не блокировать интерфейс
        def install_task():
            try:
                if not self._selected_profiles:
                    self.extensionOperationStatusChanged.emit(False, "Не выбрано ни одного профиля")
                    return
                    
                logger.info(f"Установка расширения {extension_id} для выбранных профилей: {self._selected_profiles}")
                
                # Проверяем наличие расширения в папке default_extensions
                default_extensions_path = DEFAULT_EXTENSIONS_PATH
                extension_path = os.path.join(default_extensions_path, extension_id)
                
                if not os.path.exists(extension_path):
                    self.extensionOperationStatusChanged.emit(False, f"Расширение {extension_id} не найдено в папке default_extensions")
                    return
                    
                # Устанавливаем расширение для каждого выбранного профиля
                success_count = 0
                for profile in self._selected_profiles:
                    # Проверяем, содержит ли имя профиля префикс "Profile "
                    if isinstance(profile, str) and profile.startswith("Profile "):
                        profile_path = profile
                        # Для передачи в copy_extension нужно убрать префикс
                        profile_name = profile.replace("Profile ", "")
                    else:
                        profile_path = f"Profile {profile}"
                        profile_name = profile
                    
                    # Используем тот же способ формирования путей, что и в терминальном интерфейсе
                    profile_extensions_path = CHROME_DATA_PATH / profile_path / "Extensions"
                    os.makedirs(profile_extensions_path, exist_ok=True)
                    
                    dest_path = str(profile_extensions_path / extension_id)
                    if copy_extension(extension_path, dest_path, profile_name, extension_id, True):
                        success_count += 1
                        
                if success_count > 0:
                    self.extensionOperationStatusChanged.emit(True, f"Расширение установлено для {success_count} из {len(self._selected_profiles)} профилей")
                else:
                    self.extensionOperationStatusChanged.emit(False, "Не удалось установить расширение ни для одного профиля")
                    
                # Очищаем выбранные профили
                # self._selected_profiles.clear()
                # self.selectedProfilesChanged.emit()
                
                # Обновляем список установленных расширений
                self.getInstalledExtensionsList()
                    
            except Exception as e:
                logger.error(f"Ошибка при установке расширения: {e}")
                self.extensionOperationStatusChanged.emit(False, f"Ошибка при установке расширения: {e}")
        
        # Запускаем задачу в отдельном потоке
        executor = ThreadPoolExecutor(max_workers=1)
        executor.submit(install_task)
    
    @Slot('QVariantList', bool)
    def installMultipleExtensionsForSelectedProfiles(self, extension_ids, replace):
        """
        Устанавливает несколько расширений для выбранных профилей
        
        Args:
            extension_ids: Список ID расширений
            replace: Флаг замены существующих расширений
        """
        try:
            if not extension_ids:
                self.extensionOperationStatusChanged.emit(False, "Не выбрано ни одного расширения")
                return
                
            if not self._selected_profiles:
                self.extensionOperationStatusChanged.emit(False, "Не выбрано ни одного профиля")
                return
                
            # Создаем копию выбранных профилей, чтобы избежать ошибки "Set changed size during iteration"
            selected_profiles = list(self._selected_profiles)
            
            logger.info(f"Установка расширений {extension_ids} для выбранных профилей: {selected_profiles}, replace={replace}")
            
            # Запускаем установку в отдельном потоке
            def install_task():
                try:
                    # Проверяем наличие расширений в папке default_extensions
                    missing_extensions = []
                    for ext_id in extension_ids:
                        ext_path = os.path.join(DEFAULT_EXTENSIONS_PATH, ext_id)
                        if not os.path.exists(ext_path):
                            missing_extensions.append(ext_id)
                    
                    if missing_extensions:
                        self.extensionOperationStatusChanged.emit(False, f"Расширения не найдены в папке default_extensions: {', '.join(missing_extensions)}")
                        return
                    
                    # Устанавливаем расширения для каждого выбранного профиля
                    success_count = 0
                    total_operations = len(extension_ids) * len(selected_profiles)
                    
                    for profile in selected_profiles:
                        for ext_id in extension_ids:
                            try:
                                # Получаем путь к расширению в папке default_extensions
                                src_path = os.path.join(DEFAULT_EXTENSIONS_PATH, ext_id)
                                
                                # Проверяем, содержит ли имя профиля префикс "Profile "
                                if isinstance(profile, str) and profile.startswith("Profile "):
                                    profile_path = profile
                                    # Для передачи в copy_extension нужно убрать префикс
                                    profile_name = profile.replace("Profile ", "")
                                else:
                                    profile_path = f"Profile {profile}"
                                    profile_name = profile
                                
                                # Формируем путь к папке с расширениями профиля
                                profile_extensions_path = os.path.join(CHROME_DATA_PATH, profile_path, "Extensions")
                                
                                # Создаем папку Extensions, если она не существует
                                if not os.path.exists(profile_extensions_path):
                                    os.makedirs(profile_extensions_path)
                                
                                # Формируем путь назначения
                                dest_path = os.path.join(profile_extensions_path, ext_id)
                                
                                # Копируем расширение
                                result = copy_extension(src_path, dest_path, profile_name, ext_id, replace)
                                
                                if result:
                                    success_count += 1
                                    logger.info(f"Расширение {ext_id} успешно установлено для профиля {profile}")
                                else:
                                    logger.error(f"Не удалось установить расширение {ext_id} для профиля {profile}")
                            except Exception as e:
                                logger.error(f"Ошибка при установке расширения {ext_id} для профиля {profile}: {e}")
                    
                    # Обновляем список расширений
                    self.getDefaultExtensionsList()
                    
                    if success_count == total_operations:
                        self.extensionOperationStatusChanged.emit(True, f"Все расширения ({len(extension_ids)}) успешно установлены для {len(selected_profiles)} профилей")
                    else:
                        self.extensionOperationStatusChanged.emit(True, f"Установлено {success_count} из {total_operations} расширений")
                    
                    # Очищаем выбранные профили после завершения операции
                    self._selected_profiles.clear()
                    self.selectedProfilesChanged.emit()
                
                except Exception as e:
                    logger.error(f"Ошибка при установке расширений: {e}")
                    self.extensionOperationStatusChanged.emit(False, f"Ошибка при установке расширений: {e}")
            
            # Запускаем задачу в отдельном потоке
            threading.Thread(target=install_task).start()
            
        except Exception as e:
            logger.error(f"Ошибка при установке расширений: {e}")
            self.extensionOperationStatusChanged.emit(False, f"Ошибка при установке расширений: {e}")
    
    @Slot('QVariantList', bool)
    def installMultipleExtensionsForAllProfiles(self, extension_ids, replace):
        """
        Устанавливает несколько расширений для всех профилей
        
        Args:
            extension_ids: Список ID расширений
            replace: Флаг замены существующих расширений
        """
        try:
            if not extension_ids:
                self.extensionOperationStatusChanged.emit(False, "Не выбрано ни одного расширения")
                return
                
            # Создаем копию списка расширений, чтобы избежать ошибки "Set changed size during iteration"
            extension_ids_list = list(extension_ids)
            
            logger.info(f"Установка расширений {extension_ids_list} для всех профилей, replace={replace}")
            
            # Запускаем установку в отдельном потоке
            def install_task():
                try:
                    # Проверяем наличие расширений в папке default_extensions
                    missing_extensions = []
                    for ext_id in extension_ids_list:
                        ext_path = os.path.join(DEFAULT_EXTENSIONS_PATH, ext_id)
                        if not os.path.exists(ext_path):
                            missing_extensions.append(ext_id)
                    
                    if missing_extensions:
                        self.extensionOperationStatusChanged.emit(False, f"Расширения не найдены в папке default_extensions: {', '.join(missing_extensions)}")
                        return
                    
                    # Получаем список всех профилей
                    profiles = get_profiles_list()
                    
                    # Устанавливаем расширения для каждого профиля
                    success_count = 0
                    total_operations = len(extension_ids_list) * len(profiles)
                    
                    for profile in profiles:
                        for ext_id in extension_ids_list:
                            try:
                                # Получаем путь к расширению в папке default_extensions
                                src_path = os.path.join(DEFAULT_EXTENSIONS_PATH, ext_id)
                                
                                # Проверяем, содержит ли имя профиля префикс "Profile "
                                if isinstance(profile, str) and profile.startswith("Profile "):
                                    profile_path = profile
                                    # Для передачи в copy_extension нужно убрать префикс
                                    profile_name = profile.replace("Profile ", "")
                                else:
                                    profile_path = f"Profile {profile}"
                                    profile_name = profile
                                
                                # Формируем путь к папке с расширениями профиля
                                profile_extensions_path = os.path.join(CHROME_DATA_PATH, profile_path, "Extensions")
                                
                                # Создаем папку Extensions, если она не существует
                                if not os.path.exists(profile_extensions_path):
                                    os.makedirs(profile_extensions_path)
                                
                                # Формируем путь назначения
                                dest_path = os.path.join(profile_extensions_path, ext_id)
                                
                                # Копируем расширение
                                result = copy_extension(src_path, dest_path, profile_name, ext_id, replace)
                                
                                if result:
                                    success_count += 1
                                    logger.info(f"Расширение {ext_id} успешно установлено для профиля {profile}")
                                else:
                                    logger.error(f"Не удалось установить расширение {ext_id} для профиля {profile}")
                            except Exception as e:
                                logger.error(f"Ошибка при установке расширения {ext_id} для профиля {profile}: {e}")
                    
                    # Обновляем список расширений
                    self.getDefaultExtensionsList()
                    
                    if success_count == total_operations:
                        self.extensionOperationStatusChanged.emit(True, f"Все расширения ({len(extension_ids_list)}) успешно установлены для всех профилей ({len(profiles)})")
                    else:
                        self.extensionOperationStatusChanged.emit(True, f"Установлено {success_count} из {total_operations} расширений")
                    
                    # Очищаем выбранные профили после завершения операции
                    self._selected_profiles.clear()
                    self.selectedProfilesChanged.emit()
                
                except Exception as e:
                    logger.error(f"Ошибка при установке расширений: {e}")
                    self.extensionOperationStatusChanged.emit(False, f"Ошибка при установке расширений: {e}")
            
            # Запускаем задачу в отдельном потоке
            threading.Thread(target=install_task).start()
            
        except Exception as e:
            logger.error(f"Ошибка при установке расширений: {e}")
            self.extensionOperationStatusChanged.emit(False, f"Ошибка при установке расширений: {e}")
    
    @Slot('QVariantList')
    def removeMultipleExtensionsFromAllProfiles(self, extension_ids):
        """
        Удаляет несколько расширений из всех профилей
        
        Args:
            extension_ids: Список ID расширений
        """
        try:
            if not extension_ids:
                self.extensionOperationStatusChanged.emit(False, "Не выбрано ни одного расширения")
                return
                
            logger.info(f"Удаление расширений {extension_ids} из всех профилей")
            
            # Получаем список всех профилей
            profiles = get_profiles_list()
            
            if not profiles:
                self.extensionOperationStatusChanged.emit(False, "Не найдено ни одного профиля")
                return
                
            # Удаляем расширения из каждого профиля с использованием ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=general_config['max_workers']) as executor:
                futures = []
                for profile in profiles:
                    # Профиль уже содержит префикс "Profile ", так как мы изменили get_profiles_list
                    # Функция remove_extensions теперь умеет обрабатывать имена с префиксом
                    futures.append(executor.submit(remove_extensions, profile, extension_ids))
                
                # Ждем завершения всех задач
                for future in futures:
                    future.result()
                    
            self.extensionOperationStatusChanged.emit(True, f"Расширения удалены из всех профилей")
                
        except Exception as e:
            logger.error(f"Ошибка при удалении расширений: {e}")
            self.extensionOperationStatusChanged.emit(False, f"Ошибка при удалении расширений: {e}")
    
    @Slot('QVariantList', bool)
    def removeMultipleExtensionsFromSelectedProfiles(self, extension_ids):
        """
        Удаляет несколько расширений из выбранных профилей
        
        Args:
            extension_ids: Список ID расширений
        """
        try:
            if not extension_ids:
                self.extensionOperationStatusChanged.emit(False, "Не выбрано ни одного расширения")
                return
                
            if not self._selected_profiles:
                self.extensionOperationStatusChanged.emit(False, "Не выбрано ни одного профиля")
                return
                
            logger.info(f"Удаление расширений {extension_ids} из выбранных профилей: {self._selected_profiles}")
            
            # Удаляем расширения из каждого выбранного профиля
            success_count = 0
            total_operations = len(extension_ids) * len(self._selected_profiles)
            
            for profile in self._selected_profiles:
                # Профиль может содержать или не содержать префикс "Profile "
                # Функция remove_extensions теперь умеет обрабатывать оба варианта
                remove_extensions(profile, extension_ids)
                success_count += 1
                
            if success_count == len(self._selected_profiles):
                self.extensionOperationStatusChanged.emit(True, f"Расширения успешно удалены из {success_count} профилей")
            else:
                self.extensionOperationStatusChanged.emit(False, f"Расширения удалены только из {success_count} из {len(self._selected_profiles)} профилей")
                
        except Exception as e:
            logger.error(f"Ошибка при удалении расширений: {e}")
            self.extensionOperationStatusChanged.emit(False, f"Ошибка при удалении расширений: {e}")
    
    @Slot(str, str)
    def copyExtensionFromProfileToDefault(self, profile, extension_id):
        """
        Копирует расширение из профиля в папку default_extensions
        
        Args:
            profile: Имя или номер профиля
            extension_id: ID расширения
        """
        try:
            logger.info(f"Копирование расширения {extension_id} из профиля {profile} в default_extensions")
            
            # Формируем путь к папке с расширениями профиля
            profile_extensions_path = Path(CHROME_DATA_PATH) / f"Profile {profile}" / "Extensions"
            
            if not profile_extensions_path.exists():
                self.extensionOperationStatusChanged.emit(False, f"Папка с расширениями профиля {profile} не найдена")
                return
                
            # Проверяем наличие расширения в профиле
            ext_path = profile_extensions_path / extension_id
            if not ext_path.exists():
                self.extensionOperationStatusChanged.emit(False, f"Расширение {extension_id} не найдено в профиле {profile}")
                return
                
            # Копируем расширение в папку default_extensions
            dest_path = Path(DEFAULT_EXTENSIONS_PATH) / extension_id
            
            # Если папка назначения существует, удаляем ее
            if dest_path.exists():
                shutil.rmtree(dest_path)
                
            # Создаем папку назначения
            os.makedirs(dest_path, exist_ok=True)
            
            # Копируем все версии расширения
            for version in os.listdir(ext_path):
                version_path = ext_path / version
                if os.path.isdir(version_path):
                    dest_version_path = dest_path / version
                    shutil.copytree(version_path, dest_version_path)
            
            # Обновляем список расширений
            self.getDefaultExtensionsList()
            
            self.extensionOperationStatusChanged.emit(True, f"Расширение {extension_id} успешно скопировано в default_extensions")
            
        except Exception as e:
            logger.error(f"Ошибка при копировании расширения {extension_id} из профиля {profile}: {e}")
            self.extensionOperationStatusChanged.emit(False, f"Ошибка при копировании расширения: {e}")
    
    @Slot(str)
    def copyAllExtensionsFromProfileToDefault(self, profile):
        """
        Копирует все расширения из профиля в папку default_extensions
        
        Args:
            profile: Имя или номер профиля
        """
        try:
            logger.info(f"Копирование всех расширений из профиля {profile} в default_extensions")
            
            # Формируем путь к папке с расширениями профиля
            profile_extensions_path = Path(CHROME_DATA_PATH) / f"Profile {profile}" / "Extensions"
            
            if not profile_extensions_path.exists():
                self.extensionOperationStatusChanged.emit(False, f"Папка с расширениями профиля {profile} не найдена")
                return
                
            # Получаем список расширений из профиля
            extensions_count = 0
            success_count = 0
            
            for ext_id in os.listdir(profile_extensions_path):
                ext_path = profile_extensions_path / ext_id
                if not os.path.isdir(ext_path):
                    continue
                    
                extensions_count += 1
                
                try:
                    # Копируем расширение в папку default_extensions
                    dest_path = Path(DEFAULT_EXTENSIONS_PATH) / ext_id
                    
                    # Если папка назначения существует, удаляем ее
                    if dest_path.exists():
                        shutil.rmtree(dest_path)
                        
                    # Создаем папку назначения
                    os.makedirs(dest_path, exist_ok=True)
                    
                    # Копируем все версии расширения
                    for version in os.listdir(ext_path):
                        version_path = ext_path / version
                        if os.path.isdir(version_path):
                            dest_version_path = dest_path / version
                            shutil.copytree(version_path, dest_version_path)
                            
                    success_count += 1
                except Exception as e:
                    logger.error(f"Ошибка при копировании расширения {ext_id}: {e}")
            
            # Обновляем список расширений
            self.getDefaultExtensionsList()
            
            if extensions_count == 0:
                self.extensionOperationStatusChanged.emit(False, f"В профиле {profile} не найдено расширений")
            elif success_count == extensions_count:
                self.extensionOperationStatusChanged.emit(True, f"Все расширения ({success_count}) успешно скопированы в default_extensions")
            else:
                self.extensionOperationStatusChanged.emit(True, f"Скопировано {success_count} из {extensions_count} расширений")
            
        except Exception as e:
            logger.error(f"Ошибка при копировании всех расширений из профиля {profile}: {e}")
            self.extensionOperationStatusChanged.emit(False, f"Ошибка при копировании расширений: {e}")
    
    @Slot()
    def getDefaultExtensionsList(self):
        """
        Получает список доступных дефолтных расширений и отправляет его в QML
        """
        try:
            logger.info("Получение списка доступных дефолтных расширений")
            
            # Получаем информацию о дефолтных расширениях
            extensions_info = get_all_default_extensions_info()
            
            if not extensions_info:
                self.extensionOperationStatusChanged.emit(False, "Не найдено ни одного дефолтного расширения")
                return
                
            # Формируем список расширений для QML
            extensions_list = []
            default_extensions_dir = os.path.join(PROJECT_PATH, "data", "default_extensions")
            
            for ext_id, name in extensions_info.items():
                ext_path = os.path.join(default_extensions_dir, ext_id)
                ext_name = name if name else ext_id
                ext_version = get_extension_version(ext_path)
                ext_icon_path = get_extension_icon_path(ext_path)
                
                # Преобразуем путь к иконке в URL для QML
                ext_icon_url = ""
                if ext_icon_path:
                    try:
                        # Используем pathlib для корректного формирования URL
                        path_obj = Path(ext_icon_path)
                        # Преобразуем путь в строку с прямыми слешами
                        ext_icon_url = QUrl.fromLocalFile(str(path_obj)).toString()
                    except Exception as e:
                        logger.error(f"Ошибка при формировании URL для иконки: {e}")
                
                extensions_list.append({
                    "id": ext_id,
                    "name": ext_name,
                    "version": ext_version,
                    "iconUrl": ext_icon_url
                })
            
            # Отправляем список расширений в QML
            self.extensionsListChanged.emit(extensions_list)
            
        except Exception as e:
            logger.error(f"Ошибка при получении списка дефолтных расширений: {e}")
            self.extensionOperationStatusChanged.emit(False, f"Ошибка при получении списка дефолтных расширений: {e}")
    
    @Slot(str)
    def getProfileExtensions(self, profile):
        """
        Получает список расширений из указанного профиля и отправляет его в QML
        
        Args:
            profile: Имя или номер профиля (может быть с префиксом "Profile " или без него)
        """
        try:
            logger.info(f"Получение списка расширений из профиля {profile}")
            
            # Проверяем, содержит ли имя профиля префикс "Profile "
            if not profile.startswith("Profile "):
                profile_path = f"Profile {profile}"
            else:
                profile_path = profile
            
            # Формируем путь к папке с расширениями профиля
            profile_extensions_path = Path(CHROME_DATA_PATH) / profile_path / "Extensions"
            
            if not profile_extensions_path.exists():
                self.extensionOperationStatusChanged.emit(False, f"Папка с расширениями профиля {profile} не найдена")
                return
                
            # Получаем список расширений из профиля
            extensions_list = []
            
            for ext_id in os.listdir(profile_extensions_path):
                ext_path = profile_extensions_path / ext_id
                if not os.path.isdir(ext_path):
                    continue
                    
                # Находим последнюю версию расширения
                versions = [v for v in os.listdir(ext_path) if os.path.isdir(ext_path / v)]
                if not versions:
                    continue
                    
                # Берем последнюю версию (обычно самую новую)
                latest_version = sorted(versions)[-1]
                ext_manifest_path = ext_path / latest_version / "manifest.json"
                
                # Получаем информацию о расширении из манифеста
                ext_name = ext_id
                ext_version = latest_version
                ext_icon_path = ""
                
                if os.path.exists(ext_manifest_path):
                    try:
                        with open(ext_manifest_path, 'r', encoding='utf-8') as f:
                            manifest = json.load(f)
                            ext_name = manifest.get('name', ext_id)
                            ext_version = manifest.get('version', latest_version)
                            
                            # Получаем путь к иконке
                            icons = manifest.get('icons', {})
                            icon_sizes = sorted([int(size) for size in icons.keys() if size.isdigit()], reverse=True)
                            
                            if icon_sizes:
                                icon_file = icons[str(icon_sizes[0])]
                                ext_icon_path = str(ext_path / latest_version / icon_file)
                    except Exception as e:
                        logger.error(f"Ошибка при чтении манифеста расширения {ext_id}: {e}")
                
                # Преобразуем путь к иконке в URL для QML
                ext_icon_url = ""
                if ext_icon_path and os.path.exists(ext_icon_path):
                    try:
                        # Используем pathlib для корректного формирования URL
                        path_obj = Path(ext_icon_path)
                        # Преобразуем путь в строку с прямыми слешами
                        ext_icon_url = QUrl.fromLocalFile(str(path_obj)).toString()
                    except Exception as e:
                        logger.error(f"Ошибка при формировании URL для иконки: {e}")
                
                extensions_list.append({
                    "id": ext_id,
                    "name": ext_name,
                    "version": ext_version,
                    "iconUrl": ext_icon_url
                })
            
            # Отправляем список расширений в QML
            self.extensionsListChanged.emit(extensions_list)
            
        except Exception as e:
            logger.error(f"Ошибка при получении списка расширений из профиля {profile}: {e}")
            self.extensionOperationStatusChanged.emit(False, f"Ошибка при получении списка расширений из профиля {profile}: {e}")
    
    @Slot()
    def getInstalledExtensionsList(self):
        """
        Получает список установленных расширений и отправляет его в QML
        """
        try:
            logger.info("Получение списка установленных расширений")
            
            # Получаем список всех профилей
            profiles = get_profiles_list()
            
            if not profiles:
                self.extensionOperationStatusChanged.emit(False, "Не найдено ни одного профиля")
                return
                
            # Получаем информацию о расширениях для всех профилей
            extensions_info = get_profiles_extensions_info(profiles)
            
            if not extensions_info:
                self.extensionOperationStatusChanged.emit(False, "Не найдено ни одного расширения")
                return
                
            # Формируем список расширений для QML
            extensions_list = []
            for ext_id, ext_name in extensions_info.items():
                # Формируем путь к расширению
                profile_path = os.path.join(CHROME_DATA_PATH, f"Profile {profiles[0]}")
                ext_path = os.path.join(profile_path, "Extensions", ext_id)
                
                # Получаем версию и иконку расширения
                ext_version = get_extension_version(ext_path)
                ext_icon_path = get_extension_icon_path(ext_path)
                
                # Преобразуем путь к иконке в URL для QML
                ext_icon_url = ""
                if ext_icon_path:
                    try:
                        # Используем pathlib для корректного формирования URL
                        path_obj = Path(ext_icon_path)
                        # Преобразуем путь в строку с прямыми слешами
                        ext_icon_url = QUrl.fromLocalFile(str(path_obj)).toString()
                    except Exception as e:
                        logger.error(f"Ошибка при формировании URL для иконки: {e}")
                
                # Формируем объект с информацией о расширении
                extension_info = {
                    "id": ext_id, 
                    "name": ext_name if ext_name else f"Расширение {ext_id[:8]}...",
                    "version": ext_version,
                    "iconUrl": ext_icon_url,
                    "path": ext_path
                }
                
                extensions_list.append(extension_info)
                
            # Сортируем список расширений по имени
            extensions_list.sort(key=lambda x: x["name"])
                
            # Отправляем список расширений в QML
            self.extensionsListChanged.emit(extensions_list)
            self.extensionOperationStatusChanged.emit(True, f"Найдено {len(extensions_list)} расширений")
                
        except Exception as e:
            logger.error(f"Ошибка при получении списка установленных расширений: {e}")
            self.extensionOperationStatusChanged.emit(False, f"Ошибка при получении списка установленных расширений: {e}")
    
    @Slot()
    def listInstalledExtensions(self):
        """
        Выводит список установленных расширений для всех профилей
        """
        try:
            logger.info("Получение списка установленных расширений")
            
            # Получаем список всех профилей
            profiles = get_profiles_list()
            
            if not profiles:
                self.extensionOperationStatusChanged.emit(False, "Не найдено ни одного профиля")
                return
                
            # Получаем информацию о расширениях для всех профилей
            extensions_info = get_profiles_extensions_info(profiles)
            
            if not extensions_info:
                self.extensionOperationStatusChanged.emit(False, "Не найдено ни одного расширения")
                return
                
            # Формируем сообщение со списком расширений
            message = "Установленные расширения:\n\n"
            for ext_id, name in extensions_info.items():
                ext_name = name if name else "Без имени"
                message += f"ID: {ext_id}\nИмя: {ext_name}\n\n"
                
            self.extensionOperationStatusChanged.emit(True, message)
                
        except Exception as e:
            logger.error(f"Ошибка при получении списка расширений: {e}")
            self.extensionOperationStatusChanged.emit(False, f"Ошибка при получении списка расширений: {e}")
    
    @Slot(str)
    def removeExtensionFromAllProfiles(self, extension_id):
        """
        Удаляет расширение из всех профилей
        
        Args:
            extension_id: ID расширения
        """
        try:
            logger.info(f"Удаление расширения {extension_id} из всех профилей")
            
            # Получаем список всех профилей
            profiles = get_profiles_list()
            
            if not profiles:
                self.extensionOperationStatusChanged.emit(False, "Не найдено ни одного профиля")
                return
                
            # Удаляем расширение из каждого профиля
            for profile in profiles:
                remove_extensions(profile, [extension_id])
                
            self.extensionOperationStatusChanged.emit(True, f"Расширение удалено из всех профилей")
                
        except Exception as e:
            logger.error(f"Ошибка при удалении расширения: {e}")
            self.extensionOperationStatusChanged.emit(False, f"Ошибка при удалении расширения: {e}")
    
    @Slot(str)
    def removeExtensionFromSelectedProfiles(self, extension_id):
        """
        Удаляет расширение из выбранных профилей
        
        Args:
            extension_id: ID расширения
        """
        try:
            if not self._selected_profiles:
                self.extensionOperationStatusChanged.emit(False, "Не выбрано ни одного профиля")
                return
                
            logger.info(f"Удаление расширения {extension_id} из выбранных профилей: {self._selected_profiles}")
            
            # Удаляем расширение из каждого выбранного профиля
            for profile in self._selected_profiles:
                remove_extensions(profile, [extension_id])
                
            self.extensionOperationStatusChanged.emit(True, f"Расширение удалено из выбранных профилей")
            
            # Очищаем выбранные профили
            # self._selected_profiles.clear()
            # self.selectedProfilesChanged.emit()
                
        except Exception as e:
            logger.error(f"Ошибка при удалении расширения: {e}")
            self.extensionOperationStatusChanged.emit(False, f"Ошибка при удалении расширения: {e}")

    @Slot(str)
    def installExtensionFromChromeStore(self, extension_id):
        """
        Устанавливает расширение из Chrome Web Store для выбранных профилей
        
        Args:
            extension_id: ID расширения в Chrome Web Store
        """
        # Запускаем операцию в отдельном потоке, чтобы не блокировать интерфейс
        def install_task():
            try:
                if not self._selected_profiles:
                    self.extensionOperationStatusChanged.emit(False, "Не выбрано ни одного профиля")
                    return
                    
                logger.info(f"Установка расширения {extension_id} из Chrome Web Store для выбранных профилей: {self._selected_profiles}")
                
                # Проверяем наличие расширения в папке default_extensions
                default_extensions_path = DEFAULT_EXTENSIONS_PATH
                extension_path = os.path.join(default_extensions_path, extension_id)
                
                if os.path.exists(extension_path):
                    logger.info(f"Расширение {extension_id} уже существует в папке default_extensions, используем его")
                    self.installExtensionForSelectedProfiles(extension_id)
                    return
                    
                # Устанавливаем расширение для каждого выбранного профиля
                success_count = 0
                for profile in self._selected_profiles:
                    try:
                        # Запускаем Chrome с выбранным профилем
                        chrome_process = self.chrome.launch_profile(profile, True, False, True)
                        if not chrome_process:
                            logger.error(f"Не удалось запустить Chrome для профиля {profile}")
                            continue
                            
                        time.sleep(1)
                        
                        # Подключаемся к Chrome через debug port
                        debug_port = self.chrome.debug_ports.get(profile)
                        if not debug_port:
                            logger.error(f"Не удалось получить debug port для профиля {profile}")
                            chrome_process.terminate()
                            continue
                            
                        chrome_options = Options()
                        chrome_options.add_experimental_option("debuggerAddress", f"127.0.0.1:{debug_port}")
                        service = Service(CHROME_DRIVER_PATH)
                        driver = webdriver.Chrome(service=service, options=chrome_options)
                        
                        # Открываем страницу расширения в Chrome Web Store
                        driver.get(f"https://chrome.google.com/webstore/detail/{extension_id}")
                        time.sleep(2)
                        
                        # Нажимаем кнопку "Установить"
                        try:
                            install_button = driver.find_element(By.CSS_SELECTOR, "div[aria-label='Установить']")
                            install_button.click()
                            time.sleep(2)
                            
                            # Подтверждаем установку
                            confirm_button = driver.find_element(By.CSS_SELECTOR, "div[aria-label='Установить расширение']")
                            confirm_button.click()
                            time.sleep(5)
                            
                            # Проверяем, что расширение установлено
                            # Используем тот же способ формирования путей, что и в терминальном интерфейсе
                            profile_extensions_path = CHROME_DATA_PATH / f"Profile {profile}" / "Extensions" / extension_id
                            if os.path.exists(profile_extensions_path):
                                success_count += 1
                                
                                # Копируем расширение в папку default_extensions
                                os.makedirs(os.path.join(default_extensions_path, extension_id), exist_ok=True)
                                for version in os.listdir(profile_extensions_path):
                                    version_path = os.path.join(profile_extensions_path, version)
                                    if os.path.isdir(version_path):
                                        dest_path = os.path.join(default_extensions_path, extension_id, version)
                                        shutil.copytree(version_path, dest_path, dirs_exist_ok=True)
                                        logger.info(f"Расширение {extension_id} (версия {version}) скопировано в папку default_extensions")
                                        break
                        except Exception as e:
                            logger.error(f"Ошибка при установке расширения для профиля {profile}: {e}")
                            
                        # Закрываем Chrome
                        driver.quit()
                        chrome_process.terminate()
                        chrome_process.wait()
                    except Exception as e:
                        logger.error(f"Ошибка при установке расширения для профиля {profile}: {e}")
                        
                if success_count > 0:
                    self.extensionOperationStatusChanged.emit(True, f"Расширение установлено для {success_count} из {len(self._selected_profiles)} профилей")
                else:
                    self.extensionOperationStatusChanged.emit(False, "Не удалось установить расширение ни для одного профиля")
                    
                # Очищаем выбранные профили
                # self._selected_profiles.clear()
                # self.selectedProfilesChanged.emit()
                
                # Обновляем список установленных расширений
                self.getInstalledExtensionsList()
                    
            except Exception as e:
                logger.error(f"Ошибка при установке расширения: {e}")
                self.extensionOperationStatusChanged.emit(False, f"Ошибка при установке расширения: {e}")
        
        # Запускаем задачу в отдельном потоке
        executor = ThreadPoolExecutor(max_workers=1)
        executor.submit(install_task)

    @Property('QVariantList', notify=profilesListChanged)
    def chromeScriptsList(self):
        """
        Возвращает список доступных Chrome скриптов
        
        Returns:
            list: Список названий скриптов
        """
        try:
            scripts_path = os.path.join(PROJECT_PATH, "data", "scripts", "chrome")
            scripts = []
            
            if os.path.exists(scripts_path):
                for script_dir in os.listdir(scripts_path):
                    script_path = os.path.join(scripts_path, script_dir)
                    if os.path.isdir(script_path):
                        config_path = os.path.join(script_path, "config.json")
                        if os.path.exists(config_path):
                            try:
                                with open(config_path, 'r', encoding='utf-8') as f:
                                    config = json.load(f)
                                    human_name = config.get("human_name", script_dir)
                                    scripts.append(human_name)
                            except Exception as e:
                                logger.error(f"Ошибка при чтении конфигурации скрипта {script_dir}: {e}")
            
            return scripts
        except Exception as e:
            logger.error(f"Ошибка при получении списка Chrome скриптов: {e}")
            return []
    
    @Slot('QVariantList', bool)
    def runChromeScripts(self, script_names, headless=False):
        """
        Запускает выбранные Chrome скрипты для выбранных профилей
        
        Args:
            script_names: Список названий скриптов
            headless: Флаг запуска в headless режиме
        """
        logger.debug(f"runChromeScripts вызван с параметрами: script_names={script_names}, headless={headless}")
        logger.debug(f"Текущие выбранные профили: {self._selected_profiles}")
        
        # Запускаем операцию в отдельном потоке, чтобы не блокировать интерфейс
        def run_task():
            try:
                logger.debug(f"run_task начал выполнение")
                logger.debug(f"Выбранные профили в run_task: {self._selected_profiles}")
                
                if not self._selected_profiles:
                    logger.error(f"Не выбрано ни одного профиля")
                    self.scriptOperationStatusChanged.emit(False, "Не выбрано ни одного профиля")
                    return
                    
                if not script_names:
                    logger.error(f"Не выбрано ни одного скрипта")
                    self.scriptOperationStatusChanged.emit(False, "Не выбрано ни одного скрипта")
                    return
                    
                # Создаем копию выбранных профилей, чтобы избежать ошибки "Set changed size during iteration"
                selected_profiles = list(self._selected_profiles)
                
                logger.info(f"Запуск Chrome скриптов {script_names} для профилей: {selected_profiles}, headless={headless}")
                
                # Получаем соответствие между человекочитаемыми названиями и директориями скриптов
                scripts_path = os.path.join(PROJECT_PATH, "data", "scripts", "chrome")
                script_dirs = {}
                
                if os.path.exists(scripts_path):
                    for script_dir in os.listdir(scripts_path):
                        script_path = os.path.join(scripts_path, script_dir)
                        if os.path.isdir(script_path):
                            config_path = os.path.join(script_path, "config.json")
                            if os.path.exists(config_path):
                                try:
                                    with open(config_path, 'r', encoding='utf-8') as f:
                                        config = json.load(f)
                                        human_name = config.get("human_name", script_dir)
                                        script_dirs[human_name] = script_dir
                                except Exception as e:
                                    logger.error(f"Ошибка при чтении конфигурации скрипта {script_dir}: {e}")
                
                # Получаем директории выбранных скриптов
                selected_script_dirs = []
                for script_name in script_names:
                    if script_name in script_dirs:
                        selected_script_dirs.append(script_dirs[script_name])
                    else:
                        logger.warning(f"Скрипт {script_name} не найден")
                
                if not selected_script_dirs:
                    self.scriptOperationStatusChanged.emit(False, "Не удалось найти выбранные скрипты")
                    return
                
                # Запускаем скрипты для каждого профиля
                success_count = 0
                total_operations = len(selected_profiles)
                
                for profile in selected_profiles:
                    try:
                        # Если профиль содержит префикс "Profile ", удаляем его перед запуском
                        if isinstance(profile, str) and profile.startswith("Profile "):
                            profile_name = profile.replace("Profile ", "")
                        else:
                            profile_name = profile
                            
                        self.chrome.run_scripts(profile_name, selected_script_dirs, headless)
                        success_count += 1
                    except Exception as e:
                        logger.error(f"Ошибка при запуске скриптов для профиля {profile}: {e}")
                
                if success_count == total_operations:
                    self.scriptOperationStatusChanged.emit(True, f"Скрипты успешно выполнены для всех профилей ({len(selected_profiles)})")
                else:
                    self.scriptOperationStatusChanged.emit(True, f"Скрипты выполнены для {success_count} из {total_operations} профилей")
                
            except Exception as e:
                logger.error(f"Ошибка при запуске Chrome скриптов: {e}")
                self.scriptOperationStatusChanged.emit(False, f"Ошибка при запуске Chrome скриптов: {e}")
        
        # Запускаем задачу в отдельном потоке
        threading.Thread(target=run_task).start()
    
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
            
            # Обрабатываем имена профилей, удаляя префикс "Profile " если он есть
            processed_profiles = []
            for profile in profiles:
                if isinstance(profile, str) and profile.startswith("Profile "):
                    processed_profiles.append(profile.replace("Profile ", ""))
                else:
                    processed_profiles.append(profile)
            
            # Запускаем скрипты
            logger.info("Вызываем функцию run_manager_scripts_on_multiple_profiles")
            success = run_manager_scripts_on_multiple_profiles(
                profiles=processed_profiles,
                scripts=scripts,
                shuffle_scripts=shuffle_scripts,
                gui_mode=True
            )
            logger.info(f"Функция run_manager_scripts_on_multiple_profiles выполнена с результатом: {success}")
            
            # Отправляем сигнал о завершении операции
            if success:
                logger.info(f"Отправляем сигнал об успешном выполнении скриптов для {len(processed_profiles)} профилей")
                self.managerScriptOperationStatusChanged.emit(True, f"Скрипты успешно выполнены для всех профилей ({len(processed_profiles)})")
            else:
                logger.info("Отправляем сигнал об ошибке при выполнении скриптов")
                self.managerScriptOperationStatusChanged.emit(False, "Произошла ошибка при выполнении скриптов")
                
        except Exception as e:
            logger.error(f"Ошибка при выполнении менеджер-скриптов: {e}")
            logger.info("Отправляем сигнал об ошибке при выполнении скриптов")
            self.managerScriptOperationStatusChanged.emit(False, f"Ошибка при выполнении скриптов: {e}")
    
    @Slot()
    def update_manager_scripts_list(self):
        """Обновляет список доступных менеджер-скриптов"""
        try:
            # Получаем список скриптов из директории src/manager/scripts
            scripts_dir = os.path.join(os.path.dirname(__file__), 'src', 'manager', 'scripts')
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
            logger.info(f"Обновлен список менеджер-скриптов: {self._manager_scripts_list}")
            
        except Exception as e:
            logger.error(f"Ошибка при обновлении списка менеджер-скриптов: {e}")
    
    @Property(list, notify=managerScriptsListChanged)
    def managerScriptsList(self):
        """Возвращает список доступных менеджер-скриптов"""
        return self._manager_scripts_list

    @Slot(str, result=bool)
    def exportProfilesToCSV(self, file_path):
        """
        Экспортирует список профилей с комментариями в CSV-файл
        
        Args:
            file_path: Путь к файлу для сохранения (если пустой, создается файл в директории data)
            
        Returns:
            bool: True, если экспорт успешен, иначе False
        """
        try:
            # Если путь не указан, создаем файл в директории data с текущей датой и временем
            if not file_path:
                # Создаем директорию data, если она не существует
                os.makedirs("data", exist_ok=True)
                # Генерируем имя файла с текущей датой и временем
                current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                file_path = f"data/profiles_export_{current_time}.csv"
            
            # Получаем список профилей и их комментарии
            profiles_data = []
            for profile in self._profiles_list:
                comment = self.getProfileComment(profile)
                profiles_data.append({"profile": profile, "comment": comment})
            
            # Записываем данные в CSV-файл
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['profile', 'comment']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for data in profiles_data:
                    writer.writerow(data)
            
            logger.info(f"Профили успешно экспортированы в {file_path}")
            return True
        except Exception as e:
            logger.error(f"Ошибка при экспорте профилей: {e}")
            return False
    
    @Slot()
    def updateProfileLists(self):
        """
        Обновляет список профильных списков
        """
        try:
            # Создаем директорию data, если она не существует
            os.makedirs("data", exist_ok=True)
            
            # Путь к файлу со списками профилей
            profile_lists_file = "data/profile_lists.json"
            
            # Если файл не существует, создаем его с пустой структурой
            if not os.path.exists(profile_lists_file):
                with open(profile_lists_file, 'w', encoding='utf-8') as f:
                    json.dump({"lists": {}}, f, ensure_ascii=False, indent=4)
            
            # Загружаем списки профилей из файла
            with open(profile_lists_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Преобразуем словарь списков в список для QML
            self._profile_lists = []
            for list_id, list_data in data.get("lists", {}).items():
                self._profile_lists.append({
                    "id": list_id,
                    "name": list_data.get("name", ""),
                    "profiles": list_data.get("profiles", [])
                })
            
            # Сортируем списки по имени
            self._profile_lists.sort(key=lambda x: x["name"].lower())
            
            # Уведомляем об изменении списка
            self.profileListsChanged.emit()
            logger.debug(f"Загружено {len(self._profile_lists)} списков профилей")
        except Exception as e:
            logger.error(f"Ошибка при обновлении списков профилей: {e}")
    
    @Property('QVariantList', notify=profileListsChanged)
    def profileLists(self):
        """
        Возвращает список профильных списков
        
        Returns:
            list: Список профильных списков
        """
        return self._profile_lists
    
    @Slot(str)
    def createProfileList(self, list_name):
        """
        Создает новый список профилей
        
        Args:
            list_name: Название списка
        """
        try:
            # Создаем директорию data, если она не существует
            os.makedirs("data", exist_ok=True)
            
            # Путь к файлу со списками профилей
            profile_lists_file = "data/profile_lists.json"
            
            # Если файл не существует, создаем его с пустой структурой
            if not os.path.exists(profile_lists_file):
                with open(profile_lists_file, 'w', encoding='utf-8') as f:
                    json.dump({"lists": {}}, f, ensure_ascii=False, indent=4)
            
            # Загружаем списки профилей из файла
            with open(profile_lists_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Генерируем уникальный ID для нового списка
            list_id = str(uuid.uuid4())
            
            # Добавляем новый список
            data["lists"][list_id] = {
                "name": list_name,
                "profiles": []
            }
            
            # Сохраняем изменения
            with open(profile_lists_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            
            # Обновляем список профильных списков
            self.updateProfileLists()
            
            # Уведомляем об успешном создании списка
            self.profileListOperationStatusChanged.emit(True, f"Список '{list_name}' успешно создан")
            logger.info(f"Создан новый список профилей: {list_name}")
        except Exception as e:
            self.profileListOperationStatusChanged.emit(False, f"Ошибка при создании списка: {e}")
            logger.error(f"Ошибка при создании списка профилей: {e}")
    
    @Slot(str)
    def deleteProfileList(self, list_id):
        """
        Удаляет список профилей
        
        Args:
            list_id: ID списка
        """
        try:
            # Путь к файлу со списками профилей
            profile_lists_file = "data/profile_lists.json"
            
            # Загружаем списки профилей из файла
            with open(profile_lists_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Получаем имя списка перед удалением
            list_name = data["lists"].get(list_id, {}).get("name", "")
            
            # Удаляем список
            if list_id in data["lists"]:
                del data["lists"][list_id]
            
            # Сохраняем изменения
            with open(profile_lists_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            
            # Обновляем список профильных списков
            self.updateProfileLists()
            
            # Уведомляем об успешном удалении списка
            self.profileListOperationStatusChanged.emit(True, f"Список '{list_name}' успешно удален")
            logger.info(f"Удален список профилей: {list_name}")
        except Exception as e:
            self.profileListOperationStatusChanged.emit(False, f"Ошибка при удалении списка: {e}")
            logger.error(f"Ошибка при удалении списка профилей: {e}")
    
    @Slot(str, str)
    def renameProfileList(self, list_id, new_name):
        """
        Переименовывает список профилей
        
        Args:
            list_id: ID списка
            new_name: Новое название списка
        """
        try:
            # Путь к файлу со списками профилей
            profile_lists_file = "data/profile_lists.json"
            
            # Загружаем списки профилей из файла
            with open(profile_lists_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Получаем старое имя списка
            old_name = data["lists"].get(list_id, {}).get("name", "")
            
            # Переименовываем список
            if list_id in data["lists"]:
                data["lists"][list_id]["name"] = new_name
            
            # Сохраняем изменения
            with open(profile_lists_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            
            # Обновляем список профильных списков
            self.updateProfileLists()
            
            # Уведомляем об успешном переименовании списка
            self.profileListOperationStatusChanged.emit(True, f"Список '{old_name}' переименован в '{new_name}'")
            logger.info(f"Список профилей '{old_name}' переименован в '{new_name}'")
        except Exception as e:
            self.profileListOperationStatusChanged.emit(False, f"Ошибка при переименовании списка: {e}")
            logger.error(f"Ошибка при переименовании списка профилей: {e}")
    
    @Slot(str)
    def searchProfilesByName(self, search_text):
        """
        Фильтрует список профилей по имени
        
        Args:
            search_text: Текст для поиска
        """
        try:
            from src.utils.helpers import get_profile_comments
            comments = get_profile_comments()
            
            if not search_text:
                # Если поисковый запрос пустой, показываем все профили
                filtered_profiles = []
                for profile in self._profiles_list:
                    # Получаем имя профиля без префикса для отображения
                    display_name = profile.replace('Profile ', '')
                    filtered_profiles.append({
                        "name": display_name,
                        "comment": comments.get(display_name, "")
                    })
            else:
                search_text = search_text.lower()
                filtered_profiles = []
                for profile in self._profiles_list:
                    # Получаем имя профиля без префикса для отображения
                    display_name = profile.replace('Profile ', '')
                    if search_text in display_name.lower():
                        filtered_profiles.append({
                            "name": display_name,
                            "comment": comments.get(display_name, "")
                        })
            
            self._filtered_profiles = filtered_profiles
            self.filteredProfilesListChanged.emit()
            logger.debug(f"Отфильтровано {len(filtered_profiles)} профилей по запросу '{search_text}'")
            logger.debug(f"Первый профиль в списке: {filtered_profiles[0] if filtered_profiles else 'нет профилей'}")
        except Exception as e:
            logger.error(f"Ошибка при фильтрации профилей: {e}")
    
    @Slot(str)
    def getProfilesInList(self, list_id):
        """
        Получает профили из указанного списка и устанавливает их как выбранные
        
        Args:
            list_id: ID списка
        """
        try:
            # Сохраняем ID текущего списка
            self._current_list_id = list_id
            
            # Загружаем списки профилей
            with open('data/profile_lists.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Получаем выбранный список профилей
            if 'lists' in data and list_id in data['lists']:
                selected_list = data['lists'][list_id]
                list_name = selected_list['name']
                profiles_in_list = selected_list['profiles']
                
                # Устанавливаем выбранные профили (преобразуем список в множество)
                self._selected_profiles = set(profiles_in_list)
                logger.debug(f"Загружен список профилей '{list_name}' с {len(self._selected_profiles)} профилями")
                
                # Получаем комментарии для профилей
                from src.utils.helpers import get_profile_comments
                comments = get_profile_comments()
                
                # Фильтруем профили, чтобы показать только те, которые есть в списке
                filtered_profiles = []
                
                # Показываем только профили из списка
                for profile in self._profiles_list:
                    # Получаем имя профиля без префикса для отображения
                    display_name = profile.replace('Profile ', '')
                    if display_name in profiles_in_list:
                        filtered_profiles.append({
                            "name": display_name,
                            "comment": comments.get(display_name, "")
                        })
                
                self._filtered_profiles = filtered_profiles
                self.filteredProfilesListChanged.emit()
                
                # Уведомляем об изменении выбранных профилей
                self.selectedProfilesChanged.emit()
                
                logger.debug(f"Всего профилей для отображения: {len(self._filtered_profiles)}")
                if self._filtered_profiles:
                    logger.debug(f"Первый профиль: {self._filtered_profiles[0]}")
                
                return True
            else:
                logger.warning(f"Список профилей с ID {list_id} не найден")
                return False
        except Exception as e:
            logger.error(f"Ошибка при получении профилей из списка: {e}")
            return False
    
    @Slot(str)
    def addProfilesToList(self, list_id):
        """
        Добавляет выбранные профили в указанный список
        
        Args:
            list_id: ID списка
        """
        try:
            # Путь к файлу со списками профилей
            profile_lists_file = "data/profile_lists.json"
            
            # Загружаем списки профилей из файла
            with open(profile_lists_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Получаем имя списка
            list_name = data["lists"].get(list_id, {}).get("name", "")
            
            # Получаем текущие профили в списке
            current_profiles = set(data["lists"].get(list_id, {}).get("profiles", []))
            
            # Добавляем выбранные профили
            profiles_to_add = self._selected_profiles - current_profiles
            current_profiles.update(profiles_to_add)
            
            # Обновляем список профилей
            if list_id in data["lists"]:
                data["lists"][list_id]["profiles"] = list(current_profiles)
            
            # Сохраняем изменения
            with open(profile_lists_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            
            # Обновляем список профильных списков
            self.updateProfileLists()
            
            # Обновляем отображение профилей в текущем списке
            self.getProfilesInList(list_id)
            
            # Отправляем уведомление об успешном добавлении
            self.profileListOperationStatusChanged.emit(True, f"Профили успешно добавлены в список '{list_name}'")
            logger.debug(f"Профили {profiles_to_add} добавлены в список {list_id}")
        except Exception as e:
            self.profileListOperationStatusChanged.emit(False, f"Ошибка при добавлении профилей: {e}")
            logger.error(f"Ошибка при добавлении профилей в список: {e}")
    
    @Slot(str)
    def removeProfilesFromList(self, list_id):
        """
        Удаляет выбранные профили из указанного списка
        
        Args:
            list_id: ID списка
        """
        try:
            # Путь к файлу со списками профилей
            profile_lists_file = "data/profile_lists.json"
            
            # Загружаем списки профилей из файла
            with open(profile_lists_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Получаем имя списка
            list_name = data["lists"].get(list_id, {}).get("name", "")
            
            # Получаем текущие профили в списке
            current_profiles = set(data["lists"].get(list_id, {}).get("profiles", []))
            
            # Удаляем выбранные профили
            profiles_to_remove = self._selected_profiles.intersection(current_profiles)
            current_profiles -= profiles_to_remove
            
            # Обновляем список профилей
            if list_id in data["lists"]:
                data["lists"][list_id]["profiles"] = list(current_profiles)
            
            # Сохраняем изменения
            with open(profile_lists_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            
            # Обновляем список профильных списков
            self.updateProfileLists()
            
            # Обновляем отображение профилей в текущем списке
            self.getProfilesInList(list_id)
            
            # Отправляем уведомление об успешном удалении
            self.profileListOperationStatusChanged.emit(True, f"Профили успешно удалены из списка '{list_name}'")
            logger.debug(f"Профили {profiles_to_remove} удалены из списка {list_id}")
        except Exception as e:
            self.profileListOperationStatusChanged.emit(False, f"Ошибка при удалении профилей: {e}")
            logger.error(f"Ошибка при удалении профилей из списка: {e}")

    @Slot()
    def syncProfileLists(self):
        """
        Синхронизирует списки профилей с физически существующими профилями.
        Удаляет из списков профили, которые не существуют физически.
        """
        try:
            # Получаем актуальный список профилей (без префикса "Profile ")
            actual_profiles = set(profile.replace('Profile ', '') for profile in get_profiles_list())
            logger.debug(f"Актуальные профили: {actual_profiles}")
            
            # Загружаем списки профилей из файла
            profile_lists_file = "data/profile_lists.json"
            if not os.path.exists(profile_lists_file):
                self.profileListOperationStatusChanged.emit(True, "Списки профилей синхронизированы")
                return
                
            with open(profile_lists_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            changes_made = False
            removed_count = 0
            
            # Проверяем каждый список
            for list_id, list_data in data.get("lists", {}).items():
                list_name = list_data.get("name", "")
                profiles = list_data.get("profiles", [])
                
                # Находим профили, которые не существуют физически
                invalid_profiles = [p for p in profiles if p not in actual_profiles]
                
                if invalid_profiles:
                    # Удаляем несуществующие профили из списка
                    data["lists"][list_id]["profiles"] = [p for p in profiles if p in actual_profiles]
                    changes_made = True
                    removed_count += len(invalid_profiles)
                    logger.debug(f"Из списка '{list_name}' удалены несуществующие профили: {invalid_profiles}")
            
            # Сохраняем изменения, если были удалены профили
            if changes_made:
                with open(profile_lists_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
                
                # Обновляем списки в интерфейсе
                self.updateProfileLists()
                
                # Если был выбран список, обновляем его отображение
                if hasattr(self, '_current_list_id') and self._current_list_id:
                    self.getProfilesInList(self._current_list_id)
                
                self.profileListOperationStatusChanged.emit(True, f"Синхронизация завершена. Удалено {removed_count} несуществующих профилей из списков.")
            else:
                self.profileListOperationStatusChanged.emit(True, "Все списки профилей актуальны")
                
        except Exception as e:
            logger.error(f"Ошибка при синхронизации списков профилей: {e}")
            self.profileListOperationStatusChanged.emit(False, f"Ошибка при синхронизации: {e}")

    @Slot()
    def resetCurrentList(self):
        """
        Сбрасывает текущий выбранный список профилей
        """
        self._current_list_id = ""

    @Slot()
    def deleteSelectedProfiles(self):
        """
        Полностью удаляет выбранные профили с диска
        """
        try:
            if not self._selected_profiles:
                self.profileListOperationStatusChanged.emit(False, "Не выбрано ни одного профиля для удаления")
                return
            
            from src.utils.helpers import delete_profile
            
            success_count = 0
            total_count = len(self._selected_profiles)
            deleted_profiles = []
            
            # Удаляем каждый выбранный профиль
            for profile in list(self._selected_profiles):
                if delete_profile(profile):
                    success_count += 1
                    deleted_profiles.append(profile)
                    # Удаляем профиль из списка выбранных
                    self._selected_profiles.remove(profile)
            
            # Обновляем список профилей
            self.update_profiles_list()
            
            # Синхронизируем списки профилей
            self.syncProfileLists()
            
            # Отправляем уведомление о результате
            if success_count > 0:
                self.profileListOperationStatusChanged.emit(
                    True, 
                    f"Успешно удалено {success_count} из {total_count} профилей"
                )
                logger.info(f"Удалены профили: {deleted_profiles}")
            else:
                self.profileListOperationStatusChanged.emit(
                    False, 
                    "Не удалось удалить ни одного профиля"
                )
                
        except Exception as e:
            logger.error(f"Ошибка при удалении профилей: {e}")
            self.profileListOperationStatusChanged.emit(False, f"Ошибка при удалении профилей: {e}")

    @Slot(str)
    def launchProfilesFromList(self, list_id):
        """
        Запускает все профили из указанного списка
        
        Args:
            list_id: ID списка профилей
        """
        try:
            # Загружаем списки профилей
            with open('data/profile_lists.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Получаем выбранный список профилей
            if 'lists' in data and list_id in data['lists']:
                selected_list = data['lists'][list_id]
                list_name = selected_list['name']
                profiles_in_list = selected_list['profiles']
                
                if not profiles_in_list:
                    self.profileListOperationStatusChanged.emit(False, f"Список '{list_name}' не содержит профилей")
                    return
                
                # Запускаем все профили из списка
                logger.info(f"Запуск всех профилей из списка '{list_name}'")
                self.launchProfilesByNames(profiles_in_list)
                
                self.profileListOperationStatusChanged.emit(True, f"Запущены все профили из списка '{list_name}'")
            else:
                self.profileListOperationStatusChanged.emit(False, f"Список с ID {list_id} не найден")
        except Exception as e:
            logger.error(f"Ошибка при запуске профилей из списка: {e}")
            self.profileListOperationStatusChanged.emit(False, f"Ошибка при запуске профилей: {e}")

    @Slot(str)
    def searchProfileLists(self, search_text):
        """
        Выполняет поиск по названиям списков профилей
        
        Args:
            search_text: Текст для поиска
        """
        try:
            # Загружаем списки профилей из файла
            profile_lists_file = "data/profile_lists.json"
            
            if not os.path.exists(profile_lists_file):
                self._profile_lists = []
                self.profileListsChanged.emit()
                return
                
            with open(profile_lists_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Если поисковый запрос пустой, показываем все списки
            if not search_text:
                self.updateProfileLists()
                return
            
            # Преобразуем поисковый запрос в нижний регистр для регистронезависимого поиска
            search_text = search_text.lower()
            
            # Фильтруем списки по названию
            filtered_lists = []
            for list_id, list_data in data.get("lists", {}).items():
                list_name = list_data.get("name", "").lower()
                if search_text in list_name:
                    filtered_lists.append({
                        "id": list_id,
                        "name": list_data.get("name", ""),
                        "profiles": list_data.get("profiles", [])
                    })
            
            # Сортируем списки по имени
            filtered_lists.sort(key=lambda x: x["name"].lower())
            
            # Обновляем список
            self._profile_lists = filtered_lists
            
            # Уведомляем об изменении списка
            self.profileListsChanged.emit()
            logger.debug(f"Найдено {len(filtered_lists)} списков профилей по запросу '{search_text}'")
        except Exception as e:
            logger.error(f"Ошибка при поиске списков профилей: {e}")

def setup_logger():
    logger.remove()
    logger_level = "DEBUG" if general_config['show_debug_logs'] else "INFO"
    log_format = "<white>{time:HH:mm:ss}</white> | <level>{level: <8}</level> | <white>{message}</white>"
    logger.add(sys.stderr, level=logger_level, format=log_format)
    logger.add("data/debug_log.log", level="DEBUG", format=log_format)

def main():
    app = QGuiApplication(sys.argv)
    
    # Настраиваем логгер
    setup_logger()
    
    # Создаем экземпляр ProfileManager
    profile_manager = ProfileManager()
    
    # Создаем QML движок
    engine = QQmlApplicationEngine()
    
    # Устанавливаем engine в ProfileManager
    profile_manager.engine = engine
    
    # Регистрируем ProfileManager в QML
    engine.rootContext().setContextProperty("profileManager", profile_manager)
    
    # Добавляем обработку сигналов завершения
    def signal_handler(sig, frame):
        logger.info("Получен сигнал завершения. Закрываем приложение...")
        app.quit()
        sys.exit(0)
    
    # Регистрируем обработчик для сигнала SIGINT (Ctrl+C)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Загружаем основной QML файл
    engine.load("src/client/gui/qml/main.qml")
    
    if not engine.rootObjects():
        return -1
        
    return app.exec()

if __name__ == "__main__":
    main() 