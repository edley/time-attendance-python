# Attendance Device Utility

A Python utility for communicating with **Smackbio/Anviz/ZKTeco** biometric attendance devices over TCP/IP.
Supports two protocols:

- **SBXPC protocol** (`PP` prefix, port 5005) — legacy Smackbio/ZKTeco devices
- **55AA protocol** (`aa55`/`5aa5` prefix, port 5005) — newer Anviz devices

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
- **Clear device logs** — wipe attendance and/or management log data from device memory (with confirmation)
- **List enrolled users** — fetch user IDs, privileges, names, and enabled status
- **Device information** — serial number, firmware status, device configuration
- **Read device time** — get and display the device's current date/time
- **Export to CSV/JSON** — save results for reporting and analysis
- **Saved device profiles** — store device IP, port, password, and machine ID for quick reuse
- **Real-time progress** — live status updates (SSE in web UI, inline spinner in CLI)
- **Auto-protocol detection** — automatically detects 55AA (Anviz) vs SBXPC at connection time
- **XML operations** — `GeneralOperationXML` for extended device control and configuration
- **Diagnose mode** — network diagnostics to troubleshoot connectivity issues

## Requirements

- Python 3.10+
- No external dependencies for CLI mode
- `tkinter` (included with Python on most platforms) for GUI mode
- `flask` for web UI mode (`pip install flask`)
- `supabase` for database upload (`pip install supabase`)

## Quick Start

### CLI

```bash
# Read all attendance logs (SBXPC device)
python3 attendance_device.py --ip 192.168.1.224 read-glogs

# Read attendance logs via hostname (Anviz 55AA device — auto-detected)
python3 attendance_device.py --hostname device.example.com read-glogs

# Read attendance logs and export to CSV
python3 attendance_device.py --ip 192.168.1.224 read-glogs --csv output.csv

# Read management logs
python3 attendance_device.py --ip 192.168.1.224 read-slogs

# List enrolled users
python3 attendance_device.py --ip 192.168.1.224 users

# Get device info and time
python3 attendance_device.py --ip 192.168.1.224 info
python3 attendance_device.py --ip 192.168.1.224 time

# Clear all attendance (punch) logs from the device
python3 attendance_device.py --ip 192.168.1.224 clear-glogs

# Clear all management (audit) logs from the device
python3 attendance_device.py --ip 192.168.1.224 clear-slogs

# Run network diagnostics
python3 attendance_device.py --ip 192.168.1.224 diagnose
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

## 55AA Protocol (Anviz)

Newer Anviz devices use the 55AA protocol (`\x55\xaa` command prefix, `\x5a\xa5` ACK prefix). The protocol is **auto-detected** during connection — the device announces itself with the `aa55`/`5aa5` response prefix.

### Protocol Flow

The 55AA attendance log read sequence:

1. **Heartbeat** — verify device is awake and responsive
2. **Request data** — send `08 01` + cmd=6 to get record count
3. **Prepare transfer** — two `07 01` prepare commands (cmd=0, cmd=1 with count)
4. **Trigger ACK** — send `ACK(status=0)` to request bulk data
5. **Read bulk data** — receive `aa55 DATA` + `a55a BULK` with attendance records
6. **Confirm receipt** — send `ACK(status=count)` to acknowledge
7. **Completion** — device sends `aa55 DATA(0)` marker

### Record Format

Anviz records use a 12-byte format with **seconds since 2000-01-01** timestamps:

| Offset | Size | Field | Description |
|--------|------|-------|-------------|
| 0 | 4 | Timestamp | Seconds since 2000-01-01 |
| 4 | 4 | Enroll Number | Employee ID |
| 8 | 4 | Flags | Mode/status flags |

System events (non-attendance records with small timestamp values) are automatically filtered.

## XML Payload Retrieval

Devices support XML-based query and configuration via `GeneralOperationXML` (SBXPC command `0x45`). The utility provides a `general_operation_xml()` method for custom XML operations.

### Example: Get Attendance Logs via XML

```python
from attendance_device import AttendanceDevice

dev = AttendanceDevice(ip="192.168.1.224")

dev.connect()

xml_request = """<?xml version="1.0" encoding="utf-8"?>
<Request>
  <CMD>ReadAllGLogData</CMD>
  <MSGTYPE>request</MSGTYPE>
  <MachineID>1</MachineID>
</Request>"""

