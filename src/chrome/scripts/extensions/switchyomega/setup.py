"""
Модуль для настройки Proxy SwitchyOmega с использованием Playwright.
Позволяет автоматически активировать и настроить прокси для выбранного профиля.
"""

import os
import json
import time
from pathlib import Path
from loguru import logger
from typing import Optional, Dict, Any
from playwright.sync_api import Page, expect
from dotenv import load_dotenv

def get_proxy_config(profile_name: str) -> Dict[str, Any]:
    """
    Получает настройки прокси из .env файла
    
    Args:
        profile_name: Имя профиля для которого получаем настройки
        
    Returns:
        Dict[str, Any]: Конфигурация прокси
    """
    load_dotenv()
    
    # Получаем настройки из .env
    proxy_url_env = os.getenv(f'PROXY_URL_PROFILE_{profile_name}', '')
    username = os.getenv('PROXY_USERNAME', '')
    password = os.getenv('PROXY_PASSWORD', '')
    
    if not proxy_url_env:
        raise ValueError(f"Прокси для профиля {profile_name} не настроен в .env файле")
        
    # Разбираем адрес прокси
    try:
        # Убираем протокол из URL
        proxy = proxy_url_env.split('://')[-1]
        host, port = proxy.split(':')
        port = int(port)
    except:
        raise ValueError(f"Неверный формат прокси: {proxy_url_env}")
        
    return {
        "host": host,
        "port": port,
        "username": username,
        "password": password,
        "protocol": proxy_url_env.split('://')[0]  # Используем протокол из URL
    }

