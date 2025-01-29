import os
import time
import json

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select

from .utils import parse_proxy, js_click, close_all_other_tabs


def omega_proxy_setup(profile_name: str | int, script_data_path: str, _driver: webdriver.Chrome) -> None:
    with open(os.path.join(script_data_path, 'config.json'), 'r') as f:
        config = json.load(f)

    proxy = get_proxy_by_profile_name(profile_name, script_data_path)
    if not proxy:
        raise Exception('прокси не найден')

    working_tab = _driver.current_window_handle

    _driver.get(f'chrome-extension://{config["extension_id"]}/options.html#!/profile/proxy')
    wait = WebDriverWait(_driver, 3)

    # Skip tour
    try:
        trash_modal = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@ng-click='$dismiss()']")))
        close_all_other_tabs(_driver, working_tab)
        js_click(_driver, trash_modal)
    except:
        pass

    # Set proxy
    proto, user, password, host, port = parse_proxy(proxy)
    proto_select_options = ['DIRECT', 'HTTP', 'HTTPS', 'SOCKS4', 'SOCKS5']
    proto_select = Select(wait.until(EC.element_to_be_clickable((By.XPATH, '//select[@ng-model="proxyEditors[scheme].scheme"]/option[@label="DIRECT"]/..'))))
    proto_select.select_by_index(proto_select_options.index(proto.upper()))

    host_input = wait.until(EC.element_to_be_clickable((By.XPATH, '//input[@ng-model="proxyEditors[scheme].host"]')))
    close_all_other_tabs(_driver, working_tab)
    host_input.clear()
    host_input.send_keys(host)

    port_input = wait.until(EC.element_to_be_clickable((By.XPATH, '//input[@ng-model="proxyEditors[scheme].port"]')))
    close_all_other_tabs(_driver, working_tab)
    port_input.clear()
    port_input.send_keys(port)

    auth_button = wait.until(EC.element_to_be_clickable((By.XPATH, '(//button[@title="Authentication"])[1]')))
    close_all_other_tabs(_driver, working_tab)
    js_click(_driver, auth_button)
    time.sleep(0.1)

    username_input = wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@tabindex="-1"]//div[@class="modal-content"]//input[@placeholder="Username"]')))
    close_all_other_tabs(_driver, working_tab)
    username_input.clear()
    username_input.send_keys(user)

    password_input = wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@tabindex="-1"]//div[@class="modal-content"]//input[@placeholder="Password"]')))
    close_all_other_tabs(_driver, working_tab)
    password_input.clear()
    password_input.send_keys(password)

    save_auth_btn = wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@tabindex="-1"]//div[@class="modal-content"]//button[@type="submit"]')))
    close_all_other_tabs(_driver, working_tab)
    js_click(_driver, save_auth_btn)

    time.sleep(0.1)
    apply_changes_btn = wait.until(EC.element_to_be_clickable((By.XPATH, '//a[@ng-click="applyOptions()"]')))
    close_all_other_tabs(_driver, working_tab)
    js_click(_driver, apply_changes_btn)

    # Turn it on
    _driver.get(f'chrome-extension://{config["extension_id"]}/options.html#!/ui')

    dropdown = wait.until(EC.element_to_be_clickable((By.XPATH, '//div[@on-toggle="toggled(open)"]')))
    close_all_other_tabs(_driver, working_tab)
    dropdown.click()

    set_proxy_btn = wait.until(EC.element_to_be_clickable((By.XPATH, '//ul[@role="listbox"]//span[@class="glyphicon glyphicon-globe"]')))
    close_all_other_tabs(_driver, working_tab)
    set_proxy_btn.click()

    time.sleep(0.1)
    apply_changes_btn = wait.until(EC.element_to_be_clickable((By.XPATH, '//a[@ng-click="applyOptions()"]')))
    close_all_other_tabs(_driver, working_tab)
    js_click(_driver, apply_changes_btn)

    # Turn off notifications
    _driver.get(f'chrome-extension://{config["extension_id"]}/options.html#!/general')

    input_element = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Show count of failed web requests for resources in the current tab.')]/../input[contains(@class, 'ng-empty') or contains(@class, 'ng-not-empty')]")))
    if 'ng-not-empty' in input_element.get_attribute('class'):
        close_all_other_tabs(_driver, working_tab)
        js_click(_driver, input_element)
        time.sleep(0.1)

        apply_changes_btn = wait.until(EC.element_to_be_clickable((By.XPATH, '//a[@ng-click="applyOptions()"]')))
        close_all_other_tabs(_driver, working_tab)
        js_click(_driver, apply_changes_btn)


def get_proxy_by_profile_name(profile_name: str | int, script_data_path: str) -> str | None:
    with open(os.path.join(script_data_path, 'proxies.txt'), 'r') as f:
        proxies_data = [i.strip() for i in f.readlines()]

    selected_proxy = None
    for line in proxies_data:
        name, _proxy = line.split('|')
        if name == str(profile_name):
            selected_proxy = _proxy
            break

    return selected_proxy
