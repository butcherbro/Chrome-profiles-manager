#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Инициализация скриптов для системы запуска Chrome Profile Manager.
"""

from loguru import logger
from src.scripts.metamask_import import register_script as register_metamask_import
from src.scripts.test_open_tab import register_script as register_test_open_tab

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
    
    logger.info(f"✅ Зарегистрировано скриптов: {len(pw.scripts)}")
    for script_name, script_info in pw.scripts.items():
        logger.info(f"  - {script_info['human_name']} ({script_name})") 