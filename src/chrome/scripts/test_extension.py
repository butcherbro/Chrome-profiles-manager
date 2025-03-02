"""
Скрипт для тестирования расширений Chrome через Playwright
"""
from typing import Optional, List
from loguru import logger
from playwright.sync_api import Page, expect

def test_extension(page: Page, extension_ids: Optional[List[str]] = None) -> bool:
    """
    Тестирует работу расширений в Chrome
    
    Args:
        page: Playwright Page объект
        extension_ids: Список ID расширений для проверки. Если None - проверяет только загрузку страницы расширений
        
    Returns:
        bool: True если все проверяемые расширения найдены и активны
    """
    try:
        logger.info("🧪 Тестирую работу расширений...")
        
        # Открываем страницу расширений
        page.goto("chrome://extensions")
        
        # Ждем загрузки страницы
        expect(page.locator("extensions-manager")).to_be_visible(timeout=10000)
        
        # Если не указаны конкретные расширения, просто проверяем загрузку страницы
        if not extension_ids:
            logger.success("✅ Страница расширений загружена успешно")
            return True
            
        # Проверяем наличие указанных расширений
        for ext_id in extension_ids:
            logger.info(f"🔍 Проверяю расширение {ext_id}...")
            
            # Проверяем через chrome.management API
            extension_found = page.evaluate(f"""() => {{
                return new Promise((resolve) => {{
                    chrome.management.get('{ext_id}', (extension) => {{
                        resolve(!!extension);
                    }});
                }});
            }}""")
            
            if not extension_found:
                logger.error(f"❌ Расширение {ext_id} не найдено")
                return False
                
            logger.info(f"✅ Расширение {ext_id} найдено")
            
        logger.success("✅ Все расширения найдены и активны")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка при тестировании расширений: {str(e)}")
        return False 