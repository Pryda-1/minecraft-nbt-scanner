# -*- coding: utf-8 -*-

"""

Functions that execute a scan of files stored remotely, specifically region
files.

For each region file, these functions download them, scan them, write any
results, then delete them afterwards. That is, once a region file is processed,
it is deleted afterwards. That way, not much storage is required because only
a limited number of region files are stored locally at any time.

Functionality from concurrent.futures is used to distribute the work across
all cores/threads of the CPU, making the scanner significantly faster.

AI helped write a lot of the code in this module, especially code utilising
functionality from the libraries concurrent.futures, threading, and queue,
and any SFTP-related code.

"""


#### IMPORTS ####

import os
from pathlib import Path

from datetime import datetime
import time

from concurrent.futures import (
    ProcessPoolExecutor
)
import threading
from queue import Queue, Empty

from scanner_modules.scanning_config import (
    ROOT_CACHE_DIR,
    SFTP_SCAN_RESULTS_DIR,
    WorldType,
    NUM_REGIONS_INTERVAL_TO_PRINT_ETA,
    OVERWORLD_TOTAL_REGIONS_EST,
    NETHER_TOTAL_REGIONS_EST,
    END_TOTAL_REGIONS_EST
)

from scanner_modules.helper_functions import (
    format_duration, parse_region_name
)

from scanner_modules.scanning_functions import scan_region_file

from scanner_modules.results_writing_functions import (
    update_sftp_region_scan_results
)

from scanner_modules.sftp_functions import (
    open_sftp_connection,
    sftp_download_region_file
)


#### CONSTANTS ####

SENTINEL = object()


#### SFTP SCANNING HELPER FUNCTIONS ####


def sftp_downloader_worker(
        remote_queue,
        downloaded_queue,
        download_error_queue,
        cache_dir: Path,
        max_download_attempts=3,
    ):
    """
    Worker that downloads region files from the SFTP server.
    
    Retrieves remote region-file paths from remote_queue, downloads each
    file to cache_dir, and places successfully downloaded files onto
    downloaded_queue for scanning. Failed downloads are retried up to
    max_download_attempts times, with a new SFTP connection established
    between attempts. Files that still fail after all attempts are placed
    onto download_error_queue.
    
    The worker terminates when it receives SENTINEL from remote_queue.
    """
    
    client = None
    sftp = None

    try:
        client, sftp = open_sftp_connection()

        while True:
            item = remote_queue.get()

            try:
                if item is SENTINEL:
                    return

                remote_region_file_path, download_start = item
                
                local_region_file = (
                    cache_dir / Path(remote_region_file_path).name
                )

                for attempt in range(1, max_download_attempts + 1):
                    
                    try:
                        
                        sftp_download_region_file(
                            sftp,
                            remote_region_file_path,
                            cache_dir,
                        )

                        downloaded_queue.put(
                            (local_region_file, download_start)
                        )
                        
                        break

                    except Exception as exc:
                        
                        local_region_file.unlink(missing_ok=True)

                        if attempt == max_download_attempts:
                            download_error_queue.put(
                                (remote_region_file_path, repr(exc))
                            )
                        else:
                            if sftp is not None:
                                sftp.close()
                            if client is not None:
                                client.close()

                            time.sleep(2 * attempt)
                            client, sftp = open_sftp_connection()
            
            finally:
                remote_queue.task_done()
    
    finally:
        if sftp is not None:
            sftp.close()
        if client is not None:
            client.close()


#### SFTP SCANNING FUNCTIONS ####


