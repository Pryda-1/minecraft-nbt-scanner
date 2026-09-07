# -*- coding: utf-8 -*-

"""

For servers that use SFTP for transferring server files, they can be
downloaded via SFTP and processed.

This module defines functions for loading the SFTP authentication config, 
opening a SFTP connection with the server, and for downloading specific
player data and region files.

The SFTP config is stored in a TXT file called sftp_config.txt located at
SFTP_CONFIG_FILE_PATH. It should be formatted the following way.

server_address
port_number
username
password

That is, the authentication uses a username and password. If another kind of
authentication is used, edit the functions accordingly.

AI helped write the code for connecting to a server and downloading files
via SFTP.

"""


#### IMPORTS ####

from pathlib import Path, PurePosixPath

import paramiko

from scanner_modules.scanning_config import SFTP_CONFIG_FILE_PATH


#### FUNCTIONS ####


def load_sftp_config():
    """
    Loads the SFTP config stored at SFTP_CONFIG_FILE_PATH and returns the
    results. It should be formatted as:
    
    Server address/IP
    Port number
    Username
    Password
    
    This is assuming the username and password is used to authenticate the
    connection to the server. Alter this and any other corresponding functions
    if authentication works differently.
    
    Returns
    -------
    A dictionary containing 'sftp_server_addr', 'sftp_port', 'sftp_username',
    and 'sftp_password'
    """
    
    sftp_config_file_content = SFTP_CONFIG_FILE_PATH.read_text()
    
    sftp_config_file_lines = [
        line
        for line in sftp_config_file_content.splitlines()
        if line.strip() # Skip blank lines
    ]
    
    return {
        "sftp_server_addr":  sftp_config_file_lines[0],
        "sftp_port":         int(sftp_config_file_lines[1]),
        "sftp_username":     sftp_config_file_lines[2],
        "sftp_password":     sftp_config_file_lines[3],
    }


def open_sftp_connection():
    """ Loads SFTP config and opens a connection with the server. """
    
    config = load_sftp_config()

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    client.connect(
        hostname=config["sftp_server_addr"],
        port=config["sftp_port"],
        username=config["sftp_username"],
        password=config["sftp_password"],
    )

    sftp = client.open_sftp()

    return client, sftp


def download_playerdata_files(*,
        local_dir: Path,
        remote_playerdata_dir: str,
        playerdata_files: list[str],
    ):
    """
    Downloads player data files specified in playerdata_files from
    remote_playerdata_dir and stores them in local_dir.
    
    playerdata_files can contain either
        f"{uuid}.dat"
    or
        f"{uuid}",
    for some uuid or whatever the name of the player data file is.
    """
    
    local_dir.mkdir(parents=True, exist_ok=True)

    client = None
    sftp = None
    
    total_playerdata_files = len(playerdata_files)
    
    if total_playerdata_files >= 10:
        # Will print the verbose 10 times
        files_to_print_verbose = total_playerdata_files // 10
    else:
        # Print verbose every iteration
        files_to_print_verbose = 1
    
    try:
        client, sftp = open_sftp_connection()

        for i, file in enumerate(sorted(playerdata_files)):
            
            if not file.endswith(".dat"):
                filename = f"{file}.dat"
            else:
                filename = file

            remote_path = str(PurePosixPath(remote_playerdata_dir) / filename)
            local_path = local_dir / filename
            
            # Skip downloading player data files that already exist
            # If you wish to redownload them, delete them first
            if local_path.exists():
                print(f"Skipping existing file: {local_path}")
                continue
            
            try:
                sftp.get(remote_path, str(local_path))
                
            except FileNotFoundError:
                print(f"Remote file does not exist, skipping: {remote_path}")
                pass
                
            except OSError as exc:
                # Some SFTP servers/Paramiko versions report missing files
                # as OSError
                print(f"Could not download {remote_path}, skipping.")
                print(f"  Error: {repr(exc)}")
                
                # Remove any partial local file.
                local_path.unlink(missing_ok=True)
                
            if i % files_to_print_verbose == 0:
                print(f"{i+1} out of {total_playerdata_files} "
                      + "player data files processed.")
            
        print("\nFinished downloading region files.\n")
        
    finally:
        if sftp is not None:
            sftp.close()
        if client is not None:
            client.close()


def sftp_download_region_file(
        sftp,
        remote_region_file_path: str,
        cache_dir: Path
    ) -> Path:
    """
    Downloads one region file located remotely at remote_region_file_path
    and returns the local Path of the downloaded file.
    """
    
    local_path = cache_dir / Path(remote_region_file_path).name
    
    sftp.get(remote_region_file_path, local_path)
    
    return local_path


def download_region_files(*,
        local_dir: Path,
        remote_region_dir: str,
        regions: list[str],
    ):
    """
    Downloads region files in regions from remote_region_dir and stores
    them in local_dir.

    regions can contain either:
        "r.-20.10"
    or:
        "r.-20.10.mca"
    """

    local_dir.mkdir(parents=True, exist_ok=True)

    client = None
    sftp = None
    
    total_regions = len(regions)
    
    if total_regions >= 10:
        # Will print the verbose 10 times
        regions_to_print_verbose = total_regions // 10
    else:
        # Print verbose every iteration
        regions_to_print_verbose = 1
        
    try:
        client, sftp = open_sftp_connection()
        
        for i, region in enumerate(sorted(regions)):
            
            if not region.endswith(".mca"):
                filename = f"{region}.mca"
            else:
                filename = region
            
            remote_path = str(PurePosixPath(remote_region_dir) / filename)
            local_path = local_dir / filename
            
            if local_path.exists():
                print(f"Skipping existing file: {local_path}")
                continue
            
            try:
                sftp.get(remote_path, str(local_path))

            except FileNotFoundError:
                # print(f"Remote file does not exist, skipping: {remote_path}")
                pass

            except OSError as exc:
                # Some SFTP servers/Paramiko versions report missing files
                # as OSError
                print(f"Could not download {remote_path}, skipping.")
                print(f"  Error: {repr(exc)}")

                # Remove any partial local file.
                local_path.unlink(missing_ok=True)
            
            if i % regions_to_print_verbose == 0:
                print(f"{i+1} out of {total_regions} regions processed.")

        print("\nFinished downloading region files.\n")
        
    finally:
        if sftp is not None:
            sftp.close()
        if client is not None:
            client.close()

