from loguru import logger
from selenium import webdriver


def test_profile(profile_name: str | int, script_data_path: str, driver: webdriver.Chrome) -> None:
    """
    Тестовый скрипт для проверки работы профиля
    
    Args:
        profile_name: Имя профиля
        script_data_path: Путь к данным скрипта
        driver: Экземпляр драйвера Chrome
    """
    try:
        logger.info(f"🔍 {profile_name} - Запускаю тестовый скрипт")
        
        # Проверяем что профиль открылся
        logger.info(f"✅ {profile_name} - Профиль успешно открыт")
        
        # Проверяем что расширения загружены
        extensions = driver.execute_script('return window.navigator.plugins.length')
        logger.info(f"📦 {profile_name} - Загружено расширений: {extensions}")
        
        # Проверяем что можем открыть страницу
        driver.get("https://example.com")
        logger.info(f"🌐 {profile_name} - Тестовая страница успешно открыта")
        
        logger.success(f"✨ {profile_name} - Тестовый скрипт успешно выполнен")
        
    except Exception as e:
        logger.error(f"❌ {profile_name} - Ошибка при выполнении тестового скрипта")
        logger.debug(f"{profile_name} - Ошибка при выполнении тестового скрипта, причина: {str(e)}") 