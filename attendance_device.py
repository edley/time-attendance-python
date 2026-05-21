#!/usr/bin/env python3
"""
Attendance Device Utility - SBXPC Protocol (Smackbio/Anviz)

Extracts attendance logs and user data from biometric attendance devices
that use the SBXPC protocol over TCP/IP (default port 5005).

References:
  - SBXPC OCX Reference Manual v3.12 (manual.txt)
  - Java SBXPC Sample implementation
  - GeneralLogData/SuperLogData data structures

Usage:
  # Read all attendance (general) logs
  python3 attendance_device.py --ip 192.168.1.224 --port 5005 read-glogs

  # Read attendance logs and export to CSV
  python3 attendance_device.py --ip 192.168.1.224 read-glogs --csv output.csv

  # Read all management logs
  python3 attendance_device.py --ip 192.168.1.224 read-slogs

  # Get device info
  python3 attendance_device.py --ip 192.168.1.224 info

  # Get device time
  python3 attendance_device.py --ip 192.168.1.224 time

  # List all enrolled users
  python3 attendance_device.py --ip 192.168.1.224 users
"""

import argparse
import datetime
import json
import logging
import socket
import struct
import sys
import csv
import io
import os
import time
import itertools

logger = logging.getLogger("attendance_device")

# ── Protocol Constants ──────────────────────────────────────────────────────

# Packet start bytes
CMD_PACKET_PREFIX = b"\x50\x50"

# Command codes (SBXPC / ZKTeco compatible)
CMD_CONNECT        = 0x01
CMD_EXIT           = 0x02
CMD_ENABLEDEVICE   = 0x03
CMD_DISABLEDEVICE  = 0x04
CMD_ACK_OK         = 0x05
CMD_ACK_ERROR      = 0x06
CMD_ACK_DATA       = 0x07
CMD_PREPARE_DATA   = 0x08
CMD_DATA           = 0x09
CMD_FREE_DATA      = 0x0A
CMD_DATA_READY     = 0x0B
CMD_READALLGLOGDATA = 0x32
CMD_READGLOGDATA   = 0x33
CMD_GETGLOGDATA    = 0x34
CMD_READALLSLOGDATA = 0x35
CMD_READSLOGDATA   = 0x36
CMD_GETSLOGDATA    = 0x37
CMD_READALLUSERID  = 0x38
CMD_GETALLUSERID   = 0x39
CMD_GETDEVICEINFO  = 0x3A
CMD_GETDEVICETIME  = 0x3B
CMD_SETDEVICETIME  = 0x3C
CMD_CLEARDATA      = 0x3D
CMD_GETSERIALNO    = 0x3E
CMD_GETDEVICESTATUS = 0x3F
CMD_EMPTYGLOGDATA  = 0x40
CMD_EMPTYSLOGDATA  = 0x41
CMD_GETUSERNAME    = 0x42
CMD_SETUSERNAME    = 0x43
CMD_GETPINWIDTH    = 0x44
CMD_GENERALOPERATIONXML = 0x45

# ── Verify Mode Constants (from manual) ─────────────────────────────────────

VERIFY_MODE_MAP = {
    0:   "FP+ID",
    1:   "FP",
    2:   "Password",
    3:   "Card",
    4:   "FP+Card",
    5:   "FP+Pwd",
    6:   "Card+Pwd",
    7:   "FP+Card+Pwd",
    10:  "Hand Lock",
    11:  "Prog Lock",
    12:  "Prog Open",
    13:  "Prog Close",
    14:  "Auto Recover",
    20:  "Lock Over",
    21:  "Illegal Open",
    22:  "Duress alarm",
    23:  "Tamper detect",
    30:  "FACE",
    31:  "FACE+CARD",
    32:  "FACE+PWD",
    33:  "FACE+CARD+PWD",
    34:  "FACE+FP",
    51:  "FP(In)",
    52:  "Password(In)",
    53:  "Card(In)",
    101: "FP(Out)",
    102: "Password(Out)",
    103: "Card(Out)",
    151: "FP(Extra)",
    152: "Password(Extra)",
    153: "Card(Extra)",
}

ATTEND_STATUS_MAP = {
    0: "Duty On",
    1: "Duty Off",
    2: "Overtime On",
    3: "Overtime Off",
    4: "Go In",
    5: "Go Out",
}

ANTIPASS_STATUS_MAP = {
    0: "",
    1: "AP_In",
    2: "",
    3: "AP_Out",
}

MANIPULATION_MAP = {
    3:  "Enroll User",
    4:  "Enroll Manager",
    5:  "Delete Fp Data",
    6:  "Delete Password",
    7:  "Delete Card Data",
    8:  "Delete All LogData",
    9:  "Modify System Info",
    10: "Modify System Time",
    11: "Modify Log Setting",
    12: "Modify Comm Setting",
    13: "Modify Timezone Setting",
    14: "Delete Face",
}

