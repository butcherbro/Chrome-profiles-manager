#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Тестовый скрипт для автоматизации импорта кошелька MetaMask через Playwright
"""

import os
import sys
import time
from loguru import logger

from src.chrome.playwright_chrome import PlaywrightChrome
from src.utils.constants import METAMASK_ID

# Настройка логирования
logger.remove()
logger.add(sys.stderr, level="DEBUG")

def main():
    """
    Основная функция для тестирования импорта кошелька MetaMask
    """
    # Получаем аргументы командной строки
    profile_name = sys.argv[1] if len(sys.argv) > 1 else "0"
    
    logger.info(f"🚀 Запускаем тест импорта MetaMask для профиля {profile_name}")
    
    # Создаем экземпляр PlaywrightChrome
    pw = PlaywrightChrome()
    
    try:
        # Убиваем все процессы Chrome перед запуском
        from src.utils.helpers import kill_chrome_processes
        kill_chrome_processes()
        
        # Запускаем профиль
        logger.info(f"🚀 Запускаем профиль {profile_name}...")
        if not pw.launch_profile(profile_name):
            logger.error("❌ Не удалось запустить профиль")
            return
        
        logger.info("✅ Профиль успешно запущен")
        
        # Даем время на полную загрузку расширений
        logger.info("⏳ Ждем 5 секунд для полной загрузки расширений...")
        time.sleep(5)
        
        # Проверяем, что браузер все еще открыт
        if not pw.browser or not pw.browser.contexts:
            logger.error("❌ Браузер закрыт или недоступен")
            return
        
        # Получаем контекст
        context = pw.browser.contexts[0]
        
        # Создаем новую страницу для MetaMask
        logger.info("🦊 Создаем новую страницу для MetaMask...")
        metamask_page = context.new_page()
        logger.info("✅ Создана новая страница для MetaMask")
        
        # Переходим на страницу приветствия MetaMask
        logger.info("🦊 Переходим на страницу приветствия MetaMask...")
        try:
            # Переходим на страницу MetaMask
            metamask_url = f"chrome-extension://{METAMASK_ID}/home.html#onboarding/welcome"
            metamask_page.goto(metamask_url, timeout=30000)
            logger.info("✅ Страница приветствия MetaMask открыта")
            
            # Делаем скриншот страницы приветствия
            logger.info("📸 Делаем скриншот страницы приветствия...")
            os.makedirs("screenshots", exist_ok=True)
            metamask_page.screenshot(path="screenshots/metamask_welcome.png")
            
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
                    logger.info("📸 Делаем скриншот текущей страницы...")
                    metamask_page.screenshot(path="screenshots/metamask_after_import_click.png")
                    
                    # Проверяем URL страницы
                    current_url = metamask_page.url
                    logger.info(f"🔍 Текущий URL: {current_url}")
                    
                    # Проверяем, что открылась страница импорта по URL
                    if "import-with-recovery-phrase" in current_url:
                        logger.success("✅ Страница импорта открыта (проверка по URL)")
                        
                        # Делаем скриншот страницы импорта
                        logger.info("📸 Делаем скриншот страницы импорта...")
                        metamask_page.screenshot(path="screenshots/metamask_import.png")
                        
                        # Проверяем наличие полей для ввода
                        seed_phrase_textarea = metamask_page.locator('textarea[data-testid="import-srp-text"]')
                        if seed_phrase_textarea.is_visible(timeout=5000):
                            logger.success("✅ Поле для ввода seed-фразы найдено")
                        else:
                            logger.error("❌ Поле для ввода seed-фразы не найдено")
                    else:
                        # Пробуем найти заголовок страницы импорта
                        try:
                            # Используем разные селекторы для поиска заголовка
                            import_title = metamask_page.get_by_text("Import with Secret Recovery Phrase")
                            if import_title.is_visible(timeout=5000):
                                logger.success("✅ Страница импорта открыта (проверка по тексту)")
                                
                                # Делаем скриншот страницы импорта
                                logger.info("📸 Делаем скриншот страницы импорта...")
                                metamask_page.screenshot(path="screenshots/metamask_import.png")
                            else:
                                # Пробуем другой селектор
                                import_title = metamask_page.locator('h2:has-text("Import with Secret Recovery Phrase")')
                                if import_title.is_visible(timeout=5000):
                                    logger.success("✅ Страница импорта открыта (проверка по заголовку)")
                                    
                                    # Делаем скриншот страницы импорта
                                    logger.info("📸 Делаем скриншот страницы импорта...")
                                    metamask_page.screenshot(path="screenshots/metamask_import.png")
                                else:
                                    logger.error("❌ Не удалось открыть страницу импорта")
                        except Exception as e:
                            logger.error(f"❌ Ошибка при проверке страницы импорта: {str(e)}")
                else:
                    logger.error("❌ Кнопка импорта не найдена")
            else:
                logger.error("❌ Чекбокс с условиями использования не найден")
                
                # Проверяем, может быть кошелек уже импортирован
                account_menu = metamask_page.locator('[data-testid="account-menu-icon"]')
                if account_menu.is_visible(timeout=2000):
                    logger.info("✓ MetaMask уже настроен и разблокирован")
                    
                    # Делаем скриншот главной страницы
                    logger.info("📸 Делаем скриншот главной страницы...")
                    metamask_page.screenshot(path="screenshots/metamask_main.png")
                else:
                    # Проверяем, может быть это страница разблокировки
                    unlock_title = metamask_page.get_by_text("Welcome Back!")
                    if unlock_title.is_visible(timeout=2000):
                        logger.info("✓ MetaMask требует разблокировки")
                        
                        # Делаем скриншот страницы разблокировки
                        logger.info("📸 Делаем скриншот страницы разблокировки...")
                        metamask_page.screenshot(path="screenshots/metamask_unlock.png")
                    else:
                        logger.error("❌ Не удалось определить состояние MetaMask")
            
        except Exception as e:
            logger.error(f"❌ Ошибка при работе с MetaMask: {str(e)}")
        
        # Ждем, чтобы увидеть результат
        logger.info("⏳ Ждем 10 секунд...")
        time.sleep(10)
        
        logger.success("✅ Тест успешно завершен")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при выполнении теста: {str(e)}")
    finally:
        # Закрываем браузер
        logger.info("🔒 Закрываем браузер...")
        pw.close()

if __name__ == "__main__":
    main() 