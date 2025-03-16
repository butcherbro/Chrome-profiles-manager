#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Скрипт для импорта кошельков MetaMask в профили Chrome.
Интегрируется с системой запуска скриптов Chrome Profile Manager.
"""

import os
import time
import json
from loguru import logger
from typing import Optional, Dict, Any, List
from playwright.sync_api import Page

from src.utils.constants import DEFAULT_EXTENSIONS_PATH, METAMASK_ID
from src.chrome.playwright_chrome import PlaywrightChrome
from src.utils.helpers import fix_profile_extensions_settings

# Предустановленные значения для тестирования
DEFAULT_SEED_PHRASE = "spirit snap march purchase win flavor sniff bread muffin wreck will blue"
DEFAULT_PASSWORD = "1_HEROES"

class MetamaskImport:
    """
    Класс для импорта кошелька MetaMask с использованием Playwright
    """
    
    def __init__(self, profile_name: str):
        """
        Инициализация класса для импорта MetaMask
        
        Args:
            profile_name: Имя профиля Chrome
        """
        self.profile_name = profile_name
        self.chrome = PlaywrightChrome()
        self.page = None
        
        # Загружаем конфигурацию MetaMask
        config_path = os.path.join(os.path.dirname(__file__), "..", "chrome", "config", "metamask_config.json")
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        else:
            # Используем значения по умолчанию
            self.config = {
                "selectors": {
                    "import_wallet_button": "button:has-text('Import wallet')",
                    "i_agree_button": "button:has-text('I agree')",
                    "import_with_seed_phrase": "button:has-text('Import an existing wallet')",
                    "seed_phrase_input": "textarea[placeholder='Paste Secret Recovery Phrase from clipboard']",
                    "password_input": "input[type='password']",
                    "confirm_password_input": "input[autocomplete='new-password']:nth-child(2)",
                    "terms_checkbox": "input[type='checkbox']",
                    "import_button": "button:has-text('Import')",
                    "all_done_button": "button:has-text('All Done')",
                    "got_it_button": "button:has-text('Got it')",
                    "close_popup_button": "button:has-text('Close')",
                    "next_button": "button:has-text('Next')",
                    "skip_button": "button:has-text('Skip')",
                    "networks_button": "button[data-testid='network-display']",
                    "add_network_button": "button:has-text('Add network')",
                    "add_network_manually": "button:has-text('Add a network manually')",
                    "network_name_input": "input[id='network-name']",
                    "rpc_url_input": "input[id='rpc-url']",
                    "chain_id_input": "input[id='chainId']",
                    "currency_symbol_input": "input[id='currency-symbol']",
                    "block_explorer_input": "input[id='block-explorer-url']",
                    "save_network_button": "button:has-text('Save')",
                    "close_all_button": "button[aria-label='Close']"
                },
                "timeouts": {
                    "navigation": 60000,
                    "element": 30000,
                    "action": 5000
                }
            }
    
    async def import_wallet(self, seed_phrase: str, password: str) -> bool:
        """
        Импорт кошелька MetaMask с использованием seed phrase
        
        Args:
            seed_phrase: Seed phrase (мнемоническая фраза) для импорта
            password: Пароль для кошелька
        
        Returns:
            bool: True если импорт успешен, False в противном случае
        """
        try:
            # Запускаем Chrome с профилем
            if not self.chrome.launch_profile(self.profile_name):
                logger.error(f"⛔ {self.profile_name} - не удалось запустить профиль")
                return False
            
            self.page = self.chrome.page
            
            # Открываем MetaMask
            logger.info(f"🦊 {self.profile_name} - открываем MetaMask...")
            await self.page.goto(f"chrome-extension://{METAMASK_ID}/home.html")
            
            # Проверяем, нужно ли импортировать кошелек
            try:
                # Ждем появления кнопки импорта
                import_wallet_button = await self.page.wait_for_selector(
                    self.config["selectors"]["import_wallet_button"],
                    timeout=self.config["timeouts"]["element"]
                )
                
                if import_wallet_button:
                    logger.info(f"🦊 {self.profile_name} - начинаем импорт кошелька...")
                    await import_wallet_button.click()
                    
                    # Соглашаемся с условиями
                    i_agree_button = await self.page.wait_for_selector(
                        self.config["selectors"]["i_agree_button"],
                        timeout=self.config["timeouts"]["element"]
                    )
                    await i_agree_button.click()
                    
                    # Выбираем импорт с помощью seed phrase
                    import_with_seed_phrase = await self.page.wait_for_selector(
                        self.config["selectors"]["import_with_seed_phrase"],
                        timeout=self.config["timeouts"]["element"]
                    )
                    await import_with_seed_phrase.click()
                    
                    # Вводим seed phrase
                    seed_phrase_input = await self.page.wait_for_selector(
                        self.config["selectors"]["seed_phrase_input"],
                        timeout=self.config["timeouts"]["element"]
                    )
                    await seed_phrase_input.fill(seed_phrase)
                    
                    # Вводим пароль
                    password_input = await self.page.wait_for_selector(
                        self.config["selectors"]["password_input"],
                        timeout=self.config["timeouts"]["element"]
                    )
                    await password_input.fill(password)
                    
                    # Подтверждаем пароль
                    confirm_password_input = await self.page.wait_for_selector(
                        self.config["selectors"]["confirm_password_input"],
                        timeout=self.config["timeouts"]["element"]
                    )
                    await confirm_password_input.fill(password)
                    
                    # Принимаем условия
                    terms_checkbox = await self.page.wait_for_selector(
                        self.config["selectors"]["terms_checkbox"],
                        timeout=self.config["timeouts"]["element"]
                    )
                    await terms_checkbox.click()
                    
                    # Нажимаем кнопку импорта
                    import_button = await self.page.wait_for_selector(
                        self.config["selectors"]["import_button"],
                        timeout=self.config["timeouts"]["element"]
                    )
                    await import_button.click()
                    
                    # Ждем завершения импорта
                    all_done_button = await self.page.wait_for_selector(
                        self.config["selectors"]["all_done_button"],
                        timeout=self.config["timeouts"]["navigation"]
                    )
                    await all_done_button.click()
                    
                    # Закрываем попапы, если они есть
                    try:
                        got_it_button = await self.page.wait_for_selector(
                            self.config["selectors"]["got_it_button"],
                            timeout=self.config["timeouts"]["element"]
                        )
                        if got_it_button:
                            await got_it_button.click()
                    except:
                        pass
                    
                    try:
                        close_popup_button = await self.page.wait_for_selector(
                            self.config["selectors"]["close_popup_button"],
                            timeout=self.config["timeouts"]["element"]
                        )
                        if close_popup_button:
                            await close_popup_button.click()
                    except:
                        pass
                    
                    logger.success(f"✅ {self.profile_name} - кошелек MetaMask успешно импортирован")
                    return True
                else:
                    logger.warning(f"⚠️ {self.profile_name} - кошелек MetaMask уже импортирован")
                    return True
            except Exception as e:
                logger.error(f"⛔ {self.profile_name} - ошибка при импорте кошелька: {str(e)}")
                return False
        except Exception as e:
            logger.error(f"⛔ {self.profile_name} - не удалось импортировать кошелек: {str(e)}")
            return False
        finally:
            # Закрываем браузер
            if self.chrome:
                self.chrome.close()
    
    async def add_network(self, network_config: Dict[str, Any]) -> bool:
        """
        Добавление сети в MetaMask
        
        Args:
            network_config: Конфигурация сети для добавления
                {
                    "name": "Имя сети",
                    "rpc_url": "URL RPC",
                    "chain_id": "ID цепи",
                    "currency_symbol": "Символ валюты",
                    "block_explorer_url": "URL обозревателя блоков"
                }
        
        Returns:
            bool: True если сеть успешно добавлена, False в противном случае
        """
        try:
            # Запускаем Chrome с профилем
            if not self.chrome.launch_profile(self.profile_name):
                logger.error(f"⛔ {self.profile_name} - не удалось запустить профиль")
                return False
            
            self.page = self.chrome.page
            
            # Открываем MetaMask
            logger.info(f"🦊 {self.profile_name} - открываем MetaMask...")
            await self.page.goto(f"chrome-extension://{METAMASK_ID}/home.html")
            
            # Нажимаем на кнопку сетей
            networks_button = await self.page.wait_for_selector(
                self.config["selectors"]["networks_button"],
                timeout=self.config["timeouts"]["element"]
            )
            await networks_button.click()
            
            # Нажимаем на кнопку добавления сети
            add_network_button = await self.page.wait_for_selector(
                self.config["selectors"]["add_network_button"],
                timeout=self.config["timeouts"]["element"]
            )
            await add_network_button.click()
            
            # Выбираем добавление сети вручную
            add_network_manually = await self.page.wait_for_selector(
                self.config["selectors"]["add_network_manually"],
                timeout=self.config["timeouts"]["element"]
            )
            await add_network_manually.click()
            
            # Заполняем данные сети
            network_name_input = await self.page.wait_for_selector(
                self.config["selectors"]["network_name_input"],
                timeout=self.config["timeouts"]["element"]
            )
            await network_name_input.fill(network_config["name"])
            
            rpc_url_input = await self.page.wait_for_selector(
                self.config["selectors"]["rpc_url_input"],
                timeout=self.config["timeouts"]["element"]
            )
            await rpc_url_input.fill(network_config["rpc_url"])
            
            chain_id_input = await self.page.wait_for_selector(
                self.config["selectors"]["chain_id_input"],
                timeout=self.config["timeouts"]["element"]
            )
            await chain_id_input.fill(network_config["chain_id"])
            
            currency_symbol_input = await self.page.wait_for_selector(
                self.config["selectors"]["currency_symbol_input"],
                timeout=self.config["timeouts"]["element"]
            )
            await currency_symbol_input.fill(network_config["currency_symbol"])
            
            block_explorer_input = await self.page.wait_for_selector(
                self.config["selectors"]["block_explorer_input"],
                timeout=self.config["timeouts"]["element"]
            )
            await block_explorer_input.fill(network_config["block_explorer_url"])
            
            # Сохраняем сеть
            save_network_button = await self.page.wait_for_selector(
                self.config["selectors"]["save_network_button"],
                timeout=self.config["timeouts"]["element"]
            )
            await save_network_button.click()
            
            # Ждем завершения добавления сети
            try:
                close_all_button = await self.page.wait_for_selector(
                    self.config["selectors"]["close_all_button"],
                    timeout=self.config["timeouts"]["navigation"]
                )
                if close_all_button:
                    await close_all_button.click()
            except:
                pass
            
            logger.success(f"✅ {self.profile_name} - сеть {network_config['name']} успешно добавлена")
            return True
        except Exception as e:
            logger.error(f"⛔ {self.profile_name} - не удалось добавить сеть {network_config['name']}: {str(e)}")
            return False
        finally:
            # Закрываем браузер
            if self.chrome:
                self.chrome.close()
    
    async def add_networks(self, networks: List[Dict[str, Any]]) -> bool:
        """
        Добавление нескольких сетей в MetaMask
        
        Args:
            networks: Список конфигураций сетей для добавления
        
        Returns:
            bool: True если все сети успешно добавлены, False в противном случае
        """
        success = True
        for network in networks:
            if not await self.add_network(network):
                success = False
        
        return success 

def click_metamask_button(page: Page, button_text: str, screenshots_dir: str, profile_name: str) -> bool:
    """
    Надежное нажатие на кнопку в MetaMask с использованием различных методов
    
    Args:
        page: Объект страницы Playwright
        button_text: Текст кнопки для поиска (например, "Done", "Next")
        screenshots_dir: Директория для сохранения скриншотов
        profile_name: Имя профиля для логирования
        
    Returns:
        bool: True если кнопка была успешно нажата, False в противном случае
    """
    logger.info(f"🖱️ Пытаемся нажать кнопку '{button_text}' различными способами...")
    
    # Делаем скриншот для анализа
    screenshot_path = os.path.join(screenshots_dir, f"metamask_before_{button_text.lower()}_{profile_name}.png")
    page.screenshot(path=screenshot_path)
    logger.info(f"📸 Сделан скриншот перед нажатием кнопки {button_text}: {screenshot_path}")
    
    # Сохраняем HTML-структуру страницы для анализа
    try:
        html_content = page.content()
        html_path = os.path.join(screenshots_dir, f"metamask_before_{button_text.lower()}_html_{profile_name}.txt")
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        logger.info(f"📄 Сохранена HTML-структура страницы: {html_path}")
    except Exception as e:
        logger.warning(f"⚠️ Не удалось сохранить HTML-структуру: {e}")
    
    # Метод 1: Прямой клик по тексту
    try:
        logger.info(f"🔍 Метод 1: Прямой клик по тексту '{button_text}'")
        text_element = page.locator(f"text={button_text}").first
        if text_element and text_element.is_visible(timeout=2000):
            text_element.click(force=True, timeout=5000)
            logger.info(f"✅ Кнопка '{button_text}' нажата методом 1")
            time.sleep(1)
            return True
    except Exception as e:
        logger.warning(f"⚠️ Метод 1 не сработал: {e}")
    
    # Метод 2: Поиск по точным селекторам
    selectors = [
        f"button:has-text('{button_text}')",
        f"button.onboarding-{button_text.lower()}-button",
        f"button[data-testid='onboarding-{button_text.lower()}-button']",
        f"button[role='button']:has-text('{button_text}')",
        f"//button[contains(@class, 'onboarding-{button_text.lower()}-button')]",
        f"//button[contains(text(), '{button_text}')]",
        f"//button[text()='{button_text}']",
        f"//div[contains(@class, 'onboarding-{button_text.lower()}-button')]",
        f"//div[contains(@role, 'button') and contains(text(), '{button_text}')]",
        f"//div[contains(@class, 'mm-box') and contains(text(), '{button_text}')]",
        f"//button[contains(@class, 'mm-box')]",
        f"//button[contains(@class, 'mm-button')]",
        f"//button[contains(@class, 'mm-button-primary')]",
        f"//button[contains(@class, 'mm-text')]"
    ]
    
    for i, selector in enumerate(selectors):
        try:
            logger.info(f"🔍 Метод 2.{i+1}: Поиск по селектору: {selector}")
            button = page.locator(selector).first
            if button and button.is_visible(timeout=2000):
                button.click(force=True, timeout=5000)
                logger.info(f"✅ Кнопка '{button_text}' нажата методом 2.{i+1}")
                time.sleep(1)
                return True
        except Exception as e:
            logger.warning(f"⚠️ Метод 2.{i+1} не сработал: {e}")
    
    # Метод 3: Поиск всех кнопок и проверка текста
    try:
        logger.info(f"🔍 Метод 3: Поиск всех кнопок и проверка текста")
        all_buttons = page.locator("button, div[role='button']").all()
        logger.info(f"ℹ️ Найдено {len(all_buttons)} кнопок и элементов с ролью кнопки")
        
        for i, button in enumerate(all_buttons):
            try:
                text = button.text_content().strip().lower()
                is_visible = button.is_visible()
                logger.info(f"ℹ️ Кнопка {i+1}: текст='{text}', видима={is_visible}")
                
                if button_text.lower() in text and is_visible:
                    button.click(force=True, timeout=5000)
                    logger.info(f"✅ Кнопка '{button_text}' нажата методом 3 (индекс {i+1})")
                    time.sleep(1)
                    return True
            except Exception as e:
                logger.warning(f"⚠️ Ошибка при анализе кнопки {i+1}: {e}")
    except Exception as e:
        logger.warning(f"⚠️ Метод 3 не сработал: {e}")
    
    # Метод 4: JavaScript для поиска и клика по элементу с текстом
    try:
        logger.info(f"🔍 Метод 4: JavaScript для поиска и клика по элементу с текстом")
        result = page.evaluate(f"""
            () => {{
                // Ищем все элементы с текстом "{button_text}"
                const elements = Array.from(document.querySelectorAll('*'));
                const targetElements = elements.filter(el => 
                    el.textContent && 
                    el.textContent.toLowerCase().includes("{button_text.lower()}") && 
                    (window.getComputedStyle(el).display !== 'none') &&
                    (window.getComputedStyle(el).visibility !== 'hidden')
                );
                
                // Сортируем по глубине вложенности (предпочитаем элементы с меньшей вложенностью)
                targetElements.sort((a, b) => {{
                    let depthA = 0, depthB = 0;
                    let parent = a;
                    while (parent) {{
                        depthA++;
                        parent = parent.parentElement;
                    }}
                    parent = b;
                    while (parent) {{
                        depthB++;
                        parent = parent.parentElement;
                    }}
                    return depthA - depthB;
                }});
                
                // Нажимаем на первый видимый элемент
                if (targetElements.length > 0) {{
                    console.log("Найден элемент с текстом {button_text}:", targetElements[0]);
                    targetElements[0].click();
                    return true;
                }}
                return false;
            }}
        """)
        
        if result:
            logger.info(f"✅ Кнопка '{button_text}' нажата методом 4 (JavaScript)")
            time.sleep(1)
            return True
        else:
            logger.warning(f"⚠️ Метод 4 не нашел элементов с текстом '{button_text}'")
    except Exception as e:
        logger.warning(f"⚠️ Метод 4 не сработал: {e}")
    
    # Метод 5: Использование Tab и Enter
    try:
        logger.info(f"🔍 Метод 5: Использование Tab и Enter")
        # Сначала нажимаем Tab несколько раз, чтобы переместиться по элементам
        for i in range(10):
            page.keyboard.press("Tab")
            time.sleep(0.3)
            
            # После каждого Tab проверяем, не появился ли фокус на нужной кнопке
            focused_element = page.evaluate("""
                () => {
                    const activeElement = document.activeElement;
                    return activeElement ? activeElement.textContent : null;
                }
            """)
            
            logger.info(f"ℹ️ Фокус на элементе с текстом: '{focused_element}'")
            
            if focused_element and button_text.lower() in str(focused_element).lower():
                page.keyboard.press("Enter")
                logger.info(f"✅ Кнопка '{button_text}' нажата методом 5 (Tab + Enter)")
                time.sleep(1)
                return True
        
        # Если не нашли после Tab, просто нажимаем Enter
        page.keyboard.press("Enter")
        logger.info(f"✅ Нажата клавиша Enter (метод 5)")
        time.sleep(1)
    except Exception as e:
        logger.warning(f"⚠️ Метод 5 не сработал: {e}")
    
    # Метод 6: Клик по координатам центра экрана
    try:
        logger.info(f"🔍 Метод 6: Клик по координатам центра экрана")
        viewport_size = page.viewport_size
        if viewport_size:
            center_x = viewport_size["width"] // 2
            center_y = viewport_size["height"] // 2
            logger.info(f"ℹ️ Размер окна: {viewport_size}, центр: ({center_x}, {center_y})")
            
            # Клик по центру экрана
            page.mouse.click(center_x, center_y)
            logger.info(f"✅ Выполнен клик по центру экрана (метод 6)")
            time.sleep(1)
            
            # Проверяем, изменилась ли страница
            screenshot_path = os.path.join(screenshots_dir, f"metamask_after_center_click_{profile_name}.png")
            page.screenshot(path=screenshot_path)
            logger.info(f"📸 Сделан скриншот после клика по центру: {screenshot_path}")
    except Exception as e:
        logger.warning(f"⚠️ Метод 6 не сработал: {e}")
    
    # Если ни один метод не сработал, возвращаем False
    logger.error(f"❌ Не удалось нажать кнопку '{button_text}' ни одним из методов")
    
    # Делаем финальный скриншот
    screenshot_path = os.path.join(screenshots_dir, f"metamask_button_click_failed_{button_text.lower()}_{profile_name}.png")
    page.screenshot(path=screenshot_path)
    logger.info(f"📸 Сделан скриншот после неудачных попыток нажать кнопку: {screenshot_path}")
    
    return False

def run_metamask_import(profile_name, script_data_path, page=None):
    """
    Запускает импорт кошелька MetaMask для указанного профиля
    
    Args:
        profile_name: Имя профиля
        script_data_path: Путь к директории скрипта
        page: Страница Playwright (используется только для получения контекста)
        
    Returns:
        bool: True если импорт успешен, False в противном случае
    """
    logger.info(f"🚀 Запускаем импорт кошелька MetaMask для профиля {profile_name}")
    
    # Используем предустановленные значения для тестирования
    seed_phrase = DEFAULT_SEED_PHRASE
    password = DEFAULT_PASSWORD
    
    logger.info(f"🔑 Используем seed-фразу: {seed_phrase[:10]}...")
    logger.info(f"🔑 Используем пароль: {password[:2]}******")
    
    # Создаем директорию для скриншотов
    screenshots_dir = os.path.join(script_data_path, "screenshots")
    os.makedirs(screenshots_dir, exist_ok=True)
    
    try:
        # Исправляем настройки расширений в профиле
        logger.info(f"🔧 Исправляем настройки расширений в профиле {profile_name}...")
        fix_profile_extensions_settings(profile_name)
        
        # Даем время на полную загрузку расширений
        logger.info("⏳ Ждем 5 секунд для полной загрузки расширений...")
        time.sleep(5)
        
        # Проверяем, что страница предоставлена
        if not page:
            logger.error("❌ Страница не предоставлена")
            return False
            
        # Получаем контекст из страницы
        context = page.context
        
        # Создаем новую страницу для MetaMask
        logger.info("🦊 Создаем новую страницу для MetaMask...")
        metamask_page = context.new_page()
        logger.info("✅ Создана новая страница для MetaMask")
        
        # Открываем MetaMask с параметром onboarding/welcome
        metamask_url = f"chrome-extension://{METAMASK_ID}/home.html#onboarding/welcome"
        logger.info(f"🔗 Открываем MetaMask по URL: {metamask_url}")
        
        try:
            metamask_page.goto(metamask_url, timeout=30000)
            logger.info("✅ Страница MetaMask открыта")
        except Exception as e:
            error_message = str(e)
            logger.error(f"❌ Произошла ошибка при открытии MetaMask: {error_message}")
            
            # Делаем скриншот ошибки
            screenshot_path = os.path.join(screenshots_dir, f"metamask_error_general_{profile_name}.png")
            metamask_page.screenshot(path=screenshot_path)
            logger.info(f"📸 Сделан скриншот ошибки: {screenshot_path}")
            
            # Закрываем страницу MetaMask
            metamask_page.close()
            return False
            
        # Делаем скриншот страницы приветствия
        screenshot_path = os.path.join(screenshots_dir, f"metamask_welcome_{profile_name}.png")
        metamask_page.screenshot(path=screenshot_path)
        logger.info(f"📸 Сделан скриншот страницы приветствия: {screenshot_path}")
        
        # Проверяем наличие элементов на странице
        logger.info("🔍 Проверяем наличие элементов на странице...")
        
        # Ждем загрузки страницы
        metamask_page.wait_for_load_state("networkidle", timeout=10000)
        
        # Проверяем наличие чекбокса с условиями использования
        checkbox = metamask_page.locator('label[class="onboarding__terms-label"]')
        if checkbox.is_visible(timeout=5000):
            logger.info("✅ Чекбокс с условиями использования найден")
            
            # Кликаем на чекбокс
            logger.info("🖱️ Кликаем на чекбокс с условиями использования...")
            checkbox.click()
            time.sleep(1)
            
            # Проверяем наличие кнопки импорта
            import_button = metamask_page.locator("//button[contains(@data-testid,'onboarding-import-wallet')]")
            if import_button.is_visible(timeout=5000):
                logger.info("✅ Кнопка импорта найдена")
                
                # Кликаем на кнопку импорта
                logger.info("🖱️ Кликаем на кнопку импорта...")
                import_button.click()
                
                # Увеличиваем время ожидания до 5 секунд
                logger.info("⏳ Ждем 5 секунд для загрузки страницы импорта...")
                time.sleep(5)
                
                # Делаем скриншот текущей страницы
                screenshot_path = os.path.join(screenshots_dir, f"metamask_after_import_click_{profile_name}.png")
                metamask_page.screenshot(path=screenshot_path)
                logger.info(f"📸 Сделан скриншот текущей страницы: {screenshot_path}")
                
                # Проверяем URL страницы
                current_url = metamask_page.url
                logger.info(f"🔍 Текущий URL: {current_url}")
                
                # Проверяем, что открылась страница импорта по URL
                if "import-with-recovery-phrase" in current_url:
                    logger.success("✅ Страница импорта открыта (проверка по URL)")
                    
                    # Делаем скриншот страницы импорта
                    screenshot_path = os.path.join(screenshots_dir, f"metamask_import_{profile_name}.png")
                    metamask_page.screenshot(path=screenshot_path)
                    logger.info(f"📸 Сделан скриншот страницы импорта: {screenshot_path}")
                    
                    # Проверяем наличие полей для ввода
                    seed_phrase_textarea = metamask_page.locator('textarea[data-testid="import-srp-text"]')
                    if seed_phrase_textarea.is_visible(timeout=5000):
                        logger.success("✅ Поле для ввода seed-фразы найдено")
                        
                        # Вводим seed-фразу
                        logger.info("🔑 Вводим seed-фразу...")
                        seed_phrase_textarea.fill(seed_phrase)
                        
                        # Проверяем наличие полей для ввода пароля
                        password_inputs = metamask_page.locator('input[type="password"]')
                        if password_inputs.count() >= 2:
                            logger.success("✅ Поля для ввода пароля найдены")
                            
                            # Вводим пароль
                            logger.info("🔑 Вводим пароль...")
                            password_inputs.nth(0).fill(password)
                            
                            # Подтверждаем пароль
                            logger.info("🔑 Подтверждаем пароль...")
                            password_inputs.nth(1).fill(password)
                            
                            # Принимаем условия использования
                            terms_checkbox = metamask_page.locator('input[type="checkbox"]')
                            if terms_checkbox.is_visible(timeout=5000):
                                logger.info("✅ Чекбокс с условиями использования найден")
                                terms_checkbox.check()
                                
                                # Нажимаем кнопку импорта
                                import_final_button = metamask_page.locator('button:has-text("Import")')
                                if import_final_button.is_visible(timeout=5000):
                                    import_final_button.click()
                                    logger.info("✅ Кнопка импорта нажата")
                                    
                                    # Ждем завершения импорта
                                    time.sleep(5)
                                    
                                    # Нажимаем "All Done"
                                    all_done_button = metamask_page.locator("button:has-text('All Done')")
                                    if all_done_button.is_visible(timeout=10000):
                                        all_done_button.click()
                                        logger.info("✅ Кнопка 'All Done' нажата")
                                    
                                    logger.success(f"✅ {profile_name} - кошелек MetaMask успешно импортирован")
                                    
                                    # Закрываем страницу MetaMask
                                    metamask_page.close()
                                    return True
                                else:
                                    logger.error("❌ Кнопка импорта не найдена")
                            else:
                                logger.error("❌ Чекбокс с условиями использования не найден")
                        else:
                            logger.error("❌ Не удалось найти поля для ввода пароля")
                    else:
                        logger.error("❌ Поле для ввода seed-фразы не найдено")
                else:
                    logger.error("❌ Не удалось открыть страницу импорта")
            else:
                logger.error("❌ Кнопка импорта не найдена")
        else:
            logger.error("❌ Чекбокс с условиями использования не найден")
            
            # Проверяем, может быть кошелек уже импортирован
            account_menu = metamask_page.locator('[data-testid="account-menu-icon"]')
            if account_menu.is_visible(timeout=2000):
                logger.info("✓ MetaMask уже настроен и разблокирован")
                
                # Делаем скриншот главной страницы
                screenshot_path = os.path.join(screenshots_dir, f"metamask_main_{profile_name}.png")
                metamask_page.screenshot(path=screenshot_path)
                logger.info(f"📸 Сделан скриншот главной страницы: {screenshot_path}")
                
                # Закрываем страницу MetaMask
                metamask_page.close()
                return True
            else:
                # Проверяем, может быть это страница разблокировки
                unlock_title = metamask_page.get_by_text("Welcome Back!")
                if unlock_title.is_visible(timeout=2000):
                    logger.info("✓ MetaMask требует разблокировки")
                    
                    # Делаем скриншот страницы разблокировки
                    screenshot_path = os.path.join(screenshots_dir, f"metamask_unlock_{profile_name}.png")
                    metamask_page.screenshot(path=screenshot_path)
                    logger.info(f"📸 Сделан скриншот страницы разблокировки: {screenshot_path}")
                    
                    # Закрываем страницу MetaMask
                    metamask_page.close()
                    return False
                else:
                    logger.error("❌ Не удалось определить состояние MetaMask")
                    
                    # Закрываем страницу MetaMask
                    metamask_page.close()
                    return False
                    
    except Exception as e:
        logger.error(f"❌ Ошибка при импорте кошелька MetaMask: {str(e)}")
        return False

# Функция для регистрации скрипта в системе запуска
def register_script(pw):
    """
    Регистрирует скрипт импорта MetaMask в системе запуска скриптов
    
    Args:
        pw: Экземпляр класса PlaywrightChrome
    """
    pw.scripts["metamask_import"] = {
        "human_name": "Тест импорта MetaMask",
        "method": run_metamask_import
    } 