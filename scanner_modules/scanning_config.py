# -*- coding: utf-8 -*-

"""

Constants and parameters used throughout scanner_modules.

See checking_functions.py for the constants and functions used for
checking items, block entities, and entities.

"""


#### IMPORTS ####

from pathlib import Path
from typing import Literal
import numpy as np


#### LITERALS ####

WorldType = Literal["OVERWORLD", "NETHER", "END"]


#### DIRECTORIES & PATHS ####

# PROJECT_ROOT/scanner_functions
PROJECT_ROOT_DIR = Path(__file__).resolve().parent.parent

# Root directory to store the world files locally for scanning
WORLD_FILES_ROOT_DIR = PROJECT_ROOT_DIR / "_local_world_files"
WORLD_FILES_ROOT_DIR.mkdir(exist_ok=True, parents=True)

# Root directory to store the scan results
RESULTS_ROOT_DIR = PROJECT_ROOT_DIR / "_scan_results"
RESULTS_ROOT_DIR.mkdir(exist_ok=True, parents=True)

# Directory to store the scan results of a scan on local files
LOCAL_SCAN_RESULTS_DIR = RESULTS_ROOT_DIR / "_local_scan_results"
LOCAL_SCAN_RESULTS_DIR.mkdir(exist_ok=True, parents=True)

# Directory to store the scan results of a scan on remote files (via SFTP)
# Specifically used by the functions in .sftp_scanning_functions
SFTP_SCAN_RESULTS_DIR = RESULTS_ROOT_DIR / "_sftp_scan_results"
SFTP_SCAN_RESULTS_DIR.mkdir(exist_ok=True, parents=True)

# Root directory of where to cache region files that are ready to be scanned
ROOT_CACHE_DIR = PROJECT_ROOT_DIR / "_scanner_cache"
ROOT_CACHE_DIR.mkdir(exist_ok=True, parents=True)

# Directory of the config TXT files
TXT_CONFIGS_DIR = Path(__file__).parent / "txt_configs"
TXT_CONFIGS_DIR.mkdir(exist_ok=True, parents=True)
SFTP_CONFIG_FILE_PATH    = TXT_CONFIGS_DIR / "sftp_config.txt"
COORDS_TO_SKIP_FILE_PATH = TXT_CONFIGS_DIR / "coords_to_skip.txt"


#### ETA PRINTING CONSTANTS ####

# Print ETA every 500 (or whatever) player data files scanned
NUM_PLAYERS_INTERVAL_TO_PRINT_ETA = 500
# Print ETA every 1000 (or whatever) region files scanned
NUM_REGIONS_INTERVAL_TO_PRINT_ETA = 1000

# Estimates of how many total region files exist (of a given dimension)
# Set to None if unknown
OVERWORLD_TOTAL_REGIONS_EST = None
NETHER_TOTAL_REGIONS_EST    = None
END_TOTAL_REGIONS_EST       = None


#### COORDS TO SKIP CONSTANTS ####

try:
    
    coords_file_content = COORDS_TO_SKIP_FILE_PATH.read_text()
    
    COORDS_TO_SKIP = [
        np.array([int(num) for num in line.split(",")]) 
        for line in coords_file_content.splitlines()
        if line.strip() # Skip blank lines
    ]
    
except FileNotFoundError:
    
    print()
    print(f"Error: The file '{COORDS_TO_SKIP_FILE_PATH}' could not be found.")
    print("There will be no coordinates to skip.")
    print()
    
    COORDS_TO_SKIP = []

# Block entities and entities within this distance (radius) from each set
# of coordinates in COORDS_TO_SKIP will not be scanned
AREA_RADIUS = 500