def start_sftp_region_source_scan(*,
        remote_region_dir: str,
        world_type: WorldType,
        scanning_entities: bool,
        
        max_regions_to_scan=None,
        
        max_download_workers: int = 10,
        max_scan_workers: int = None,
        max_in_flight: int = None,
        
        already_scanned_regions: set,
        
        findings_file_path: Path,
        corrupt_chunks_file_path: Path,
        corrupt_regions_file_path: Path,
        regions_scanned_file_path: Path,
    ):
    """
    Starts the actual scan of the region files using SFTP. This function is
    called in sftp_region_source_scan. See sftp_region_source_scan below for
    more details.
    """
    
    regions_scanned = 0
    regions_submitted = 0
    chunks_scanned = 0
    
    # Used to print estimated time left every now and then based on how many
    # total region files there are. If total_regions is None, however, this
    # will not ever be printed. See scanner_modules.scanning_config for more
    # details.
    total_regions = {
        "OVERWORLD": OVERWORLD_TOTAL_REGIONS_EST,
        "NETHER": NETHER_TOTAL_REGIONS_EST,
        "END": END_TOTAL_REGIONS_EST,
    }[world_type]
    
    if max_scan_workers is None:
        max_scan_workers = os.cpu_count()
    
    regions_in_flight = 0
    
    if max_in_flight is None:
        max_in_flight = max_scan_workers * 4
    
    if max_in_flight < max_download_workers:
        raise ValueError(
            "max_in_flight should be at least max_download_workers"
        )
    
    if scanning_entities:
        cache_dir = ROOT_CACHE_DIR / world_type / "entities"
    else:
        cache_dir = ROOT_CACHE_DIR / world_type / "region"
    cache_dir.mkdir(exist_ok=True, parents=True)
    
    scan_start = time.perf_counter()
    
    # Use one SFTP connection only for listing remote files.
    list_client, list_sftp = open_sftp_connection()
    
    try:
        remote_files = list_sftp.listdir_iter(remote_region_dir)

        remote_queue = Queue(maxsize=max_download_workers * 2)
        downloaded_queue = Queue()
        download_error_queue = Queue()

        download_threads = []
        
        for _ in range(max_download_workers):
            t = threading.Thread(
                target=sftp_downloader_worker,
                args=(
                    remote_queue, downloaded_queue,
                    download_error_queue, cache_dir
                ),
            )
            t.start()
            download_threads.append(t)
        
        try:
            with ProcessPoolExecutor(
                    max_workers=max_scan_workers
            ) as scan_executor:
        
                scan_futures = {}
                remote_files_exhausted = False
        
                while True:
        
                    ## Feed downloader queue ##
                    while (
                        not remote_files_exhausted
                        and remote_queue.qsize() < max_download_workers * 2
                        and regions_in_flight < max_in_flight
                    ):
                        
                        if (
                            max_regions_to_scan is not None
                            and regions_submitted >= max_regions_to_scan
                        ):
                            remote_files_exhausted = True
                            break
                        
                        try:
                            region_attrs = next(remote_files)
                        except StopIteration:
                            remote_files_exhausted = True
                            break
                        
                        if region_attrs.st_size == 0:
                            continue
                        
                        region_filename = region_attrs.filename
                        
                        if not region_filename.endswith(".mca"):
                            continue
                        
                        # Skip region files that are already scanned
                        rX, rZ = parse_region_name(region_filename)
                        if (rX, rZ) in already_scanned_regions:
                            continue
                        
                        remote_region_file_path = (
                            f"{remote_region_dir}/{region_filename}"
                        )
                        
                        remote_queue.put(
                            (remote_region_file_path, time.perf_counter())
                        )
                        
                        regions_submitted += 1
                        regions_in_flight += 1
                    
                    ## Move downloaded files into scan pool ##
                    while True:
                        
                        try:
                            local_region_file, download_start = (
                                downloaded_queue.get_nowait()
                            )
                        except Empty:
                            break
                        
                        scan_future = scan_executor.submit(
                            scan_region_file,
                            local_region_file,
                            scanning_entities,
                        )
        
                        scan_futures[scan_future] = local_region_file
                    
                    ## Collect completed scans ##
                    done_scans = [
                        f for f in scan_futures
                        if f.done()
                    ]
                    
                    for scan_future in done_scans:
                        local_region_file = scan_futures.pop(scan_future)
        
                        try:
                            region_results = scan_future.result()
                            
                            update_sftp_region_scan_results(
                                
                                new_findings=region_results["findings"],
                                corrupt_chunks=
                                    region_results["corrupt_chunks"],
                                corrupt_regions=
                                    region_results["corrupt_regions"],
                                region_name=local_region_file.stem,
                                
                                findings_file_path=findings_file_path,
                                corrupt_chunks_file_path=
                                    corrupt_chunks_file_path,
                                corrupt_regions_file_path=
                                    corrupt_regions_file_path,
                                regions_scanned_file_path=
                                    regions_scanned_file_path,
                                
                            )
                            
                            chunks_scanned += region_results["chunks_scanned"]
                            
                        finally:
                            local_region_file.unlink(missing_ok=True)
                            regions_in_flight -= 1
                        
                        regions_scanned += 1
                        
                        ## Print estimated time left ##
                        if (
                                total_regions is not None and
                                regions_scanned %
                                NUM_REGIONS_INTERVAL_TO_PRINT_ETA
                                == 0
                            ):
                            
                            elapsed = time.perf_counter() - scan_start
                            avg_time_per_region = elapsed / regions_scanned
                            remaining_regions = (
                                total_regions - regions_scanned
                            )
                            percentage_regions_scanned = (
                                100 * regions_scanned / total_regions
                            )
                            eta_seconds = (
                                avg_time_per_region * remaining_regions
                            )
                            
                            print(
                                f"Scanned {regions_scanned}/{total_regions} "
                                f"({percentage_regions_scanned:.1f}%) "
                                f"- ETA: {format_duration(eta_seconds)}"
                            )
                        
                        ## Print some other stuff ##
                        if (
                                regions_scanned %
                                (4 * NUM_REGIONS_INTERVAL_TO_PRINT_ETA)
                                == 0
                            ):
                            
                            print(
                                f"In flight: {regions_in_flight}, "
                                f"scan futures: {len(scan_futures)}, "
                                f"remote queue: {remote_queue.qsize()}, "
                                f"downloaded queue: {downloaded_queue.qsize()}"
                            )
                        
                        print()
                        
                    if (
                        remote_files_exhausted
                        and regions_scanned == regions_submitted
                        and downloaded_queue.empty()
                        and not scan_futures
                    ):
                        break
                    
                    try:
                        failed_remote_file, error_text = (
                            download_error_queue.get_nowait()
                        )
                    except Empty:
                        pass
                    else:
                        raise RuntimeError(
                            f"Failed to download {failed_remote_file}:"
                            f" {error_text}"
                        )
                    
                    time.sleep(0.05)
            
            
            print("Regions scanned:", regions_scanned)
            print("Chunks scanned:", chunks_scanned)
            
        finally:
            
            # Tell downloader threads to stop
            for _ in range(max_download_workers):
                remote_queue.put(SENTINEL)
        
            remote_queue.join()
        
            for t in download_threads:
                t.join()
            
    finally:
        list_sftp.close()
        list_client.close()


