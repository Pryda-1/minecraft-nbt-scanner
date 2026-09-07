# -*- coding: utf-8 -*-

"""

Functions that execute a scan of a given player data or region file.

"""


#### IMPORTS ####

from pathlib import Path

import itertools

import nbtlib
import anvil

from scanner_modules.helper_functions import (
    uuid_to_any_mc_name,
    check_if_skipping_area
)

from scanner_modules.checking_functions import (
    check_item,
    check_block_entity,
    check_entity,
)


#### SCANNING FUNCTIONS ####


def scan_playerdata_file(playerdata_file_path: Path):
    """
    Scans the given player data file located at playerdata_file_path.
    
    Returns the MC username, 'UUID' (in the name of the player data file),
    and the item ID of the flagged item if an item is flagged. Returns None
    otherwise.
    
    Note: if an item is flagged in the inventory, the function will skip
    scanning the equipment and ender chest. Similarly, if an item is flagged
    in the equipment, the function will skip scanning the ender chest.
    """
    
    player_nbt = nbtlib.load(playerdata_file_path)
    
    flag = False
    flagged_item_id = None
    
    ## Search inventory ##
    
    if "Inventory" in player_nbt:
        
        for item in player_nbt["Inventory"]:
            
            flag, flagged_item_id = check_item(item)
            
            if flag:
                break
    
    ## Search equipment if nothing flagged in inventory ##
    
    if not flag and "equipment" in player_nbt:
        
        for slot, item in player_nbt["equipment"].items():
            
            flag, flagged_item_id = check_item(item)
            
            if flag:
                break
    
    ## Search enderchest if nothing flagged in inventory & equipment ##
    
    if not flag and "EnderItems" in player_nbt:
        
        for item in player_nbt["EnderItems"]:
            
            flag, flagged_item_id = check_item(item)
            
            if flag:
                break
    
    ## Return the results if an item is flagged; None otherwise. ##
    
    if flag:
        
        uuid = playerdata_file_path.stem
        
        mc_username = uuid_to_any_mc_name(uuid)
        
        return {
            "username": mc_username,
            "uuid": uuid,
            "flagged_item_id": flagged_item_id
        }
        
    else:
        
        return None


def scan_region_file(
        region_file: Path,
        scanning_entities: bool,
        scan_chunk_fully: bool = True,
    ):
    """
    Scans a region file containing data about either block entities
    or entities.
    
    Inputs
    ------
    region_file: The path of the local region (.mca) file.
    scanning_entities: True if scanning entities; False if scanning block
        entities.
    scan_chunk_fully: True if scanning the chunk fully; False if stopping the
        scan of the chunk as soon as an entity or block entity is flagged.
    """
    
    if scanning_entities:
        scanning_obj = "Entities"
    else:
        scanning_obj = "block_entities"
    
    findings = []
    chunks_scanned = 0
    corrupt_chunks = []
    
    try:
        region = anvil.Region.from_file(str(region_file))
    except Exception as e:
        return {
            "chunks_scanned": 0,
            "findings": [],
            "corrupt_chunks": [],
            "corrupt_regions": [{
                "region": region_file.name,
                "error": repr(e),
            }]
        }
    
    ## ITERATE OVER THE CHUNKS WITHIN THE REGION FILE ##
    
    for cx, cz in itertools.product(range(32), repeat=2):

        try:
            chunk = region.chunk_data(cx, cz)
        except Exception as e:
            corrupt_chunks.append({
                "region": region_file.name,
                "cx": cx,
                "cz": cz,
                "error": repr(e),
            })
            continue
        
        if chunk is None or scanning_obj not in chunk:
            continue
        
        chunks_scanned += 1
        
        for obj in chunk[scanning_obj]:
            
            if scanning_entities:
                x = int(obj['Pos'][0].value)
                y = int(obj['Pos'][1].value)
                z = int(obj['Pos'][2].value)
            else:
                x = obj['x'].value
                y = obj['y'].value
                z = obj['z'].value
            
            # Stop scanning this chunk if skipping
            if check_if_skipping_area(x, y, z):
                break
            
            if scanning_entities:
                flag, obj_id, flagged_item_id = check_entity(obj)
            else:
                flag, obj_id, flagged_item_id = check_block_entity(obj)
            
            if flag:
                
                findings.append({
                    "region": region_file.name,
                    "cx": cx,
                    "cz": cz,
                    "x": x,
                    "y": y,
                    "z": z,
                    "obj_id": obj_id,
                    "flagged_item_id": flagged_item_id
                })
                
                # If not scan_chunk_fully, stop scanning chunk
                if not scan_chunk_fully:
                    break
    
    return {
        "chunks_scanned": chunks_scanned,
        "findings": findings,
        "corrupt_chunks": corrupt_chunks,
        "corrupt_regions": []
    }

