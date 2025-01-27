import os
import shutil
import subprocess
import sys
import time
import subprocess
import questionary
import threading
from server.server import run_fastapi_server
import socket
from automation.initial_setup import initial_setup
from automation.omega_proxy_setup import omega_proxy_setup



PROJECT_PATH = os.getcwd()
CHROME_DATA_PATH = os.path.join(PROJECT_PATH, "profiles")
DEFAULT_EXTENSIONS_PATH = os.path.join(PROJECT_PATH, "default_extensions")
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe" if sys.platform == "win32" else "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
CHROME_DRIVER_PATH = os.path.join(os.getcwd(), "automation", "chromedriver")

TEMPLATE_PATH = os.path.join(PROJECT_PATH, "client", "template.html")
HTML_OUTPUT_PATH = os.path.join(CHROME_DATA_PATH, "WelcomePages")
DEBUG_PORTS = {}


def create_chrome_profile(profile_name: str) -> None:
    profile_path = os.path.join(CHROME_DATA_PATH, f'Profile {profile_name}')

    try:
        os.makedirs(profile_path)
    except FileExistsError:
        print(f'Profile {profile_name} already exists')
        return

    profile_extensions_path = os.path.join(profile_path, "Extensions")
    os.makedirs(profile_extensions_path, exist_ok=True)
    for extension in os.listdir(DEFAULT_EXTENSIONS_PATH):
        src_folder = os.path.join(DEFAULT_EXTENSIONS_PATH, extension)
        dest_folder = os.path.join(profile_extensions_path, extension)
        shutil.copytree(src_folder, dest_folder, dirs_exist_ok=True)

    init_profile(profile_name)

    print(f'Profile {profile_name} created')


def init_profile(profile_name: str):
    launch_args, free_port = create_launch_flags(profile_name)
    chrome_process = subprocess.Popen([CHROME_PATH, *launch_args])
    time.sleep(0.5)
    chrome_process.terminate()
    chrome_process.wait()


def create_launch_flags(profile_name: str, debug: bool = False) -> list[str]:
    profile_path = os.path.join(CHROME_DATA_PATH, f'Profile {profile_name}')
    profile_extensions_path = os.path.join(profile_path, "Extensions")
    profile_html_path = get_profile_page(profile_name)

    all_extensions = []
    for ext_id in os.listdir(profile_extensions_path):
        versions_dir = os.path.join(profile_extensions_path, ext_id)
        if os.path.isdir(versions_dir):
            for version in os.listdir(versions_dir):
                version_path = os.path.join(versions_dir, version)
                if os.path.isfile(os.path.join(version_path, "manifest.json")):
                    all_extensions.append(version_path)

    load_arg = ",".join(all_extensions)

    flags =  [
        f"--user-data-dir={CHROME_DATA_PATH}",
        f"--profile-directory={f'Profile {profile_name}'}",
        "--no-first-run",
        f"--load-extension={load_arg}",
        f"file:///{profile_html_path}",
        "--no-sync",
        "--disable-features=IdentityConsistency",
        "--disable-accounts-receiver"
    ]

    free_port = None
    if debug:
        free_port = find_free_port()
        if free_port:
            flags.append(f'--remote-debugging-port={free_port}')
        else:
            print('Missing free ports for debug')

    return flags, free_port

def find_free_port(start_port=9222, max_port=9300):
    for port in range(start_port, max_port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            result = s.connect_ex(('127.0.0.1', port))
            if result != 0:  # 0 means port is in use
                return port
    return None


def get_profile_page(profile_name: str):
    os.makedirs(HTML_OUTPUT_PATH, exist_ok=True)
    
    profile_html_path = os.path.join(HTML_OUTPUT_PATH, f"{profile_name}.html")
    
    # if os.path.exists(profile_html_path):
    #     return profile_html_path
    
    with open(TEMPLATE_PATH, 'r') as template_file:
        template_content = template_file.read()
    
    profile_page_content = template_content.replace("{{ profile_name }}", profile_name)
    
    with open(profile_html_path, 'w') as profile_page_file:
        profile_page_file.write(profile_page_content)
    
    return profile_html_path

    
def launch_profile(profile_name: str, debug=False) -> int:
    launch_args, free_port = create_launch_flags(profile_name, debug)
    with open(os.devnull, 'w') as devnull:  # to avoid Chrome log spam
        subprocess.Popen([CHROME_PATH, *launch_args], stdout=devnull, stderr=devnull)

    time.sleep(2)
    return free_port


def get_profiles():
    profiles = []
    for item in os.listdir(CHROME_DATA_PATH):
        item_path = os.path.join(CHROME_DATA_PATH, item)
        
        if os.path.isdir(item_path) and item.startswith("Profile"):
            profiles.append(item.replace('Profile ', ''))
    
    return profiles


def main():
    # server_thread = threading.Thread(target=run_fastapi_server)
    # server_thread.daemon = True  # Обеспечивает закрытие потока при завершении программы
    # server_thread.start()

    time.sleep(1)

    profiles = get_profiles()
    
    if not profiles:
        print("No profiles found")
        return

    selected_profiles = questionary.checkbox(
        "Select profiles to launch:",
        choices=profiles
    ).ask()

    if not selected_profiles:
        print("No profiles selected")
        return
    
    for profile in selected_profiles:
        debug_port = launch_profile(profile, True)
        DEBUG_PORTS["profile"] = debug_port
        initial_setup(debug_port, CHROME_DRIVER_PATH)

    # server_thread.join()


if __name__ == '__main__':
    create_chrome_profile("1")
    # main()
    debug_port = launch_profile("1", True)
    DEBUG_PORTS["profile"] = debug_port
    # initial_setup(debug_port, CHROME_DRIVER_PATH, "1")
    omega_proxy_setup(debug_port, CHROME_DRIVER_PATH, "1", "http://user:pass@10.10.10.10:800")