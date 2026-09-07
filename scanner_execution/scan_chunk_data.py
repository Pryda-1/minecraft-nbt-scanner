# -*- coding: utf-8 -*-

"""

Scans chunk data stored in various directories LOCALLY.

"""


#### IMPORTS ####

from scanner_modules.local_scan_functions import region_dir_scan
from scanner_modules.scanning_config import WORLD_FILES_ROOT_DIR


#### CONSTANTS ####

OVERWORLD_REGION_DIR   = WORLD_FILES_ROOT_DIR / "region"
OVERWORLD_ENTITIES_DIR = WORLD_FILES_ROOT_DIR / "entities"

NETHER_REGION_DIR      = WORLD_FILES_ROOT_DIR / "DIM-1" / "region"
NETHER_ENTITIES_DIR    = WORLD_FILES_ROOT_DIR / "DIM-1" / "entities"

END_REGION_DIR         = WORLD_FILES_ROOT_DIR / "DIM1"  / "region"
END_ENTITIES_DIR       = WORLD_FILES_ROOT_DIR / "DIM1"  / "entities"

# Store the paths in a list and iterate over them
REGIONS_DICT = [
    {
         "world_type": "OVERWORLD",
         "scanning_entities": False,
         "region_dir": OVERWORLD_REGION_DIR
    },
    
    {
         "world_type": "OVERWORLD",
         "scanning_entities": True,
         "region_dir": OVERWORLD_ENTITIES_DIR
    },
    
    {
         "world_type": "NETHER",
         "scanning_entities": False,
         "region_dir": NETHER_REGION_DIR
    },
    
    {
         "world_type": "NETHER",
         "scanning_entities": True,
         "region_dir": NETHER_ENTITIES_DIR
    },
    
    {
         "world_type": "END",
         "scanning_entities": False,
         "region_dir": END_REGION_DIR
    },
    
    {
         "world_type": "END",
         "scanning_entities": True,
         "region_dir": END_ENTITIES_DIR
    },
]


#### EXECUTE SCANS ####

if __name__ == "__main__":

    for region_dict in REGIONS_DICT:
        
        world_type = region_dict["world_type"]
        scanning_entities = region_dict["scanning_entities"]
        region_dir = region_dict["region_dir"]
        
        if not scanning_entities:
            scanning_obj_str = "block entities"
        else:
            scanning_obj_str = "entities"
        
        if region_dir.is_dir():
            
            print(f"{world_type} {scanning_obj_str} scan started!")
            print()
            print()
            
            region_dir_scan(
                region_dir=region_dir,
                world_type=world_type,
                scanning_entities=scanning_entities
            )
            
            print()
            print()
            print(f"{world_type} {scanning_obj_str} scan finished!")
        
        else:
            
            print(f"WARNING: directory {region_dir} does not exist!")
            print("Cannot execute scan.")
        
        print()
        print()
        print()
        print()
        print()

