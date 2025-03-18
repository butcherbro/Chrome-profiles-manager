#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Скрипт для импорта кошельков Metamask Wallet в профили Chrome с использованием Playwright.
Поддерживает импорт как через seed-фразу, так и через приватный ключ.
"""

import os
import time
import json
from loguru import logger
from playwright.sync_api import Page
from typing import Optional, Dict, Any

# Импортируем модуль с общими функциями
from src.utils.common_actions import click_element

def get_txt_line_by_profile_name(profile_name: str, file_path: str) -> Optional[str]:
    """
    Получает строку из файла secrets.txt по имени профиля
    
    Args:
        profile_name: Имя профиля
        file_path: Путь к файлу secrets.txt
        
    Returns:
        Optional[str]: Строка с данными профиля или None, если не найдена
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip().startswith(f"{profile_name}|"):
                    return line.strip()
    except Exception as e:
        logger.error(f"❌ Ошибка при чтении файла {file_path}: {str(e)}")
    return None

def is_twelve_words_string(text: str) -> bool:
    """
    Проверяет, является ли строка seed-фразой из 12 слов
    
    Args:
        text: Строка для проверки
        
    Returns:
        bool: True если это seed-фраза из 12 слов, False в противном случае
    """
    words = text.strip().split()
    return len(words) == 12 and all(word.isalpha() for word in words)

def run_metamask_import(profile_name: str, script_data_path: str, page: Page = None) -> bool:
    """
    Запускает импорт кошелька Metamask Wallet для указанного профиля
    
    Args:
        profile_name: Имя профиля
        script_data_path: Путь к директории скрипта
        page: Страница Playwright
        
    Returns:
        bool: True если импорт успешен, False в противном случае
    """
    logger.info(f"🚀 Запускаем импорт Metamask Wallet для профиля {profile_name}")
    
    try:
        # Получаем данные из secrets.txt
        secrets_file_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "secrets.txt")
        profile_data = get_txt_line_by_profile_name(profile_name, secrets_file_path)
        
        if not profile_data:
            logger.error("❌ Приватный ключ или сид фраза не найдены")
            return False
            
        # Разбираем строку данных
        parts = profile_data.split('|')
        if len(parts) == 3:  # Формат: profile_name|secret|password
            profile_name, secret, password = parts
        elif len(parts) == 4:  # Формат: profile_name|wallet_type|secret|password
            profile_name, wallet_type, secret, password = parts
            # Проверяем тип кошелька, если он указан
            if wallet_type.lower() != 'rabby':
                logger.warning(f"⚠️ Тип кошелька {wallet_type} не соответствует ожидаемому (rabby), но продолжаем импорт")
        else:
            logger.error("❌ Неверный формат данных. Ожидается: profile_name|secret|password или profile_name|wallet_type|secret|password")
            return False
            
        is_seed_phrase = is_twelve_words_string(secret)
        
        # Создаем директорию для скриншотов
        screenshots_dir = os.path.join(script_data_path, "screenshots")
        os.makedirs(screenshots_dir, exist_ok=True)
        
        # Проверяем, что страница предоставлена
        if not page:
            logger.error("❌ Страница не предоставлена")
            return False
            
        # Получаем контекст из страницы
        context = page.context
        
        # Пауза перед открытием новой вкладки
        time.sleep(0.5)
        
        # Создаем страницу и сразу переходим на URL
        metamask_url = f"chrome-extension://nkbihfbeogaeaoehlefnkodbefgpgknn/home.html#onboarding/welcome"
        logger.info(f"🔗 Открываем Metamask по URL: {metamask_url}")
        metamask_page = context.new_page()
        metamask_page.goto(metamask_url, wait_until="networkidle")  # wait_until опционально
    
        # Отмечаем чекбокс согласия с условиями
        terms_checkbox = metamask_page.get_by_test_id('onboarding-terms-checkbox')
        terms_checkbox.click()  

        # Нажимаем на кнопку "Import an existing wallet"
        import_wallet_button = metamask_page.get_by_test_id('onboarding-import-wallet')
        import_wallet_button.click()

        # Нажимаем на кнопку "No thanks"
        no_thanks_button = metamask_page.get_by_test_id('metametrics-no-thanks')
        no_thanks_button.click()

        # Вводим слова seed-фразы
        words = secret.split()
        for i, word in enumerate(words):
            word_input = metamask_page.get_by_test_id(f"import-srp__srp-word-{i}")
            word_input.fill(word)
            logger.info(f"✍️ Введено слово {i+1} из 12")
        
        # Нажимаем на кнопку "Confirm"
        confirm_button = metamask_page.get_by_test_id('import-srp-confirm')
        confirm_button.click()

        # Вводим пароль
        for test_id in ('create-password-new', 'create-password-confirm'):
            input_element = metamask_page.get_by_test_id(test_id)
            input_element.fill(value=password)

        # Нажимаем на кнопку "Confirm"
        confirm_button = metamask_page.get_by_test_id('create-password-terms')
        confirm_button.click()

        # Нажимаем на кнопку "Import"
        import_button = metamask_page.get_by_test_id('create-password-import')
        import_button.click()

        # Нажимаем на кнопку "Done"
        done_button = metamask_page.get_by_test_id('onboarding-complete-done')
        done_button.click()

        # Нажимаем на кнопку "Next"
        next_button = metamask_page.get_by_test_id('pin-extension-next')
        next_button.click()

        # Нажимаем на кнопку "Done"
        done_button = metamask_page.get_by_test_id('pin-extension-done')
        done_button.click()

        # Нажимаем на кнопку "Got it"
        got_it_button = metamask_page.get_by_text('Got it')
        got_it_button.click()
        
        return True  # Успешное завершение
        
    except Exception as e:
        logger.error(f"❌ Ошибка при импорте Metamask Wallet: {str(e)}")
        
        # Делаем скриншот ошибки
        try:
            screenshot_path = os.path.join(screenshots_dir, f"metamask_error_{profile_name}.png")
            metamask_page.screenshot(path=screenshot_path)
            logger.info(f"📸 Сделан скриншот ошибки: {screenshot_path}")
        except:
            pass
            
        return False  # Неудачное завершение


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