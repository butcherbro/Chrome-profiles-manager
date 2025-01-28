import time
from lib2to3.pgen2 import driver

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


EXTENSION_ID: str = 'padekgcemlokbadohgkifijomclgjgif'
proxy = 'https://user:password@host:8000'

def omega_proxy_setup(name: str | int, _driver: webdriver.Chrome) -> None:
    working_tab = _driver.current_window_handle

    _driver.get(f'chrome-extension://{EXTENSION_ID}/options.html#!/profile/proxy')
    wait = WebDriverWait(_driver, 3)

    # Skip tour
    try:
        trash_modal = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@ng-click='$dismiss()']")))
        close_all_other_tabs(_driver, working_tab)
        js_click(_driver, trash_modal)
    except:
        pass

    # TODO: proto selection

    # Set proxy
    proto, user, password, host, port = parse_proxy(proxy)
    proto_select = wait.until(EC.element_to_be_clickable((By.XPATH, '//select[@ng-model="proxyEditors[scheme].scheme"]/option[@label="DIRECT"]/..')))

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
    _driver.get(f'chrome-extension://{EXTENSION_ID}/options.html#!/ui')

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
    _driver.get(f'chrome-extension://{EXTENSION_ID}/options.html#!/general')

    input_element = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Show count of failed web requests for resources in the current tab.')]/../input[contains(@class, 'ng-empty') or contains(@class, 'ng-not-empty')]")))
    if 'ng-not-empty' in input_element.get_attribute('class'):
        close_all_other_tabs(_driver, working_tab)
        js_click(_driver, input_element)
        time.sleep(0.1)

        apply_changes_btn = wait.until(EC.element_to_be_clickable((By.XPATH, '//a[@ng-click="applyOptions()"]')))
        close_all_other_tabs(_driver, working_tab)
        js_click(_driver, apply_changes_btn)


def close_all_other_tabs(_driver: webdriver.Chrome, current_tab: str) -> None:
    for handle in _driver.window_handles:
        if handle != current_tab:
            _driver.switch_to.window(handle)
            _driver.close()

    _driver.switch_to.window(current_tab)


def js_click(_driver: webdriver.Chrome, element: WebElement) -> None:
    _driver.execute_script("arguments[0].click();", element)


def parse_proxy(_proxy: str) -> tuple[str, str, str, str, str]:
    proto = _proxy.split('://')[0]
    user = _proxy.split('://')[1].split(':')[0]
    password = _proxy.split('@')[0].split(':')[-1]
    host = _proxy.split('@')[1].split(':')[0]
    port = _proxy.split('@')[1].split(':')[1]

    return proto, user, password, host, port