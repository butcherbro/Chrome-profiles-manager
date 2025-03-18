#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Модуль с общими функциями для работы с Playwright.
Содержит типовые действия, которые часто используются в скриптах.
"""

import os
import time
from loguru import logger
from playwright.sync_api import Page, Locator
from typing import Optional, Dict, Any, Union

def click_element(
    page: Page, 
    selector: str, 
    log_message: str = "Нажимаем на элемент", 
    timeout: int = 30000,
    sleep_before: float = 0.5,
    take_screenshot: bool = False,
    screenshot_dir: str = None,
    screenshot_name: str = None,
    highlight: bool = True
) -> bool:
    """
    Находит элемент на странице и кликает по нему
    
    Args:
        page: Страница Playwright
        selector: Селектор элемента (может быть комбинированным с запятой)
        log_message: Сообщение для логирования
        timeout: Таймаут ожидания элемента в миллисекундах
        sleep_before: Задержка перед кликом в секундах
        take_screenshot: Делать ли скриншот перед кликом
        screenshot_dir: Директория для сохранения скриншота
        screenshot_name: Имя файла скриншота
        highlight: Подсвечивать ли элемент перед кликом
        
    Returns:
        bool: True если клик выполнен успешно, False в противном случае
    """
    logger.info(f"🖱️ {log_message}...")
    
    # Добавляем задержку перед действием
    if sleep_before > 0:
        time.sleep(sleep_before)
    
    try:
        # Создаем локатор
        element = page.locator(selector)
        
        # Проверяем видимость элемента
        if element.is_visible(timeout=timeout):
            # Делаем скриншот перед кликом, если нужно
            if take_screenshot and screenshot_dir and screenshot_name:
                screenshot_path = os.path.join(screenshot_dir, screenshot_name)
                page.screenshot(path=screenshot_path)
                logger.info(f"📸 Сделан скриншот перед кликом: {screenshot_path}")
            
            # Подсвечиваем элемент, если нужно
            if highlight:
                try:
                    element.highlight()
                except:
                    pass  # Игнорируем ошибку, если запущено в headless режиме
            
            # Кликаем по элементу
            element.click()
            logger.info(f"✅ {log_message} - успешно")
            return True
        else:
            logger.error(f"❌ Элемент не найден: {selector}")
            return False
    except Exception as e:
        logger.error(f"❌ Ошибка при клике на элемент: {str(e)}")
        return False

def fill_input(
    page: Page, 
    selector: str, 
    value: str,
    log_message: str = "Заполняем поле", 
    timeout: int = 30000,
    sleep_before: float = 0.5,
    highlight: bool = True
) -> bool:
    """
    Находит поле ввода на странице и заполняет его
    
    Args:
        page: Страница Playwright
        selector: Селектор поля ввода
        value: Значение для ввода
        log_message: Сообщение для логирования
        timeout: Таймаут ожидания элемента в миллисекундах
        sleep_before: Задержка перед вводом в секундах
        highlight: Подсвечивать ли элемент перед вводом
        
    Returns:
        bool: True если ввод выполнен успешно, False в противном случае
    """
    logger.info(f"✍️ {log_message}...")
    
    # Добавляем задержку перед действием
    if sleep_before > 0:
        time.sleep(sleep_before)
    
    try:
        # Создаем локатор
        input_field = page.locator(selector)
        
        # Проверяем видимость поля ввода
        if input_field.is_visible(timeout=timeout):
            # Подсвечиваем элемент, если нужно
            if highlight:
                try:
                    input_field.highlight()
                except:
                    pass  # Игнорируем ошибку, если запущено в headless режиме
            
            # Заполняем поле
            input_field.fill(value)
            logger.info(f"✅ {log_message} - успешно")
            return True
        else:
            logger.error(f"❌ Поле ввода не найдено: {selector}")
            return False
    except Exception as e:
        logger.error(f"❌ Ошибка при заполнении поля: {str(e)}")
        return False

def wait_for_element(
    page: Page, 
    selector: str, 
    log_message: str = "Ожидаем элемент", 
    timeout: int = 30000,
    state: str = "visible"
) -> bool:
    """
    Ожидает появления элемента на странице
    
    Args:
        page: Страница Playwright
        selector: Селектор элемента
        log_message: Сообщение для логирования
        timeout: Таймаут ожидания элемента в миллисекундах
        state: Состояние элемента для ожидания (visible, hidden, attached, detached)
        
    Returns:
        bool: True если элемент появился, False в противном случае
    """
    logger.info(f"⏱️ {log_message}...")
    
    try:
        # Создаем локатор
        element = page.locator(selector)
        
        # Ожидаем элемент
        element.wait_for(state=state, timeout=timeout)
        logger.info(f"✅ {log_message} - успешно")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка при ожидании элемента: {str(e)}")
        return False

def check_element_exists(
    page: Page, 
    selector: str, 
    log_message: str = "Проверяем наличие элемента", 
    timeout: int = 5000
) -> bool:
    """
    Проверяет наличие элемента на странице
    
    Args:
        page: Страница Playwright
        selector: Селектор элемента
        log_message: Сообщение для логирования
        timeout: Таймаут ожидания элемента в миллисекундах
        
    Returns:
        bool: True если элемент найден, False в противном случае
    """
    logger.info(f"🔍 {log_message}...")
    
    try:
        # Создаем локатор
        element = page.locator(selector)
        
        # Проверяем видимость элемента
        is_visible = element.is_visible(timeout=timeout)
        
        if is_visible:
            logger.info(f"✅ {log_message} - элемент найден")
        else:
            logger.info(f"ℹ️ {log_message} - элемент не найден")
            
        return is_visible
    except Exception as e:
        logger.error(f"❌ Ошибка при проверке наличия элемента: {str(e)}")
        return False 