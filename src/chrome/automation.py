"""
Модуль для асинхронной автоматизации Chrome через Playwright
"""
import os
import asyncio
import subprocess
from loguru import logger
from playwright.async_api import async_playwright, Page, BrowserContext
import socket
import time
import json
import shutil
from sys import platform
from typing import List, Optional

from src.utils.constants import (
    CHROME_DATA_PATH,
    CHROME_PATH,
    DEFAULT_EXTENSIONS_PATH
)

class AsyncPlaywrightAutomation:
    """Класс для асинхронной автоматизации действий в Chrome через Playwright"""
    
    def __init__(self):
        """Инициализация"""
        self.playwright = None
        self.browser = None
        self.context = None
        self.chrome_process = None
        
    def _find_free_port(self) -> int:
        """Находит свободный порт"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            s.listen(1)
            port = s.getsockname()[1]
        return port
        
    def _get_profile_extensions(self, profile_path: str) -> list[str]:
        """
        Получает список расширений профиля
        
        Args:
            profile_path: Путь к профилю
            
        Returns:
            list[str]: Список путей к расширениям
        """
        extensions = []
        extensions_path = os.path.join(profile_path, "Extensions")
        
        if os.path.exists(extensions_path):
            for ext_id in os.listdir(extensions_path):
                ext_path = os.path.join(extensions_path, ext_id)
                if os.path.isdir(ext_path):
                    # Берем последнюю версию расширения
                    versions = sorted(os.listdir(ext_path))
                    if versions:
                        latest_version = versions[-1]
                        full_path = os.path.join(ext_path, latest_version)
                        logger.info(f"✓ Найдено расширение: {ext_id} (версия {latest_version})")
                        extensions.append(full_path)
                        
        return extensions
        
    async def launch_profile(self, profile_name: str) -> bool:
        """
        Запускает профиль Chrome
        
        Args:
            profile_name: Имя профиля
            
        Returns:
            bool: True если запуск успешен
        """
        try:
            # Формируем пути
            profile_path = os.path.join(CHROME_DATA_PATH, f"{profile_name}")
            
            # Проверяем существование профиля
            if not os.path.exists(profile_path):
                logger.error(f"❌ Профиль {profile_name} не найден")
                return False
                
            # Получаем список расширений профиля
            extensions = self._get_profile_extensions(profile_path)
            
            # Находим свободный порт для отладки
            debug_port = self._find_free_port()
            
            # Для macOS создаем отдельную директорию для каждого профиля
            if platform == "darwin":
                # Создаем отдельный путь для профиля
                standalone_profile_path = os.path.join(os.path.dirname(CHROME_DATA_PATH), f"standalone_{profile_name}")
                os.makedirs(standalone_profile_path, exist_ok=True)
                
                # Если директория пустая, копируем содержимое из основного профиля
                if not os.listdir(standalone_profile_path) and os.path.exists(profile_path):
                    try:
                        # Копируем содержимое профиля в отдельную директорию
                        for item in os.listdir(profile_path):
                            source = os.path.join(profile_path, item)
                            dest = os.path.join(standalone_profile_path, item)
                            if os.path.isdir(source):
                                try:
                                    shutil.copytree(source, dest, dirs_exist_ok=True)
                                except Exception as copy_err:
                                    logger.debug(f"Не удалось скопировать директорию {source}: {copy_err}")
                            else:
                                try:
                                    shutil.copy2(source, dest)
                                except Exception as copy_err:
                                    logger.debug(f"Не удалось скопировать файл {source}: {copy_err}")
                        logger.info(f'✅ Создан автономный профиль для {profile_name}')
                    except Exception as e:
                        logger.error(f'⛔ Ошибка при создании автономного профиля: {e}')
                
                # Используем новый путь как отдельную директорию данных пользователя
                user_data_dir = standalone_profile_path
                # Для macOS не используем флаг profile-directory
                profile_dir_flag = ""
                
                # Добавляем уникальный app-id для macOS
                unique_app_id = f"com.google.Chrome.profile{profile_name.replace(' ', '')}"
            else:
                # Для остальных ОС используем обычную схему
                user_data_dir = CHROME_DATA_PATH
                # Для других ОС используем флаг profile-directory
                profile_dir_flag = f"--profile-directory=Profile {profile_name}"
            
            # Формируем список аргументов запуска
            launch_args = [
                f"--user-data-dir={user_data_dir}",
            ]
            
            # Добавляем флаг profile-directory для не-macOS
            if profile_dir_flag:
                launch_args.append(profile_dir_flag)
            
            # Добавляем уникальный app-id для macOS
            if platform == "darwin" and "unique_app_id" in locals():
                launch_args.append(f"--app-id={unique_app_id}")
            
            # Добавляем общие флаги
            launch_args.extend([
                f"--remote-debugging-port={debug_port}",
                "--no-first-run",
                "--no-default-browser-check",
                "--enable-extensions",
                "--make-default-browser=false",
                "--start-maximized",
                "--enable-automation",
                "--no-sandbox"
            ])
            
            # Добавляем пути к расширениям
            for ext_path in extensions:
                launch_args.append(f"--load-extension={ext_path}")
            
            # Запускаем Chrome
            logger.info(f"🚀 Запускаю Chrome для профиля {profile_name}...")
            
            # Запускаем Chrome напрямую
            self.chrome_process = subprocess.Popen(
                [CHROME_PATH, *launch_args],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Ждем пока порт станет доступен
            logger.info("⏳ Жду подключения к порту отладки...")
            max_attempts = 10
            attempt = 0
            
            while attempt < max_attempts:
                try:
                    # Пробуем подключиться к Chrome DevTools
                    self.playwright = await async_playwright().start()
                    self.browser = await self.playwright.chromium.connect_over_cdp(
                        f"http://localhost:{debug_port}"
                    )
                    
                    # Если подключились успешно, получаем контекст
                    contexts = self.browser.contexts
                    if contexts:
                        self.context = contexts[0]
                        logger.success(f"✅ Профиль {profile_name} успешно запущен")
                        return True
                    
                    # Если контекст не получен, закрываем соединение и пробуем снова
                    await self.browser.close()
                    await self.playwright.stop()
                    
                except Exception:
                    attempt += 1
                    await asyncio.sleep(1)
                    continue
                    
            raise Exception("Не удалось подключиться к Chrome DevTools")
            
        except Exception as e:
            logger.error(f"❌ Ошибка при запуске профиля {profile_name}: {str(e)}")
            await self.close()
            return False
            
    async def run_script(self, script_function) -> bool:
        """
        Запуск асинхронного скрипта Playwright
        
        Args:
            script_function: Асинхронная функция скрипта для выполнения
            
        Returns:
            bool: True если скрипт успешно выполнен
        """
        try:
            if not self.context:
                raise Exception("Браузер не запущен")
                
            # Запускаем скрипт
            return await script_function(self.context)
            
        except Exception as e:
            logger.error(f"❌ Ошибка при выполнении скрипта: {str(e)}")
            return False
            
    async def close(self):
        """Закрытие браузера"""
        try:
            if self.chrome_process:
                self.chrome_process.terminate()
                await asyncio.sleep(1)
                try:
                    self.chrome_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.chrome_process.kill()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
        except Exception as e:
            logger.error(f"❌ Ошибка при закрытии браузера: {str(e)}")

async def run_multiple_profiles(profile_names: list[str], script_function) -> list[bool]:
    """
    Запускает скрипт последовательно в нескольких профилях
    
    Args:
        profile_names: Список имен профилей
        script_function: Асинхронная функция скрипта для выполнения
        
    Returns:
        list[bool]: Список результатов выполнения для каждого профиля
    """
    try:
        results = []
        for profile_name in profile_names:
            automation = AsyncPlaywrightAutomation()
            try:
                if await automation.launch_profile(profile_name):
                    logger.info(f"🚀 Запускаю скрипт для профиля {profile_name}")
                    result = await automation.run_script(script_function)
                    results.append(result)
                else:
                    results.append(False)
                    
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"❌ Ошибка при выполнении скрипта для профиля {profile_name}: {str(e)}")
                results.append(False)
                
        return results
        
    except Exception as e:
        logger.error(f"❌ Ошибка при запуске профилей: {str(e)}")
        return [False] * len(profile_names) 