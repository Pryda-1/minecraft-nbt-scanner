# -*- coding: utf-8 -*-

"""

Helper functions.

"""


#### IMPORTS ####

from pathlib import Path
import json
import numpy as np
import requests
from uuid import UUID
import urllib.error
import urllib.request

from scanner_modules.scanning_config import COORDS_TO_SKIP, AREA_RADIUS


#### HELPER FUNCTIONS ####


def uuid_to_name(uuid):
    """
    Fetch the username of the player given the player's UUID.
    
    AI generated this function.
    """
    
    uuid = uuid.replace("-", "")
    url = f"https://api.mojang.com/user/profile/{uuid}"
    return requests.get(url).json()["name"]


def floodgate_uuid_to_name(uuid_str, floodgate_prefix="_"):
    """
    Fetch the username of a Bedrock/Floodgate player from their
    Floodgate UUID.
    
    By default, assumes this server uses '_' as the Floodgate
    username prefix.
    
    AI generated this function.
    """
    
    try:
        u = UUID(str(uuid_str))
    except ValueError:
        return None
    
    # Floodgate-style UUIDs often look like:
    # 00000000-0000-0000-0009-0000042d9f07
    # For these, the upper 64 bits are zero and the lower 64 bits contain
    # the XUID
    if (u.int >> 64) != 0:
        return None

    xuid = u.int & ((1 << 64) - 1)

    if xuid == 0:
        return None

    url = f"https://api.geysermc.org/v2/xbox/gamertag/{xuid}"

    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.load(response)
    except (
        urllib.error.HTTPError,
        urllib.error.URLError,
        TimeoutError,
        json.JSONDecodeError,
    ):
        return None

    gamertag = data.get("gamertag")

    if not gamertag:
        return None

    return floodgate_prefix + gamertag


def uuid_to_any_mc_name(uuid_str):
    """
    Given the 'UUID' that appears in the name of the player data file,
    fetch the username of the player.
    
    Try Java UUID lookup first, then Floodgate/Bedrock lookup.
    """
    
    mc_username = None
    
    try:
        mc_username = uuid_to_name(uuid_str)
    except:
        mc_username = None
    
    if mc_username is None:
        mc_username = floodgate_uuid_to_name(uuid_str)
    
    if mc_username is None:
        mc_username = "Unknown (offline / not found)"
    
    return mc_username


def format_duration(seconds):
    """ Format the duration in seconds to more readable values. """
    
    if seconds < 60:
        return f"{seconds:.0f}s"
    
    if seconds < 3600:
        return f"{seconds/60:.1f}m"
    
    return f"{seconds/3600:.1f}h"


def get_region_coords(file: Path):
    """
    Given the path of a region file r.X.Z.mca, return the region
    coordinates X and Z as integers.
    """
    _, x, z = file.stem.split(".")
    return int(x), int(z)


def to_world_coords(region_x, region_z, cx, cz):
    """
    Returns the world coords of the centre-ish block of a chunk located at
    (cx, cz) within a region (region_x, region_z).
    """
    return (
        16 * (region_x * 32 + cx) + 8,
        16 * (region_z * 32 + cz) + 8,
    )


def check_if_skipping_area(x, y, z):
    """
    Given coordinates (x, y, z) of a block entity or entity, return True if
    not scanning it because its distance to one of the coordinates in
    COORDS_TO_SKIP is less than AREA_RADIUS. Otherwise, return False.
    """
    
    cur_coords = np.array([x, y, z])
    
    if len(COORDS_TO_SKIP) > 0 and any(
            (
                np.sqrt(np.sum((cur_coords - COORDS_TO_SKIP[i]) ** 2))
                < AREA_RADIUS
            )
            for i in range(len(COORDS_TO_SKIP))
        ):
        return True
    
    return False


def parse_region_name(region_name: str):
    """ Given a string 'r.rX.rZ(.mca)', returns (rX, rZ). """
    
    region_name = Path(region_name).name

    if region_name.endswith(".mca"):
        region_name = region_name[:-4]

    _, rX, rZ = region_name.split(".")
    return (int(rX), int(rZ))


def get_region_coords_from_world_coordinates(x: float, z: float):
    """
    Given coordinates (x, z), returns (rX, rZ), the region coordinates
    of the region the given coordinates are in.
    """
    return int(np.floor(x / 512)), int(np.floor(z / 512))


def get_region_files_overlapping_rect(x1: int, z1: int, x2: int, z2: int):
    """
    Given two diagonal (x, z) coordinates of a rectangular area, return
    the names of all region files that overlap completely or partially
    within the rectangle.
    """
    
    x_min, x_max = sorted((x1, x2))
    z_min, z_max = sorted((z1, z2))
    
    rX_min = x_min // 512
    rX_max = x_max // 512
    
    rZ_min = z_min // 512
    rZ_max = z_max // 512
    
    region_files = []
    
    for rX in range(rX_min, rX_max + 1):
        for rZ in range(rZ_min, rZ_max + 1):
            region_files.append(f"r.{rX}.{rZ}.mca")
    
    return region_files


def get_region_files_overlapping_rect_from_txt_file(
        area_diagonals_file_path: Path
    ):
    """
    Reads in the diagonal coordinates from the TXT file located at
    area_diagonals_file_path in txt_configs, then calls and returns
    get_region_files_overlapping_rect (see above).
    
    The TXT file needs to be formatted as
    - line 1: x1 z1
    - line 2: x2 z2
    
    x1, z1, x2, and z2 should be integers.
    """
    
    with open(area_diagonals_file_path, "r") as file:
        x1, z1 = file.readline().strip().split()
        x2, z2 = file.readline().strip().split()
    
    # Convert from strings to integers
    x1, z1 = int(x1), int(z1)
    x2, z2 = int(x2), int(z2)
    
    return get_region_files_overlapping_rect(x1, z1, x2, z2)