class SwitchyOmegaSetup:
    """Класс для настройки Proxy SwitchyOmega"""
    
    def __init__(self, page: Page):
        """
        Инициализация настройщика SwitchyOmega
        
        Args:
            page: Объект страницы Playwright
        """
        self.page = page
        self.extension_id = "padekgcemlokbadohgkifijomclgjgif"
        
    def restore_extension(self) -> bool:
        """
        Восстанавливает расширение если оно было отключено Chrome
        
        Returns:
            bool: True если восстановление успешно
        """
        try:
            # Открываем страницу расширений
            self.page.goto("chrome://extensions")
            self.page.wait_for_load_state("domcontentloaded")
            
            # Находим карточку SwitchyOmega
            card = self.page.locator(f"#extension-card-{self.extension_id}")
            if card.count() == 0:
                logger.error("❌ Не удалось найти карточку расширения SwitchyOmega")
                return False
            
            # Проверяем наличие кнопки Manage extension
            manage_button = card.get_by_role("button", name="Manage extension")
            if manage_button.count() > 0:
                manage_button.click()
                logger.info("✅ Открыты настройки SwitchyOmega")
                
                # Ждем загрузки страницы настроек
                self.page.wait_for_load_state("domcontentloaded")
                
                # Включаем расширение
                toggle = self.page.locator('input[type="checkbox"]').first
                if not toggle.is_checked():
                    toggle.click()
                    logger.info("✅ SwitchyOmega успешно включен")
                
                return True
                
            return True  # Если кнопки нет, значит расширение не отключено
            
        except Exception as e:
            logger.error("❌ Ошибка при восстановлении SwitchyOmega")
            logger.debug(f"Причина: {str(e)}")
            return False
        
    def activate_extension(self) -> bool:
        """
        Активирует расширение SwitchyOmega в Chrome
        
        Returns:
            bool: True если активация успешна
        """
        try:
            # Сначала пробуем восстановить расширение если оно отключено
            if not self.restore_extension():
                return False
            
            # Открываем страницу расширений
            self.page.goto("chrome://extensions")
            self.page.wait_for_load_state("domcontentloaded")
            
            # Находим карточку SwitchyOmega по ID
            card = self.page.locator(f"#extension-card-{self.extension_id}")
            if card.count() == 0:
                logger.error("❌ Не удалось найти карточку расширения SwitchyOmega")
                return False
            
            # Проверяем, включено ли расширение
            toggle = card.locator('input[type="checkbox"]')
            if toggle.count() == 0:
                logger.error("❌ Не удалось найти переключатель расширения")
                return False
                
            # Если расширение выключено, включаем его
            if not toggle.is_checked():
                toggle.click()
                logger.info("✅ SwitchyOmega успешно активирован")
            
            return True
            
        except Exception as e:
            logger.error("❌ Ошибка при активации SwitchyOmega")
            logger.debug(f"Причина: {str(e)}")
            return False
        
    def setup_proxy(self, proxy_config: Dict[str, Any]) -> bool:
        """
        Настраивает прокси в SwitchyOmega
        
        Args:
            proxy_config: Конфигурация прокси
                {
                    "host": str,
                    "port": int,
                    "username": str,
                    "password": str,
                    "protocol": str
                }
                
        Returns:
            bool: True если настройка успешна
        """
        try:
            # Активируем расширение если нужно
            if not self.activate_extension():
                return False
            
            # Открываем страницу настроек расширения
            self.page.goto(f"chrome-extension://{self.extension_id}/options.html")
            
            # Ждем загрузки страницы
            self.page.wait_for_selector("#ui-content")
            
            # Создаем новый профиль прокси
            self._create_proxy_profile(proxy_config)
            
            # Применяем настройки
            self.page.click("#apply-options")
            
            # Ждем сообщения об успехе
            self.page.wait_for_selector(".alert-success")
            
            # Включаем прокси
            self.page.goto(f"chrome-extension://{self.extension_id}/popup.html")
            self.page.wait_for_selector(".switch-rule")
            
            # Выбираем профиль прокси
            self.page.click(".switch-rule")
            self.page.click("text=Default Proxy")
            
            logger.info("✅ Прокси успешно настроен и включен в SwitchyOmega")
            return True
            
        except Exception as e:
            logger.error("❌ Ошибка при настройке прокси в SwitchyOmega")
            logger.debug(f"Причина: {str(e)}")
            return False
            
    def _create_proxy_profile(self, proxy_config: Dict[str, Any]):
        """
        Создает новый профиль прокси
        
        Args:
            proxy_config: Конфигурация прокси
        """
        # Нажимаем кнопку New Profile
        self.page.click(".btn-new-profile")
        
        # Выбираем тип профиля Proxy Profile
        self.page.click("text=Proxy Profile")
        
        # Вводим имя профиля
        profile_name = "Default Proxy"
        self.page.fill("#profile-name", profile_name)
        
        # Выбираем протокол
        protocol = proxy_config.get("protocol", "http").lower()
        self.page.select_option('select[ng-model="rule.protocol"]', protocol)
        
        # Вводим хост и порт
        self.page.fill('input[ng-model="rule.host"]', proxy_config["host"])
        self.page.fill('input[ng-model="rule.port"]', str(proxy_config["port"]))
        
        # Если есть аутентификация
        if proxy_config.get("username") and proxy_config.get("password"):
            self.page.click("#auth")
            self.page.fill('input[ng-model="rule.username"]', proxy_config["username"])
            self.page.fill('input[ng-model="rule.password"]', proxy_config["password"])
            
        # Сохраняем профиль
        self.page.click('.btn-primary >> text=Save')
        
        # Устанавливаем как профиль по умолчанию
        self.page.click(f"#profile-{profile_name} .btn-default")

def setup_switchyomega(profile_name: str) -> bool:
    """
    Функция для настройки SwitchyOmega
    
    Args:
        profile_name: Имя профиля Chrome
        
    Returns:
        bool: True если настройка успешна
    """
    try:
        from playwright.sync_api import sync_playwright
        
        # Получаем настройки прокси из .env
        proxy_config = get_proxy_config(profile_name)
        
        with sync_playwright() as p:
            # Запускаем браузер с нужным профилем
            browser = p.chromium.launch_persistent_context(
                user_data_dir=f"data/profiles/Profile {profile_name}",
                headless=False
            )
            
            # Используем первую страницу
            page = browser.pages[0]
            
            # Настраиваем SwitchyOmega
            setup = SwitchyOmegaSetup(page)
            result = setup.setup_proxy(proxy_config)
            
            # Закрываем браузер
            browser.close()
            
            return result
            
    except Exception as e:
        logger.error(f"❌ Ошибка при настройке SwitchyOmega для профиля {profile_name}")
        logger.debug(f"Причина: {str(e)}")
        return False 