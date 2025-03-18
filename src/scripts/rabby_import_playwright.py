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

# Импортируем модуль с общими функциями
from src.utils.common_actions import click_element, fill_input, wait_for_element, check_element_exists

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
        time.sleep(1.5)
        
        # Создаем страницу и сразу переходим на URL
        rabby_url = f"chrome-extension://acmacodkjbdgmoleebolmdjonilkdbch/index.html#/new-user/guide"
        logger.info(f"🔗 Открываем Rabby по URL: {rabby_url}")
        rabby_page = context.new_page()
        rabby_page.goto(rabby_url, wait_until="networkidle")  # wait_until опционально
        time.sleep(1)

        click_element(
            page=rabby_page,
            selector="button:has-text('I already have an address')",
            log_message="Нажимаем 'I already have an address'...",
            timeout=10000,
            highlight=True
         )
        
        # Добавляем задержку для загрузки следующей страницы
        time.sleep(0.5)

        if is_seed_phrase:
            # Импорт через seed-фразу
            logger.info("🔑 Импортируем через seed-фразу...")
                    # Добавляем задержку для загрузки следующей страницы
            time.sleep(0.5)
            
            # Пробуем прямой клик по тексту
            logger.info("🔄 Пробуем прямой клик по тексту 'Seed Phrase'...")
            try:
                rabby_page.click("text=Seed Phrase")
                logger.info("✅ Клик по тексту 'Seed Phrase' выполнен")
                
                # Добавляем задержку
                time.sleep(0.5)
            except Exception as direct_click_error:
                logger.error(f"❌ Ошибка при прямом клике: {str(direct_click_error)}")         
            
            # Вводим слова seed-фразы
            words = secret.split()
            for i, word in enumerate(words, 1):
                word_input = rabby_page.locator(f"input[placeholder*='•'], .is-mnemonics-input input, input.ant-input >> nth={i-1}")
                word_input.fill(word)
                logger.info(f"✍️ Введено слово {i} из 12")
            
            # Добавляем задержку после ввода seed-фразы
            time.sleep(0.5)

             #  кликаем на кнопку Confirm  - Используем функцию из общего модуля
            click_element(
                    page=rabby_page,
                    selector="button:has-text('Confirm'),   button.ant-btn-primary",
                    log_message="Нажатие кнопки Confirm",
                    timeout=10000,
                    highlight=True
                )
           
            time.sleep(0.5)
            
            # Проверяем, появилось ли поле для ввода пароля
            logger.info("🔍 Проверяем наличие поля для ввода пароля...")
            try:
                # Проверяем видимость поля для ввода пароля
                password_visible = rabby_page.is_visible("#password, input[placeholder*='Password']")
                logger.info(f"👁️ Поле для ввода пароля видимо: {password_visible}")
                
                if password_visible:
                    # Вводим пароль
                    logger.info("🔑 Вводим пароль...")
                    rabby_page.fill("#password, input[placeholder*='Password']", password)
                    logger.info("✅ Пароль введен")
                    
                    # Вводим подтверждение пароля
                    logger.info("🔑 Вводим подтверждение пароля...")
                    rabby_page.fill("#confirmPassword, input[placeholder*='Confirm']", password)
                    logger.info("✅ Подтверждение пароля введено")

                 #  кликаем на кнопку Confirm  - Используем функцию из общего модуля
                click_element(
                    page=rabby_page,
                    selector="button:has-text('Confirm'),   button.ant-btn-primary",
                    log_message="Нажатие кнопки Confirm",
                    timeout=10000,
                    highlight=True
                 ) 

            except Exception as password_check_error:
                logger.error(f"❌ Ошибка при проверке поля для ввода пароля: {str(password_check_error)}")
            
            # Если это seed-фраза, кликаем на кнопку Import
            if is_seed_phrase:

                #  кликаем на кнопку Import  - Используем функцию из общего модуля
                click_element(
                    page=rabby_page,
                    selector="button:has-text('Import'),  button.ant-btn-primary",
                    log_message="Нажатие кнопки Import",
                    timeout=10000,
                    highlight=True
                )
             
              #  кликаем на кнопку Get Started  - Используем функцию из общего модуля
                click_element(
                    page=rabby_page,
                    selector="button:has-text('Get Started'),  button.ant-btn-primary",
                    log_message="Нажатие кнопки Get Started",
                    timeout=10000,
                    highlight=True
                )

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