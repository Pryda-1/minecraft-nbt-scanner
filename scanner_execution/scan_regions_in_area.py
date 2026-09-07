# -*- coding: utf-8 -*-

"""

Downloads and scans specific region files that are within or partially
within a rectangular area defined by the diagonal coordinates in
scanner_modules/txt_configs/world_type_diagonal_coords_of_area.txt, where
'world_type' is replaced with 'overworld', 'nether', or 'end'.

This txt file should be formatted as
 - line 1: X1, Z1
 - line 2: X2, Z2

"""


#### IMPORTS ####

from scanner_modules.scanning_config import (
    WORLD_FILES_ROOT_DIR, TXT_CONFIGS_DIR
)
from scanner_modules.helper_functions import (
    get_region_files_overlapping_rect_from_txt_file
)
from scanner_modules.sftp_functions import download_region_files
from scanner_modules.local_scan_functions import region_dir_scan


#### CONSTANTS ####

WORLD_TYPES = ["OVERWORLD", "NETHER", "END"]

OVERWORLD_AREA_DIAGONALS_FILE_PATH = (
    TXT_CONFIGS_DIR / "overworld_diagonal_coords_of_area.txt"
)
NETHER_AREA_DIAGONALS_FILE_PATH = (
    TXT_CONFIGS_DIR / "nether_diagonal_coords_of_area.txt"
)

OVERWORLD_REMOTE_REGION_DIR   = "world/region"
OVERWORLD_REMOTE_ENTITIES_DIR = "world/entities"

NETHER_REMOTE_REGION_DIR      = "world_nether/DIM-1/region"
NETHER_REMOTE_ENTITIES_DIR    = "world_nether/DIM-1/entities"

SPECIFIC_REGION_FILES_DIR  = WORLD_FILES_ROOT_DIR / "_specific_region_files"
OVERWORLD_REGION_FILES_DIR = SPECIFIC_REGION_FILES_DIR / "OVERWORLD"
NETHER_REGION_FILES_DIR    = SPECIFIC_REGION_FILES_DIR / "NETHER"


#### DOWNLOAD REGION FILES AND SCAN THEM ####

if __name__ == "__main__":
    
    for world_type in WORLD_TYPES:
        
        if world_type == "OVERWORLD":
            area_diagonals_file_path = OVERWORLD_AREA_DIAGONALS_FILE_PATH
            local_root_dir = OVERWORLD_REGION_FILES_DIR
            remote_region_dir   = OVERWORLD_REMOTE_REGION_DIR
            remote_entities_dir = OVERWORLD_REMOTE_ENTITIES_DIR
        elif world_type == "NETHER":
            area_diagonals_file_path = NETHER_AREA_DIAGONALS_FILE_PATH
            local_root_dir = NETHER_REGION_FILES_DIR
            remote_region_dir   = NETHER_REMOTE_REGION_DIR
            remote_entities_dir = NETHER_REMOTE_ENTITIES_DIR
        elif world_type == "END":
            continue
        else:
            raise Exception(f"Invalid world type: {world_type}.")
        
        regions = get_region_files_overlapping_rect_from_txt_file(
            area_diagonals_file_path
        )
    
        ## Block entities ##
        
        local_dir = local_root_dir / "region"
        local_dir.mkdir(exist_ok=True, parents=True)
        
        download_region_files(
            local_dir = local_dir,
            remote_region_dir = remote_region_dir,
            regions = regions,
        )
        
        region_dir_scan(
            region_dir = local_dir,
            world_type = world_type,
            scanning_entities = False,
            scan_chunk_fully = True,
        )
        
        ## Entities ##
        
        local_dir = local_root_dir / "entities"
        local_dir.mkdir(exist_ok=True, parents=True)
        
        download_region_files(
            local_dir = local_dir,
            remote_region_dir = remote_entities_dir,
            regions = regions,
        )
        
        region_dir_scan(
            region_dir = local_dir,
            world_type = world_type,
            scanning_entities = True,
            scan_chunk_fully = True,
        )