BACKUP_NUMBER_MAP = {
    10: "Password",
    11: "Card",
    13: "Card",
    14: "FACE",
}

DEVICE_STATUS_NAMES = {
    1: "Manager Count",
    2: "User Count",
    3: "FP Count",
    4: "Password Count",
    5: "SLog Count",
    6: "GLog Count",
    7: "Card Count",
    8: "Alarm Status",
    9: "Face Count",
    10: "SLog Not Read",
    11: "GLog Not Read",
}

DEVICE_INFO_NAMES = {
    1: "Max Managers",
    2: "Device ID",
    3: "Language",
    4: "Auto Power-Off(min)",
    5: "Door Open Time(sec)",
    6: "GLog Warning",
    7: "SLog Warning",
    8: "Re-Verify Interval(min)",
    9: "Baudrate",
    10: "Parity",
    11: "Stop Bit",
    12: "Date Separator",
    13: "Verification Mode",
    14: "Door Mode",
    15: "Door Sensor Type",
    16: "Door Open Timeout(min)",
    17: "Anti-Pass",
    18: "Auto Sleep(min)",
    19: "Daylight Offset",
    20: "UDP Server",
    21: "DHCP Use",
    23: "Manager PC IP",
    24: "Event Send Type",
}


# ── Packet Layer ────────────────────────────────────────────────────────────

def make_packet(command: int, machine_id: int = 1, data: bytes = b"") -> bytes:
    """Build an SBXPC command packet.

    Format:
      [0x50, 0x50] [MachineID:1] [Command:1] [DataLen:2 LE] [Data:N] [Checksum:2 LE]
    """
    payload = struct.pack("<H", len(data)) + data
    buf = CMD_PACKET_PREFIX + bytes([machine_id, command]) + payload
    checksum = sum(buf) & 0xFFFF
    buf += struct.pack("<H", checksum)
    return buf


def parse_reply(data: bytes):
    """Parse an SBXPC reply packet. Returns (command, error_code, payload)."""
    if len(data) < 8:
        raise ValueError(f"Packet too short: {len(data)} bytes")
    if data[:2] != CMD_PACKET_PREFIX:
        raise ValueError(f"Bad prefix: {data[:2].hex()}")
    machine_id = data[2]
    command = data[3]
    payload_len = struct.unpack("<H", data[4:6])[0]
    payload = data[6:6 + payload_len]
    if len(data) >= 8 + payload_len:
        checksum_recv = struct.unpack("<H", data[6 + payload_len:8 + payload_len])[0]
        checksum_calc = sum(data[:6 + payload_len]) & 0xFFFF
        if checksum_recv != checksum_calc:
            logger.warning("Checksum mismatch: recv=%04x calc=%04x", checksum_recv, checksum_calc)
    return command, machine_id, payload


# ── Status / Progress Indicator ─────────────────────────────────────────────

class StatusIndicator:
    """Inline status indicator for the terminal.

    Shows a spinner with the current step description and elapsed time,
    updated in-place on stderr so stdout remains clean for output/data.
    """

    def __init__(self):
        self._spinner = itertools.cycle("⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏")
        self._enabled = sys.stderr.isatty()
        self._current = ""
        self._phase = 0
        self._step_start: float = 0.0
        self._global_start: float = 0.0

    def _elapsed(self, since: float) -> str:
        secs = int(time.time() - since)
        if secs >= 3600:
            return f"{secs//3600:02d}:{(secs%3600)//60:02d}:{secs%60:02d}"
        return f"{secs//60:02d}:{secs%60:02d}"

    def _total_elapsed(self) -> str:
        if self._global_start:
            return self._elapsed(self._global_start)
        return ""

    def _step_elapsed(self) -> str:
        if self._step_start:
            return self._elapsed(self._step_start)
        return ""

    def step(self, msg: str):
        """Mark a new step. Prints a completed marker for the previous step,
        then starts a new spinner line with elapsed time."""
        now = time.time()
        if self._global_start == 0:
            self._global_start = now
        self._phase += 1
        elapsed_total = self._total_elapsed()
        if self._enabled:
            if self._current:
                print(f"\r\x1b[K\x1b[32m✓\x1b[0m {self._current}  [{self._step_elapsed()}]", file=sys.stderr)
            self._step_start = now
            self._current = msg
            self._tick()
        else:
            if self._current:
                print(f"✓ {self._current}  [{self._step_elapsed()}]", file=sys.stderr)
            self._step_start = now
            self._current = msg
            prefix = f"[{elapsed_total}]" if elapsed_total else ""
            print(f"{prefix}  {msg} ...", file=sys.stderr)

    def tick(self, msg: str | None = None):
        """Advance the spinner in place, showing step elapsed time."""
        if not self._enabled:
            return
        if msg:
            self._current = msg
        self._tick()

    def _tick(self):
        c = next(self._spinner)
        elapsed = self._step_elapsed()
        total = self._total_elapsed()
        print(f"\r\x1b[K{c} {self._current}  [{elapsed} / {total}]", end="", file=sys.stderr, flush=True)

    def ok(self, msg: str | None = None):
        """Mark the current step as completed with a checkmark and timings."""
        elapsed = self._step_elapsed()
        label = msg if msg else self._current
        full = f"{label}  [{elapsed}]"
        if self._enabled:
            print(f"\r\x1b[K\x1b[32m✓\x1b[0m {full}", file=sys.stderr)
        else:
            print(f"✓ {full}", file=sys.stderr)
        self._current = ""
        self._step_start = 0.0

    def fail(self, msg: str | None = None):
        """Mark the current step as failed with a cross and timings."""
        elapsed = self._step_elapsed() if self._step_start else ""
        label = msg if msg else self._current
        full = f"{label}" + (f"  [{elapsed}]" if elapsed else "")
        if self._enabled:
            print(f"\r\x1b[K\x1b[31m✗\x1b[0m {full}", file=sys.stderr)
        else:
            print(f"✗ {full}", file=sys.stderr)
        self._current = ""
        self._step_start = 0.0

    def write(self, msg: str):
        """Write an informational line without disturbing the spinner."""
        if self._enabled:
            print(f"\r\x1b[K{msg}", file=sys.stderr)
            if self._current:
                self._tick()
        else:
            print(msg, file=sys.stderr)


