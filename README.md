# Attendance Device Utility

A Python utility for communicating with **Smackbio/Anviz** biometric attendance devices over TCP/IP using the **SBXPC protocol** (port 5005). Supports reading attendance logs, management logs, user lists, and device information.

## Interfaces

Three interfaces are provided:

| Interface | File | Description |
|-----------|------|-------------|
| **CLI** | `attendance_device.py` | Command-line tool for scripting and automation |
| **Desktop GUI** | `attendance_gui.py` | Tkinter-based graphical interface |
| **Web UI** | `attendance_web.py` | Flask web app with real-time SSE progress streaming |

## Features

- **Read attendance (general) logs** — download clock-in/out records with verify mode, attendance status, and anti-pass info
- **Read management (supervisor) logs** — track user enrollment, deletion, and device configuration changes
- **List enrolled users** — fetch user IDs, privileges, names, and enabled status
- **Device information** — serial number, firmware status, device configuration
- **Read device time** — get and display the device's current date/time
- **Export to CSV/JSON** — save results for reporting and analysis
- **Saved device profiles** — store device IP, port, password, and machine ID for quick reuse
- **Real-time progress** — live status updates (SSE in web UI, inline spinner in CLI)

## Requirements

- Python 3.10+
- No external dependencies for CLI mode
- `tkinter` (included with Python on most platforms) for GUI mode
- `flask` for web UI mode (`pip install flask`)

## Quick Start

### CLI

```bash
# Read all attendance logs
python3 attendance_device.py --ip 192.168.1.224 read-glogs

# Read attendance logs and export to CSV
python3 attendance_device.py --ip 192.168.1.224 read-glogs --csv output.csv

# Read management logs
python3 attendance_device.py --ip 192.168.1.224 read-slogs

# List enrolled users
python3 attendance_device.py --ip 192.168.1.224 users

# Get device info and time
python3 attendance_device.py --ip 192.168.1.224 info
python3 attendance_device.py --ip 192.168.1.224 time
```

### GUI

```bash
python3 attendance_gui.py
```

### Web UI

```bash
pip install flask
python3 attendance_web.py
# Open http://127.0.0.1:5000
```

## SBXPC Protocol

The SBXPC protocol is used by Smackbio, Anviz, and ZKTeco-compatible devices over TCP (default port 5005). This implementation supports:

- **Attendance records** (General Log Data) — 20/24-byte records with enrolled user ID, verify mode, attendance status, anti-pass status, and timestamp
- **Management records** (Supervisor Log Data) — 40-byte records tracking administrative actions (enroll, delete, setting changes)
- **User database** — user ID, privilege level, backup number (finger/password/card), enabled status, and name
- **Device status/configuration** — serial number, user/fingerprint/log counts, device info parameters
- **XML operations** — `GeneralOperationXML` for extended device control

### Verify Mode Codes

| Code | Mode |
|------|------|
| 1 | Fingerprint |
| 2 | Password |
| 3 | Card |
| 4 | Fingerprint + Card |
| 30 | Face |
| 51 | In: Fingerprint |
| 101 | Out: Fingerprint |

### Attendance Status

| Code | Status |
|------|--------|
| 0 | Duty On |
| 1 | Duty Off |
| 4 | Go In |
| 5 | Go Out |

## Project Files

| File | Purpose |
|------|---------|
| `attendance_device.py` | Core SBXPC protocol implementation & CLI |
| `attendance_gui.py` | Tkinter desktop GUI |
| `attendance_web.py` | Flask web UI with SSE |
| `extract_docx.py` | Extracts text from the SBXPC reference manual DOCX |
| `analyze_jar.py` | Java class file parser for analyzing the sample JAR |
| `dump_class.py` | Java class file disassembler |
| `manual.txt` | Extracted SBXPC OCX Reference Manual v3.12 |
| `Java_SBXPCSample/` | Official Java reference implementation |

## Device Profiles

All three interfaces support saving device profiles to `~/.attendance_devices.json` for quick reconnection.

## Reference

The implementation is based on the [SBXPC OCX Reference Manual v3.12](manual.txt) and the official Java SDK sample included in `Java_SBXPCSample/`.
