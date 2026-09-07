# -*- coding: utf-8 -*-

"""

Download and optionally scan the player data files defined in a TXT file
in txt_configs.

The file should be formatted as
- line 1: playerdata_filename1
- line 2: playerdata_filename2.dat
- line 3: playerdata_filename3
- etc.

'.dat' at the end is optional.

"""


#### IMPORTS ####

from scanner_modules.scanning_config import (
    WORLD_FILES_ROOT_DIR, TXT_CONFIGS_DIR
)
from scanner_modules.local_scan_functions import playerdata_dir_scan
from scanner_modules.sftp_functions import download_playerdata_files


#### CONSTANTS ####

# Directory where the particular player data files are stored
PLAYERDATA_DIR = WORLD_FILES_ROOT_DIR / "_specific_playerdata_files"
PLAYERDATA_DIR.mkdir(exist_ok=True, parents=True)

# Player data files remote directory. Keep as type str.
REMOTE_PLAYERDATA_DIR = "world/playerdata"

PLAYERDATA_FILE_NAMES_PATH = (
    TXT_CONFIGS_DIR / "specific_playerdata_file_names.txt"
)
assert PLAYERDATA_FILE_NAMES_PATH.exists()

# True if executing scan; False if not
EXECUTE_SCAN = False


#### DOWNLOAD FILES AND SCAN THEM ####

if __name__ == "__main__":
    
    ## READ IN PLAYER DATA FILE NAMES ##

    with open(PLAYERDATA_FILE_NAMES_PATH, "r") as file:
        PLAYERDATA_FILE_NAMES = [line.strip() for line in file]

    print("Player data file names:")
    print(PLAYERDATA_FILE_NAMES)
    print()
    
    ## Download files ##
    
    download_playerdata_files(
        local_dir = PLAYERDATA_DIR,
        remote_playerdata_dir = REMOTE_PLAYERDATA_DIR,
        playerdata_files = PLAYERDATA_FILE_NAMES
    )
    
    ## Execute scan ##
    
    if EXECUTE_SCAN:
    
        print("Scanning player data files.")
        
        playerdata_dir_scan(playerdata_dir=PLAYERDATA_DIR)
        
        print("Finished scanning player data files.")

