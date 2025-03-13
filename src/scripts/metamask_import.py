import os
import time
import json
from loguru import logger
from typing import Optional, Dict, Any, List

from src.utils.constants import DEFAULT_EXTENSIONS_PATH, METAMASK_ID
from src.chrome.playwright_chrome import PlaywrightChrome


class MetamaskImport:
    """
    Класс для импорта кошелька MetaMask с использованием Playwright
    """
    
    def __init__(self, profile_name: str):
        """
        Инициализация класса для импорта MetaMask
        
        Args:
            profile_name: Имя профиля Chrome
        """
        self.profile_name = profile_name
        self.chrome = PlaywrightChrome()
        self.page = None
        
        # Загружаем конфигурацию MetaMask
        config_path = os.path.join(os.path.dirname(__file__), "..", "chrome", "config", "metamask_config.json")
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        else:
            # Используем значения по умолчанию
            self.config = {
                "selectors": {
                    "import_wallet_button": "button:has-text('Import wallet')",
                    "i_agree_button": "button:has-text('I agree')",
                    "import_with_seed_phrase": "button:has-text('Import an existing wallet')",
                    "seed_phrase_input": "textarea[placeholder='Paste Secret Recovery Phrase from clipboard']",
                    "password_input": "input[type='password']",
                    "confirm_password_input": "input[autocomplete='new-password']:nth-child(2)",
                    "terms_checkbox": "input[type='checkbox']",
                    "import_button": "button:has-text('Import')",
                    "all_done_button": "button:has-text('All Done')",
                    "got_it_button": "button:has-text('Got it')",
                    "close_popup_button": "button:has-text('Close')",
                    "next_button": "button:has-text('Next')",
                    "skip_button": "button:has-text('Skip')",
                    "networks_button": "button[data-testid='network-display']",
                    "add_network_button": "button:has-text('Add network')",
                    "add_network_manually": "button:has-text('Add a network manually')",
                    "network_name_input": "input[id='network-name']",
                    "rpc_url_input": "input[id='rpc-url']",
                    "chain_id_input": "input[id='chainId']",
                    "currency_symbol_input": "input[id='currency-symbol']",
                    "block_explorer_input": "input[id='block-explorer-url']",
                    "save_network_button": "button:has-text('Save')",
                    "close_all_button": "button[aria-label='Close']"
                },
                "timeouts": {
                    "navigation": 60000,
                    "element": 30000,
                    "action": 5000
                }
            }
    
    async def import_wallet(self, seed_phrase: str, password: str) -> bool:
        """
        Импорт кошелька MetaMask с использованием seed phrase
        
        Args:
            seed_phrase: Seed phrase (мнемоническая фраза) для импорта
            password: Пароль для кошелька
        
        Returns:
            bool: True если импорт успешен, False в противном случае
        """
        try:
            # Запускаем Chrome с профилем
            if not self.chrome.launch_profile(self.profile_name):
                logger.error(f"⛔ {self.profile_name} - не удалось запустить профиль")
                return False
            
            self.page = self.chrome.page
            
            # Открываем MetaMask
            logger.info(f"🦊 {self.profile_name} - открываем MetaMask...")
            await self.page.goto(f"chrome-extension://{METAMASK_ID}/home.html")
            
            # Проверяем, нужно ли импортировать кошелек
            try:
                # Ждем появления кнопки импорта
                import_wallet_button = await self.page.wait_for_selector(
                    self.config["selectors"]["import_wallet_button"],
                    timeout=self.config["timeouts"]["element"]
                )
                
                if import_wallet_button:
                    logger.info(f"🦊 {self.profile_name} - начинаем импорт кошелька...")
                    await import_wallet_button.click()
                    
                    # Соглашаемся с условиями
                    i_agree_button = await self.page.wait_for_selector(
                        self.config["selectors"]["i_agree_button"],
                        timeout=self.config["timeouts"]["element"]
                    )
                    await i_agree_button.click()
                    
                    # Выбираем импорт с помощью seed phrase
                    import_with_seed_phrase = await self.page.wait_for_selector(
                        self.config["selectors"]["import_with_seed_phrase"],
                        timeout=self.config["timeouts"]["element"]
                    )
                    await import_with_seed_phrase.click()
                    
                    # Вводим seed phrase
                    seed_phrase_input = await self.page.wait_for_selector(
                        self.config["selectors"]["seed_phrase_input"],
                        timeout=self.config["timeouts"]["element"]
                    )
                    await seed_phrase_input.fill(seed_phrase)
                    
                    # Вводим пароль
                    password_input = await self.page.wait_for_selector(
                        self.config["selectors"]["password_input"],
                        timeout=self.config["timeouts"]["element"]
                    )
                    await password_input.fill(password)
                    
                    # Подтверждаем пароль
                    confirm_password_input = await self.page.wait_for_selector(
                        self.config["selectors"]["confirm_password_input"],
                        timeout=self.config["timeouts"]["element"]
                    )
                    await confirm_password_input.fill(password)
                    
                    # Принимаем условия
                    terms_checkbox = await self.page.wait_for_selector(
                        self.config["selectors"]["terms_checkbox"],
                        timeout=self.config["timeouts"]["element"]
                    )
                    await terms_checkbox.click()
                    
                    # Нажимаем кнопку импорта
                    import_button = await self.page.wait_for_selector(
                        self.config["selectors"]["import_button"],
                        timeout=self.config["timeouts"]["element"]
                    )
                    await import_button.click()
                    
                    # Ждем завершения импорта
                    all_done_button = await self.page.wait_for_selector(
                        self.config["selectors"]["all_done_button"],
                        timeout=self.config["timeouts"]["navigation"]
                    )
                    await all_done_button.click()
                    
                    # Закрываем попапы, если они есть
                    try:
                        got_it_button = await self.page.wait_for_selector(
                            self.config["selectors"]["got_it_button"],
                            timeout=self.config["timeouts"]["element"]
                        )
                        if got_it_button:
                            await got_it_button.click()
                    except:
                        pass
                    
                    try:
                        close_popup_button = await self.page.wait_for_selector(
                            self.config["selectors"]["close_popup_button"],
                            timeout=self.config["timeouts"]["element"]
                        )
                        if close_popup_button:
                            await close_popup_button.click()
                    except:
                        pass
                    
                    logger.success(f"✅ {self.profile_name} - кошелек MetaMask успешно импортирован")
                    return True
                else:
                    logger.warning(f"⚠️ {self.profile_name} - кошелек MetaMask уже импортирован")
                    return True
            except Exception as e:
                logger.error(f"⛔ {self.profile_name} - ошибка при импорте кошелька: {str(e)}")
                return False
        except Exception as e:
            logger.error(f"⛔ {self.profile_name} - не удалось импортировать кошелек: {str(e)}")
            return False
        finally:
            # Закрываем браузер
            if self.chrome:
                self.chrome.close()
    
    async def add_network(self, network_config: Dict[str, Any]) -> bool:
        """
        Добавление сети в MetaMask
        
        Args:
            network_config: Конфигурация сети для добавления
                {
                    "name": "Имя сети",
                    "rpc_url": "URL RPC",
                    "chain_id": "ID цепи",
                    "currency_symbol": "Символ валюты",
                    "block_explorer_url": "URL обозревателя блоков"
                }
        
        Returns:
            bool: True если сеть успешно добавлена, False в противном случае
        """
        try:
            # Запускаем Chrome с профилем
            if not self.chrome.launch_profile(self.profile_name):
                logger.error(f"⛔ {self.profile_name} - не удалось запустить профиль")
                return False
            
            self.page = self.chrome.page
            
            # Открываем MetaMask
            logger.info(f"🦊 {self.profile_name} - открываем MetaMask...")
            await self.page.goto(f"chrome-extension://{METAMASK_ID}/home.html")
            
            # Нажимаем на кнопку сетей
            networks_button = await self.page.wait_for_selector(
                self.config["selectors"]["networks_button"],
                timeout=self.config["timeouts"]["element"]
            )
            await networks_button.click()
            
            # Нажимаем на кнопку добавления сети
            add_network_button = await self.page.wait_for_selector(
                self.config["selectors"]["add_network_button"],
                timeout=self.config["timeouts"]["element"]
            )
            await add_network_button.click()
            
            # Выбираем добавление сети вручную
            add_network_manually = await self.page.wait_for_selector(
                self.config["selectors"]["add_network_manually"],
                timeout=self.config["timeouts"]["element"]
            )
            await add_network_manually.click()
            
            # Заполняем данные сети
            network_name_input = await self.page.wait_for_selector(
                self.config["selectors"]["network_name_input"],
                timeout=self.config["timeouts"]["element"]
            )
            await network_name_input.fill(network_config["name"])
            
            rpc_url_input = await self.page.wait_for_selector(
                self.config["selectors"]["rpc_url_input"],
                timeout=self.config["timeouts"]["element"]
            )
            await rpc_url_input.fill(network_config["rpc_url"])
            
            chain_id_input = await self.page.wait_for_selector(
                self.config["selectors"]["chain_id_input"],
                timeout=self.config["timeouts"]["element"]
            )
            await chain_id_input.fill(network_config["chain_id"])
            
            currency_symbol_input = await self.page.wait_for_selector(
                self.config["selectors"]["currency_symbol_input"],
                timeout=self.config["timeouts"]["element"]
            )
            await currency_symbol_input.fill(network_config["currency_symbol"])
            
            block_explorer_input = await self.page.wait_for_selector(
                self.config["selectors"]["block_explorer_input"],
                timeout=self.config["timeouts"]["element"]
            )
            await block_explorer_input.fill(network_config["block_explorer_url"])
            
            # Сохраняем сеть
            save_network_button = await self.page.wait_for_selector(
                self.config["selectors"]["save_network_button"],
                timeout=self.config["timeouts"]["element"]
            )
            await save_network_button.click()
            
            # Ждем завершения добавления сети
            try:
                close_all_button = await self.page.wait_for_selector(
                    self.config["selectors"]["close_all_button"],
                    timeout=self.config["timeouts"]["navigation"]
                )
                if close_all_button:
                    await close_all_button.click()
            except:
                pass
            
            logger.success(f"✅ {self.profile_name} - сеть {network_config['name']} успешно добавлена")
            return True
        except Exception as e:
            logger.error(f"⛔ {self.profile_name} - не удалось добавить сеть {network_config['name']}: {str(e)}")
            return False
        finally:
            # Закрываем браузер
            if self.chrome:
                self.chrome.close()
    
    async def add_networks(self, networks: List[Dict[str, Any]]) -> bool:
        """
        Добавление нескольких сетей в MetaMask
        
        Args:
            networks: Список конфигураций сетей для добавления
        
        Returns:
            bool: True если все сети успешно добавлены, False в противном случае
        """
        success = True
        for network in networks:
            if not await self.add_network(network):
                success = False
        
        return success 