# ── Device Connection ───────────────────────────────────────────────────────

class AttendanceDevice:
    """Represents a connection to an SBXPC attendance device."""

    def __init__(self, ip: str, port: int = 5005, password: int = 0,
                 machine_id: int = 1, timeout: float = 10.0,
                 status: StatusIndicator | None = None):
        self.ip = ip
        self.port = port
        self.password = password
        self.machine_id = machine_id
        self.timeout = timeout
        self._sock: socket.socket | None = None
        self._status = status or StatusIndicator()

    # ── Connection ──────────────────────────────────────────────────────

    def connect(self) -> bool:
        """Open TCP connection and authenticate with the device."""
        logger.info("Connecting to %s:%d (timeout=%ds, password=%d) ...",
                     self.ip, self.port, self.timeout, self.password)

        # ── TCP connection ───────────────────────────────────────────
        self._status.step(f"TCP connection to {self.ip}:{self.port}")

        self._status.tick("Resolving hostname ...")
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self._status.tick(f"Setting socket timeout ({self.timeout}s) ...")
        self._sock.settimeout(self.timeout)

        self._status.tick(f"Attempting connection (attempt 1/1, port {self.port}) ...")
        try:
            self._sock.connect((self.ip, self.port))
            self._status.ok(f"TCP connection established to {self.ip}:{self.port}")
        except socket.timeout:
            self._status.fail(f"Connection timed out ({self.timeout}s)")
            raise ConnectionError(
                f"Connection timed out after {self.timeout}s — "
                f"no device responding at {self.ip}:{self.port}. "
                f"Verify: (1) device IP is correct, (2) device is powered on, "
                f"(3) device port {self.port} is reachable (check firewall), "
                f"(4) device is configured for TCP/IP on port {self.port}."
            )
        except OSError as e:
            self._status.fail(f"Connection failed: {e}")
            raise ConnectionError(
                f"Cannot connect to {self.ip}:{self.port} — {e}. "
                f"Check device IP, network connectivity, and firewall settings."
            )

        self._status.tick("Configuring TCP keepalive ...")
        self._set_keepalive()

        # ── SBXPC handshake ───────────────────────────────────────────
        self._status.step("SBXPC protocol handshake")

        self._status.tick("Sending connect request to device ...")
        pkt = make_packet(CMD_CONNECT, self.machine_id, b"\x00" * 4)

        self._status.tick("Waiting for device acknowledgment ...")
        try:
            cmd, mid, payload = self._send_recv(pkt)
        except ConnectionError:
            self._status.fail("No response from device")
            raise ConnectionError(
                f"Connected to {self.ip}:{self.port} but device did not respond "
                f"to SBXPC handshake. Verify the device uses SBXPC protocol "
                f"and port {self.port} is correct."
            )

        if cmd == CMD_ACK_ERROR:
            self._status.fail("Device rejected connection request")
            raise ConnectionError(
                f"Device at {self.ip}:{self.port} rejected the connection. "
                f"Check communication password (currently set to {self.password})."
            )

        self._status.ok("SBXPC handshake successful")

        # ── Password authentication ───────────────────────────────────
        if self.password != 0:
            self._status.step("Device authentication")

            self._status.tick("Sending authentication credentials ...")
            pkt = make_packet(CMD_CONNECT, self.machine_id,
                              struct.pack("<I", self.password))

            self._status.tick("Waiting for authentication response ...")
            cmd, mid, payload = self._send_recv(pkt)

            if cmd == CMD_ACK_ERROR:
                self._status.fail("Authentication rejected (bad password)")
                raise ConnectionError(
                    f"Device at {self.ip}:{self.port} rejected password {self.password}."
                )
            self._status.ok("Authentication successful")

        return True

    def disconnect(self):
        """Send exit and close the connection."""
        if not self._sock:
            return
        try:
            pkt = make_packet(CMD_EXIT, self.machine_id)
            self._sock.sendall(pkt)
        except OSError:
            pass
        try:
            self._sock.close()
        except OSError:
            pass
        self._sock = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *args):
        self.disconnect()

    def _set_keepalive(self):
        """Enable TCP keepalive."""
        try:
            self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        except OSError:
            pass

    def _send_recv(self, pkt: bytes) -> tuple:
        """Send a packet and receive the reply."""
        if not self._sock:
            raise ConnectionError("Not connected")
        logger.debug("  >> send: cmd=0x%02x len=%d", pkt[3], len(pkt))
        self._sock.sendall(pkt)

        # Read header first (8 bytes minimum)
        header = self._recv_all(8)
        if len(header) < 8:
            raise ConnectionError("Connection closed while reading header")

        payload_len = struct.unpack("<H", header[4:6])[0]
        logger.debug("  << recv: cmd=0x%02x payload_len=%d", header[3], payload_len)
        rest = self._recv_all(payload_len + 2)  # payload + checksum
        reply = header + rest
        return parse_reply(reply)

    def _recv_all(self, n: int) -> bytes:
        """Read exactly n bytes from the socket."""
        chunks = []
        while n > 0:
            chunk = self._sock.recv(n)
            if not chunk:
                raise ConnectionError("Connection closed by remote end")
            chunks.append(chunk)
            n -= len(chunk)
        return b"".join(chunks)

    # ── Device Control ───────────────────────────────────────────────────

    def enable_device(self, enable: bool = True) -> bool:
        """Enable or disable the device for PC access."""
        pkt = make_packet(CMD_ENABLEDEVICE if enable else CMD_DISABLEDEVICE,
                          self.machine_id)
        cmd, mid, payload = self._send_recv(pkt)
        return cmd == CMD_ACK_OK

    def get_device_time(self) -> dict | None:
        """Read the current date/time from the device."""
        self._status.step("Reading device time")
        pkt = make_packet(CMD_GETDEVICETIME, self.machine_id)
        cmd, mid, payload = self._send_recv(pkt)
        if cmd != CMD_ACK_DATA or len(payload) < 8:
            self._status.fail("Failed to read device time")
            return None
        # Payload: YYYY(2) MM(2) DD(2) HH(2) mm(2) ss(2) reserved(2)
        parts = struct.unpack("<HHHHHHH", payload[:14])
        result = {
            "year": parts[0],
            "month": parts[1],
            "day": parts[2],
            "hour": parts[3],
            "minute": parts[4],
            "second": parts[5],
            "day_of_week": parts[6],
        }
        self._status.ok(f"Device time: {parts[0]:04d}-{parts[1]:02d}-{parts[2]:02d} "
                        f"{parts[3]:02d}:{parts[4]:02d}:{parts[5]:02d}")
        return result

    def get_device_info(self, param: int = 2) -> int | None:
        """Read a device info parameter (see manual for param values)."""
        pkt = make_packet(CMD_GETDEVICEINFO, self.machine_id,
                          struct.pack("<I", param))
        cmd, mid, payload = self._send_recv(pkt)
        if cmd != CMD_ACK_DATA or len(payload) < 4:
            return None
        return struct.unpack("<I", payload[:4])[0]

    def get_device_status(self, param: int = 6) -> int | None:
        """Read a device status value (see manual for param values)."""
        pkt = make_packet(CMD_GETDEVICESTATUS, self.machine_id,
                          struct.pack("<I", param))
        cmd, mid, payload = self._send_recv(pkt)
        if cmd != CMD_ACK_DATA or len(payload) < 4:
            return None
        return struct.unpack("<I", payload[:4])[0]

    def get_serial_number(self) -> str | None:
        """Get the device serial number."""
        pkt = make_packet(CMD_GETSERIALNO, self.machine_id)
        cmd, mid, payload = self._send_recv(pkt)
        if cmd != CMD_ACK_DATA:
            return None
        return payload.decode("utf-8", errors="replace").strip("\x00").strip()

    def get_pin_width(self) -> int:
        """Get the PIN width (number of digits) used by the device."""
        pkt = make_packet(CMD_GETPINWIDTH, self.machine_id)
        cmd, mid, payload = self._send_recv(pkt)
        if cmd != CMD_ACK_DATA or len(payload) < 4:
            return 4
        return struct.unpack("<I", payload[:4])[0]

    # ── Attendance (General) Log Reading ────────────────────────────────

    def read_attendance_logs(self, all_logs: bool = True) -> list[dict]:
        """Read attendance (general log) records from the device.

        Args:
            all_logs: True to read ALL logs (ignoring read mark),
                      False to read only new logs.

        Returns a list of attendance record dicts with keys:
            enroll_number, verify_mode, verify_mode_name,
            attend_status, attend_status_name,
            antipass_status, antipass_status_name,
            year, month, day, hour, minute, second,
            timestamp (ISO format)
        """
        self.enable_device(False)
        try:
            return self._do_read_glogs(all_logs)
        finally:
            self.enable_device(True)

    def _do_read_glogs(self, all_logs: bool) -> list[dict]:
        """Internal: execute the GLog read sequence."""
        cmd = CMD_READALLGLOGDATA if all_logs else CMD_READGLOGDATA
        label = "all attendance logs" if all_logs else "new attendance logs"
        self._status.step(f"Requesting {label}")
        pin_width = self.get_pin_width()

        pkt = make_packet(cmd, self.machine_id)
        cmd_resp, mid, payload = self._send_recv(pkt)

        if cmd_resp == CMD_ACK_ERROR:
            self._status.fail("Device refused attendance log request")
            return []

        records = []
        packet_no = 0
        total_bytes = 0
        self._status.tick(f"Receiving attendance log data ...")

        while True:
            pkt = make_packet(CMD_GETGLOGDATA, self.machine_id)
            cmd_resp, mid, payload = self._send_recv(pkt)

            if cmd_resp != CMD_ACK_DATA:
                break
            if not payload or len(payload) < 12:
                break

            packet_no += 1
            total_bytes += len(payload)
            before = len(records)

            offset = 0
            rec_size = 20
            if len(payload) >= 24 and len(payload) % 24 == 0:
                rec_size = 24

            while offset + rec_size <= len(payload):
                if rec_size == 24:
                    enroll_no, verify_mode, year, month, day, hour, minute, second = \
                        struct.unpack("<IIHHHHHH", payload[offset+4:offset+24])
                else:
                    enroll_no, verify_mode, year, month, day, hour, minute, second = \
                        struct.unpack("<IIHHHHHH", payload[offset:offset+20])

                vm_info = self._parse_verify_mode(verify_mode)

                rec = {
                    "enroll_number": enroll_no,
                    "verify_mode_raw": verify_mode,
                    "verify_mode": vm_info["verify_mode"],
                    "verify_mode_name": vm_info["verify_mode_name"],
                    "attend_status": vm_info["attend_status"],
                    "attend_status_name": vm_info["attend_status_name"],
                    "antipass_status": vm_info["antipass_status"],
                    "antipass_status_name": vm_info["antipass_status_name"],
                    "year": year,
                    "month": month,
                    "day": day,
                    "hour": hour,
                    "minute": minute,
                    "second": second,
                }
                try:
                    dt = datetime.datetime(year, month, day, hour, minute, second)
                    rec["timestamp"] = dt.isoformat()
                except (ValueError, OverflowError):
                    rec["timestamp"] = None

                records.append(rec)
                offset += rec_size

            new_recs = len(records) - before
            kb = total_bytes / 1024
            self._status.tick(
                f"Receiving attendance logs  "
                f"| packets: {packet_no}  "
                f"| records: {len(records)}  "
                f"| data: {kb:.1f} KB"
            )

        if records:
            kb = total_bytes / 1024
            self._status.ok(
                f"Downloaded {len(records)} attendance records "
                f"in {packet_no} packets ({kb:.1f} KB)"
            )
        else:
            self._status.ok("No attendance records found")
        return records

    @staticmethod
    def _parse_verify_mode(verify_mode: int) -> dict:
        """Parse the verify_mode field which encodes multiple status values.

        From manual: Little Endian encoding:
          BYTE 0 - verify mode
          BYTE 1 - attendance status
          BYTE 2 - anti-pass status
        """
        antipass = (verify_mode >> 16) & 0xFF
        daigong = antipass // 4
        antipass = antipass % 4
        verify = verify_mode & 0xFF
        attend = (verify_mode >> 8) & 0xFF

        return {
            "verify_mode": verify,
            "verify_mode_name": VERIFY_MODE_MAP.get(verify, f"Unknown({verify})"),
            "attend_status": attend,
            "attend_status_name": ATTEND_STATUS_MAP.get(attend, ""),
            "antipass_status": antipass,
            "antipass_status_name": ANTIPASS_STATUS_MAP.get(antipass, ""),
            "daigong": daigong,
        }

    # ── Management Log Reading ───────────────────────────────────────────

    def read_management_logs(self, all_logs: bool = True) -> list[dict]:
        """Read management (supervisor log) records from the device.

        Args:
            all_logs: True to read ALL logs, False to read only new logs.

        Returns a list of management record dicts with keys:
            s_enroll_number, g_enroll_number, manipulation, manipulation_name,
            backup_number, backup_number_name,
            year, month, day, hour, minute, second, timestamp
        """
        self.enable_device(False)
        try:
            return self._do_read_slogs(all_logs)
        finally:
            self.enable_device(True)

    def _do_read_slogs(self, all_logs: bool) -> list[dict]:
        cmd = CMD_READALLSLOGDATA if all_logs else CMD_READSLOGDATA
        label = "all management logs" if all_logs else "new management logs"
        self._status.step(f"Requesting {label}")
        pkt = make_packet(cmd, self.machine_id)
        cmd_resp, mid, payload = self._send_recv(pkt)

        if cmd_resp == CMD_ACK_ERROR:
            self._status.fail("Device refused management log request")
            return []

        records = []
        packet_no = 0
        total_bytes = 0
        self._status.tick(f"Receiving management log data ...")

        while True:
            pkt = make_packet(CMD_GETSLOGDATA, self.machine_id)
            cmd_resp, mid, payload = self._send_recv(pkt)

            if cmd_resp != CMD_ACK_DATA:
                break
            if not payload or len(payload) < 28:
                break

            packet_no += 1
            total_bytes += len(payload)

            offset = 0
            rec_size = 40
            while offset + rec_size <= len(payload):
                fields = struct.unpack("<IIIIIIIIHHHHHH",
                                       payload[offset:offset+rec_size])
                (tm_no, s_enroll, s_machine, g_enroll,
                 g_machine, manipulation, backup_no, _reserved,
                 year, month, day, hour, minute, second) = fields

                manip_name = MANIPULATION_MAP.get(manipulation,
                                                  f"Unknown({manipulation})")

                bn_name = None
                if backup_no < 10:
                    bn_name = f"Finger {backup_no}"
                elif backup_no in BACKUP_NUMBER_MAP:
                    bn_name = BACKUP_NUMBER_MAP[backup_no]
                else:
                    bn_name = f"Unknown({backup_no})"

                rec = {
                    "s_enroll_number": s_enroll,
                    "g_enroll_number": g_enroll,
                    "manipulation": manipulation,
                    "manipulation_name": manip_name,
                    "backup_number": backup_no,
                    "backup_number_name": bn_name,
                    "year": year,
                    "month": month,
                    "day": day,
                    "hour": hour,
                    "minute": minute,
                    "second": second,
                }
                try:
                    dt = datetime.datetime(year, month, day, hour, minute, second)
                    rec["timestamp"] = dt.isoformat()
                except (ValueError, OverflowError):
                    rec["timestamp"] = None

                records.append(rec)
                offset += rec_size

            kb = total_bytes / 1024
            self._status.tick(
                f"Receiving management logs  "
                f"| packets: {packet_no}  "
                f"| records: {len(records)}  "
                f"| data: {kb:.1f} KB"
            )

        if records:
            kb = total_bytes / 1024
            self._status.ok(
                f"Downloaded {len(records)} management records "
                f"in {packet_no} packets ({kb:.1f} KB)"
            )
        else:
            self._status.ok("No management records found")
        return records

    # ── User List ────────────────────────────────────────────────────────

    def read_users(self) -> list[dict]:
        """Read all enrolled users from the device.

        Returns a list of user dicts with keys:
            enroll_number, backup_number, privilege, enabled
        """
        self.enable_device(False)
        try:
            return self._do_read_users()
        finally:
            self.enable_device(True)

    def _do_read_users(self) -> list[dict]:
        self._status.step("Fetching enrolled users")
        pkt = make_packet(CMD_READALLUSERID, self.machine_id)
        cmd_resp, mid, payload = self._send_recv(pkt)
        if cmd_resp == CMD_ACK_ERROR:
            self._status.fail("Device refused user list request")
            return []

        users = []
        packet_no = 0
        self._status.tick("Receiving user data ...")
        while True:
            pkt = make_packet(CMD_GETALLUSERID, self.machine_id)
            cmd_resp, mid, payload = self._send_recv(pkt)
            if cmd_resp != CMD_ACK_DATA:
                break
            if not payload or len(payload) < 20:
                break

            packet_no += 1

            offset = 0
            while offset + 20 <= len(payload):
                enroll_no, em_no, backup_no, priv, enable_flag = \
                    struct.unpack("<IIIII", payload[offset:offset+20])
                users.append({
                    "enroll_number": enroll_no,
                    "backup_number": backup_no,
                    "privilege": priv,
                    "enabled": (enable_flag & 0xFF) == 1,
                })
                offset += 20

            self._status.tick(
                f"Receiving users  "
                f"| packets: {packet_no}  "
                f"| users: {len(users)}"
            )

        if users:
            self._status.tick(f"Fetching names for {len(users)} users ...")
            for i, user in enumerate(users):
                name = self._get_user_name(user["enroll_number"])
                user["name"] = name if name else ""
                if i % 10 == 0 or i == len(users) - 1:
                    self._status.tick(
                        f"Fetching user names  "
                        f"| {i+1}/{len(users)}  "
                        f"| current: #{user['enroll_number']}"
                    )
            self._status.ok(f"Found {len(users)} users")
        else:
            self._status.ok("No users enrolled")

        return users

    def _get_user_name(self, enroll_number: int) -> str | None:
        """Get the name of a user by enroll number."""
        pkt = make_packet(CMD_GETUSERNAME, self.machine_id,
                          struct.pack("<I", enroll_number))
        cmd_resp, mid, payload = self._send_recv(pkt)
        if cmd_resp != CMD_ACK_DATA:
            return None
        return payload.decode("utf-8", errors="replace").strip("\x00").strip()

    # ── GeneralOperationXML ──────────────────────────────────────────────

    def general_operation_xml(self, xml_request: str) -> str | None:
        """Send an XML request and receive XML response.

        This uses the SBXPC GeneralOperationXML method.
        The XML request format:
          <REQUEST>command</REQUEST>
          <MSGTYPE>request</MSGTYPE>
          <MachineID>1</MachineID>
          ...additional params...
        """
        xml_bytes = xml_request.encode("utf-8")
        pkt = make_packet(CMD_GENERALOPERATIONXML, self.machine_id, xml_bytes)
        cmd_resp, mid, payload = self._send_recv(pkt)
        if cmd_resp == CMD_ACK_ERROR:
            return None
        return payload.decode("utf-8", errors="replace").strip("\x00")


