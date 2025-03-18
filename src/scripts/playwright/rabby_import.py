#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Скрипт для импорта кошельков Rabby Wallet в профили Chrome с использованием Playwright.
Поддерживает импорт как через seed-фразу, так и через приватный ключ.
"""

import os
import time
import json
from loguru import logger
from playwright.sync_api import Page
from typing import Optional, Dict, Any

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

def run_rabby_import(profile_name: str, script_data_path: str, page: Page = None) -> bool:
    """
    Запускает импорт кошелька Rabby Wallet для указанного профиля
    
    Args:
        profile_name: Имя профиля
        script_data_path: Путь к директории скрипта
        page: Страница Playwright
        
    Returns:
        bool: True если импорт успешен, False в противном случае
    """
    logger.info(f"🚀 Запускаем импорт Rabby Wallet для профиля {profile_name}")
    
    try:
        # Загружаем конфигурацию
        config_path = os.path.join(os.path.dirname(__file__), "..", "..", "chrome", "config", "rabby_config.json")
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Получаем данные из secrets.txt
        secrets_file_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "secrets.txt")
        profile_data = get_txt_line_by_profile_name(profile_name, secrets_file_path)
        
        if not profile_data:
            logger.error("❌ Приватный ключ или сид фраза не найдены")
            return False
            
        profile_name, wallet_type, secret, password = profile_data.split('|')
        
        # Проверяем, что это данные для Rabby
        if wallet_type.lower() != 'rabby':
            logger.error(f"❌ Неверный тип кошелька: {wallet_type}, ожидается: rabby")
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
        
        # Создаем новую страницу для Rabby
        logger.info("🦊 Создаем новую страницу для Rabby...")
        rabby_page = context.new_page()
        
        # Задержка перед запуском если указана
        if config.get("run_delay_sec"):
            logger.info(f"⏳ Ждем {config['run_delay_sec']} секунд перед запуском...")
            time.sleep(config["run_delay_sec"])
        
        # Открываем Rabby
        rabby_url = f"chrome-extension://{config['extension_id']}/index.html#/new-user/guide"
        logger.info(f"🔗 Открываем Rabby по URL: {rabby_url}")
        rabby_page.goto(rabby_url)
        
        # Делаем скриншот начальной страницы
        screenshot_path = os.path.join(screenshots_dir, f"rabby_start_{profile_name}.png")
        rabby_page.screenshot(path=screenshot_path)
        logger.info(f"📸 Сделан скриншот начальной страницы: {screenshot_path}")
        
        # Нажимаем "I already have an address"
        logger.info("🖱️ Нажимаем 'I already have an address'...")
        import_btn = rabby_page.locator(config["selectors"]["import_address_button"])
        import_btn.wait_for(state="visible", timeout=config["timeouts"]["element"])
        import_btn.click()
        
        if is_seed_phrase:
            # Импорт через seed-фразу
            logger.info("🔑 Импортируем через seed-фразу...")
            
            seed_btn = rabby_page.locator(config["selectors"]["seed_phrase_button"])
            seed_btn.wait_for(state="visible", timeout=config["timeouts"]["element"])
            seed_btn.click()
            
            # Вводим слова seed-фразы
            words = secret.split()
            for i, word in enumerate(words, 1):
                word_input = rabby_page.locator(f"{config['selectors']['seed_phrase_inputs']} >> nth={i-1}")
                word_input.fill(word)
                logger.info(f"✍️ Введено слово {i} из 12")
        else:
            # Импорт через приватный ключ
            logger.info("🔑 Импортируем через приватный ключ...")
            
            private_key_btn = rabby_page.locator(config["selectors"]["private_key_button"])
            private_key_btn.wait_for(state="visible", timeout=config["timeouts"]["element"])
            private_key_btn.click()
            
            # Вводим приватный ключ
            private_key_input = rabby_page.locator(config["selectors"]["private_key_input"])
            private_key_input.fill(secret)
        
        # Нажимаем Confirm
        confirm_btn = rabby_page.locator(config["selectors"]["confirm_button"])
        confirm_btn.wait_for(state="visible", timeout=config["timeouts"]["element"])
        confirm_btn.click()
        
        # Вводим пароль
        password_input = rabby_page.locator(config["selectors"]["password_input"])
        password_input.fill(password)
        
        # Подтверждаем пароль
        confirm_password_input = rabby_page.locator(config["selectors"]["confirm_password_input"])
        confirm_password_input.fill(password)
        
        # Нажимаем кнопку подтверждения импорта
        confirm_import_btn = rabby_page.locator(config["selectors"]["confirm_button"])
        confirm_import_btn.wait_for(state="visible", timeout=config["timeouts"]["element"])
        confirm_import_btn.click()
        
        # Если это seed-фраза, нужно подтвердить импорт выбранных адресов
        if is_seed_phrase:
            import_selected_btn = rabby_page.locator(config["selectors"]["import_button"])
            import_selected_btn.wait_for(state="visible", timeout=config["timeouts"]["element"])
            import_selected_btn.click()
        
        # Делаем финальный скриншот
        screenshot_path = os.path.join(screenshots_dir, f"rabby_final_{profile_name}.png")
        rabby_page.screenshot(path=screenshot_path)
        logger.info(f"📸 Сделан финальный скриншот: {screenshot_path}")
        
        logger.success(f"✅ {profile_name} - Rabby Wallet успешно импортирован")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка при импорте Rabby Wallet: {str(e)}")
        
        # Делаем скриншот ошибки
        try:
            screenshot_path = os.path.join(screenshots_dir, f"rabby_error_{profile_name}.png")
            rabby_page.screenshot(path=screenshot_path)
            logger.info(f"📸 Сделан скриншот ошибки: {screenshot_path}")
        except:
            pass
            
        return False

# Функция для регистрации скрипта в системе запуска
def register_script(pw):
    """
    Регистрирует скрипт импорта Rabby Wallet в системе запуска скриптов
    
    Args:
        pw: Экземпляр класса PlaywrightChrome
    """
    pw.scripts["rabby_import"] = {
        "human_name": "Импорт Rabby Wallet",
        "method": run_rabby_import
    } 