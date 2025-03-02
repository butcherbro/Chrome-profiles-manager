"""
Скрипт для автоматизации импорта кошелька MetaMask через Playwright
"""
import time
import os
from loguru import logger
from playwright.sync_api import Page, expect, TimeoutError, BrowserContext
from src.utils.constants import DEFAULT_EXTENSIONS_PATH
from src.chrome.scripts.test_extension import test_extension

METAMASK_ID = "nkbihfbeogaeaoehlefnkodbefgpgknn"

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
            
        # Проверяем наличие расширения в папке
        metamask_path = os.path.join(DEFAULT_EXTENSIONS_PATH, METAMASK_ID)
        if not os.path.exists(metamask_path):
            logger.error("❌ Расширение MetaMask не найдено в папке расширений")
            return False
            
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
                    return True
            except TimeoutError:
                pass
            
            # Шаг 4: Проверка загрузки страницы импорта
            try:
                import_title = metamask_page.get_by_text("Import with Secret Recovery Phrase")
                if import_title.is_visible(timeout=5000):
                    logger.success("✅ Страница импорта открыта")
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
                    
                    # Ждем чекбокс и кликаем
                    checkbox = metamask_page.locator('label[class="onboarding__terms-label"]')
                    if checkbox.is_visible(timeout=5000):
                        checkbox.click()
                        time.sleep(1)
                        
                        # Кликаем кнопку импорта
                        import_button = metamask_page.locator("//button[contains(@data-testid,'onboarding-import-wallet')]")
                        if import_button.is_visible(timeout=5000):
                            import_button.click()
                            time.sleep(1)
                            
                            # Проверяем что открылась страница импорта
                            if import_title.is_visible(timeout=5000):
                                logger.success("✅ Страница импорта открыта через альтернативный путь")
                                return True
                                
            except TimeoutError:
                logger.error("❌ Не удалось открыть страницу импорта")
                return False
            
            logger.error("❌ Не удалось открыть страницу импорта")
            return False
            
        except Exception as e:
            logger.error(f"❌ Ошибка при загрузке страницы: {str(e)}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Ошибка при выполнении скрипта: {str(e)}")
        return False 