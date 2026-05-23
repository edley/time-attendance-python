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
import select
import typing

logger = logging.getLogger("attendance_device")

# ── Protocol Constants ──────────────────────────────────────────────────────

# Packet start bytes
CMD_PACKET_PREFIX = b"\x50\x50"
CMD_PACKET_PREFIX_55AA = b"\x55\xaa"
CMD_PACKET_ACK_55AA = b"\x5a\xa5"
CMD_PACKET_DATA_55AA = b"\xaa\x55"
CMD_PACKET_BULK_55AA = b"\xa5\x5a"
ANVIZ_PROTOCOL_PREFIXES = {CMD_PACKET_ACK_55AA, CMD_PACKET_DATA_55AA, CMD_PACKET_BULK_55AA}

# Fixed blocks for Anviz 55AA protocol modes
# Bytes 4-11 of the 16-byte command packet; 79 19 XX YY encodes the mode
ANVIZ_FIXEDBLOCK_STATUS     = bytes.fromhex("79 19 52 00 00 00 00 00")
ANVIZ_FIXEDBLOCK_MODE_SWITCH = bytes.fromhex("79 19 16 01 00 00 00 00")
ANVIZ_FIXEDBLOCK_GET_COUNT  = bytes.fromhex("79 19 07 01 00 00 00 00")
ANVIZ_FIXEDBLOCK_READ_DATA  = bytes.fromhex("79 19 08 01 00 00 00 00")

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
    0:   "Finger Print",
    1:   "Finger Print",
    2:   "Password",
    3:   "Card",
    4:   "Finger Print + Card",
    5:   "Finger Print + Password",
    6:   "Card + Password",
    7:   "Finger Print + Card + Password",
    8:   "Finger Print + PIN",
    9:   "PIN",
    10:  "Hand Lock",
    11:  "Prog Lock",
    12:  "Prog Open",
    13:  "Prog Close",
    14:  "Auto Recover",
    15:  "Finger Print + ID",
    16:  "ID Card",
    17:  "IC Card",
    18:  "Finger Print + IC Card",
    19:  "Finger Print + ID + Password",
    20:  "Lock Over",
    21:  "Illegal Open",
    22:  "Duress alarm",
    23:  "Tamper detect",
    24:  "PIN + Card",
    25:  "Finger Print + PIN + Card",
    30:  "Face",
    31:  "Face + Card",
    32:  "Face + Password",
    33:  "Face + Card + Password",
    34:  "Face + Finger Print",
     51:  "Finger Print (In)",
    52:  "Password (In)",
    53:  "Card (In)",
    54:  "Finger Print + Card (In)",
    55:  "Finger Print + Password (In)",
    56:  "Card + Password (In)",
    57:  "Finger Print + Card + Password (In)",
    80:  "Face (In)",
    81:  "Face + Card (In)",
    82:  "Face + Password (In)",
    83:  "Face + Card + Password (In)",
    84:  "Face + Finger Print (In)",
    101: "Finger Print (Out)",
    102: "Password (Out)",
    103: "Card (Out)",
    104: "Finger Print + Card (Out)",
    105: "Finger Print + Password (Out)",
    106: "Card + Password (Out)",
    107: "Finger Print + Card + Password (Out)",
    130: "Face (Out)",
    131: "Face + Card (Out)",
    132: "Face + Password (Out)",
    133: "Face + Card + Password (Out)",
    134: "Face + Finger Print (Out)",
    151: "Finger Print (Extra)",
    152: "Password (Extra)",
    153: "Card (Extra)",
    154: "Finger Print + Card (Extra)",
    155: "Finger Print + Password (Extra)",
    156: "Card + Password (Extra)",
    157: "Finger Print + Card + Password (Extra)",
    180: "Face (Extra)",
    181: "Face + Card (Extra)",
    182: "Face + Password (Extra)",
    183: "Face + Card + Password (Extra)",
    184: "Face + Finger Print (Extra)",
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


def make_packet_anviz(command_field: int, machine_id: int = 1,
                      fixed_block: bytes | None = None) -> bytes:
    """Build a 55AA-protocol command packet (16 bytes fixed size).

    Format:
      [0x55, 0xaa] [MachineID:2 LE] [FixedBlock:8] [CmdField:2 LE] [Checksum:2 LE]

    The fixed block encodes the device mode/state.  Default is status mode.
    """
    mid_bytes = struct.pack("<H", machine_id)
    fb = ANVIZ_FIXEDBLOCK_STATUS if fixed_block is None else fixed_block
    cmd_bytes = struct.pack("<H", command_field)
    buf = CMD_PACKET_PREFIX_55AA + mid_bytes + fb + cmd_bytes
    checksum = sum(buf) & 0xFFFF
    return buf + struct.pack("<H", checksum)


