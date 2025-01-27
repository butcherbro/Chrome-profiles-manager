import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .establish_connection import establish_connection


def omega_proxy_setup(
        debug_port: int,
        chromedriver_path: str,
        name: str | int,
        proxy: str,
        extension_id: str = 'padekgcemlokbadohgkifijomclgjgif'
        ) -> None:
    
    # TODO: pass connected driver
    try:
        driver = establish_connection(debug_port, chromedriver_path, name)
        print(f'{name} - connection established')
        
    except Exception as e:
        print(f'{name} - failed to connect to chrome via debug port {debug_port}, reason: {e}')
        return
    
    try:
        initial_url = driver.current_url
        driver.get(f'chrome-extension://{extension_id}/options.html#!/profile/proxy')
        wait = WebDriverWait(driver, 5)

        # # Skip tour
        # trash_modales = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//button[@ng-click='$dismiss()']")))
        # if trash_modales:
        #     trash_modales[0].click()

        # TODO: proto selection

        # Set proxy
        proto, user, password, host, port = parse_proxy(proxy)
        proto_select = wait.until(EC.presence_of_element_located((By.XPATH, '//select[@ng-model="proxyEditors[scheme].scheme"]/option[@label="DIRECT"]/..')))

        host_input = driver.find_element(By.XPATH, '//input[@ng-model="proxyEditors[scheme].host"]')
        port_input = driver.find_element(By.XPATH, '//input[@ng-model="proxyEditors[scheme].port"]')
        host_input.clear()
        host_input.send_keys(host)
        port_input.clear()
        port_input.send_keys(port)

        auth_button = driver.find_element(By.XPATH, '(//button[@title="Authentication"])[1]')
        auth_button.click()

        username_input = wait.until(EC.presence_of_element_located((By.XPATH, '//div[@tabindex="-1"]//div[@class="modal-content"]//input[@placeholder="Username"]')))
        password_input = driver.find_element(By.XPATH, '//div[@tabindex="-1"]//div[@class="modal-content"]//input[@placeholder="Password"]')
        username_input.clear()
        username_input.send_keys(user)
        password_input.clear()
        password_input.send_keys(password)

        save_auth_btn= driver.find_element(By.XPATH, '//div[@tabindex="-1"]//div[@class="modal-content"]//button[@type="submit"]')
        save_auth_btn.click()

        apply_changes_btn = wait.until(EC.presence_of_element_located((By.XPATH, '//a[@ng-click="applyOptions()"]')))
        apply_changes_btn.click()

        # Turn it on
        driver.get(f'chrome-extension://{extension_id}/options.html#!/ui')

        dropdown = wait.until(EC.presence_of_element_located((By.XPATH, '//div[@on-toggle="toggled(open)"]')))
        dropdown.click()
        set_proxy_btn = driver.find_element(By.XPATH, '//ul[@role="listbox"]//span[@class="glyphicon glyphicon-globe"]')
        set_proxy_btn.click()

        # Turn off notifications
        driver.get(f'chrome-extension://{extension_id}/options.html#!/general')

        input_element = driver.find_element(By.XPATH, "//span[contains(text(), 'Show count of failed web requests for resources in the current tab.')]/../input[contains(@class, 'ng-empty') or contains(@class, 'ng-not-empty')]")
        if 'ng-not-empty' in input_element.get_attribute('class'):
            input_element.click()

            apply_changes_btn = wait.until(EC.presence_of_element_located((By.XPATH, '//a[@ng-click="applyOptions()"]')))
            apply_changes_btn.click()
            

        print(f'{name} - omega proxy set')
    except Exception as e:
        print(f'{name} - failed to set omega proxy, reason: {e}')
        return


    driver.get(initial_url)
    driver.quit()


def parse_proxy(proxy) -> list[str, str, str, str]:
    proto = proxy.split('://')[0]
    user = proxy.split('://')[1].split(':')[0]
    password = proxy.split(':')[1].split('@')[0]
    host = proxy.split('@')[1].split(':')[0]
    port = proxy.split('@')[1].split(':')[1]

    return proto, user, password, host, port