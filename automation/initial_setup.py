import time

from selenium import webdriver

from .establish_connection import establish_connection


def initial_setup(debug_port: int, chromedriver_path: str, name: str | int) -> None:
    # TODO: pass connected driver
    try:
        driver = establish_connection(debug_port, chromedriver_path, name)
        print(f'{name} - connection established')

    except Exception as e:
        print(f'{name} - failed to connect to chrome via debug port {debug_port}, reason: {e}')
        return
    
    initial_url = driver.current_url

    turn_off_sync(driver, name)

    if name:
        set_profile_name(driver, name)

    turn_off_autofill(driver, name)

    adjust_privacy_choices(driver, name)

    adjust_tabs_memorizing(driver, name)

        
    driver.get(initial_url)
    driver.quit()


def dive_into_shadowroots(driver: webdriver.Chrome, host_tags):
    final_sr = driver
    for host in host_tags:
        element = final_sr.find_element(By.CSS_SELECTOR, host)
        shadow_root = element.shadow_root
        final_sr = shadow_root

    return final_sr


def turn_off_sync(driver: webdriver.Chrome, name: str | int):
    try:
        host_tags = [
            "settings-ui",
            "settings-main",
            "settings-basic-page",
            "settings-people-page",
            "settings-sync-page",
            "settings-personalization-options",
            "settings-toggle-button"
        ]

        driver.get("chrome://settings/syncSetup")
        time.sleep(0.5)

        final_sr = dive_into_shadowroots(driver, host_tags)

        toggle = final_sr.find_element(By.CSS_SELECTOR, 'cr-toggle')
        if toggle.get_attribute('aria-pressed') == 'true':
            toggle.click()

        print(f"{name} - sync off")
    except Exception as e:
        print(f"{name} - failed to switch off sync, reason: {e}")


def set_profile_name(driver: webdriver.Chrome, name: str | int):
    try:
        host_tags = [
            "settings-ui",
            "settings-main",
            "settings-basic-page",
            "settings-people-page",
            "settings-manage-profile",
            # "cr-input"
        ]

        driver.get("chrome://settings/manageProfile")
        time.sleep(0.5)

        final_sr = dive_into_shadowroots(driver, host_tags)
        click_to_save_element = final_sr.find_element(By.CSS_SELECTOR, 'cr-input')

        final_sr = click_to_save_element.shadow_root

        input = final_sr.find_element(By.CSS_SELECTOR, 'input')
        input.clear()
        input.send_keys(name)
        click_to_save_element.click()
        time.sleep(0.2)

        print(f"{name} - name set")
    except Exception as e:
        print(f"{name} - failed to set name, reason: {e}")


def turn_off_autofill(driver:  webdriver.Chrome, name: str | int):
    try:
        host_tags = [
            "password-manager-app",
            "settings-section"
        ]

        driver.get('chrome://password-manager/settings')
        time.sleep(0.5)

        final_sr = dive_into_shadowroots(driver, host_tags)

        pass_toggle_host = final_sr.find_element(By.ID, 'passwordToggle')
        sr = pass_toggle_host.shadow_root
        pass_toggle = sr.find_element(By.CSS_SELECTOR, 'cr-toggle')
        if pass_toggle.get_attribute('aria-pressed') == 'true':
            pass_toggle.click()
        
        auto_sign_in_toggle_host = final_sr.find_element(By.ID, 'autosigninToggle')
        sr = auto_sign_in_toggle_host.shadow_root
        auto_sign_in_toggle = sr.find_element(By.CSS_SELECTOR, 'cr-toggle')
        if auto_sign_in_toggle.get_attribute('aria-pressed') == 'true':
            auto_sign_in_toggle.click()
        
        print(f"{name} - autofill off")
    except Exception as e:
        print(f"{name} - failed to turn off autofill, reason: {e}")


def adjust_privacy_choices(driver:  webdriver.Chrome, name: str | int):
    try:
        host_tags = [
            "settings-ui",
            "settings-main",
            "settings-basic-page",
            "settings-privacy-page",
            "settings-privacy-guide-dialog",
            "settings-privacy-guide-page"
        ]

        driver.get('chrome://settings/privacy/guide?step=welcome')
        time.sleep(0.5)

        unique_sr = dive_into_shadowroots(driver, host_tags)

        welcome_fragment_element = unique_sr.find_element(By.CSS_SELECTOR, 'privacy-guide-welcome-fragment')
        welcome_fragment_sr = welcome_fragment_element.shadow_root
        start_button = welcome_fragment_sr.find_element(By.ID, 'startButton')
        start_button.click()

        host_tags = [
            'privacy-guide-msbb-fragment',
            'settings-toggle-button'
        ]

        searches_and_browser_better_sr = dive_into_shadowroots(unique_sr, host_tags)
        searches_and_browser_better_toggle = searches_and_browser_better_sr.find_element(By.ID, 'control')
        if searches_and_browser_better_toggle.get_attribute('aria-pressed') == 'true':
            searches_and_browser_better_toggle.click()

        next_button = unique_sr.find_element(By.ID, 'nextButton')
        next_button.click()

        host_tags = [
            'privacy-guide-safe-browsing-fragment',
            'settings-collapse-radio-button#safeBrowsingRadioStandard'
        ]

        safe_browsing_sr = dive_into_shadowroots(unique_sr, host_tags)
        standard_mode_radio_btn = safe_browsing_sr.find_element(By.ID, 'button')
        if standard_mode_radio_btn.get_attribute('aria-checked') == 'false': 
            safe_browsing_sr.find_element(By.ID, 'radioCollapse').click()

        next_button = unique_sr.find_element(By.ID, 'nextButton')
        next_button.click()

        host_tags = [
            'privacy-guide-cookies-fragment',
            'settings-collapse-radio-button#block3PIncognito'
        ]

        block_cookies_in_incognito_sr = dive_into_shadowroots(unique_sr, host_tags)
        block_cookies_in_incognito_radio_btn = block_cookies_in_incognito_sr.find_element(By.ID, 'button')
        if block_cookies_in_incognito_radio_btn.get_attribute('aria-checked') == 'false': 
            block_cookies_in_incognito_sr.find_element(By.ID, 'radioCollapse').click()

        next_button = unique_sr.find_element(By.ID, 'nextButton')
        next_button.click()


        finish_fragment_element = unique_sr.find_element(By.CSS_SELECTOR, 'privacy-guide-completion-fragment')
        finish_fragment_sr = finish_fragment_element.shadow_root
        done_button = finish_fragment_sr.find_element(By.ID, 'leaveButton')
        done_button.click()

        print(f"{name} - privacy choices adjusted")
    except Exception as e:
        print(f"{name} - failed to adjust privacy choices, reason: {e}")


def adjust_tabs_memorizing(driver:  webdriver.Chrome, name: str | int):
    try:
        host_tags = [
            "settings-ui",
            "settings-main",
            "settings-basic-page",
            "settings-on-startup-page"
        ]

        options = [
            'Open the New tab page',
            'Continue where you left off',
            'Open a specific page or set of pages'
        ]

        driver.get('chrome://settings/onStartup')
        time.sleep(0.5)

        final_sr = dive_into_shadowroots(driver, host_tags)
        chosen_option = final_sr.find_element(By.CSS_SELECTOR, "controlled-radio-button[label='Open the New tab page']")
        chosen_option.click()

        print(f"{name} - tabs memorizing adjusted")
    except Exception as e:
        print(f"{name} - failed to adjust tabs memorizing, reason: {e}")