def parse_reply(data: bytes):
    """Parse an SBXPC or 55AA reply packet. Returns (command, machine_id, payload)."""
    if len(data) < 8:
        raise ValueError(f"Packet too short: {len(data)} bytes")

    prefix = data[:2]

    # 55AA protocol (Anviz)
    if prefix == CMD_PACKET_ACK_55AA or prefix == CMD_PACKET_DATA_55AA:
        mid = struct.unpack("<H", data[2:4])[0]
        if len(data) == 8 and prefix == CMD_PACKET_ACK_55AA:
            # ACK: 5aa5 [mid:2] [status:2] [chk:2]
            status = struct.unpack("<H", data[4:6])[0]
            return status, mid, b""
        # Data response: aa55 [mid:2] [field:2] [count:2] [records...] [chk:2]
        hdr_size = 8  # prefix(2) + mid(2) + field(2) + count(2)
        rec_count = struct.unpack("<H", data[6:8])[0]
        rec_size = 4  # each record appears to be 4 bytes
        payload_end = hdr_size + rec_count * rec_size
        payload = data[hdr_size:payload_end]
        return 0, mid, payload

    # Standard SBXPC protocol (PP prefix)
    if prefix != CMD_PACKET_PREFIX:
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

    def __init__(self, log_file: str | None = None):
        self._spinner = itertools.cycle("⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏")
        self._enabled = sys.stderr.isatty()
        self._current = ""
        self._phase = 0
        self._step_start: float = 0.0
        self._global_start: float = 0.0
        self._log_fh: typing.TextIO | None = None
        if log_file:
            try:
                self._log_fh = open(log_file, "a", buffering=1)
                self._log_fh.write(f"\n--- Session started {datetime.datetime.now().isoformat()} ---\n")
                self._log_fh.flush()
            except OSError as e:
                logger.warning("Cannot open log file %s: %s", log_file, e)

    def _log(self, msg: str):
        """Write a plain-text line to the log file (no ANSI codes)."""
        if self._log_fh:
            try:
                self._log_fh.write(msg + "\n")
                self._log_fh.flush()
            except OSError:
                pass

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
                out = f"✓ {self._current}  [{self._step_elapsed()}]"
                print(f"\r\x1b[K\x1b[32m✓\x1b[0m {self._current}  [{self._step_elapsed()}]", file=sys.stderr)
                self._log(out)
            self._step_start = now
            self._current = msg
            self._tick()
        else:
            if self._current:
                out = f"✓ {self._current}  [{self._step_elapsed()}]"
                print(out, file=sys.stderr)
                self._log(out)
            self._step_start = now
            self._current = msg
            prefix = f"[{elapsed_total}]" if elapsed_total else ""
            line = f"{prefix}  {msg} ..."
            print(line, file=sys.stderr)
            self._log(line)

    def tick(self, msg: str | None = None):
        """Advance the spinner in place, showing step elapsed time."""
        if msg:
            self._current = msg
        if not self._enabled and msg:
            line = f"  [{self._total_elapsed()}] {msg}"
            print(line, file=sys.stderr)
            self._log(line)
            return
        if self._enabled:
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
        out = f"✓ {full}"
        if self._enabled:
            print(f"\r\x1b[K\x1b[32m✓\x1b[0m {full}", file=sys.stderr)
        else:
            print(out, file=sys.stderr)
        self._log(out)
        self._current = ""
        self._step_start = 0.0

    def fail(self, msg: str | None = None):
        """Mark the current step as failed with a cross and timings."""
        elapsed = self._step_elapsed() if self._step_start else ""
        label = msg if msg else self._current
        full = f"{label}" + (f"  [{elapsed}]" if elapsed else "")
        out = f"✗ {full}"
        if self._enabled:
            print(f"\r\x1b[K\x1b[31m✗\x1b[0m {full}", file=sys.stderr)
        else:
            print(out, file=sys.stderr)
        self._log(out)
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
        self._log(msg)

    def _step_elapsed_seconds(self) -> float:
        if self._step_start:
            return time.time() - self._step_start
        return 0.0

    def waiting(self, msg: str):
        """Alias for tick — log a waiting/polling state."""
        self.tick(msg)

    def startup(self, msg: str):
        """Log an initialisation message."""
        self.write(msg)


# ── Device Connection ───────────────────────────────────────────────────────

