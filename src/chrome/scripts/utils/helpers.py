from selenium.webdriver.remote.webelement import WebElement
from selenium import webdriver


def parse_proxy(proxy: str) -> tuple[str, str, str, str, str]:
    proto = proxy.split('://')[0]
    user = proxy.split('://')[1].split(':')[0]
    password = proxy.split('@')[0].split(':')[-1]
    host = proxy.split('@')[1].split(':')[0]
    port = proxy.split('@')[1].split(':')[1]

    return proto, user, password, host, port


def js_click(_driver: webdriver.Chrome, element: WebElement) -> None:
    _driver.execute_script("arguments[0].click();", element)


def close_all_other_tabs(_driver: webdriver.Chrome, current_tab: str) -> None:
    for handle in _driver.window_handles:
        if handle != current_tab:
            _driver.switch_to.window(handle)
            _driver.close()

    _driver.switch_to.window(current_tab)
