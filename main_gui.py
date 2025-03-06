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
    copy_extension_from_profile_to_default
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

class ProfileManager(QObject):
    profilesListChanged = Signal()
    selectedProfilesChanged = Signal()
    filteredProfilesListChanged = Signal()
    commentSaveStatusChanged = Signal(bool, str)  # Сигнал для уведомления о статусе сохранения (успех/неудача, сообщение)
    profileCreationStatusChanged = Signal(bool, str)  # Сигнал для уведомления о статусе создания профилей (успех/неудача, сообщение)
    extensionOperationStatusChanged = Signal(bool, str)  # Сигнал для уведомления о статусе операций с расширениями (успех/неудача, сообщение)
    extensionsListChanged = Signal('QVariantList')  # Сигнал для уведомления об изменении списка расширений

    def __init__(self):
        super().__init__()
        self.chrome = Chrome()
        self._profiles_list = []
        self._selected_profiles = set()
        self._filtered_profiles = []
        self.update_profiles_list()
        
    @Slot()
    def update_profiles_list(self):
        try:
            self._profiles_list = get_profiles_list()
            self.profilesListChanged.emit()
            # Очищаем выбранные профили при обновлении списка
            self._selected_profiles.clear()
            self.selectedProfilesChanged.emit()
        except Exception as e:
            logger.error(f"Error updating profiles list: {e}")
            
    @Property('QVariantList', notify=profilesListChanged)
    def profilesList(self):
        return self._profiles_list

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
        return profile_name in self._selected_profiles
        
    @Slot(str, bool)
    def toggleProfileSelection(self, profile_name, is_selected):
        try:
            if is_selected and profile_name not in self._selected_profiles:
                self._selected_profiles.add(profile_name)
                self.selectedProfilesChanged.emit()
                logger.debug(f"Profile {profile_name} selected")
            elif not is_selected and profile_name in self._selected_profiles:
                self._selected_profiles.discard(profile_name)
                self.selectedProfilesChanged.emit()
                logger.debug(f"Profile {profile_name} deselected")
        except Exception as e:
            logger.error(f"Error toggling profile {profile_name}: {e}")

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
        try:
            self._selected_profiles.clear()
            self.selectedProfilesChanged.emit()
            logger.debug("Deselected all profiles")
        except Exception as e:
            logger.error(f"Error deselecting all profiles: {e}")
        
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
                # Запускаем профиль
                self.chrome.launch_profile(profile)
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
                    # Используем те же параметры, что и в терминальном интерфейсе
                    self.chrome.launch_profile(
                        str(name),
                        debug=False,
                        headless=False,
                        maximized=False
                    )
                    logger.info(f"✅  {name} - профиль запущен")
                else:
                    logger.warning(f"❌  {name} - профиль не найден")
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
        run_chrome_scripts_on_multiple_profiles()
        
    @Slot()
    def run_manager_scripts(self):
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
                    # Используем тот же способ формирования путей, что и в терминальном интерфейсе
                    profile_extensions_path = CHROME_DATA_PATH / f"Profile {profile}" / "Extensions"
                    os.makedirs(profile_extensions_path, exist_ok=True)
                    
                    dest_path = str(profile_extensions_path / extension_id)
                    if copy_extension(extension_path, dest_path, profile, extension_id, True):
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
                    # Используем тот же способ формирования путей, что и в терминальном интерфейсе
                    profile_extensions_path = CHROME_DATA_PATH / f"Profile {profile}" / "Extensions"
                    os.makedirs(profile_extensions_path, exist_ok=True)
                    
                    dest_path = str(profile_extensions_path / extension_id)
                    if copy_extension(extension_path, dest_path, profile, extension_id, replace):
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
                    # Используем тот же способ формирования путей, что и в терминальном интерфейсе
                    profile_extensions_path = CHROME_DATA_PATH / f"Profile {profile}" / "Extensions"
                    os.makedirs(profile_extensions_path, exist_ok=True)
                    
                    dest_path = str(profile_extensions_path / extension_id)
                    if copy_extension(extension_path, dest_path, profile, extension_id, replace):
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
                    # Используем тот же способ формирования путей, что и в терминальном интерфейсе
                    profile_extensions_path = CHROME_DATA_PATH / f"Profile {profile}" / "Extensions"
                    os.makedirs(profile_extensions_path, exist_ok=True)
                    
                    dest_path = str(profile_extensions_path / extension_id)
                    if copy_extension(extension_path, dest_path, profile, extension_id, True):
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
                                
                                # Формируем путь к папке с расширениями профиля
                                profile_extensions_path = os.path.join(CHROME_DATA_PATH, f"Profile {profile}", "Extensions")
                                
                                # Создаем папку Extensions, если она не существует
                                if not os.path.exists(profile_extensions_path):
                                    os.makedirs(profile_extensions_path)
                                
                                # Формируем путь назначения
                                dest_path = os.path.join(profile_extensions_path, ext_id)
                                
                                # Копируем расширение
                                result = copy_extension(src_path, dest_path, profile, ext_id, replace)
                                
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
                                
                                # Формируем путь к папке с расширениями профиля
                                profile_extensions_path = os.path.join(CHROME_DATA_PATH, f"Profile {profile}", "Extensions")
                                
                                # Создаем папку Extensions, если она не существует
                                if not os.path.exists(profile_extensions_path):
                                    os.makedirs(profile_extensions_path)
                                
                                # Формируем путь назначения
                                dest_path = os.path.join(profile_extensions_path, ext_id)
                                
                                # Копируем расширение
                                result = copy_extension(src_path, dest_path, profile, ext_id, replace)
                                
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
            profile: Имя или номер профиля
        """
        try:
            logger.info(f"Получение списка расширений из профиля {profile}")
            
            # Формируем путь к папке с расширениями профиля
            profile_extensions_path = Path(CHROME_DATA_PATH) / f"Profile {profile}" / "Extensions"
            
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
            for ext_id, profiles_dict in extensions_info.items():
                # Получаем путь к расширению из первого профиля, где оно установлено
                first_profile = next(iter(profiles_dict))
                ext_path = profiles_dict[first_profile]
                
                # Получаем имя, версию и иконку расширения
                ext_name = get_extension_name(ext_path) if ext_path else "Без имени"
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
                    "name": ext_name if ext_name and ext_name != ext_id else f"Расширение {ext_id[:8]}...",
                    "version": ext_version,
                    "iconUrl": ext_icon_url,
                    "path": ext_path
                }
                
                extensions_list.append(extension_info)
                
            # Сортируем список расширений по имени
            extensions_list.sort(key=lambda x: x["name"])
                
            # Отправляем список расширений в QML
            self.extensionsListChanged.emit(extensions_list)
            self.extensionOperationStatusChanged.emit(True, f"Найдено {len(extensions_list)} расширений в профиле {profile}")
                
        except Exception as e:
            logger.error(f"Ошибка при получении списка расширений из профиля {profile}: {e}")
            self.extensionOperationStatusChanged.emit(False, f"Ошибка при получении списка расширений из профиля {profile}: {e}")
    
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

def setup_logger():
    logger.remove()
    logger_level = "DEBUG" if general_config['show_debug_logs'] else "INFO"
    log_format = "<white>{time:HH:mm:ss}</white> | <level>{level: <8}</level> | <white>{message}</white>"
    logger.add(sys.stderr, level=logger_level, format=log_format)
    logger.add("data/debug_log.log", level="DEBUG", format=log_format)

def main():
    setup_logger()
    
    app = QGuiApplication(sys.argv)
    engine = QQmlApplicationEngine()
    
    # Регистрируем объект для использования в QML
    profile_manager = ProfileManager()
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