# ── Output Helpers ───────────────────────────────────────────────────────────

def records_to_csv(records: list[dict], output: str | None = None) -> str:
    """Write records to CSV and return the content. If output is None, return as string."""
    if not records:
        return ""
    fieldnames = list(records[0].keys())

    buf = io.StringIO() if output is None else io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(records)
    content = buf.getvalue()

    if output:
        with open(output, "w", newline="") as f:
            f.write(content)
        logger.info("Wrote %d records to %s", len(records), output)

    return content


def records_to_json(records: list[dict], output: str | None = None,
                    pretty: bool = True) -> str:
    """Write records as JSON."""
    kwargs = {"indent": 2} if pretty else {}
    content = json.dumps(records, **kwargs)
    if output:
        with open(output, "w") as f:
            f.write(content)
        logger.info("Wrote %d records to %s", len(records), output)
    return content


# ── CLI ──────────────────────────────────────────────────────────────────────

def build_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Attendance Device Utility - SBXPC Protocol (Smackbio/Anviz)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--ip", required=True, help="Device IP address")
    parser.add_argument("--port", type=int, default=5005,
                        help="TCP port (default: 5005)")
    parser.add_argument("--password", type=int, default=0,
                        help="Communication password (default: 0)")
    parser.add_argument("--machine", type=int, default=1,
                        help="Machine number/ID (default: 1)")
    parser.add_argument("--timeout", type=float, default=10.0,
                        help="Connection timeout in seconds (default: 10)")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Verbose logging")

    sup = parser.add_argument_group("Supabase integration")
    sup.add_argument("--supabase-url", help="Supabase project URL (or SUPABASE_URL env)")
    sup.add_argument("--supabase-key", help="Supabase API key (or SUPABASE_KEY env)")
    sup.add_argument("--supabase-device-id", help="Device identifier for Supabase records")
    sup.add_argument("--supabase-device-name", help="Device display name for Supabase records")
    sup.add_argument("--supabase-no-paired", action="store_true",
                     help="Skip paired check-in/check-out upload")

    sub = parser.add_subparsers(dest="command", required=True)

    for cmd in ("read-glogs", "read-slogs", "users"):
        p = sub.add_parser(cmd, help={
            "read-glogs": "Read attendance (general) logs from device",
            "read-slogs": "Read management (supervisor) logs from device",
            "users": "List all enrolled users",
        }[cmd])
        p.add_argument("--csv", help="Output file path for CSV")
        p.add_argument("--json", help="Output file path for JSON")

    sub.add_parser("info", help="Show device information")
    sub.add_parser("time", help="Show device date/time")

    return parser