class AttendanceDevice:
    """Represents a connection to an SBXPC attendance device."""

    def __init__(self, ip: str, port: int = 5005, password: int = 0,
                 machine_id: int = 1, timeout: float = 10.0,
                 hostname: str | None = None,
                 status: StatusIndicator | None = None):
        self.ip = ip
        self.port = port
        self.password = password
        self.machine_id = machine_id
        self.timeout = timeout
        self.hostname = hostname
        self._sock: socket.socket | None = None
        self._use_anviz = False  # True when device uses 55AA protocol
        self._status = status or StatusIndicator()

    @property
    def _connect_addr(self) -> str:
        """Return the address to connect to (hostname takes priority over IP)."""
        return self.hostname if self.hostname else self.ip

    # ── Connection ──────────────────────────────────────────────────────

    def connect(self) -> bool:
        """Open TCP connection and authenticate with the device."""
        logger.info("Connecting to %s:%d (timeout=%ds, password=%d) ...",
                     self.ip, self.port, self.timeout, self.password)

        # ── DNS resolution ────────────────────────────────────────────
        connect_target = self._connect_addr
        display_target = f"{self.ip}:{self.port}"
        if self.hostname:
            display_target = f"{self.hostname} ({self.ip})"

        self._status.step(f"Network resolution for {connect_target}")
        self._status.tick("Performing DNS lookup ...")
        resolved_addr = connect_target
        try:
            addrinfo = socket.getaddrinfo(
                connect_target, self.port, socket.AF_INET, socket.SOCK_STREAM
            )
            resolved_addr = addrinfo[0][4][0]
            if resolved_addr != connect_target:
                self._status.tick(f"Resolved {connect_target} → {resolved_addr}")
            else:
                self._status.tick(f"Resolved to {resolved_addr}")
        except socket.gaierror as e:
            self._status.fail(f"DNS resolution failed: {e}")
            raise ConnectionError(
                f"Cannot resolve '{connect_target}' — {e}. "
                f"Verify the hostname or IP address is correct."
            )
        self._status.ok(f"Target resolved: {connect_target} → {resolved_addr}:{self.port}")

        # ── TCP connection (non-blocking with progress) ───────────────
        conn_label = f"{resolved_addr}:{self.port}"
        self._status.step(f"TCP connection to {conn_label}")

        self._status.tick("Creating TCP socket ...")
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setblocking(False)

        self._status.tick("Initiating TCP handshake ...")
        connect_start = time.time()
        try:
            self._sock.connect((resolved_addr, self.port))
        except BlockingIOError:
            pass  # Expected for non-blocking sockets

        # Wait for connection to complete using select
        last_tick = 0.0
        connected = False
        while True:
            elapsed = time.time() - connect_start
            remaining = self.timeout - elapsed

            if remaining <= 0:
                self._sock.close()
                self._sock = None
                self._status.fail(f"TCP connection timed out after {elapsed:.1f}s")
                host_help = ""
                if self.hostname:
                    host_help = (
                        f"  Hostname '{self.hostname}' resolved to {resolved_addr}.\n"
                    )
                raise ConnectionError(
                    f"TCP connection to {display_target} timed out "
                    f"after {elapsed:.1f}s (timeout={self.timeout}s).\n"
                    f"  Device at {resolved_addr} did not respond to TCP SYN.\n"
                    f"{host_help}"
                    f"  Possible causes:\n"
                    f"    (1) Device is powered off or disconnected from the network\n"
                    f"    (2) Firewall blocking port {self.port}\n"
                    f"    (3) Wrong IP address (ping {self.ip} to verify)\n"
                    f"    (4) Device is on a different subnet / VLAN\n"
                    f"    (5) Device uses a different port (default is 5005)\n"
                    f"\n"
                    f"  Next steps:\n"
                    f"    Run diagnostics: python3 attendance_device.py "
                    f"--ip {self.ip} --hostname {self.hostname or ''} diagnose"
                )

            _, ready, errors = select.select(
                [self._sock], [self._sock], [self._sock], 0.5
            )

            if ready or errors:
                # Connection completed (or failed)
                err = self._sock.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
                if err:
                    err_str = os.strerror(err)
                    self._sock.close()
                    self._sock = None
                    self._status.fail(f"Connection failed: {err_str}")
                    raise ConnectionError(
                        f"Connection to {display_target} failed — {err_str}. "
                        f"Check if the device is reachable and port {self.port} is open."
                    )
                connected = True
                break

            # Update tick every ~1s to show live progress
            if elapsed - last_tick >= 1.0:
                last_tick = elapsed
                self._status.tick(
                    f"Waiting for TCP connection response "
                    f"({elapsed:.0f}s / {self.timeout}s) ..."
                )

        connect_duration = time.time() - connect_start
        self._sock.setblocking(True)
        self._sock.settimeout(self.timeout)
        self._status.ok(
            f"TCP connection established ({connect_duration:.1f}s)"
        )

        # ── TCP keepalive ─────────────────────────────────────────────
        self._status.tick("Enabling TCP keepalive ...")
        self._set_keepalive()

        # ── Protocol handshake ────────────────────────────────────────
        # Try 55AA protocol first (Anviz devices), fall back to SBXPC.
        # ALWAYS use the original TCP socket — sending a probe packet
        # on a different protocol can confuse the device's state machine.
        self._status.step("Protocol handshake")

        # Some devices send an unsolicited banner right after TCP connect.
        # Try reading it first before sending anything.
        self._status.tick("Listening for device banner ...")
        banner = b""
        try:
            self._sock.settimeout(1.0)
            banner = self._sock.recv(1024)
        except (OSError, socket.timeout):
            pass

        if len(banner) >= 2 and banner[:2] in (CMD_PACKET_ACK_55AA, CMD_PACKET_DATA_55AA):
            self._status.ok("55AA (Anviz) protocol detected (banner)")
            self._use_anviz = True
            self._sock.settimeout(self.timeout)
            return True

        # Try 55AA handshake with cmd=0 (hello/connect command)
        self._status.tick("Sending 55AA handshake ...")
        anviz_ok = False
        for cmd_val, label in [(0, "cmd=0"), (1, "cmd=1")]:
            if anviz_ok:
                break
            pkt = make_packet_anviz(cmd_val, self.machine_id)
            try:
                self._sock.settimeout(5.0)
                self._sock.sendall(pkt)
                resp = self._recv_all(8)
                if len(resp) >= 2 and resp[:2] in (CMD_PACKET_ACK_55AA, CMD_PACKET_DATA_55AA):
                    anviz_ok = True
                    self._use_anviz = True
                    self._status.ok(f"55AA (Anviz) protocol detected ({label})")
            except (OSError, ConnectionError):
                pass

        if anviz_ok:
            self._sock.settimeout(self.timeout)
            status_code, _, _ = parse_reply(resp)
            if status_code != 1:
                self._status.fail(f"Device rejected connection (status={status_code})")
                raise ConnectionError(
                    f"Device at {resolved_addr}:{self.port} rejected 55AA connection. "
                    f"Status code: {status_code}. Check communication password."
                )
            # Consume trailing data (device may send status after ACK)
            self._status.tick("Clearing initial status data ...")
            self._sock.settimeout(0.3)
            try:
                while True:
                    chunk = self._sock.recv(4096)
                    if not chunk:
                        break
            except (OSError, socket.timeout):
                pass
            self._sock.settimeout(self.timeout)
            self._status.tick("Ready")
            return True

        # ── Fall back to SBXPC ────────────────────────────────────────
        self._sock.settimeout(self.timeout)
        self._status.tick("55AA failed, trying SBXPC protocol ...")
        pkt = make_packet(CMD_CONNECT, self.machine_id, b"\x00" * 4)

        try:
            self._status.tick("Waiting for device acknowledgment ...")
            cmd, mid, payload = self._send_recv(pkt)
        except ConnectionError:
            elapsed_phase = self._status._step_elapsed_seconds()
            self._status.fail(f"No response after {elapsed_phase:.1f}s")
            raise ConnectionError(
                f"Connected to {resolved_addr}:{self.port} via TCP but device did not "
                f"respond to any known protocol ({elapsed_phase:.1f}s).\n"
                f"  Target: {connect_target} → {resolved_addr}\n"
                f"  Possible causes:\n"
                f"    (1) Device uses a different protocol (not SBXPC/Anviz)\n"
                f"    (2) Device needs a different port\n"
                f"    (3) Device firmware does not support PC access\n"
                f"    (4) Device is busy (try again later)"
            )

        if cmd == CMD_ACK_ERROR:
            self._status.fail("Device rejected connection request")
            raise ConnectionError(
                f"Device at {resolved_addr}:{self.port} rejected the connection. "
                f"Check communication password (currently set to {self.password})."
            )

        self._status.ok("SBXPC handshake successful")

        # ── Password authentication (SBXPC only) ──────────────────────
        if self.password != 0:
            self._status.step("Device authentication")

            self._status.tick("Sending authentication credentials ...")
            pkt = make_packet(CMD_CONNECT, self.machine_id,
                              struct.pack("<I", self.password))

            try:
                cmd, mid, payload = self._send_recv(pkt)
            except ConnectionError:
                elapsed_phase = self._status._step_elapsed_seconds()
                self._status.fail(f"Authentication timed out after {elapsed_phase:.1f}s")
                raise ConnectionError(
                    f"Device at {resolved_addr}:{self.port} did not respond to "
                    f"authentication request ({elapsed_phase:.1f}s)."
                )

            if cmd == CMD_ACK_ERROR:
                self._status.fail("Authentication rejected (bad password)")
                raise ConnectionError(
                    f"Device at {resolved_addr}:{self.port} rejected password "
                    f"{self.password}. Verify the communication password."
                )
            self._status.ok("Authentication successful")

        return True

    def disconnect(self):
        """Send exit (SBXPC) or just close (55AA) the connection."""
        if not self._sock:
            return
        if not self._use_anviz:
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
        logger.debug("  >> send: len=%d %s", len(pkt), pkt.hex())
        self._sock.sendall(pkt)

        if self._use_anviz:
            return self._anviz_recv_response()

        # Standard SBXPC protocol (PP prefix)
        header = self._recv_all(8)
        if len(header) < 8:
            raise ConnectionError("Connection closed while reading header")

        payload_len = struct.unpack("<H", header[4:6])[0]
        logger.debug("  << recv: cmd=0x%02x payload_len=%d", header[3], payload_len)

        total_size = 6 + payload_len + 2  # header(6) + payload + checksum(2)
        if total_size <= 8:
            reply = header[:total_size]
        else:
            rest = self._recv_all(total_size - 8)
            reply = header + rest
        return parse_reply(reply)

    def _anviz_recv_response(self) -> tuple:
        """Receive and parse a 55AA-protocol response.

        The device often sends ACK+DATA (or ACK+BULK) as separate packets.
        This reads ALL available data within a short timeout window,
        then parses the concatenated response.

        Returns normalized (command, machine_id, payload).
        """
        data = b""
        deadline = time.time() + self.timeout
        while time.time() < deadline:
            remaining = deadline - time.time()
            # After we already have data, use short timeout for trailing packets
            wait = 0.3 if data else remaining
            try:
                self._sock.settimeout(min(wait, remaining))
                chunk = self._sock.recv(4096)
                if not chunk:
                    break
                data += chunk
            except socket.timeout:
                if data:
                    break  # got data, idle 300ms — done reading
                # No data yet — keep polling
            except OSError:
                break
        self._sock.settimeout(self.timeout)

        if not data:
            raise ConnectionError("Connection closed while reading response")

        prefix = data[:2]
        logger.debug("  << recv: prefix=%s len=%d", prefix.hex(), len(data))

        # ── ACK (5aa5) ─────────────────────────────────────────────────
        if prefix == CMD_PACKET_ACK_55AA:
            if len(data) < 8:
                raise ValueError(f"Short ACK packet: {len(data)} bytes")
            status = struct.unpack("<H", data[4:6])[0]
            mid = struct.unpack("<H", data[2:4])[0]
            extra = data[8:]

            # Data (aa55 or a55a) follows the ACK — return the data portion
            if extra:
                if extra[:2] == CMD_PACKET_DATA_55AA and len(extra) >= 8:
                    rec_count = struct.unpack("<H", extra[6:8])[0]
                    expected = 8 + rec_count * 4 + 2
                    if len(extra) >= expected:
                        payload = extra[8:expected - 2]
                        # Preserve any trailing data (a55a bulk after aa55)
                        trailing = extra[expected:]
                        if trailing:
                            payload += trailing
                        return (CMD_ACK_DATA, mid, payload)
                    return (CMD_ACK_DATA, mid, extra[8:])
                # Bulk data (a55a) after ACK
                return (CMD_ACK_DATA, mid, extra)

            if status == 1:
                return (CMD_ACK_OK, mid, b"")
            return (CMD_ACK_ERROR, mid, b"")

        # ── Data (aa55) ────────────────────────────────────────────────
        if prefix == CMD_PACKET_DATA_55AA:
            if len(data) < 8:
                raise ValueError(f"Short data packet: {len(data)} bytes")
            mid = struct.unpack("<H", data[2:4])[0]
            rec_count = struct.unpack("<H", data[6:8])[0]
            expected_len = 8 + rec_count * 4 + 2
            if len(data) >= expected_len:
                payload = data[8:expected_len - 2]
                extra = data[expected_len:]
                if extra:
                    payload += extra
            else:
                payload = data[8:]
            return (CMD_ACK_DATA, mid, payload)

        # ── Bulk data (a55a) ────────────────────────────────────────────
        if prefix == CMD_PACKET_BULK_55AA:
            mid = struct.unpack("<H", data[2:4])[0]
            return (CMD_ACK_DATA, mid, data)

        raise ValueError(f"Unknown 55AA prefix: {prefix.hex()}")

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

    def _make_cmd_pkt(self, cmd: int, data: bytes = b"") -> bytes:
        """Build a command packet using the detected protocol."""
        if self._use_anviz:
            return make_packet_anviz(cmd, self.machine_id)
        return make_packet(cmd, self.machine_id, data)

    def enable_device(self, enable: bool = True) -> bool:
        """Enable or disable the device for PC access."""
        if self._use_anviz:
            return True  # 55AA protocol does not need enable/disable
        pkt = make_packet(CMD_ENABLEDEVICE if enable else CMD_DISABLEDEVICE,
                          self.machine_id)
        cmd, mid, payload = self._send_recv(pkt)
        return cmd == CMD_ACK_OK

    def empty_attendance_logs(self) -> bool:
        """Clear all attendance (general) log data from the device.

        Disables the device for PC access first (SBXPC), sends the clear
        command, then re-enables the device.

        Returns True if the device acknowledged the clear.
        """
        self._status.step("Clearing attendance logs from device")
        if not self._use_anviz:
            self._status.write("Disabling device for PC access ...")
            self.enable_device(False)
        pkt = self._make_cmd_pkt(CMD_EMPTYGLOGDATA)
        cmd, mid, payload = self._send_recv(pkt)
        ok = cmd == CMD_ACK_OK
        if not self._use_anviz:
            self._status.write("Re-enabling device ...")
            self.enable_device(True)
        if ok:
            self._status.ok("Attendance logs cleared successfully")
        else:
            self._status.fail("Failed to clear attendance logs")
        return ok

    def empty_management_logs(self) -> bool:
        """Clear all management (supervisor) log data from the device.

        Disables the device for PC access first (SBXPC), sends the clear
        command, then re-enables the device.

        Returns True if the device acknowledged the clear.
        """
        self._status.step("Clearing management logs from device")
        if not self._use_anviz:
            self._status.write("Disabling device for PC access ...")
            self.enable_device(False)
        pkt = self._make_cmd_pkt(CMD_EMPTYSLOGDATA)
        cmd, mid, payload = self._send_recv(pkt)
        ok = cmd == CMD_ACK_OK
        if not self._use_anviz:
            self._status.write("Re-enabling device ...")
            self.enable_device(True)
        if ok:
            self._status.ok("Management logs cleared successfully")
        else:
            self._status.fail("Failed to clear management logs")
        return ok

    def get_device_time(self) -> dict | None:
        """Read the current date/time from the device."""
        self._status.step("Reading device time")
        pkt = self._make_cmd_pkt(CMD_GETDEVICETIME)
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
        pkt = self._make_cmd_pkt(CMD_GETDEVICEINFO)
        cmd, mid, payload = self._send_recv(pkt)
        if cmd != CMD_ACK_DATA or len(payload) < 4:
            return None
        return struct.unpack("<I", payload[:4])[0]

    def get_device_status(self, param: int = 6) -> int | None:
        """Read a device status value (see manual for param values)."""
        pkt = self._make_cmd_pkt(CMD_GETDEVICESTATUS)
        cmd, mid, payload = self._send_recv(pkt)
        if cmd != CMD_ACK_DATA or len(payload) < 4:
            return None
        return struct.unpack("<I", payload[:4])[0]

    def get_serial_number(self) -> str | None:
        """Get the device serial number."""
        pkt = self._make_cmd_pkt(CMD_GETSERIALNO)
        cmd, mid, payload = self._send_recv(pkt)
        if cmd != CMD_ACK_DATA:
            return None
        return payload.decode("utf-8", errors="replace").strip("\x00").strip()

    def get_pin_width(self) -> int:
        """Get the PIN width (number of digits) used by the device."""
        pkt = self._make_cmd_pkt(CMD_GETPINWIDTH)
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
        if self._use_anviz:
            return self._read_glogs_anviz(all_logs)
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

    # ── 55AA Log Reading ───────────────────────────────────────────────

    def _send_anviz_ack(self, status: int = 0, cmd_field: int = 1):
        """Send an ACK packet back to the device.

        The 55AA ACK format (from vendor captures):
          5aa5 [mid:2] [cmd_field:2] [status:2] [chk:2]  (10 bytes)

        Sending ACK(status=0) after receiving the record count triggers
        the device to send the a55a bulk data.
        """
        if not self._sock:
            return
        mid_bytes = struct.pack("<H", self.machine_id)
        cmd_bytes = struct.pack("<H", cmd_field)
        status_bytes = struct.pack("<H", status)
        payload = (CMD_PACKET_ACK_55AA + mid_bytes + cmd_bytes + status_bytes)
        chk = struct.pack("<H", sum(payload) & 0xFFFF)
        pkt = payload + chk
        logger.debug("  >> send ACK: len=%d %s", len(pkt), pkt.hex())
        self._sock.sendall(pkt)

    def _read_glogs_anviz(self, all_logs: bool = True) -> list[dict]:
        """Read attendance logs using the 55AA protocol (Anviz devices).

        Protocol sequence (from vendor captures):
          1. Status heartbeat         (cmd=1, fixed=52 00)
          2. Request data             (cmd=0 or 6, fixed=08 01)
          3. Send prepare cmds        (cmd=0 then cmd=1 with count, fixed=07 01)
          4. Send ACK(status=0)        triggers bulk data transfer
          5. Read aa55 DATA + a55a BULK
          6. Send ACK(status=count)   confirm receipt
          7. Read aa55 DATA(0)        completion marker
          8. Parse bulk response into record dicts
        """
        self._status.step("Reading attendance logs (55AA protocol)")

        # Step 1: Heartbeat
        self._status.tick("Sending heartbeat ...")
        pkt = make_packet_anviz(1, self.machine_id, ANVIZ_FIXEDBLOCK_STATUS)
        cmd, mid, payload = self._send_recv(pkt)
        if cmd not in (CMD_ACK_OK, CMD_ACK_DATA):
            self._status.fail("Heartbeat failed")
            return []

        # Step 2: Request data (08 01 + cmd=6/0) → get record count
        # Try cmd=6 first (used by current firmware in vendor capture)
        data_cmd_values = [6, 0]
        raw_data = b""
        record_count = 0

        for data_cmd in data_cmd_values:
            self._status.tick(f"Requesting data (cmd={data_cmd}) ...")
            pkt = make_packet_anviz(data_cmd, self.machine_id,
                                    ANVIZ_FIXEDBLOCK_READ_DATA)
            cmd, mid, raw_data = self._send_recv(pkt)

            if cmd != CMD_ACK_DATA:
                continue

            # Check if response already contains a55a bulk data
            if CMD_PACKET_BULK_55AA in raw_data[:8]:
                break

            # Response is aa55 data with record count
            if len(raw_data) >= 4:
                logger.debug("aa55 raw_data hex: %s", raw_data.hex())
                # aa55 DATA format: aa55 [mid_or_status:4] [count:4] [chk:2]
                # or:            aa55 [mid:2] [field1:2] [field2:2] [count:4]
                # count is at offset 6 or 8 depending on format
                if raw_data[:2] == CMD_PACKET_PREFIX_55AA and len(raw_data) >= 12:
                    # Try offset 6 (4-byte header) first, fallback to offset 8
                    candidate = struct.unpack("<I", raw_data[6:10])[0]
                    if 0 < candidate < 100000:
                        record_count = candidate
                    else:
                        record_count = struct.unpack("<I", raw_data[8:12])[0]
                else:
                    record_count = struct.unpack("<I", raw_data[:4])[0]
                self._status.tick(f"Device reports {record_count} records")

            if record_count == 0:
                continue

            # Vendor sends two 07 01 prepare commands before trigger ACK:
            #   cmd=0        (param=0)      → "ready to transfer"
            #   cmd=1        (param=count)  → "expecting N records"
            for prep_cmd, prep_param in [(0, 0), (1, record_count)]:
                self._status.tick(f"Preparing transfer (cmd={prep_cmd}, param={prep_param}) ...")
                fb_07 = ANVIZ_FIXEDBLOCK_GET_COUNT  # 8 bytes (07 01)
                # Embed param at fixed-block bytes 4-5 (LE)
                fb_with_param = fb_07[:4] + struct.pack("<H", prep_param) + fb_07[6:8]
                pkt = make_packet_anviz(prep_cmd, self.machine_id, fb_with_param)
                cmd2, mid2, rdata = self._send_recv(pkt)
                if cmd2 not in (CMD_ACK_OK, CMD_ACK_DATA):
                    logger.warning("Prepare cmd=%d failed (cmd=%d)", prep_cmd, cmd2)

            # Step 3: Send ACK to trigger bulk data transfer
            self._status.tick("Requesting data transfer ...")
            self._send_anviz_ack(0)

            # Read the bulk data that follows (device sends aa55 DATA first,
            # then a55a BULK ~300ms later)
            bulk = b""
            deadline = time.time() + self.timeout
            while time.time() < deadline:
                remaining = deadline - time.time()
                try:
                    self._sock.settimeout(min(0.5, remaining))
                    chunk = self._sock.recv(4096)
                    if not chunk:
                        break
                    bulk += chunk
                    if CMD_PACKET_BULK_55AA in bulk:
                        break
                except socket.timeout:
                    if CMD_PACKET_BULK_55AA in bulk:
                        break
                except OSError:
                    break
            self._sock.settimeout(self.timeout)

            if CMD_PACKET_BULK_55AA in bulk:
                raw_data = bulk
                break

        # Step 4: Send ACK(status=count) to confirm receipt
        if record_count > 0 and CMD_PACKET_BULK_55AA in raw_data:
            self._status.tick("Confirming data receipt ...")
            self._send_anviz_ack(record_count)

            # Step 5: Device sends aa55 DATA(00000000) as completion marker
            try:
                self._sock.settimeout(2)
                marker = self._sock.recv(4096)
                logger.debug("Completion marker: %s", marker.hex() if marker else "(empty)")
            except socket.timeout:
                logger.debug("No completion marker (timeout)")
            self._sock.settimeout(self.timeout)

        # Step 6: Extract a55a bulk data and parse records
        a55a_idx = raw_data.find(CMD_PACKET_BULK_55AA)
        if a55a_idx >= 0:
            records = self._parse_anviz_bulk(raw_data[a55a_idx:], record_count)
        else:
            records = self._parse_anviz_bulk(raw_data, record_count)

        if records:
            self._status.ok(f"Downloaded {len(records)} attendance records")
        else:
            self._status.ok("No attendance records parsed")
        return records

    def _parse_anviz_bulk(self, data: bytes, expected_count: int) -> list[dict]:
        """Parse bulk a55a attendance data into record dicts.

        From vendor tcpdump analysis, records in the a55a bulk response
        are 12 bytes each:
          [timestamp_or_special:4 LE] [enroll_number:4 LE] [flags:4 LE]

        The first record may be preceded by a `5aa5 0100` sync marker (4 bytes)
        that follows the a55a packet header.

        The flags field upper 16 bits appear to be a marker (0xffff = valid),
        and the lower 16 bits encode mode/status info.
        """
        if len(data) < 8:
            return []

        RECORD_SIZE = 12

        # Find the best alignment by scoring each trial offset.
        # Score: +1 for each valid enroll (1..65000), +extra if enroll <= 100
        best_offset = 0
        best_score = -1

        for trial_offset in range(min(24, len(data))):
            score = 0
            pos = trial_offset
            while pos + RECORD_SIZE <= len(data):
                enroll = struct.unpack("<I", data[pos + 4:pos + 8])[0]
                if 1 <= enroll <= 100:
                    score += 5
                elif 1 <= enroll <= 65000:
                    score += 1
                pos += RECORD_SIZE

            if score > best_score:
                best_score = score
                best_offset = trial_offset

        # Parse from the best offset
        pos = best_offset
        parsed = []
        ANVIZ_EPOCH = datetime.datetime(2000, 1, 1)
        MIN_VALID_TS = 365 * 24 * 3600  # ~1 year in seconds (filters system events)

        while pos + RECORD_SIZE <= len(data):
            chunk = data[pos:pos + RECORD_SIZE]
            ts_or_id = struct.unpack("<I", chunk[0:4])[0]
            enroll = struct.unpack("<I", chunk[4:8])[0]
            flags = struct.unpack("<I", chunk[8:12])[0]

            if enroll == 0 or enroll > 65000:
                pos += RECORD_SIZE
                continue

            # Skip system events (ts_or_id < 1 year = not a real timestamp)
            if ts_or_id < MIN_VALID_TS:
                pos += RECORD_SIZE
                continue

            # Timestamp: seconds since 2000-01-01
            dt = None
            try:
                dt = ANVIZ_EPOCH + datetime.timedelta(seconds=ts_or_id)
            except (OverflowError, ValueError):
                pos += RECORD_SIZE
                continue

            # Flags: lower 16 bits encode mode/status info
            flags_lower = flags & 0xFFFF

            # Normalize to standard SBXPC-compatible fields
            vm_info = self._parse_verify_mode(flags_lower)

            rec = {
                "enroll_number": enroll,
                "verify_mode_raw": flags_lower,
                "verify_mode": vm_info["verify_mode"],
                "verify_mode_name": vm_info["verify_mode_name"],
                "attend_status": vm_info["attend_status"],
                "attend_status_name": vm_info["attend_status_name"],
                "antipass_status": vm_info["antipass_status"],
                "antipass_status_name": vm_info["antipass_status_name"],
                "flags_raw": flags_lower,
                "year": dt.year,
                "month": dt.month,
                "day": dt.day,
                "hour": dt.hour,
                "minute": dt.minute,
                "second": dt.second,
                "timestamp": dt.isoformat(),
            }

            parsed.append(rec)
            pos += RECORD_SIZE

        return parsed

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
    parser.add_argument("--ip", help="Device IP address (not required if --hostname is given)")
    parser.add_argument("--port", type=int, default=5005,
                        help="TCP port (default: 5005)")
    parser.add_argument("--password", type=int, default=0,
                        help="Communication password (default: 0)")
    parser.add_argument("--machine", type=int, default=1,
                        help="Machine number/ID (default: 1)")
    parser.add_argument("--timeout", type=float, default=10.0,
                        help="Connection timeout in seconds (default: 10)")
    parser.add_argument("--hostname",
                        help="Device hostname (uses DNS resolution instead of direct IP)")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Verbose logging")
    parser.add_argument("--log-file",
                        help="Path to write a detailed session log file")

    sup = parser.add_argument_group("Supabase integration")
    sup.add_argument("--supabase-url", help="Supabase project URL (or SUPABASE_URL env)")
    sup.add_argument("--supabase-key", help="Supabase API key (or SUPABASE_KEY env)")
    sup.add_argument("--supabase-device-id", help="Device identifier for Supabase records")
    sup.add_argument("--supabase-device-name", help="Device display name for Supabase records")
    sup.add_argument("--supabase-department", help="Department name for attendance records")
    sup.add_argument("--supabase-place", help="Location/place name for attendance records")
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

    sub.add_parser("clear-glogs", help="Clear all attendance (general) logs from device")
    sub.add_parser("clear-slogs", help="Clear all management (supervisor) logs from device")
    sub.add_parser("info", help="Show device information")
    sub.add_parser("time", help="Show device date/time")
    sub.add_parser("diagnose", help="Run network diagnostics to troubleshoot connectivity")

    return parser