response = dev.general_operation_xml(xml_request)
if response:
    print(response)

dev.disconnect()
```

### Example: Get Device Information

```python
xml_request = """<?xml version="1.0" encoding="utf-8"?>
<Request>
  <CMD>GetDeviceInfo</CMD>
  <MSGTYPE>request</MSGTYPE>
  <MachineID>1</MachineID>
</Request>"""

response = dev.general_operation_xml(xml_request)
```

### Example: Set Device Time

```python
import datetime

now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
xml_request = f"""<?xml version="1.0" encoding="utf-8"?>
<Request>
  <CMD>SetDeviceTime</CMD>
  <MSGTYPE>request</MSGTYPE>
  <MachineID>1</MachineID>
  <Time>{now}</Time>
</Request>"""

response = dev.general_operation_xml(xml_request)
```

## Project Files

| File | Purpose |
|------|---------|
| `attendance_device.py` | Core protocol implementation (SBXPC + 55AA) & CLI |
| `attendance_gui.py` | Tkinter desktop GUI |
| `attendance_web.py` | Flask web UI with SSE |
| `extract_docx.py` | Extracts text from the SBXPC reference manual DOCX |
| `analyze_jar.py` | Java class file parser for analyzing the sample JAR |
| `dump_class.py` | Java class file disassembler |
| `manual.txt` | Extracted SBXPC OCX Reference Manual v3.12 |
| `attendance_supabase.py` | Supabase database upload module |
| `supabase_schema.sql` | PostgreSQL schema for Supabase tables |
| `Java_SBXPCSample/` | Official Java reference implementation |

## Supabase Integration

Attendance records can be automatically uploaded to a Supabase PostgreSQL database.

### Database Schema

Run `supabase_schema.sql` in the Supabase SQL Editor to create the required tables:

- **`attendance_logs`** — raw clock events (one row per log entry)
- **`attendance_records`** — paired check-in/check-out records (one row per employee per day)
- **`attendance_daily`** — view with daily summary and hours worked

### CLI

```bash
# Upload attendance logs to Supabase after reading
python3 attendance_device.py --ip 192.168.1.224 read-glogs \
  --supabase-url https://xyz.supabase.co \
  --supabase-key your-key \
  --supabase-device-id "office-01" \
  --supabase-device-name "Main Office"
```

Alternatively, set `SUPABASE_URL` and `SUPABASE_KEY` environment variables.

### GUI

Configure Supabase in the "Supabase Integration" card — set URL, API Key, and check "Upload records to Supabase". Settings are saved to `~/.attendance_supabase.json`.

### Web UI

Scroll to the "Supabase Integration" section, enter your credentials, check the enable box, and click Save Settings. Records will upload automatically after each operation.

### Database Structure

Each raw log entry (`attendance_logs`) includes:

| Field | Description |
|-------|-------------|
| `device_id` | Device identifier |
| `enroll_number` | Employee ID from the device |
| `employee_name` | Employee name (if available) |
| `record_timestamp` | Full timestamp of the clock event |
| `record_date` | Date of the event |
| `verify_mode_name` | How the employee verified (FP, Card, Password, Face, etc.) |
| `attend_status_name` | Event type (Go In, Go Out, Duty On, Duty Off) |
| `event_type` | Inferred type (`check_in` / `check_out`) |

Paired records (`attendance_records`) consolidate check-in and check-out per employee per day for easy reporting.

## Device Profiles

All three interfaces support saving device profiles to `~/.attendance_devices.json` for quick reconnection.

## Status

- **GUI tabs** — 6 tabs: Device (profile selection + details), Operation (execute + export), Clear (clear attendance/management logs with confirmation), Status (who's inside), Data (Supabase table viewer), Settings (Supabase config)
- **Supabase** — table creation via API needs service_role key; falls back to SQL in log. Upload checkbox works immediately (no save required)
- **55AA protocol** — auto-detected with `cmd=0` hello packet; works with Anviz devices at `csofttestlab.gotdns.org:5005`
- **Hostname saving** — fixed; hostname persists across app restarts

## Reference

The implementation is based on the [SBXPC OCX Reference Manual v3.12](manual.txt), the official Java SDK sample included in `Java_SBXPCSample/`, and traffic captures from Anviz 55AA devices.
