<p align="center">
  <b>🇬🇧 English</b> • <a href="README.ru.md">🇷🇺 Русский</a> • <a href="README.uk.md">🇺🇦 Українська</a>
</p>

# Epson AutoScan Automation

[![Python](https://img.shields.io/badge/Python-3.x-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?logo=windows&logoColor=white)](https://www.microsoft.com/windows)
[![Protocol](https://img.shields.io/badge/Protocol-eSCL-green.svg)](https://mopria.org/spec-download)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

Windows background service, Tkinter control panel, system tray tool, and Print Spooler watchdog for automatically capturing and saving scans from network Epson MFPs over the eSCL protocol.

## Overview

When a standalone copy is made on a network Epson printer/scanner (e.g., Epson L3350 Series), `epson_autoscan_service.py` detects the printer's transition from `Processing` back to `Idle` via eSCL (`ScannerStatus`), filters out regular PC/mobile print jobs, triggers a network JPEG scan over HTTPS eSCL, removes accidental blank pages, and saves the resulting file locally with a Windows toast/balloon notification.

## Features

- **Automatic Copy-Triggered Scanning (`epson_autoscan_service.py`)**:
  - Polls `https://<printer_ip>/eSCL/ScannerStatus` every second.
  - Distinguishes standalone hardware copies from PC print/scan jobs by inspecting the printer Web UI status page (`INFO_PRTINFO/TOP`), Windows Print Spooler (`Win32_PrintJob`), and active TCP connections (`Get-NetTCPConnection`).
  - Submits an A4 full-platen eSCL `ScanSettings` job (`2550x3510`, configurable DPI and color mode), downloads the JPEG via `/NextDocument`, saves `EpsonScan_YYYYMMDD_HHMMSS.jpg`, and releases the job (`DELETE`).
- **Blank Page Detection**: Uses Pillow (`PIL`) ink-pixel thresholding on automatic scans to move blank scans (such as phone-print triggers) to the Windows Recycle Bin (`SHFileOperationW`).
- **Manual On-Demand Scan**: Supports `--scan-now` CLI flag to trigger an immediate scan bypassing blank-page deletion.
- **GUI Settings Panel (`epson_autoscan_gui.py`)**: Tkinter interface to configure `printer_ip`, `save_dir`, `dpi` (`100`/`200`/`300`/`600`/`1200`), `color_mode` (`RGB24`, `Grayscale8`, `BlackAndWhite1`), and `enabled` state in `config.json`.
- **System Tray & Spooler Watchdog (`watchdog/`)**:
  - `tray_app.py`: System tray icon ("Epson Tools") for restarting the Windows Print Spooler, triggering an immediate scan, toggling autoscan, and launching diagnostics.
  - `watchdog.ps1`: PowerShell monitor (10s interval, 60s cooldown) that restarts `Spooler` if the service stops, PrintService Event ID `842` (`0x80004005`) occurs, or a print job stays stuck for 40+ seconds.
  - `install.ps1` / `Install.bat` & `diagnose.ps1`: Registers the `EpsonSpoolerWatchdog` startup Scheduled Task (as `SYSTEM`), enables PrintService Operational logging, creates Desktop shortcuts, and prints printer/spooler diagnostics.

## Usage

### Service & Manual Scan

```powershell
# Run background autoscan service
python epson_autoscan_service.py

# Trigger a single manual scan immediately
python epson_autoscan_service.py --scan-now
```

### GUI & Tray App

```powershell
# Open Tkinter settings panel
python epson_autoscan_gui.py

# Start system tray utility
pythonw watchdog/tray_app.py
```

### Spooler Watchdog Installation (Administrator)

Run `watchdog/Install.bat` (or `powershell -ExecutionPolicy Bypass -File watchdog/install.ps1` as Administrator) after placing the watchdog scripts in `C:\ProgramData\EpsonSpoolerWatchdog\`.

## Tech Stack

- **Python 3.x** (`urllib`, `ssl`, `xml.etree.ElementTree`, `tkinter`, `ctypes`)
- **Pillow (`PIL`)** — Blank-page ink analysis & tray icon rendering
- **pystray** — Windows system tray integration
- **PowerShell & Windows Task Scheduler** — Print Spooler watchdog & diagnostics
- **eSCL (AirScan)** — Network scanning over HTTPS

## Setup & Configuration

Edit `config.json` (or configure via `epson_autoscan_gui.py`):

```json
{
  "printer_ip": "<YOUR_PRINTER_IP>",
  "save_dir": "C:\\Users\\<YourUser>\\Pictures",
  "dpi": 300,
  "color_mode": "RGB24",
  "enabled": true
}
```

Install optional Python dependencies for blank-page detection and the tray icon:

```powershell
pip install pillow pystray
```

> **Note:** `watchdog/tray_app.py`, `watchdog/install.ps1`, `watchdog/watchdog.ps1`, and `watchdog/diagnose.ps1` reference local paths (`D:\EpsonAutoScan\`, `C:\ProgramData\EpsonSpoolerWatchdog\`) and printer name (`L3350 Series(Сеть)`). Update those variables if your environment differs.

## Project Structure

```text
epson-autoscan-automation/
├── watchdog/
│   ├── Install.bat              # Elevated installer launcher
│   ├── diagnose.ps1             # Spooler & PrintService event diagnostics
│   ├── install.ps1              # Scheduled Task & Desktop shortcut setup
│   ├── tray_app.py              # Windows system tray utility
│   └── watchdog.ps1             # Print Spooler watchdog loop
├── config.json                  # Scanner IP, output folder, DPI, color mode
├── epson_autoscan_gui.py        # Tkinter configuration UI
├── epson_autoscan_service.py    # Background eSCL autoscan service
├── LICENSE                      # Apache License 2.0
├── NOTICE                       # Attribution notice
├── README.md                    # English documentation
├── README.ru.md                 # Russian documentation
└── README.uk.md                 # Ukrainian documentation
```

## License & Attribution

This project is licensed under the [Apache License 2.0](LICENSE) — see the [NOTICE](NOTICE) file for attribution details.

If you find this project useful, please consider starring or [forking it on GitHub](https://github.com/mriamys/epson-autoscan-automation) and keeping attribution to the original repository: [https://github.com/mriamys/epson-autoscan-automation](https://github.com/mriamys/epson-autoscan-automation).
