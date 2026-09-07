# -*- coding: utf-8 -*-

"""

Functions that write the results of the findings into TXT files.

"""


#### IMPORTS ####

from pathlib import Path

from scanner_modules.scanning_config import (
    LOCAL_SCAN_RESULTS_DIR, WorldType
)

from scanner_modules.helper_functions import to_world_coords


#### RESULTS WRITING FUNCTIONS: LOCAL SCANS ####


def write_playerdata_scan_results(*,
        scan_timestamp,
        players_scanned: int,
        findings,
        scan_duration,
    ):
    """
    Writes the results of a scan of locally stored player data files into a
    TXT file.
    """
    
    playerdata_report_file = (
        LOCAL_SCAN_RESULTS_DIR / 
        f"playerdata_scan_{scan_timestamp}.txt"
    )
    
    with open(playerdata_report_file, "w", encoding="utf-8") as f:
        
        f.write("=========== PLAYER DATA SCAN ===========\n\n")
        f.write(f"Total players scanned: {players_scanned}\n")
        f.write(f"Players with a flagged item: {len(findings)}\n")
        f.write(f"Scan duration: {scan_duration:.2f} seconds\n\n")
        f.write("=" * 40 + "\n\n\n")
        
        for finding in findings:
            
            username        = finding["username"]
            uuid            = finding["uuid"]
            flagged_item_id = finding["flagged_item_id"]
            
            f.write(f"Player:  {username}  [ {uuid} ]\n")
            f.write(f"Flagged item:  {flagged_item_id}\n\n")


def write_region_scan_results(*,
        scan_timestamp,
        scan_duration,
        regions_scanned: int,
        chunks_scanned: int,
        findings,
        corrupt_chunks,
        corrupt_regions,
        world_type: WorldType,
        scanning_entities: bool,
    ):
    """
    Writes the results of a scan of locally stored region files into a
    TXT file.
    """
    
    if scanning_entities:
        scan_type_title     = "ENTITIES"
        scan_type_line      = "Entity"
        scan_file_name_part = "ENTITIES"
    else:
        scan_type_title     = "BLOCK ENTITIES"
        scan_type_line      = "Block entity"
        scan_file_name_part = "BLOCK_ENTITIES"
    
    # Sort the findings by the coordinates
    findings.sort(
        key=lambda f: (
            f["x"],
            f["z"],
            f["y"]
        )
    )
    
    report_file = (
        LOCAL_SCAN_RESULTS_DIR / 
        f"{world_type}_{scan_file_name_part}_scan_{scan_timestamp}.txt"
    )
    
    with open(report_file, "w", encoding="utf-8") as f:
    
        f.write(f"======== {world_type} {scan_type_title} SCAN ========\n\n")
        f.write(f"Total regions scanned: {regions_scanned}\n")
        f.write(f"Total chunks scanned: {chunks_scanned}\n")
        f.write(f"Flagged chunks: {len(findings)}\n")
        f.write(f"Scan duration: {scan_duration:.2f} seconds\n\n")
        f.write("=" * (24 + len(world_type) + len(scan_type_title)) + "\n\n")
        
        ## Report the findings ##
        
        for finding in findings:
            
            region  = finding["region"]
            cx, cz  = finding["cx"], finding["cz"]
            x, y, z = finding['x'], finding['y'], finding['z']
            obj_id  = finding['obj_id']
            flagged_item_id = finding['flagged_item_id']
            
            f.write(f"Chunk ({cx}, {cz}) in region {region}\n")
            f.write(f"{scan_type_line}: {obj_id}\n")
            f.write(f"Coords: {x} {y} {z}\n")
            f.write(f"Flagged item: {flagged_item_id}\n\n")
        
        f.write("=" * (24 + len(world_type) + len(scan_type_title)) + "\n\n")
        
        ## Report corrupt chunks (error when loading chunk data) ##
        
        f.write("\n\n\n")
        f.write("====== CORRUPT CHUNKS ======\n\n")
        
        for corrupt_chunk in corrupt_chunks:
            
            region = corrupt_chunk["region"]
            region_name_splitted = region.split(".")
            rx, rz = int(region_name_splitted[1]), int(region_name_splitted[2])
            cx, cz = corrupt_chunk["cx"], corrupt_chunk["cz"]
            x, z   = to_world_coords(rx, rz, cx, cz)
            error  = corrupt_chunk["error"]
            
            f.write(f"Chunk ({cx}, {cz}) in region {region}\n")
            f.write(f"Coordinates (x, z): ({x}, {z})\n")
            f.write(f"ERROR: {error}\n\n")
        
        f.write("=" * 28 + "\n\n")
        
        ## Report corrupt regions (error when loading region file) ##
        
        f.write("\n\n")
        f.write("====== CORRUPT REGIONS ======\n\n")
        
        for corrupt_region in corrupt_regions:
            
            region = corrupt_region["region"]
            error  = corrupt_region["error"]
            
            f.write(f"Region: {region}\n")
            f.write(f"ERROR: {error}\n\n")
        
        f.write("=" * 29 + "\n")


#### RESULTS WRITING FUNCTIONS: SFTP SCANS ####


def update_sftp_region_scan_results(*,
        new_findings: list,
        corrupt_chunks: list,
        corrupt_regions: list,
        region_name: str,
        findings_file_path: Path,
        corrupt_chunks_file_path: Path,
        corrupt_regions_file_path: Path,
        regions_scanned_file_path: Path,
    ):
    """
    Opens the existing TXT file where the region scan results are stored
    to update it based on any new findings from the latest region scanned.
    Also writes corrupt chunks and regions (chunks and regions that could
    not be read) into separate files.
    Also writes the names of regions scanned into a file so the scan can
    be resumed by skipping these files.
    """
    
    ## Findings file ##
    
    with open(findings_file_path, "a", encoding="utf-8") as f:
        
        for finding in new_findings:
            
            region  = finding["region"]
            cx, cz  = finding["cx"], finding["cz"]
            x, y, z = finding['x'], finding['y'], finding['z']
            obj_id  = finding['obj_id']
            flagged_item_id = finding['flagged_item_id']
            
            f.write(f"Chunk ({cx}, {cz}) in region {region}\n")
            f.write(f"Object ID: {obj_id}\n")
            f.write(f"Coords: {x} {y} {z}\n")
            f.write(f"Flagged item: {flagged_item_id}\n\n")
    
    ## Corrupt chunks ##
    
    with open(corrupt_chunks_file_path, "a", encoding="utf-8") as f:
        
        for corrupt_chunk in corrupt_chunks:
            
            region = corrupt_chunk["region"]
            region_name_splitted = region.split(".")
            rx, rz = int(region_name_splitted[1]), int(region_name_splitted[2])
            cx, cz = corrupt_chunk["cx"], corrupt_chunk["cz"]
            x, z   = to_world_coords(rx, rz, cx, cz)
            error  = corrupt_chunk["error"]
            
            f.write(f"Chunk ({cx}, {cz}) in region {region}\n")
            f.write(f"Coordinates (x, z): ({x}, {z})\n")
            f.write(f"ERROR: {error}\n\n")
    
    ## Corrupt region files ##
    
    with open(corrupt_regions_file_path, "a", encoding="utf-8") as f:
        
        for corrupt_region in corrupt_regions:
            
            region = corrupt_region["region"]
            error  = corrupt_region["error"]
            
            f.write(f"Region: {region}\n")
            f.write(f"ERROR: {error}\n\n")
    
    ## Add region name into the regions scanned file ##
    
    with open(regions_scanned_file_path, "a", encoding="utf-8") as f:
        
        f.write(region_name + "\n")

