# minecraft-nbt-scanner

Python tools for scanning Minecraft Java Edition world files to locate and flag
specific items, block entities, and entities.

The scanner can inspect player `.dat` files as well as region `.mca` files and
supports both local world scanning and scanning a remote server world over SFTP.

## Features

- Scan player data (`playerdata/*.dat`) for specific items in:
  - Player inventories
  - Equipment
  - Ender chests
  - Flagging the player if a match is found. (Currently, the scanner does not
    report which of these locations contained the item.)
- Scan world region files (`region/*.mca`) for:
  - Specific block entities such as mob spawners, command blocks, etc.
  - Items contained within block entities such as chests, hoppers, shulkers,
    etc., flagging the block entity if a specific item is found.
- Scan entity region files (`entities/*.mca`) for:
  - Specific dropped items
  - Specific entities such as Ender Dragons, minecarts with command blocks, etc.
  - Items contained within entities such as donkeys equipped with a chest, etc.,
    flagging the entity if a specific item is found.
- Flag and report the locations of specific block entities or entities.
- Scan large remote worlds directly over SFTP without downloading the entire
  world first by downloading, processing, and then deleting files afterwards.
- Use a local cache for remotely downloaded region files and limit the number
  of files in flight to prevent the local cache from consuming excessive disk
  space.
- Resume interrupted SFTP scans without rescanning completed region files.
- Record scan results incrementally so progress is preserved if the scan is
  interrupted.
- Record corrupt or unreadable chunks encountered during scanning.
- Download individual region or player files for targeted investigation.

See docstrings of modules or functions for more details.

## Safety

The scanner is read-only with respect to the Minecraft world. Normal scanning
does not modify the world files or the remote server. Remote SFTP scans download
temporary copies of region files to the local cache, process them, and then
delete the local copies after processing.

Any actions taken to remove or modify flagged data are performed separately
from the scanning process.

## Requirements

- Python 3.14
- [`numpy`](https://numpy.org/)
- [`nbtlib`](https://pypi.org/project/nbtlib/)
- [`anvil-parser2`](https://pypi.org/project/anvil-parser2/)
- [`requests`](https://pypi.org/project/requests/)
- [`paramiko`](https://www.paramiko.org/)

Additional packages may be required depending on which utilities are used.
Some dependencies, including `frozendict` and `nbt`, are installed
transitively alongside the packages above.

## Installation

Clone the repository:

```bash
git clone git@github.com:Pryda-1/minecraft-nbt-scanner.git
cd minecraft-nbt-scanner