def cmd_info(dev: AttendanceDevice):
    """Show device information."""
    info = {}
    info["IP"] = dev.ip
    info["Port"] = dev.port

    serial = dev.get_serial_number()
    if serial:
        info["Serial Number"] = serial

    dev_time = dev.get_device_time()
    if dev_time:
        dt = f"{dev_time['year']:04d}-{dev_time['month']:02d}-{dev_time['day']:02d} " \
             f"{dev_time['hour']:02d}:{dev_time['minute']:02d}:{dev_time['second']:02d}"
        info["Device Time"] = dt

    for param in (2, 13, 3, 1):
        dev._status.step(f"Reading device info (param {param})")
        val = dev.get_device_info(param)
        if val is not None:
            info[DEVICE_INFO_NAMES.get(param, f"Info#{param}")] = val
        dev._status.ok(f"{DEVICE_INFO_NAMES.get(param, f'Info#{param}')} = {val}")

    for param in (6, 2, 11, 10):
        dev._status.step(f"Reading device status (param {param})")
        val = dev.get_device_status(param)
        if val is not None:
            info[DEVICE_STATUS_NAMES.get(param, f"Status#{param}")] = val
        dev._status.ok(f"{DEVICE_STATUS_NAMES.get(param, f'Status#{param}')} = {val}")

    print()
    print(json.dumps(info, indent=2))


