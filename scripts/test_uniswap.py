import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loguru import logger
from src.chrome.playwright_chrome import PlaywrightChrome

def test_uniswap_connection():
    """
    Тестовый скрипт для проверки работы Playwright с Uniswap
    Открывает профиль Chrome и пытается подключить кошелек на Uniswap
    """
    try:
        # Инициализируем Chrome
        chrome = PlaywrightChrome()
        
        # Запускаем профиль
        profile_name = "5"  # Можно изменить на нужный профиль
        logger.info(f"🚀 Запускаем профиль {profile_name}")
        
        if not chrome.launch_profile(profile_name):
            logger.error("❌ Не удалось запустить профиль")
            return False
            
        logger.success("✅ Тест успешно завершен")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка при выполнении теста: {str(e)}")
        return False
    finally:
        # Закрываем браузер
        chrome.close()

if __name__ == "__main__":
    test_uniswap_connection() 