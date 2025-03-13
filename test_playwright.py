#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Тестовый скрипт для проверки работы Playwright с Chrome
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

def check_extensions(pw, extension_ids):
    """
    Проверяет доступность расширений в браузере
    
    Args:
        pw: Экземпляр PlaywrightChrome
        extension_ids: Список ID расширений для проверки
        
    Returns:
        dict: Словарь с результатами проверки {extension_id: success}
    """
    results = {}
    
    # Создаем новую страницу для проверки расширений
    try:
        # Создаем новую страницу для тестирования
        test_page = pw.browser.contexts[0].new_page()
        logger.info("✅ Создана новая страница для проверки расширений")
        
        # Открываем нейтральную страницу для начала
        test_page.goto("about:blank", timeout=10000)
        
        for ext_id in extension_ids:
            logger.info(f"🔍 Проверяем расширение {ext_id}...")
            try:
                # Пробуем открыть страницу расширения
                ext_url = f"chrome-extension://{ext_id}/popup.html"
                test_page.goto(ext_url, timeout=10000)
                
                # Делаем скриншот
                os.makedirs("screenshots", exist_ok=True)
                test_page.screenshot(path=f"screenshots/extension_{ext_id}.png")
                
                logger.success(f"✅ Расширение {ext_id} доступно")
                results[ext_id] = True
            except Exception as e:
                logger.warning(f"⚠️ Не удалось открыть расширение {ext_id}: {str(e)}")
                try:
                    # Пробуем альтернативный URL
                    ext_url = f"chrome-extension://{ext_id}/index.html"
                    test_page.goto(ext_url, timeout=10000)
                    
                    # Делаем скриншот
                    test_page.screenshot(path=f"screenshots/extension_{ext_id}_index.png")
                    
                    logger.success(f"✅ Расширение {ext_id} доступно через index.html")
                    results[ext_id] = True
                except Exception as e:
                    logger.warning(f"⚠️ Не удалось открыть расширение {ext_id} через index.html: {str(e)}")
                    
                    # Пробуем еще один альтернативный URL
                    try:
                        ext_url = f"chrome-extension://{ext_id}/home.html"
                        test_page.goto(ext_url, timeout=10000)
                        
                        # Делаем скриншот
                        test_page.screenshot(path=f"screenshots/extension_{ext_id}_home.png")
                        
                        logger.success(f"✅ Расширение {ext_id} доступно через home.html")
                        results[ext_id] = True
                    except Exception as e:
                        logger.warning(f"⚠️ Не удалось открыть расширение {ext_id} через home.html: {str(e)}")
                        results[ext_id] = False
                        
                    # Возвращаемся на нейтральную страницу после ошибки
                    try:
                        test_page.goto("about:blank", timeout=5000)
                    except:
                        pass
        
        # Закрываем тестовую страницу
        try:
            test_page.close()
        except:
            pass
            
    except Exception as e:
        logger.error(f"❌ Ошибка при проверке расширений: {str(e)}")
    
    return results