def sftp_region_source_scan(
        remote_region_dir: str,
        world_type: WorldType,
        scanning_entities: bool,
        max_regions_to_scan: int = None,
        max_download_workers: int = 10,
        max_scan_workers: int = None,
        max_in_flight: int = None,
        resume_regions_file_path: Path = None,
    ):
    """
    Scans the entities (entities folder) or block_entities (region folder) and
    makes a TXT file reporting the results.
    
    Instead of scanning the region files that exist in a local directory,
    this function will incrementally download region files from the remote
    directory in the server, scanning them and deleting them
    afterwards. It downloads the region files via SFTP.
    
    Inputs
    ------
    remote_region_dir: The path to the region (r.X.Z.mca) files in the
        server. Type: str.
    world_type: "OVERWORLD", "NETHER", "END".
    scanning_entities: True if scanning entities; False if scanning block
        entities.
    max_regions_to_scan: the number of regions to scan before ending the scan
        early. Used for debugging/testing. Set to None if all region files
        wish to be scanned.
    max_download_workers: the maximum number of workers that download the
        region files. Default: 10.
    max_scan_workers: the maximum number of workers that scan region files
        stored in the cache. When None, this is chosen automatically.
    max_in_flight: the maximum number of region files cached and ready to be
        scanned at any time. If None, will be determined automatically.
    resume_regions_file_path: Path to a TXT file of the regions that
        have already been scanned. Formatted r.X1.Y1\nr.X2.Y2\nr.X3.Y3\n...
    """
    
    ## Create file name prefix of the scan results ##
    
    results_filename_prefix = world_type
    
    if scanning_entities:
        results_filename_prefix += "_ENTITIES_"
    else:
        results_filename_prefix += "_BLOCK_ENTITIES_"
    
    ## Create the paths of the results files ##
    
    findings_file_path = (
        SFTP_SCAN_RESULTS_DIR / (results_filename_prefix + "findings")
    )
    
    corrupt_chunks_file_path = (
        SFTP_SCAN_RESULTS_DIR / (results_filename_prefix + "corrupt_chunks")
    )
    
    corrupt_regions_file_path = (
        SFTP_SCAN_RESULTS_DIR / (results_filename_prefix + "corrupt_regions")
    )
    
    ## Create report files; add scan timestamp at top ##
    
    scan_timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    write_mode = "a" if resume_regions_file_path is not None else "w"

    with open(findings_file_path, write_mode, encoding="utf-8") as f:
        f.write(f"\n\n===== Scan started/resumed {scan_timestamp} =====\n\n")

    with open(corrupt_chunks_file_path, write_mode, encoding="utf-8") as f:
        f.write(f"\n\n===== Scan started/resumed {scan_timestamp} =====\n\n")

    with open(corrupt_regions_file_path, write_mode, encoding="utf-8") as f:
        f.write(f"\n\n===== Scan started/resumed {scan_timestamp} =====\n\n")
    
    # Store already scanned regions in a set.
    # If the already-scanned-regions file exists, use it to continue adding
    # more names of scanned region files into. Otherwise, create the path
    # of a new file to do so.
    # This allows for the scanner to be stopped and resumed.
    
    already_scanned_regions = set()

    if resume_regions_file_path is not None:
        
        if not resume_regions_file_path.exists():
            raise FileNotFoundError(
                f"Already-scanned regions file not found: "
                f"{resume_regions_file_path}"
            )
        
        with open(resume_regions_file_path, "r", encoding="utf-8") as f_old:
            for region_name in f_old:
                region_name = region_name.strip()
                
                # Skip whitespace / blank line
                if not region_name:
                    continue
                
                already_scanned_regions.add(parse_region_name(region_name))
        
        regions_scanned_file_path = resume_regions_file_path
        
    else:
        regions_scanned_file_path = (
            SFTP_SCAN_RESULTS_DIR /
            (results_filename_prefix + "regions_scanned")
        )
    
        regions_scanned_file_path.write_text("", encoding="utf-8")
    
    ## START SCAN ##
    
    scan_start = time.perf_counter()
    
    start_sftp_region_source_scan(
        
        remote_region_dir = remote_region_dir,
        world_type = world_type,
        scanning_entities = scanning_entities,
        
        max_regions_to_scan = max_regions_to_scan,
        
        max_download_workers = max_download_workers,
        max_scan_workers = max_scan_workers,
        max_in_flight = max_in_flight,
        
        already_scanned_regions = already_scanned_regions,
        
        findings_file_path = findings_file_path,
        corrupt_chunks_file_path = corrupt_chunks_file_path,
        corrupt_regions_file_path = corrupt_regions_file_path,
        regions_scanned_file_path = regions_scanned_file_path,
        
    )
    
    scan_duration = time.perf_counter() - scan_start
    
    if scanning_entities:
        print(
            f"{world_type} Entities - scan time: "
            f"{format_duration(scan_duration)}"
        )
    else:
        print(
            f"{world_type} Block Entities - scan time: "
            f"{format_duration(scan_duration)}"
        )

