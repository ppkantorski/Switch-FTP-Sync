# Switch FTP Sync (macOS / Windows)

## Overview

**Switch FTP Sync** is an app that monitors an FTP server for Nintendo Switch screenshots as well as specified directories and downloads them to a local directory. The script is designed to work across Windows, macOS, and Linux.

## Features

- Connects to an FTP server and checks for new files in specified directories.
- Downloads new screenshots to a local directory.
- Logs all actions with timestamps.
- Clears terminal lines for a clean and readable output.

## Requirements

- Computer runing macOS or Windows 10/11.
- Python 3.x (for building)
- FTP server accessible with the necessary credentials
    - Requires [sys-ftpd](https://github.com/cathery/sys-ftpd) or a similar background FTP module running on the Switch.

## Configuration

The script reads configuration details from a `config.ini` file located in the same directory as the script. Below is an example `config.ini` file:

```ini
[FTP]
server = X.X.X.X
port = 5000
user = root
pass = 

[Screenshots]
dt_format = %Y-%m-%d_%H-%M-%S
output_path = 
sync_screenshots = False

[File Sync]
server_path_1 = 
output_path_1 = 
sync_files_1 = False

server_path_2 = 
output_path_2 =
sync_files_2 = False

server_path_3 =
output_path_3 =
sync_files_3 = False

server_path_4 =
output_path_4 =
sync_files_4 = False

server_path_5 =
output_path_5 =
sync_files_5 = False


[Settings]
check_rate = 15
auto_start = False
```

- `ftp_server`: IP address of the FTP server.
- `ftp_port`: Port number of the FTP server.
- `ftp_user`: Username for FTP login.
- `ftp_pass`: Password for FTP login (leave empty if no password).
- `output_path`: Local directory where files will be saved.
- `auto_start`: Variable for auto start (`True`/`False`)
- `check_rate`: Time interval (in seconds) to wait between checks.
- `dt_format`: Format of image file name.

## Usage

1. Clone or download the repository.
2. Run the build script to geenerate the compiled application (and install necessary packages):
    - `python3 make.py`
