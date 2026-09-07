# -*- coding: utf-8 -*-

"""

Functions that execute a scan of files stored in a local directory.

"""


#### IMPORTS ####

from pathlib import Path

from datetime import datetime
import time

from concurrent.futures import (
    ProcessPoolExecutor,
    as_completed
)

from scanner_modules.scanning_config import (
    WorldType,
    NUM_PLAYERS_INTERVAL_TO_PRINT_ETA,
    NUM_REGIONS_INTERVAL_TO_PRINT_ETA
)

from scanner_modules.scanning_functions import (
    scan_playerdata_file,
    scan_region_file
)

from scanner_modules.results_writing_functions import (
    write_playerdata_scan_results,
    write_region_scan_results
)

from scanner_modules.helper_functions import format_duration


#### PLAYERDATA LOCAL DIRECTORY SCAN ####

def playerdata_dir_scan(playerdata_dir: Path):
    """
    Executes a scan of player data (.dat) files stored locally in
    playerdata_dir and writes the results.
    """
    
    findings = []
    
    # Timestamp used in the name of the results (.txt) file
    scan_timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    scan_start = time.perf_counter()
    
    total_players = len(list(playerdata_dir.glob("*.dat")))
    players_scanned = 0
    
    for playerdata_file_path in playerdata_dir.iterdir():
        
        if playerdata_file_path.suffix != ".dat": # Only load .dat files
            continue
        
        player_result = scan_playerdata_file(playerdata_file_path)
        
        if player_result is not None:
            findings.append(player_result)
        
        players_scanned += 1
        
        if players_scanned % NUM_PLAYERS_INTERVAL_TO_PRINT_ETA == 0:
            
            # Print estimated time left until scan completion
            
            elapsed = time.perf_counter() - scan_start
            
            avg_time_per_player = elapsed / players_scanned
            
            remaining_players = (
                total_players - players_scanned
            )
            
            eta_seconds = (
                avg_time_per_player * remaining_players
            )
            
            print(
                f"Scanned {players_scanned}/{total_players} "
                f"({100 * players_scanned / total_players:.1f}%) "
                f"- ETA: {format_duration(eta_seconds)}"
            )
    
    scan_duration = time.perf_counter() - scan_start
    
    # Write results into TXT file
    
    write_playerdata_scan_results(
        scan_timestamp = scan_timestamp,
        players_scanned = players_scanned,
        findings = findings,
        scan_duration = scan_duration,
    )


#### REGIONS LOCAL DIRECTORY SCAN ####

def region_dir_scan(
        region_dir: Path,
        world_type: WorldType,
        scanning_entities: bool,
        scan_chunk_fully: bool = True,
    ):
    
    """
    Scans region files containing data about the block entities (typically
    stored in the 'region' folder) or entities (typically stored in the
    'entities' folder), then writes the results of flagged block entities or
    entites. Data about both are stored in region (.mca) files.
    
    AI helped with the code to parallelise the scanning across cores and
    threads of the CPU using functionality from `concurrent.futures`.
    
    Inputs
    ------
    region_dir: The directory containing the local region (.mca) files.
    world_type: "OVERWORLD", "NETHER", "END".
    scanning_entities: True if scanning entities; False if scanning block
        entities.
    scan_chunk_fully: True if scanning the chunk fully; False if stopping the
        scan of the chunk as soon as an entity or block entity is flagged.
    """
    
    # Timestamp used in the name of the results (.txt) file
    scan_timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    regions_scanned = 0
    chunks_scanned = 0
    findings = []
    corrupt_chunks = []
    corrupt_regions = []
    
    region_files = [
        f for f in region_dir.glob("*.mca")
        if f.stat().st_size > 0
    ]
    total_regions = len(region_files)
    
    scan_start = time.perf_counter()
    
    with ProcessPoolExecutor() as executor:
        
        futures = [
            executor.submit(
                scan_region_file,
                region_file,
                scanning_entities,
                scan_chunk_fully
            )
            for region_file in region_files
        ]
        
        for future in as_completed(futures):
            
            region_results = future.result()        
            
            chunks_scanned += region_results["chunks_scanned"]
            findings.extend(region_results["findings"])
            corrupt_chunks.extend(region_results["corrupt_chunks"])
            corrupt_regions.extend(region_results["corrupt_regions"])
    
            regions_scanned += 1
            
            if regions_scanned % NUM_REGIONS_INTERVAL_TO_PRINT_ETA == 0:
                
                # Print estimated time left until scan completion
                
                elapsed = time.perf_counter() - scan_start
    
                avg_time_per_region = elapsed / regions_scanned
    
                remaining_regions = (
                    total_regions - regions_scanned
                )
    
                eta_seconds = avg_time_per_region * remaining_regions
    
                print(
                    f"Scanned {regions_scanned}/{total_regions} "
                    f"({100 * regions_scanned / total_regions:.1f}%) "
                    f"- ETA: {format_duration(eta_seconds)}"
                )
    
    scan_duration = time.perf_counter() - scan_start
    
    # Write results into TXT file
    
    write_region_scan_results(
        
        scan_timestamp = scan_timestamp,
        scan_duration = scan_duration,
        
        regions_scanned = regions_scanned,
        chunks_scanned = chunks_scanned,
        findings = findings,
        corrupt_chunks = corrupt_chunks,
        corrupt_regions = corrupt_regions,
        
        world_type = world_type,
        scanning_entities = scanning_entities,
        
    )

