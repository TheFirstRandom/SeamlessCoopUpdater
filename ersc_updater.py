import subprocess
from json import JSONDecodeError
import requests # requires installation (pip install requests)
import sys
import json
import os
import zipfile
import shutil
import configparser
import time
from tqdm import tqdm # requires installation (pip install tqdm)

# Define globals
eldenring_dir = r"C:\Program Files (x86)\Steam\steamapps\common\ELDEN RING\Game"
cwd = os.getcwd()
repo_url = "https://api.github.com/repos/LukeYui/EldenRingSeamlessCoopRelease/releases/latest"

def get_release():
    try:
        # Get response from GitHub repository
        response = requests.get(repo_url, timeout=7)
        response.raise_for_status()

        # Extract release data from response
        release_data = response.json()

        return release_data

    except requests.Timeout:
        # Exit, if request timed out
        print("Request timed out. Exit in 5 seconds.")

        time.sleep(5)
        sys.exit(1)

    except requests.RequestException as e:
        # Exit, if an error occured
        print(f"Request error: {e}. Exit in 15 seconds.")

        input("Press any key to exit. ")
        sys.exit(1)   

def get_appdata():
    try:
        # Try to get appdata out the appdata.json file
    	with open(os.path.join(cwd, "appdata.json"), "r") as file:
            appdata = json.load(file)

            return appdata

    except JSONDecodeError:
        return None

def compare_versions(new_version, old_version):
    # Converting versions from "vX.X.X" to [X, X, X]
    new_v_list = list(map(int, new_version[1:].split(".")))
    old_v_list = list(map(int, old_version[1:].split(".")))

    if new_v_list[0] > old_v_list[0]:
        # If major version is higher than the installed
        return True
    
    elif new_v_list[1] > old_v_list[1]:
        # If minor version is higher than the installed
        return True

    elif new_v_list[2] > old_v_list[2]:
        # If patch version is higher than the installed
        return True

    else:
        # If the version isn't newer
        return False

print("Searching for newest release and current installation...")

# Get newest version
release_data = get_release()
new_version = release_data["tag_name"] # vX.X.X
print(f"Newest release: {release_data["name"]}")

# Try to get current installation
try:
    old_version = get_appdata()["current_installation"]
    print(f"Current installation: {old_version}")
except TypeError:
    # If there is no current installation
    old_version = "v0.0.0"
    print("Mod is not, or manually installed. Installing anyway. ")

# Check, if a new install is necessary
want_install = compare_versions(new_version, old_version)

if want_install is not True:
    print("Requirements already met. Launching modded Elden Ring in 5 seconds.")
    subprocess.Popen([os.path.join(eldenring_dir, "ersc_launcher.exe")], cwd=eldenring_dir)
    sys.exit(0)

shutil.copy(os.path.join(eldenring_dir, "SeamlessCoop", "ersc_settings.ini"), cwd)

download_url = release_data["assets"][0]["browser_download_url"]
download_response = requests.get(download_url, stream=True)

# Check, if download was not successfully
if not download_response.status_code == 200:
    print(f"HTTP Error: {str(download_response.status_code)}: {download_response.reason}. Exit in 5 seconds.")

    time.sleep(5)
    sys.exit(download_response.status_code)

# Get total file size
total_size = int(download_response.headers.get("Content-Length", 0))

# Download file and show progress
with open(os.path.join(eldenring_dir, "ersc.zip"), "wb") as file:
    with tqdm(total=total_size, unit="B", unit_scale=True, desc="Downloading release") as progress_bar:
        for chunk in download_response.iter_content(chunk_size=1024):
            if chunk:
                file.write(chunk)
                progress_bar.update(len(chunk))

print("Installing files...")
# Extract archive to a temporary directory
with zipfile.ZipFile(os.path.join(eldenring_dir, "ersc.zip"), "r") as zip_ref:
    zip_ref.extractall(os.path.join(eldenring_dir))

# Read new and old settings
new_settings = configparser.ConfigParser()
new_settings.read(os.path.join(eldenring_dir, "SeamlessCoop", "ersc_settings.ini"))

old_settings = configparser.ConfigParser()
old_settings.read(os.path.join(cwd, "ersc_settings.ini"))

# Compare new and old settings, to find new options
new_things = {}
for section in new_settings:
    if section in old_settings:
        # If section exists in old settings, compare options
        for option in new_settings[section]:
            if option in old_settings[section]:
                # If option exists in old settings, copy value from old settings
                new_settings[section][option] = old_settings[section][option]
            else:
                # If option does not exist in old settings, add it to new settings
                new_things[section][option] = new_settings[section][option]
    else:
        # If section does not exist in old settings, add it to new settings
        new_things[section] = new_settings[section]

# If there are some, print the new options
if new_things:
    print(f"There are new options in the ersc_settings.ini: {new_things}. Continuing in 5 seconds. ")
    time.sleep(5)

# Write the settings
with open(os.path.join(eldenring_dir, "SeamlessCoop", "ersc_settings.ini"), "w") as file:
    new_settings.write(file)

# Write new version to appdata.json
print("Updating appdata...")
appdata = {"current_installation": new_version}
with open(os.path.join(cwd, "appdata.json"), "w") as file:
    json.dump(appdata, file)

# Remove old files
print("Cleaning up...")
os.remove(os.path.join(cwd, "ersc_settings.ini"))
os.remove(os.path.join(eldenring_dir, "ersc.zip"))

# Launch the game
print("Installed release successfully. Launching modded Elden Ring in 5 seconds. ")
time.sleep(5)
subprocess.Popen([os.path.join(eldenring_dir, "ersc_launcher.exe")], cwd=eldenring_dir)
sys.exit(0)
