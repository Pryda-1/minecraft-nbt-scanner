# -*- coding: utf-8 -*-

"""

Scans the playerdata stored LOCALLY in the directory PLAYERDATA_DIR.

"""


#### IMPORTS ####

from scanner_modules.local_scan_functions import playerdata_dir_scan
from scanner_modules.scanning_config import WORLD_FILES_ROOT_DIR


#### CONSTANTS ####

# Directory where the player data is stored
PLAYERDATA_DIR = WORLD_FILES_ROOT_DIR / "playerdata"
assert PLAYERDATA_DIR.exists()


#### EXECUTE SCAN ####

if __name__ == "__main__":

    playerdata_dir_scan(
        playerdata_dir=PLAYERDATA_DIR
    )

