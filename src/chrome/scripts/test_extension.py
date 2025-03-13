#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Модуль для тестирования расширений Chrome через Playwright
"""

import os
import time
from loguru import logger
from playwright.sync_api import Page, TimeoutError

def test_extension(page: Page, extension_ids: list[str]) -> bool:
    """
    Проверяет доступность расширений в браузере
    
    Args:
        page: Страница Playwright
        extension_ids: Список ID расширений для проверки
        
    Returns:
        bool: True если все расширения доступны
    """
    results = {}
    
    try:
        # Сначала открываем пустую страницу
        page.goto("about:blank", timeout=10000)
        time.sleep(1)  # Даем время на загрузку
        
        for ext_id in extension_ids:
            logger.info(f"🔍 Проверяем расширение {ext_id}...")
            
            # Пробуем разные URL для расширения
            urls_to_try = [
                f"chrome-extension://{ext_id}/popup.html",
                f"chrome-extension://{ext_id}/index.html",
                f"chrome-extension://{ext_id}/home.html",
                f"chrome-extension://{ext_id}/home.html#welcome",
                f"chrome-extension://{ext_id}/home.html#unlock"
            ]
            
            success = False
            for url in urls_to_try:
                try:
                    page.goto(url, timeout=10000)
                    
                    # Ждем загрузки страницы
                    page.wait_for_load_state("domcontentloaded", timeout=5000)
                    
                    # Делаем скриншот
                    os.makedirs("screenshots", exist_ok=True)
                    page.screenshot(path=f"screenshots/extension_{ext_id}_{url.split('/')[-1].split('.')[0]}.png")
                    
                    logger.success(f"✅ Расширение {ext_id} доступно через {url}")
                    success = True
                    break
                except Exception as e:
                    logger.debug(f"⚠️ Не удалось открыть {url}: {str(e)}")
                    continue
            
            if not success:
                logger.warning(f"⚠️ Не удалось открыть ни один URL для расширения {ext_id}")
                
            results[ext_id] = success
            
            # Возвращаемся на пустую страницу после проверки
            try:
                page.goto("about:blank", timeout=5000)
            except:
                pass
        
        # Выводим результаты
        logger.info("📊 Результаты проверки расширений:")
        all_success = True
        for ext_id, success in results.items():
            status = "✅" if success else "❌"
            logger.info(f"{status} {ext_id}")
            if not success:
                all_success = False
        
        return all_success
        
    except Exception as e:
        logger.error(f"❌ Ошибка при проверке расширений: {str(e)}")
        return False

def test_metamask(page: Page) -> bool:
    """
    Специализированная функция для тестирования MetaMask
    
    Args:
        page: Страница Playwright
        
    Returns:
        bool: True если MetaMask доступен
    """
    from src.utils.constants import METAMASK_ID
    
    try:
        # Сначала открываем пустую страницу
        page.goto("about:blank", timeout=10000)
        time.sleep(1)  # Даем время на загрузку
        
        # Пробуем разные URL для MetaMask
        urls_to_try = [
            f"chrome-extension://{METAMASK_ID}/home.html#welcome",
            f"chrome-extension://{METAMASK_ID}/home.html#unlock",
            f"chrome-extension://{METAMASK_ID}/home.html",
            f"chrome-extension://{METAMASK_ID}/popup.html"
        ]
        
        for url in urls_to_try:
            try:
                logger.info(f"🦊 Пробуем открыть MetaMask через {url}...")
                page.goto(url, timeout=10000)
                
                # Ждем загрузки страницы
                page.wait_for_load_state("domcontentloaded", timeout=5000)
                
                # Делаем скриншот
                os.makedirs("screenshots", exist_ok=True)
                page.screenshot(path=f"screenshots/metamask_{url.split('/')[-1].split('.')[0].split('#')[-1]}.png")
                
                # Проверяем, что это действительно MetaMask
                try:
                    # Проверяем наличие логотипа или характерных элементов
                    logo = page.locator("img[alt='MetaMask']")
                    if logo.is_visible(timeout=2000):
                        logger.success(f"✅ MetaMask доступен через {url}")
                        return True
                except:
                    # Проверяем по тексту
                    if "MetaMask" in page.content():
                        logger.success(f"✅ MetaMask доступен через {url}")
                        return True
                    else:
                        logger.debug(f"⚠️ Страница открылась, но не похожа на MetaMask")
                        continue
                
            except Exception as e:
                logger.debug(f"⚠️ Не удалось открыть {url}: {str(e)}")
                continue
        
        logger.warning(f"⚠️ Не удалось открыть ни один URL для MetaMask")
        return False
        
    except Exception as e:
        logger.error(f"❌ Ошибка при проверке MetaMask: {str(e)}")
        return False 