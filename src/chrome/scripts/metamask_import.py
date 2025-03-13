#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Скрипт для автоматизации импорта кошелька MetaMask через Playwright
"""

import time
import os
from loguru import logger
from playwright.sync_api import Page, expect, TimeoutError, BrowserContext
from src.utils.constants import METAMASK_ID
from src.chrome.scripts.test_extension import test_extension

def verify_metamask_extension(context: BrowserContext, check_extension: bool = True) -> bool:
    """
    Проверяет наличие и корректную загрузку расширения MetaMask
    
    Args:
        context: Контекст браузера Playwright
        check_extension: Флаг, определяющий нужно ли проверять расширение
        
    Returns:
        bool: True если расширение найдено и загружено или проверка отключена
    """
    try:
        # Если проверка отключена, сразу возвращаем True
        if not check_extension:
            logger.info("ℹ️ Проверка расширений отключена")
            return True
            
        # Проверяем доступность расширения
        logger.info("🔍 Проверяю доступность MetaMask...")
        
        # Создаем новую страницу для проверки
        test_page = context.new_page()
        
        try:
            # Используем универсальную функцию проверки расширений
            if test_extension(test_page, [METAMASK_ID]):
                test_page.close()
                return True
                
            test_page.close()
            return False
            
        except Exception as e:
            logger.error(f"❌ Ошибка при проверке расширений: {str(e)}")
            test_page.close()
            return False
        
    except Exception as e:
        logger.error(f"❌ Ошибка при проверке MetaMask: {str(e)}")
        return False

def metamask_import_wallet(context: BrowserContext, check_extension: bool = True) -> bool:
    """
    Автоматизация импорта кошелька MetaMask
    
    Args:
        context: Контекст браузера Playwright
        check_extension: Флаг, определяющий нужно ли проверять расширение
        
    Returns:
        bool: True если импорт успешно начат
    """
    try:
        # Шаг 1: Проверка расширения (если включена)
        if not verify_metamask_extension(context, check_extension):
            return False
            
        # Шаг 2: Создание страницы и переход к импорту
        logger.info("🦊 Открываю страницу импорта MetaMask...")
        metamask_page = context.new_page()
        
        try:
            # Сначала открываем пустую страницу
            metamask_page.goto("about:blank", timeout=10000)
            time.sleep(1)  # Даем время на загрузку
            
            # Сразу переходим на страницу импорта
            metamask_page.goto(
                f"chrome-extension://{METAMASK_ID}/home.html#onboarding/import-with-recovery-phrase",
                wait_until="load",
                timeout=10000
            )
            
            # Шаг 3: Проверка, не импортирован ли уже кошелек
            try:
                account_menu = metamask_page.locator('[data-testid="account-menu-icon"]')
                if account_menu.is_visible(timeout=2000):
                    logger.info("✓ MetaMask уже настроен и разблокирован")
                    metamask_page.close()
                    return True
            except TimeoutError:
                pass
            
            # Шаг 4: Проверка загрузки страницы импорта
            try:
                import_title = metamask_page.get_by_text("Import with Secret Recovery Phrase")
                if import_title.is_visible(timeout=5000):
                    logger.success("✅ Страница импорта открыта")
                    
                    # Делаем скриншот страницы импорта
                    os.makedirs("screenshots", exist_ok=True)
                    metamask_page.screenshot(path="screenshots/metamask_import.png")
                    
                    return True
                else:
                    # Если не удалось открыть страницу импорта напрямую, 
                    # пробуем через стандартный путь
                    logger.info("⚠️ Пробую альтернативный путь...")
                    metamask_page.goto(
                        f"chrome-extension://{METAMASK_ID}/home.html#onboarding/welcome",
                        wait_until="load",
                        timeout=10000
                    )
                    
                    # Делаем скриншот страницы приветствия
                    metamask_page.screenshot(path="screenshots/metamask_welcome.png")
                    
                    # Ждем загрузки страницы
                    metamask_page.wait_for_load_state("networkidle", timeout=10000)
                    
                    # Ждем чекбокс и кликаем
                    checkbox = metamask_page.locator('label[class="onboarding__terms-label"]')
                    if checkbox.is_visible(timeout=5000):
                        logger.info("✅ Чекбокс с условиями использования найден")
                        checkbox.click()
                        time.sleep(1)
                        
                        # Кликаем кнопку импорта
                        import_button = metamask_page.locator("//button[contains(@data-testid,'onboarding-import-wallet')]")
                        if import_button.is_visible(timeout=5000):
                            logger.info("✅ Кнопка импорта найдена")
                            import_button.click()
                            time.sleep(1)
                            
                            # Проверяем что открылась страница импорта
                            if import_title.is_visible(timeout=5000):
                                logger.success("✅ Страница импорта открыта через альтернативный путь")
                                
                                # Делаем скриншот страницы импорта
                                metamask_page.screenshot(path="screenshots/metamask_import_alt.png")
                                
                                return True
                                
            except TimeoutError:
                logger.error("❌ Не удалось открыть страницу импорта")
                metamask_page.close()
                return False
            
            logger.error("❌ Не удалось открыть страницу импорта")
            metamask_page.close()
            return False
            
        except Exception as e:
            logger.error(f"❌ Ошибка при загрузке страницы: {str(e)}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Ошибка при выполнении скрипта: {str(e)}")
        return False

def fill_import_form(page: Page, seed_phrase: str, password: str) -> bool:
    """
    Заполняет форму импорта кошелька MetaMask
    
    Args:
        page: Страница Playwright с открытой формой импорта
        seed_phrase: Сид-фраза для импорта
        password: Пароль для нового кошелька
        
    Returns:
        bool: True если форма успешно заполнена и отправлена
    """
    try:
        # Проверяем, что мы на странице импорта
        import_title = page.get_by_text("Import with Secret Recovery Phrase")
        if not import_title.is_visible(timeout=5000):
            logger.error("❌ Страница импорта не открыта")
            return False
            
        logger.info("📝 Заполняю форму импорта...")
        
        # Заполняем сид-фразу
        seed_input = page.locator("//input[@placeholder='Paste Secret Recovery Phrase from clipboard']")
        if seed_input.is_visible(timeout=5000):
            seed_input.fill(seed_phrase)
            logger.info("✅ Сид-фраза введена")
        else:
            logger.error("❌ Поле для ввода сид-фразы не найдено")
            return False
            
        # Заполняем пароль
        password_input = page.locator("//input[@autocomplete='new-password']").first
        if password_input.is_visible(timeout=5000):
            password_input.fill(password)
            logger.info("✅ Пароль введен")
        else:
            logger.error("❌ Поле для ввода пароля не найдено")
            return False
            
        # Заполняем подтверждение пароля
        confirm_password_input = page.locator("//input[@autocomplete='new-password']").nth(1)
        if confirm_password_input.is_visible(timeout=5000):
            confirm_password_input.fill(password)
            logger.info("✅ Подтверждение пароля введено")
        else:
            logger.error("❌ Поле для подтверждения пароля не найдено")
            return False
            
        # Принимаем условия использования
        terms_checkbox = page.locator("//div[contains(@class, 'check-box')]").first
        if terms_checkbox.is_visible(timeout=5000):
            terms_checkbox.click()
            logger.info("✅ Условия использования приняты")
        else:
            logger.error("❌ Чекбокс с условиями использования не найден")
            return False
            
        # Нажимаем кнопку импорта
        import_button = page.locator("//button[contains(@data-testid, 'import-srp-confirm')]")
        if import_button.is_visible(timeout=5000):
            import_button.click()
            logger.info("✅ Кнопка импорта нажата")
        else:
            logger.error("❌ Кнопка импорта не найдена")
            return False
            
        # Ждем завершения импорта
        success_text = page.get_by_text("Congratulations")
        if success_text.is_visible(timeout=30000):
            logger.success("✅ Импорт успешно завершен")
            
            # Делаем скриншот страницы успешного импорта
            os.makedirs("screenshots", exist_ok=True)
            page.screenshot(path="screenshots/metamask_import_success.png")
            
            # Нажимаем кнопку "All Done"
            all_done_button = page.locator("//button[contains(@data-testid, 'onboarding-complete-done')]")
            if all_done_button.is_visible(timeout=5000):
                all_done_button.click()
                logger.info("✅ Кнопка 'All Done' нажата")
            
            return True
        else:
            logger.error("❌ Импорт не завершен")
            return False
            
    except Exception as e:
        logger.error(f"❌ Ошибка при заполнении формы импорта: {str(e)}")
        return False 