def main():
    """
    Основная функция для тестирования Playwright с Chrome
    """
    # Получаем аргументы командной строки
    browser_type = sys.argv[1] if len(sys.argv) > 1 else "chrome"
    profile_name = sys.argv[2] if len(sys.argv) > 2 else "0"
    
    logger.info(f"🚀 Запускаем тест Playwright с {browser_type}, профиль {profile_name}")
    
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
            
        # Открываем тестовую страницу сначала
        try:
            logger.info("🌐 Открываем тестовую страницу...")
            pw.page.goto("about:blank", timeout=10000)  # Сначала открываем пустую страницу
            time.sleep(1)  # Даем время на загрузку
            
            # Теперь пробуем открыть Google
            pw.page.goto("https://www.google.com", timeout=30000)
            logger.info("✅ Тестовая страница открыта успешно")
            
            # Делаем скриншот тестовой страницы
            logger.info("📸 Делаем скриншот тестовой страницы...")
            os.makedirs("screenshots", exist_ok=True)
            pw.page.screenshot(path="screenshots/test_page.png")
            logger.info("✅ Скриншот тестовой страницы сохранен")
        except Exception as e:
            logger.warning(f"⚠️ Не удалось открыть тестовую страницу: {str(e)}")
            # Пробуем открыть другую страницу
            try:
                logger.info("🌐 Пробуем открыть альтернативную тестовую страницу...")
                pw.page.goto("https://example.com", timeout=30000)
                logger.info("✅ Альтернативная тестовая страница открыта успешно")
                
                # Делаем скриншот альтернативной страницы
                logger.info("📸 Делаем скриншот альтернативной страницы...")
                pw.page.screenshot(path="screenshots/alternative_page.png")
                logger.info("✅ Скриншот альтернативной страницы сохранен")
            except Exception as e:
                logger.error(f"❌ Не удалось открыть ни одну тестовую страницу: {str(e)}")
        
        # Проверяем, что браузер все еще открыт
        if not pw.browser or not pw.browser.contexts:
            logger.error("❌ Браузер закрыт или недоступен")
            return
        
        # Получаем список расширений из профиля
        extensions_path = os.path.join(pw._PlaywrightChrome__get_profile_path(profile_name), "Extensions")
        extension_ids = []
        
        if os.path.exists(extensions_path):
            extension_ids = [ext_id for ext_id in os.listdir(extensions_path) 
                            if os.path.isdir(os.path.join(extensions_path, ext_id)) and ext_id != "Temp"]
            logger.info(f"📦 Найдено {len(extension_ids)} расширений: {extension_ids}")
        else:
            logger.warning("⚠️ Папка с расширениями не найдена")
        
        # Проверяем все расширения
        if extension_ids:
            results = check_extensions(pw, extension_ids)
            
            # Выводим результаты
            logger.info("📊 Результаты проверки расширений:")
            for ext_id, success in results.items():
                status = "✅" if success else "❌"
                logger.info(f"{status} {ext_id}")
        
        # Проверяем, что браузер все еще открыт
        if not pw.browser or not pw.browser.contexts:
            logger.error("❌ Браузер закрыт или недоступен")
            return
        
        # Специально проверяем MetaMask в отдельной странице
        logger.info(f"🦊 Проверяем MetaMask (ID: {METAMASK_ID})...")
        
        try:
            # Проверяем, что браузер все еще открыт
            if not pw.browser or not pw.browser.contexts:
                logger.error("❌ Браузер закрыт или недоступен")
                return
                
            # Получаем контекст
            context = pw.browser.contexts[0]
            
            # Создаем новую страницу для MetaMask
            metamask_page = context.new_page()
            logger.info("✅ Создана новая страница для проверки MetaMask")
            
            # Сначала открываем пустую страницу
            metamask_page.goto("about:blank", timeout=10000)
            time.sleep(1)  # Даем время на загрузку
            
            # Пробуем открыть страницу welcome
            try:
                metamask_url = f"chrome-extension://{METAMASK_ID}/home.html#welcome"
                metamask_page.goto(metamask_url, timeout=30000)
                logger.info("✅ Страница MetaMask welcome открыта")
                
                # Делаем скриншот страницы MetaMask
                logger.info("📸 Делаем скриншот MetaMask welcome...")
                metamask_page.screenshot(path="screenshots/metamask_welcome.png")
                metamask_success = True
            except Exception as e:
                logger.warning(f"⚠️ Не удалось открыть страницу welcome: {str(e)}")
                try:
                    # Пробуем открыть страницу unlock
                    metamask_url = f"chrome-extension://{METAMASK_ID}/home.html#unlock"
                    metamask_page.goto(metamask_url, timeout=30000)
                    logger.info("✅ Страница разблокировки MetaMask открыта")
                    
                    # Делаем скриншот страницы MetaMask
                    logger.info("📸 Делаем скриншот MetaMask unlock...")
                    metamask_page.screenshot(path="screenshots/metamask_unlock.png")
                    metamask_success = True
                except Exception as e:
                    logger.warning(f"⚠️ Не удалось открыть страницу unlock: {str(e)}")
                    try:
                        # Пробуем открыть основную страницу
                        metamask_url = f"chrome-extension://{METAMASK_ID}/popup.html"
                        metamask_page.goto(metamask_url, timeout=30000)
                        logger.info("✅ Страница popup MetaMask открыта")
                        
                        # Делаем скриншот страницы MetaMask
                        logger.info("📸 Делаем скриншот MetaMask popup...")
                        metamask_page.screenshot(path="screenshots/metamask_popup.png")
                        metamask_success = True
                    except Exception as e:
                        logger.warning(f"⚠️ Не удалось открыть страницу popup: {str(e)}")
                        
                        # Пробуем открыть любую доступную страницу MetaMask
                        try:
                            metamask_url = f"chrome-extension://{METAMASK_ID}/home.html"
                            metamask_page.goto(metamask_url, timeout=30000)
                            logger.info("✅ Страница home MetaMask открыта")
                            
                            # Делаем скриншот страницы MetaMask
                            logger.info("📸 Делаем скриншот MetaMask home...")
                            metamask_page.screenshot(path="screenshots/metamask_home.png")
                            metamask_success = True
                        except Exception as e:
                            logger.error(f"❌ Не удалось открыть ни одну страницу MetaMask: {str(e)}")
                            metamask_success = False
            
            # Закрываем страницу MetaMask
            try:
                metamask_page.close()
            except:
                pass
                
            # Выводим результат проверки MetaMask
            if metamask_success:
                logger.success("✅ MetaMask успешно проверен")
            else:
                logger.error("❌ Не удалось проверить MetaMask")
                
        except Exception as e:
            logger.error(f"❌ Ошибка при проверке MetaMask: {str(e)}")
        
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