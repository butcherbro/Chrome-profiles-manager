"""
Модуль для настройки MetaMask с использованием Playwright.
Позволяет автоматически настроить кошелек для выбранного профиля.
"""

import os
import json
import time
from pathlib import Path
from loguru import logger
from typing import Optional, Dict, Any, List
from playwright.sync_api import Page, expect

class MetaMaskSetup:
    """Класс для настройки MetaMask"""
    
    def __init__(self, page: Page):
        """
        Инициализация настройщика MetaMask
        
        Args:
            page: Объект страницы Playwright
        """
        self.page = page
        self.extension_id = "nkbihfbeogaeaoehlefnkodbefgpgknn"
        
    def setup_wallet(self, wallet_config: Dict[str, Any]) -> bool:
        """
        Настраивает кошелек MetaMask
        
        Args:
            wallet_config: Конфигурация кошелька
                {
                    "password": str,
                    "seed_phrase": Optional[str],
                    "private_key": Optional[str],
                    "networks": Optional[List[Dict[str, Any]]]
                }
                
        Returns:
            bool: True если настройка успешна
        """
        try:
            # Открываем страницу расширения
            self.page.goto(f"chrome-extension://{self.extension_id}/home.html")
            
            # Ждем загрузки страницы
            expect(self.page.locator("#app-content")).to_be_visible(timeout=5000)
            
            # Если есть seed phrase, импортируем кошелек
            if wallet_config.get("seed_phrase"):
                self._import_wallet_from_seed(wallet_config["seed_phrase"], wallet_config["password"])
            # Если есть private key, импортируем его
            elif wallet_config.get("private_key"):
                self._import_wallet_from_private_key(wallet_config["private_key"], wallet_config["password"])
            # Иначе создаем новый кошелек
            else:
                self._create_new_wallet(wallet_config["password"])
                
            # Если есть сети для добавления
            if wallet_config.get("networks"):
                for network in wallet_config["networks"]:
                    self._add_network(network)
                    
            logger.info("✅ MetaMask успешно настроен")
            return True
            
        except Exception as e:
            logger.error("⛔ Ошибка при настройке MetaMask")
            logger.debug(f"Причина: {str(e)}")
            return False
            
    def unlock_wallet(self, password: str) -> bool:
        """
        Разблокирует кошелек MetaMask
        
        Args:
            password: Пароль от кошелька
            
        Returns:
            bool: True если разблокировка успешна
        """
        try:
            # Открываем новую страницу
            page = self.page.context.new_page()
            
            # Открываем страницу расширения через chrome://extensions
            page.goto("chrome://extensions")
            
            # Находим и кликаем на кнопку Details для MetaMask
            metamask_card = page.locator(f"[id*='{self.extension_id}']")
            metamask_card.locator("text=Details").click()
            
            # Находим и кликаем на ссылку для открытия расширения
            extension_link = page.locator("text=extension page")
            extension_link.click()
            
            # Переключаемся на новую страницу
            pages = self.page.context.pages
            metamask_page = pages[-1]  # последняя открытая страница
            
            # Ждем загрузки страницы
            expect(metamask_page.locator("#app-content")).to_be_visible(timeout=5000)
            
            # Вводим пароль
            metamask_page.locator("#password").fill(password)
            metamask_page.locator("text=Unlock").click()
            
            # Ждем разблокировки
            expect(metamask_page.locator(".account-menu__icon")).to_be_visible(timeout=5000)
            
            logger.info("✅ MetaMask успешно разблокирован")
            return True
            
        except Exception as e:
            logger.error("⛔ Ошибка при разблокировке MetaMask")
            logger.debug(f"Причина: {str(e)}")
            return False
            
    def _create_new_wallet(self, password: str):
        """
        Создает новый кошелек
        
        Args:
            password: Пароль для кошелька
        """
        # Нажимаем Create New Wallet
        self.page.locator("text=Create New Wallet").click()
        
        # Соглашаемся с условиями
        self.page.locator("text=I Agree").click()
        
        # Вводим пароль
        self.page.locator("#create-password").fill(password)
        self.page.locator("#confirm-password").fill(password)
        self.page.locator("text=Create").click()
        
        # Сохраняем seed phrase
        seed_phrase = self.page.locator(".backup-phrase__content").text_content()
        logger.info(f"Seed phrase: {seed_phrase}")
        
        # Подтверждаем сохранение
        self.page.locator("text=Next").click()
        self.page.locator("text=Remind me later").click()
        
    def _import_wallet_from_seed(self, seed_phrase: str, password: str):
        """
        Импортирует кошелек из seed phrase
        
        Args:
            seed_phrase: Seed phrase
            password: Пароль для кошелька
        """
        # Нажимаем Import Wallet
        self.page.locator("text=Import Wallet").click()
        
        # Соглашаемся с условиями
        self.page.locator("text=I Agree").click()
        
        # Вводим seed phrase
        self.page.locator("#import-srp__srp").fill(seed_phrase)
        
        # Вводим пароль
        self.page.locator("#password").fill(password)
        self.page.locator("#confirm-password").fill(password)
        
        # Подтверждаем импорт
        self.page.locator("text=Import").click()
        
    def _import_wallet_from_private_key(self, private_key: str, password: str):
        """
        Импортирует кошелек из приватного ключа
        
        Args:
            private_key: Приватный ключ
            password: Пароль для кошелька
        """
        # Нажимаем Import Wallet
        self.page.locator("text=Import Wallet").click()
        
        # Соглашаемся с условиями
        self.page.locator("text=I Agree").click()
        
        # Выбираем импорт приватного ключа
        self.page.locator("text=Private Key").click()
        
        # Вводим приватный ключ
        self.page.locator("#private-key-box").fill(private_key)
        
        # Вводим пароль
        self.page.locator("#password").fill(password)
        self.page.locator("#confirm-password").fill(password)
        
        # Подтверждаем импорт
        self.page.locator("text=Import").click()
        
    def _add_network(self, network_config: Dict[str, Any]):
        """
        Добавляет новую сеть
        
        Args:
            network_config: Конфигурация сети
                {
                    "name": str,
                    "rpc_url": str,
                    "chain_id": int,
                    "currency_symbol": str,
                    "explorer_url": Optional[str]
                }
        """
        # Открываем настройки сети
        self.page.locator(".account-menu__icon").click()
        self.page.locator("text=Settings").click()
        self.page.locator("text=Networks").click()
        
        # Нажимаем Add Network
        self.page.locator("text=Add Network").click()
        
        # Вводим данные сети
        self.page.locator("#network-name").fill(network_config["name"])
        self.page.locator("#rpc-url").fill(network_config["rpc_url"])
        self.page.locator("#chainId").fill(str(network_config["chain_id"]))
        self.page.locator("#currency-symbol").fill(network_config["currency_symbol"])
        
        if network_config.get("explorer_url"):
            self.page.locator("#block-explorer-url").fill(network_config["explorer_url"])
            
        # Сохраняем сеть
        self.page.locator("text=Save").click()
        
def setup_metamask(page: Page, wallet_config: Dict[str, Any]) -> bool:
    """
    Функция-обертка для настройки MetaMask
    
    Args:
        page: Объект страницы Playwright
        wallet_config: Конфигурация кошелька
        
    Returns:
        bool: True если настройка успешна
    """
    setup = MetaMaskSetup(page)
    return setup.setup_wallet(wallet_config)
    
def unlock_metamask(page: Page, password: str) -> bool:
    """
    Функция-обертка для разблокировки MetaMask
    
    Args:
        page: Объект страницы Playwright
        password: Пароль от кошелька
        
    Returns:
        bool: True если разблокировка успешна
    """
    setup = MetaMaskSetup(page)
    return setup.unlock_wallet(password) 