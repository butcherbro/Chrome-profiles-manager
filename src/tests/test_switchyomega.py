"""
Модуль для тестирования расширения SwitchyOmega с использованием Playwright
"""
import os
import time
from pathlib import Path
from loguru import logger
from playwright.sync_api import sync_playwright, Page, BrowserContext

from src.utils.helpers import kill_chrome_processes
from src.utils.constants import CHROME_DATA_PATH

class SwitchyOmegaTester:
    """Класс для тестирования SwitchyOmega"""
    
    def __init__(self):
        """Инициализация тестера"""
        self.profile_path = None
        self.context = None
        self.page = None
        
    def test_profile(self, profile_name: str) -> bool:
        """
        Тестирует SwitchyOmega в указанном профиле
        
        Args:
            profile_name: Имя профиля
            
        Returns:
            bool: True если тест успешен
        """
        try:
            # Закрываем все процессы Chrome
            logger.info("Закрываю все процессы Chrome...")
            kill_chrome_processes()
            time.sleep(2)
            
            # Формируем путь к профилю
            self.profile_path = os.path.join(CHROME_DATA_PATH, f"Profile {profile_name}")
            
            # Запускаем тест
            with sync_playwright() as p:
                # Запускаем браузер с профилем
                logger.info(f"Запускаю профиль {profile_name}...")
                self.context = self._launch_browser(p)
                if not self.context:
                    return False
                    
                # Получаем страницу
                self.page = self.context.pages[0]
                if not self.page:
                    self.page = self.context.new_page()
                
                # Тестируем расширение
                result = self._test_extension()
                
                # Закрываем браузер
                self.context.close()
                
                return result
                
        except Exception as e:
            logger.error(f"❌ Ошибка при тестировании профиля {profile_name}")
            logger.debug(f"Причина: {str(e)}")
            return False
            
        finally:
            # Убиваем процессы Chrome
            kill_chrome_processes()
    
    def _launch_browser(self, playwright) -> BrowserContext:
        """Запускает браузер с нужными параметрами"""
        try:
            # Получаем список расширений
            extensions = []
            extensions_path = os.path.join(self.profile_path, "Extensions")
            
            if os.path.exists(extensions_path):
                for ext_id in os.listdir(extensions_path):
                    ext_path = os.path.join(extensions_path, ext_id)
                    if os.path.isdir(ext_path):
                        # Получаем последнюю версию расширения
                        versions = [v for v in os.listdir(ext_path) if os.path.isdir(os.path.join(ext_path, v))]
                        if versions:
                            latest_version = sorted(versions)[-1]
                            extensions.append(os.path.join(ext_path, latest_version))
            
            # Запускаем браузер
            context = playwright.chromium.launch_persistent_context(
                user_data_dir=self.profile_path,
                headless=False,
                args=[
                    f"--load-extension={ext_path}" for ext_path in extensions
                ]
            )
            
            logger.success(f"✅ Браузер успешно запущен")
            return context
            
        except Exception as e:
            logger.error(f"❌ Ошибка при запуске браузера")
            logger.debug(f"Причина: {str(e)}")
            return None
    
    def _test_extension(self) -> bool:
        """Тестирует расширение SwitchyOmega"""
        try:
            # Переходим на страницу расширений
            logger.info("Открываю страницу расширений...")
            self.page.goto("chrome://extensions/")
            time.sleep(5)  # Увеличиваем время ожидания
            
            # Делаем скриншот страницы
            self.page.screenshot(path="debug_extensions.png")
            logger.info("📸 Сделан скриншот страницы расширений (debug_extensions.png)")
            
            # Ищем карточку SwitchyOmega
            logger.info("Ищу карточку SwitchyOmega...")
            
            # Пробуем разные локаторы
            cards = []
            try:
                cards = self.page.locator('extensions-item').all()
                logger.info(f"Найдено расширений через extensions-item: {len(cards)}")
            except:
                pass
                
            if not cards:
                try:
                    cards = self.page.locator('div[role="listitem"]').all()
                    logger.info(f"Найдено расширений через div[role=listitem]: {len(cards)}")
                except:
                    pass
            
            if not cards:
                try:
                    cards = self.page.locator('div.extension-list-item').all()
                    logger.info(f"Найдено расширений через div.extension-list-item: {len(cards)}")
                except:
                    pass
            
            for card in cards:
                try:
                    # Пробуем разные способы получить имя
                    name = ""
                    try:
                        name = card.locator('#name').inner_text()
                    except:
                        try:
                            name = card.locator('.extension-name').inner_text()
                        except:
                            try:
                                name = card.locator('div[role="heading"]').inner_text()
                            except:
                                continue
                    
                    logger.info(f"Найдено расширение: {name}")
                    
                    if "Proxy SwitchyOmega" in name:
                        logger.info("✅ Нашел SwitchyOmega!")
                        
                        # Проверяем состояние
                        toggle = None
                        try:
                            toggle = card.locator('#enableToggle')
                        except:
                            try:
                                toggle = card.locator('input[type="checkbox"]')
                            except:
                                try:
                                    toggle = card.locator('.extension-toggle')
                                except:
                                    logger.error("❌ Не удалось найти переключатель")
                                    continue
                        
                        if not toggle:
                            logger.error("❌ Не удалось найти переключатель")
                            continue
                        
                        is_enabled = toggle.get_attribute('aria-pressed') == 'true'
                        logger.info(f"Состояние: {'включено' if is_enabled else 'выключено'}")
                        
                        if not is_enabled:
                            logger.info("Пробую включить...")
                            toggle.click()
                            time.sleep(1)
                            
                            # Проверяем что включилось
                            is_enabled = toggle.get_attribute('aria-pressed') == 'true'
                            if is_enabled:
                                logger.success("✅ SwitchyOmega успешно включен")
                            else:
                                logger.error("❌ Не удалось включить SwitchyOmega")
                        
                        # Делаем скриншот карточки
                        card.screenshot(path="debug_switchyomega.png")
                        logger.info("📸 Сделан скриншот карточки SwitchyOmega (debug_switchyomega.png)")
                        return True
                        
                except Exception as e:
                    logger.error(f"Ошибка при обработке карточки: {str(e)}")
            
            logger.error("❌ SwitchyOmega не найден")
            return False
            
        except Exception as e:
            logger.error("❌ Ошибка при тестировании расширения")
            logger.debug(f"Причина: {str(e)}")
            return False 