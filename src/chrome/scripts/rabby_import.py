import os
import time
import json
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from loguru import logger

from .utils import js_click, close_all_other_tabs, get_txt_line_by_profile_name, is_twelve_words_string


def rabby_import(profile_name: str | int, script_data_path: str | Path, driver: webdriver.Chrome):
    """
    Импорт кошелька в Rabby Wallet
    
    Args:
        profile_name: Имя профиля
        script_data_path: Путь к данным скрипта
        driver: Экземпляр драйвера Chrome
    """
    # Загружаем конфигурацию
    with open(os.path.join(script_data_path, 'config.json'), 'r', encoding="utf-8") as f:
        config = json.load(f)

    # Получаем данные для импорта
    secrets_file_path = os.path.join(script_data_path, 'secrets.txt')
    profile_data = get_txt_line_by_profile_name(profile_name, secrets_file_path)
    if not profile_data:
        raise Exception('приватный ключ или сид фраза не найдены')
    _, secret, password = profile_data.split('|')

    is_seed_phrase = is_twelve_words_string(secret)
    working_tab = driver.current_window_handle
    wait = WebDriverWait(driver, 10)  # Увеличиваем timeout до 10 секунд

    if config["run_delay_sec"]:
        logger.debug(f"{profile_name} - waiting {config['run_delay_sec']} sec")
        time.sleep(config["run_delay_sec"])

    close_all_other_tabs(driver, working_tab)

    # Открываем popup.html
    driver.get(f'chrome-extension://{config["extension_id"]}/popup.html')
    time.sleep(2)  # Даем время на загрузку

    # Переходим на страницу импорта через JavaScript
    driver.execute_script("window.location.href = 'index.html#/new-user/guide'")
    time.sleep(2)

    # Нажимаем I already have an address
    import_btn_xpath = "//button[contains(., 'I already have an address')]"
    import_btn = wait.until(EC.element_to_be_clickable((By.XPATH, import_btn_xpath)))
    js_click(driver, import_btn)
    time.sleep(1)

    if is_seed_phrase:
        # Импорт через seed phrase
        seed_phrase_btn_xpath = "//div[text()='Seed Phrase']"
        seed_phrase_btn = wait.until(EC.element_to_be_clickable((By.XPATH, seed_phrase_btn_xpath)))
        js_click(driver, seed_phrase_btn)
        time.sleep(1)

        # Вводим слова
        words = secret.split()
        for i, word in enumerate(words, 1):
            input_xpath = f"//div[contains(@class, 'is-mnemonics-input')]//input[{i}]"
            word_input = wait.until(EC.presence_of_element_located((By.XPATH, input_xpath)))
            word_input.send_keys(word)
            time.sleep(0.1)
    else:
        # Импорт через private key
        private_key_btn_xpath = "//div[text()='Private Key']"
        private_key_btn = wait.until(EC.element_to_be_clickable((By.XPATH, private_key_btn_xpath)))
        js_click(driver, private_key_btn)
        time.sleep(1)

        # Вводим private key
        key_input_xpath = "//input[@id='privateKey']"
        key_input = wait.until(EC.presence_of_element_located((By.XPATH, key_input_xpath)))
        key_input.send_keys(secret)

    # Нажимаем Confirm
    confirm_btn_xpath = "//button[contains(., 'Confirm')]"
    confirm_btn = wait.until(EC.element_to_be_clickable((By.XPATH, confirm_btn_xpath)))
    js_click(driver, confirm_btn)
    time.sleep(1)

    # Вводим пароль
    password_input_xpath = "//input[@id='password']"
    password_input = wait.until(EC.presence_of_element_located((By.XPATH, password_input_xpath)))
    password_input.send_keys(password)

    confirm_password_xpath = "//input[@id='confirmPassword']"
    confirm_password = wait.until(EC.presence_of_element_located((By.XPATH, confirm_password_xpath)))
    confirm_password.send_keys(password)

    # Подтверждаем создание
    final_confirm_xpath = "//button[contains(., 'Confirm')]"
    final_confirm = wait.until(EC.element_to_be_clickable((By.XPATH, final_confirm_xpath)))
    js_click(driver, final_confirm)

    if is_seed_phrase:
        # Для seed phrase нужно подтвердить импорт выбранных адресов
        import_btn_xpath = "//button[contains(., 'Import')]"
        import_btn = wait.until(EC.element_to_be_clickable((By.XPATH, import_btn_xpath)))
        js_click(driver, import_btn)

    logger.info(f"✅ {profile_name} - Кошелек успешно импортирован")
    time.sleep(2)