def cmd_time(dev: AttendanceDevice):
    """Show device time."""
    t = dev.get_device_time()
    if not t:
        dev._status.fail("Failed to read device time")
        return


def _upload_to_supabase(args, records: list[dict], status):
    """Upload records to Supabase if configured."""
    supabase_url = args.supabase_url or os.environ.get("SUPABASE_URL")
    supabase_key = args.supabase_key or os.environ.get("SUPABASE_KEY")
    if not supabase_url or not supabase_key:
        return
    try:
        from attendance_supabase import SupabaseConfig, upload_to_supabase
    except ImportError:
        status.write("Supabase support not installed (pip install supabase)")
        return
    cfg = SupabaseConfig(
        url=supabase_url, key=supabase_key,
        device_id=args.supabase_device_id or args.machine,
        device_name=args.supabase_device_name or "",
        device_ip=args.ip,
    )
    if not records:
        status.write("No records to upload to Supabase")
        return
    status.step("Uploading to Supabase")
    result = upload_to_supabase(
        records, cfg, status=status,
        upload_paired=not args.supabase_no_paired,
    )
    parts = [f"{k}={v}" for k, v in result.items() if v]
    if parts:
        status.ok(f"Supabase upload complete ({', '.join(parts)})")
    else:
        status.fail("Supabase upload failed")


