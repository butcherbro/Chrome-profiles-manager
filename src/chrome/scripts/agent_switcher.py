import os
import time
import json

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from loguru import logger

from .utils import js_click, close_all_other_tabs


def agent_switcher(profile_name: str | int, script_data_path: str, _driver: webdriver.Chrome):
    with open(os.path.join(script_data_path, 'config.json'), 'r') as f:
        config = json.load(f)

    working_tab = _driver.current_window_handle
    wait = WebDriverWait(_driver, 3)


    # General settings
    _driver.get(f'chrome-extension://{config["extension_id"]}/options/index.html#/general')
    time.sleep(0.5)

    base_row_xpath = '(//aside//div[contains(@class, "row")])'

    for i in range(2):
        for index, setting in enumerate(config['general_settings']):
            checkbox_xpath = f'{base_row_xpath}[{index+1}]//input[@type="checkbox"]'  # Xpath matches starts with index 1
            checkbox = wait.until(EC.element_to_be_clickable((By.XPATH, checkbox_xpath)))

            if checkbox.is_selected() != setting['must_be_enabled']:
                close_all_other_tabs(_driver, working_tab)
                js_click(_driver, checkbox)
                time.sleep(0.1)
                logger.debug(f'{profile_name} - general setting "{setting["human_name"]}" adjusted to {setting["must_be_enabled"]}')
        time.sleep(0.5)

    # Generator settings
    _driver.get(f'chrome-extension://{config["extension_id"]}/options/index.html#/generator')
    time.sleep(0.5)

    for i in range(2):
        for setting in config['generator_settings']:
            checkbox_xpath = f'//input[@id="{setting["id"]}"]'
            checkbox = wait.until(EC.element_to_be_clickable((By.XPATH, checkbox_xpath)))

            if checkbox.is_selected() != setting['must_be_enabled']:
                close_all_other_tabs(_driver, working_tab)
                js_click(_driver, checkbox)
                time.sleep(0.1)
                logger.debug(f'{profile_name} - generator setting "{setting["human_name"]}" adjusted to {setting["must_be_enabled"]}')
        time.sleep(0.5)

    # Generate UA
    _driver.get(f'chrome-extension://{config["extension_id"]}/popup/index.html')
    time.sleep(0.5)

    for i in range(2):
        generate_ua_btn = wait.until(EC.element_to_be_clickable((By.XPATH, '//span[contains(text(), "Get new agent")]/..')))
        close_all_other_tabs(_driver, working_tab)
        js_click(_driver, generate_ua_btn)
        time.sleep(0.5)
