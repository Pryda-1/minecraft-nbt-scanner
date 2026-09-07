# -*- coding: utf-8 -*-

"""

Implements the 'download -> scan -> delete' pipeline with SFTP to scan the
region files.

"""


#### IMPORTS ####

from scanner_modules.sftp_scan_functions import sftp_region_source_scan


#### CONSTANTS ####

# Paths to all region file directories in the server
# Keep these as strings!

OVERWORLD_REMOTE_REGION_DIR   = "world/region"
OVERWORLD_REMOTE_ENTITIES_DIR = "world/entities"

NETHER_REMOTE_REGION_DIR      = "world_nether/DIM-1/region"
NETHER_REMOTE_ENTITIES_DIR    = "world_nether/DIM-1/entities"

END_REMOTE_REGION_DIR         = "world_the_end/DIM1/region"
END_REMOTE_ENTITIES_DIR       = "world_the_end/DIM1/entities"


#### BEGIN THE SCAN ####

if __name__ == "__main__":
    
    print("Overworld region scan started.")
    
    sftp_region_source_scan(
        remote_region_dir=OVERWORLD_REMOTE_REGION_DIR,
        world_type="OVERWORLD",
        scanning_entities=False
    )
    
    print("Overworld region scan finished.")

