import requests # IMPORTANT: requires installation (pip install requests)
import sys
import json
import os
import zipfile
import re
import shutil
import configparser

old_config_file = os.path.join(os.getcwd(), "data", "ersc_settings.ini")
new_config_file = r"C:\Program Files (x86)\Steam\steamapps\common\ELDEN RING\Game\SeamlessCoop\ersc_settings.ini"

def get_newest_version():
    url = "https://api.github.com/repos/LukeYui/EldenRingSeamlessCoopRelease/releases/latest"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        release_data = response.json()

        tag_name = release_data['tag_name']
        release_name = release_data['name']
        release_url = release_data['html_url']

        needed_data = {
            "tag_name": tag_name,
            "release_name": release_name,
            "release_url": release_url
        }

        print("Newest version:")
        print("name: " + release_name)
        print("url: " + release_url)
        print()

        return needed_data

    except requests.Timeout:
        print("The request timed out. Please try again later.")
        sys.exit(1)
    except requests.RequestException as err:
        print(f"Error during the request: {err}")
        sys.exit(1)

def compare_versions(new_version, old_version):
    try:
        v_new = list(map(int, new_version.split('.')))
        v_old = list(map(int, old_version.split('.')))

        for i in range(max(len(v_new), len(v_old))):
            v_new_part = v_new[i] if i < len(v_new) else 0
            v_old_part = v_old[i] if i < len(v_old) else 0

            if v_new_part > v_old_part:
                return True
            elif v_new_part < v_old_part:
                return False
        return False
    except ValueError as e:
        print(f"Version comparison error: {e}")
        sys.exit(1)

def search_updates():
    print("Searching for newest release...")
    needed_data = get_newest_version()
    new_version = needed_data["tag_name"][1:]

    current_installation_path = os.path.join(os.getcwd(), "data", "current_installation.json")
    try:
        with open(current_installation_path, "r") as file:
            current_data = json.load(file)
            old_version = current_data["tag_name"][1:]
    except json.JSONDecodeError:
        try:
            if os.path.exists(r"C:\Program Files (x86)\Steam\steamapps\common\ELDEN RING\Game\SeamlessCoop"):
                print("The SeamlessCoop Mod seems to be installed but not with the SeamlessCoop Updater.")
                print("""Choose an option...
[1] Enter the current version manually
[2] Update anyway
[3] Exit
                """)
                first_install = input("> ")
                if first_install == "1":
                    print("Enter installed version [vX.X.X]...")
                    old_version = input("> ")[1:]
                    pattern = r"^\d+\.\d+\.\d+$"
                    if re.match(pattern, old_version):
                        compare_versions(new_version, old_version)
                    else:
                        print("Invalid input [vX.X.X]. Exiting.")
                        sys.exit(1)
                elif first_install == "2":
                    old_version = "v1.0.0"[1:]
                    install_ersc(needed_data, current_installation_path)
                elif first_install == "3":
                    sys.exit(0)
                else:
                    print("Invalid input [1/2/3]. Exiting.")
                    sys.exit(1)
            else:
                print("It looks as if no version of the ERSC has been installed yet. Continuing...")
                old_version = "v1.0.0"[1:]
                install_ersc(needed_data, current_installation_path)
        except OSError as e:
            print(f"File error: {e}")
            sys.exit(1)
    except FileNotFoundError as e:
        print(f"Current installation file not found: {e}")
        sys.exit(1)

    print("Comparing versions...")
    upgrade = compare_versions(new_version, old_version)
    if upgrade:
        print(f"New update {needed_data['release_name']} available. Do you want to install it? [Y/n]")
        want_install = input("> ")
        if want_install in ["Y", "y", ""]:
            install_ersc(needed_data, current_installation_path)
        elif want_install in ["n", "N"]:
            sys.exit(0)
        else:
            print("Invalid input [Y/n]. Exiting.")
            sys.exit(1)
    else:
        print("ERSC is already up to date. Exiting.")
        sys.exit(0)

def read_config(filename):
    config = configparser.ConfigParser()
    try:
        config.read(filename)

        all_items = set()
        for section in config.sections():
            all_items.update(config.items(section))
        return all_items
    except configparser.Error as e:
        print(f"Error reading the config file: {e}")
        sys.exit(1)

def compare_configs():
    try:
        old_config = read_config(old_config_file)
        new_config = read_config(new_config_file)

        old_keys = {key for key, value in old_config}
        new_keys = {key for key, value in new_config}

        only_in_old = old_keys - new_keys
        only_in_new = new_keys - old_keys

        if only_in_old and only_in_new:
            print("""There are new options in the ersc_settings.ini file. 
The updater cannot replace the file with the old one because of this. 
You must therefore make the settings yourself.""")
            input("Press any key to continue...")
            return False
        else:
            print("Configs are equal.")
            return True
    except Exception as e:
        print(f"Error comparing config files: {e}")
        sys.exit(1)

def install_ersc(needed_data, current_installation_path):
    elden_ring_path = r"C:\Program Files (x86)\Steam\steamapps\common\ELDEN RING\Game"

    print("Do you want to keep your ersc_settings.ini file? [Y/n]")
    keep_settings = input("> ")
    if keep_settings in ["Y", "y", ""]:
        try:
            print("Saving config...")
            shutil.move(new_config_file, old_config_file)
        except OSError as e:
            print(f"Error moving the config file: {e}")
            sys.exit(1)

    url = f"https://github.com/LukeYui/EldenRingSeamlessCoopRelease/releases/download/{needed_data['tag_name']}/ersc.zip"
    print(f"Downloading files from {url}")
    file_name = f"ersc {needed_data['tag_name']}.zip"
    file_path = os.path.join(os.getcwd(), "data", file_name)

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        with open(file_path, 'wb') as file:
            file.write(response.content)
        print(f"Download of file successful: {file_path}")
    except requests.Timeout:
        print("The request timed out. Please try again later.")
        sys.exit(1)
    except requests.RequestException as err:
        print(f"Error downloading the file: {err}")
        sys.exit(1)
    except OSError as e:
        print(f"File error: {e}")
        sys.exit(1)

    try:
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(elden_ring_path)
        os.remove(file_path)
    except zipfile.BadZipFile as e:
        print(f"Error extracting the ZIP file: {e}")
        sys.exit(1)

    if keep_settings in ["Y", "y", ""]:
        print("Comparing old and new ersc_settings.ini...")
        if compare_configs():
            try:
                print("Overwriting new ersc_settings.ini...")
                shutil.move(old_config_file, new_config_file)
            except OSError as e:
                print(f"Error overwriting the config file: {e}")
                sys.exit(1)

    try:
        with open(current_installation_path, "w") as file:
            json.dump(needed_data, file, indent=4)
    except OSError as e:
        print(f"Error writing the current installation data: {e}")
        sys.exit(1)

    print("New version installed successfully.")
    input("Press any key to exit. ")
    sys.exit(0)

print("""Welcome to the Elden Ring SeamlessCoop Updater

Important: This project is an updater for the SeamlessCoop Mod for Elden Ring, which is created by LukeYui. 
It was not coded by or in cooperation with the developer of the mod and is not officially supported. 
Credits to the Mod: https://github.com/LukeYui/EldenRingSeamlessCoopRelease
""")
search_updates()
