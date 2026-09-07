# -*- coding: utf-8 -*-

"""

Load a particle player data (.dat) file into Python stored in some
folder/directory PLAYERDATA_DIR.

"""


import nbtlib

from scanner_modules.scanning_config import WORLD_FILES_ROOT_DIR
from scanner_modules.helper_functions import uuid_to_any_mc_name


if __name__ == "__main__":
    
    # Folder/directory that the player data file is stored in
    # (change accordingly)
    PLAYERDATA_DIR = (
        WORLD_FILES_ROOT_DIR /
        "playerdata"
    )
    
    # UUID of player in the name of the file
    # (don't put .dat at the end)
    uuid = "00000000-0000-0000-0000-000000000000"
    
    # Path to the player data file
    playerdata_file_path = (
        PLAYERDATA_DIR / f"{uuid}.dat"
    )
    
    # Print the username of the UUID
    print(uuid_to_any_mc_name(uuid))
    
    # Load player data file into Python
    player_nbt = nbtlib.load(playerdata_file_path)
    
    # Print keys of player_nbt
    print(player_nbt.keys())

