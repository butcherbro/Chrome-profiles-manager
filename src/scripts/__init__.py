#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Инициализация скриптов для системы запуска Chrome Profile Manager.
"""

from loguru import logger
from src.scripts.metamask_import import register_script as register_metamask_import
from src.scripts.test_open_tab import register_script as register_test_open_tab
from src.scripts.rabby_import_playwright import register_script as register_rabby_import

def register_all_scripts(pw):
    """
    Регистрирует все доступные скрипты в системе запуска
    
    Args:
        pw: Экземпляр класса PlaywrightChrome
    """
    logger.info("📝 Регистрация скриптов в системе запуска...")
    
    # Регистрируем скрипт импорта MetaMask
    register_metamask_import(pw)
    
    # Регистрируем скрипт теста открытия вкладки
    register_test_open_tab(pw)
    
    # Регистрируем скрипт импорта Rabby
    register_rabby_import(pw)
    
    logger.info(f"✅ Зарегистрировано скриптов: {len(pw.scripts)}")
    for script_name, script_info in pw.scripts.items():
        logger.info(f"  - {script_info['human_name']} ({script_name})") 