def cmd_info(dev: AttendanceDevice):
    """Show device information."""
    info = {}
    info["IP"] = dev.ip
    info["Port"] = dev.port
    if dev.hostname:
        info["Hostname"] = dev.hostname

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


COMMON_PORTS = [5005, 4370, 80, 8080, 443, 8081, 8000, 3000]


def cmd_diagnose(args, status):
    """Run connectivity diagnostics against the target device."""
    if not args.ip and not args.hostname:
        print("ERROR: Provide --ip or --hostname to diagnose", file=sys.stderr)
        return

    label = args.ip or ""
    if args.hostname:
        label = f"{args.hostname}" + (f" ({args.ip})" if args.ip else "")
    status.startup(f"Diagnostics for {label}")

    # 1. Hostname resolution + IP validation
    if args.hostname:
        status.step(f"Resolving hostname '{args.hostname}'")
        try:
            addrinfo = socket.getaddrinfo(
                args.hostname, args.port, socket.AF_INET, socket.SOCK_STREAM
            )
            host_ip = addrinfo[0][4][0]
            status.ok(f"Resolved to {host_ip}")
        except socket.gaierror as e:
            status.fail(f"DNS lookup failed: {e}")
            return

        if args.ip and host_ip != args.ip:
            status.write(f"\n  {'=' * 55}")
            status.write(f"  \u26A0  MISMATCH: --ip {args.ip} != hostname resolves to {host_ip}")
            status.write(f"  {'=' * 55}")
            status.write(f"  The hostname '{args.hostname}' resolves to {host_ip},")
            status.write(f"  but you provided --ip {args.ip}.")
            status.write(f"  Use --ip {host_ip} or just rely on --hostname.\n")
        resolved = host_ip
    else:
        status.step("DNS resolution")
        resolved = args.ip
        try:
            addrinfo = socket.getaddrinfo(
                args.ip, args.port, socket.AF_INET, socket.SOCK_STREAM
            )
            status.ok(f"Using IP {args.ip}")
        except socket.gaierror as e:
            status.fail(f"DNS lookup failed: {e}")
            return
        # Try reverse DNS to suggest hostname
        try:
            host, _, _ = socket.gethostbyaddr(args.ip)
            status.write(f"  (reverse DNS: {host})")
        except socket.herror:
            pass

    # 2. TCP port scan
    open_ports = []
    for port in COMMON_PORTS:
        status.tick(f"Testing port {port} ...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        try:
            result = sock.connect_ex((resolved, port))
            if result == 0:
                open_ports.append(port)
                status.write(f"  Port {port}: OPEN")
            else:
                status.write(f"  Port {port}: closed / no response")
        except OSError as e:
            status.write(f"  Port {port}: error ({e})")
        finally:
            sock.close()

    if open_ports:
        status.ok(f"Open port(s): {', '.join(map(str, open_ports))}")
    else:
        status.fail("No open ports found on the target device")
        print(file=sys.stderr)
        print("  \u2192 Troubleshooting steps:", file=sys.stderr)
        print(f"    1. Verify the device is powered on and connected to the network", file=sys.stderr)
        print(f"    2. Ping the device: ping {resolved}", file=sys.stderr)
        print(f"    3. Check if a firewall is blocking outgoing connections", file=sys.stderr)
        print(f"    4. Verify the device IP address is correct", file=sys.stderr)
        print(f"    5. Check if the device is on the same network/subnet", file=sys.stderr)
        print(f"    6. Try connecting from a different device on the same network", file=sys.stderr)
        return

    # 3. If SBXPC port is open, test SBXPC handshake
    if args.port in open_ports or 5005 in open_ports:
        test_port = args.port if args.port in open_ports else 5005
        status.step(f"SBXPC handshake test (port {test_port})")
        status.tick("Connecting ...")
        dev = AttendanceDevice(
            ip=args.ip or resolved,
            port=test_port,
            password=args.password,
            machine_id=args.machine,
            timeout=5,
            hostname=args.hostname,
            status=status,
        )
        try:
            dev.connect()
            dev.disconnect()
            status.ok("SBXPC connection successful")
        except (ConnectionError, OSError) as e:
            status.fail(f"SBXPC handshake failed: {e}")
    else:
        status.write("SBXPC port not open — device may use a different protocol or port")


def _upload_to_supabase(args, records: list[dict], status):
    """Upload records to Supabase if configured."""
    supabase_url = args.supabase_url or os.environ.get("SUPABASE_URL")
    supabase_key = args.supabase_key or os.environ.get("SUPABASE_KEY")
    if not supabase_url or not supabase_key:
        return
    try:
        from attendance_supabase import SupabaseConfig, upload_to_supabase
    except ImportError:
        status.write("Supabase module not found (attendance_supabase.py missing)")
        return
    cfg = SupabaseConfig(
        url=supabase_url, key=supabase_key,
        device_id=args.supabase_device_id or args.machine,
        device_name=args.supabase_device_name or "",
        device_ip=args.ip,
        department=args.supabase_department or "",
        place=args.supabase_place or "",
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

    log_handlers = [logging.StreamHandler()]
    if args.log_file:
        fh = logging.FileHandler(args.log_file)
        fh.setLevel(logging.DEBUG)
        log_handlers.append(fh)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="%(asctime)s %(levelname)s: %(message)s",
        handlers=log_handlers,
    )
    if args.log_file:
        logger.info("Session log written to %s", args.log_file)

    status = StatusIndicator(log_file=args.log_file)

    # ── Diagnose command (no connection needed) ─────────────────────
    if args.command == "diagnose":
        cmd_diagnose(args, status)
        return

    # ── Validate connection target ──────────────────────────────────
    if not args.ip and not args.hostname:
        print("ERROR: Provide --ip (IP address) or --hostname to identify the device.",
              file=sys.stderr)
        sys.exit(1)

    dev = AttendanceDevice(
        ip=args.ip or args.hostname,
        port=args.port,
        password=args.password,
        machine_id=args.machine,
        timeout=args.timeout,
        hostname=args.hostname or None,
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

        elif args.command == "clear-glogs":
            ok = dev.empty_attendance_logs()
            status.write("Attendance logs cleared" if ok else "Failed to clear attendance logs")

        elif args.command == "clear-slogs":
            ok = dev.empty_management_logs()
            status.write("Management logs cleared" if ok else "Failed to clear management logs")

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
