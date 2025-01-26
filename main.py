import os
import shutil
import subprocess
import sys

PROJECT_PATH = os.getcwd()
ALL_PROFILES_PATH = os.path.join(PROJECT_PATH, "profiles")
DEFAULT_EXTENSIONS_PATH = os.path.join(PROJECT_PATH, "default_extensions")


def create_chrome_profile(profile_name: str) -> None:
    profile_path = os.path.join(ALL_PROFILES_PATH, profile_name)
    try:
        os.makedirs(profile_path)
    except FileExistsError:
        print(f'Profile {profile_name} already exists')

    profile_extensions_dir = os.path.join(profile_path, "Extensions")
    os.makedirs(profile_extensions_dir, exist_ok=True)
    for extension in os.listdir(DEFAULT_EXTENSIONS_PATH):
        src_folder = os.path.join(DEFAULT_EXTENSIONS_PATH, extension)
        dest_folder = os.path.join(profile_extensions_dir, extension)
        shutil.copytree(src_folder, dest_folder, dirs_exist_ok=True)


def launch_profile(profile_name: str):
    profile_path = os.path.join(ALL_PROFILES_PATH, profile_name)

    if not os.path.exists(profile_path):
        return
    if sys.platform == "win32":
        chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    elif sys.platform == "darwin":
        chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    else:
        return

    profile_extensions_dir = os.path.join(profile_path, "Extensions")
    all_extensions = []
    for ext_id in os.listdir(profile_extensions_dir):
        versions_dir = os.path.join(profile_extensions_dir, ext_id)
        if os.path.isdir(versions_dir):
            for version in os.listdir(versions_dir):
                version_path = os.path.join(versions_dir, version)
                if os.path.isfile(os.path.join(version_path, "manifest.json")):
                    all_extensions.append(version_path)

    load_arg = ",".join(all_extensions)
    subprocess.run([
        chrome_path,
        f"--user-data-dir={profile_path}",
        "--no-first-run",
        f"--load-extension={load_arg}"
    ])


if __name__ == "__main__":
    create_chrome_profile("2")
    launch_profile('2')