def main():
    parser = build_cli()
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="%(levelname)s: %(message)s",
    )

    status = StatusIndicator()
    dev = AttendanceDevice(
        ip=args.ip,
        port=args.port,
        password=args.password,
        machine_id=args.machine,
        timeout=args.timeout,
        status=status,
    )

    try:
        status.step("Connecting to device")
        dev.connect()
        status.ok("Connected to device")

        if args.command == "read-glogs":
            records = dev.read_attendance_logs(all_logs=True)
            if records:
                status.write(f"Total: {len(records)} attendance records")
                if args.csv:
                    status.step(f"Writing CSV to {args.csv}")
                    records_to_csv(records, args.csv)
                    status.ok(f"Exported {len(records)} records to {args.csv}")
                if args.json:
                    status.step(f"Writing JSON to {args.json}")
                    records_to_json(records, args.json)
                    status.ok(f"Exported {len(records)} records to {args.json}")
                if not args.csv and not args.json:
                    print()
                    print(records_to_json(records, pretty=True))
            else:
                status.write("No attendance records found")
            _upload_to_supabase(args, records, status)

        elif args.command == "read-slogs":
            records = dev.read_management_logs(all_logs=True)
            if records:
                status.write(f"Total: {len(records)} management records")
                if args.csv:
                    status.step(f"Writing CSV to {args.csv}")
                    records_to_csv(records, args.csv)
                    status.ok(f"Exported {len(records)} records to {args.csv}")
                if args.json:
                    status.step(f"Writing JSON to {args.json}")
                    records_to_json(records, args.json)
                    status.ok(f"Exported {len(records)} records to {args.json}")
                if not args.csv and not args.json:
                    print()
                    print(records_to_json(records, pretty=True))
            else:
                status.write("No management records found")

        elif args.command == "users":
            users = dev.read_users()
            if users:
                status.write(f"Total: {len(users)} users")
                if args.csv:
                    status.step(f"Writing CSV to {args.csv}")
                    records_to_csv(users, args.csv)
                    status.ok(f"Exported {len(users)} users to {args.csv}")
                if args.json:
                    status.step(f"Writing JSON to {args.json}")
                    records_to_json(users, args.json)
                    status.ok(f"Exported {len(users)} users to {args.json}")
                if not args.csv and not args.json:
                    print()
                    print(records_to_json(users, pretty=True))
            else:
                status.write("No users found")

        elif args.command == "info":
            cmd_info(dev)

        elif args.command == "time":
            cmd_time(dev)

        status.step("Disconnecting")
        dev.disconnect()
        status.ok("Done")

    except (ConnectionError, OSError) as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        if not args.verbose:
            print("(use -v for detailed debug output)", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
