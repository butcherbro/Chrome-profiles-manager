from src.chrome.playwright_chrome import PlaywrightChrome
import time
from loguru import logger


def test_launch_profile():
    """Тест запуска профиля Chrome через Playwright"""
    chrome = PlaywrightChrome()
    
    try:
        # Запускаем профиль 5
        logger.info("Запускаем профиль 5...")
        if not chrome.launch_profile("5", headless=False):
            logger.error("Не удалось запустить профиль")
            return
            
        # Переходим на Uniswap
        logger.info("Переходим на Uniswap...")
        chrome.page.goto("https://app.uniswap.org/swap", wait_until="networkidle")
        time.sleep(10)  # Увеличиваем время ожидания загрузки страницы
        
        # Шаг 1: Ищем кнопку Connect Wallet
        logger.info("Шаг 1: Ищем кнопку Connect Wallet...")
        # Используем более надежный селектор
        connect_button = chrome.page.locator('button:has-text("Connect")')
        if connect_button.is_visible():
            logger.success("Кнопка Connect Wallet найдена")
            
            # Шаг 2: Нажимаем кнопку Connect Wallet
            logger.info("Шаг 2: Нажимаем кнопку Connect Wallet...")
            connect_button.click()
            logger.success("Кнопка Connect Wallet успешно нажата")
            
            # Шаг 3: Ждем появления кнопки MetaMask
            logger.info("Шаг 3: Ждем появления кнопки MetaMask...")
            metamask_button = chrome.page.wait_for_selector('button:has-text("MetaMask")', timeout=30000)
            logger.info("Шаг 4: Нажимаем кнопку MetaMask...")
            metamask_button.click()
            logger.success("Кнопка MetaMask успешно нажата")
            
            # Шаг 5: Ждем подключения MetaMask
            logger.info("Шаг 5: Ждем подключения MetaMask...")
            time.sleep(5)  # Даем время на появление окна MetaMask
        else:
            logger.error("Кнопка Connect Wallet не найдена или не видима")
        
        # Держим браузер открытым для проверки
        logger.info("Браузер запущен и готов к работе. Для завершения нажмите Ctrl+C")
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Завершение работы...")
    except Exception as e:
        logger.error(f"Произошла ошибка: {str(e)}")
    finally:
        chrome.close()


if __name__ == "__main__":
    test_launch_profile() 