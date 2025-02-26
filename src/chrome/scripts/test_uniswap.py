import time
from loguru import logger
from selenium import webdriver


def test_uniswap(profile_name: str | int, script_data_path: str, driver: webdriver.Chrome) -> None:
    """
    Тестовый скрипт для проверки работы с Uniswap
    
    Args:
        profile_name: Имя профиля
        script_data_path: Путь к данным скрипта
        driver: Экземпляр драйвера Chrome
    """
    try:
        logger.info(f"🔍 {profile_name} - Запускаю тест Uniswap")
        
        # Переходим на Uniswap
        logger.info(f"🌐 {profile_name} - Переходим на Uniswap...")
        driver.get("https://app.uniswap.org/swap")
        time.sleep(2)  # Даем время на загрузку
        
        # Ищем кнопку Connect Wallet
        logger.info(f"🔍 {profile_name} - Ищем кнопку Connect Wallet...")
        connect_button = driver.find_element("xpath", "//button[contains(@data-testid,'navbar-connect-wallet')]")
        
        # Кликаем по кнопке
        logger.info(f"🖱️ {profile_name} - Нажимаем кнопку Connect Wallet...")
        connect_button.click()
        time.sleep(2)  # Даем время на открытие модального окна
        
        logger.success(f"✨ {profile_name} - Тест Uniswap успешно выполнен")
        
    except Exception as e:
        logger.error(f"❌ {profile_name} - Ошибка при выполнении теста Uniswap")
        logger.debug(f"{profile_name} - Ошибка при выполнении теста Uniswap, причина: {str(e)}") 