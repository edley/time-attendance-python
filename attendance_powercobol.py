"""Local PowerCobol "table" — attendance data as a CSV file for PowerCOBOL.

Writes the attendance_daily record set as a comma-separated file with
CR/LF line endings so it can be read by a Fujitsu PowerCOBOL program
using ORGANIZATION IS LINE SEQUENTIAL.

The COBOL program should READ the first record (header line) and discard
it, then process the remaining data records.

Environment variables:
  POWERCOBOL_CSV_PATH  - Path to the CSV file
                        (default: ~/.attendance_powercobol.csv)

COBOL FD sketch (adjust field lengths to match your needs):
----------------------------------------------------------------
  FD  ATTENDANCE-FILE
      ORGANIZATION IS LINE SEQUENTIAL.
  01  ATTENDANCE-RECORD          PIC X(512).

  01  ATTENDANCE-DATA.
      05  AT-DEVICE-ID           PIC X(20).
      05  AT-PLACE               PIC X(30).
      05  AT-DEPARTMENT          PIC X(30).
      05  AT-ENROLL-NUMBER       PIC 9(6).
      05  AT-EMPLOYEE-NAME       PIC X(40).
      05  AT-RECORD-DATE         PIC X(10).
      05  AT-CHECK-IN            PIC X(25).
      05  AT-CHECK-OUT           PIC X(25).
      05  AT-VERIFY-MODE-IN      PIC 9(3).
      05  AT-VERIFY-MODE-IN-NAME PIC X(30).
      05  AT-VERIFY-MODE-OUT     PIC 9(3).
      05  AT-VERIFY-MODE-OUT-NAME PIC X(30).
      05  AT-CHECK-IN-METHOD     PIC X(30).
      05  AT-CHECK-OUT-METHOD    PIC X(30).
      05  AT-ATTENDANCE-STATUS   PIC X(20).
      05  AT-HOURS-WORKED         PIC 9(5)V99.
----------------------------------------------------------------
To use fixed-width instead of CSV, set POWERCOBOL_FIXEDWIDTH=1.
"""

import csv
import logging
import os

logger = logging.getLogger("attendance_powercobol")

CSV_PATH = os.path.expanduser(
    os.environ.get("POWERCOBOL_CSV_PATH", "~/.attendance_powercobol.csv")
)

USE_FIXEDWIDTH = os.environ.get("POWERCOBOL_FIXEDWIDTH", "") == "1"

FIELDNAMES = [
    "device_id",
    "place",
    "department",
    "enroll_number",
    "employee_name",
    "record_date",
    "check_in",
    "check_out",
    "verify_mode_in",
    "verify_mode_in_name",
    "verify_mode_out",
    "verify_mode_out_name",
    "check_in_method",
    "check_out_method",
    "attendance_status",
    "hours_worked",
]

# Fixed-width field sizes (used when POWERCOBOL_FIXEDWIDTH=1)
FIELD_WIDTHS = {
    "device_id": 20,
    "place": 30,
    "department": 30,
    "enroll_number": 6,
    "employee_name": 40,
    "record_date": 10,
    "check_in": 25,
    "check_out": 25,
    "verify_mode_in": 3,
    "verify_mode_in_name": 30,
    "verify_mode_out": 3,
    "verify_mode_out_name": 30,
    "check_in_method": 30,
    "check_out_method": 30,
    "attendance_status": 20,
    "hours_worked": 8,
}


class PowerCobolConfig:
    def __init__(self, csv_path: str | None = None):
        self.csv_path = csv_path or CSV_PATH


def _compute_status(check_in: str | None, check_out: str | None) -> str:
    if not check_in and not check_out:
        return "missing_both"
    if not check_in:
        return "missing_check_in"
    if not check_out:
        return "missing_check_out"
    return "complete"


def _compute_hours(check_in: str | None, check_out: str | None) -> float | None:
    if not check_in or not check_out:
        return None
    try:
        import datetime
        cin = datetime.datetime.fromisoformat(check_in)
        cout = datetime.datetime.fromisoformat(check_out)
        return round((cout - cin).total_seconds() / 3600, 4)
    except (ValueError, TypeError):
        return None


def _build_rows(paired_records: list[dict]) -> list[dict]:
    """Convert paired records into dicts matching the fieldnames."""
    rows = []
    for rec in paired_records:
        check_in = rec.get("check_in")
        check_out = rec.get("check_out")
        vin = (rec.get("verify_mode_in_name") or "")
        vout = (rec.get("verify_mode_out_name") or "")
        hrs = _compute_hours(check_in, check_out)
        rows.append({
            "device_id": rec.get("device_id", ""),
            "place": rec.get("place", "") or rec.get("device_name", ""),
            "department": rec.get("department", ""),
            "enroll_number": rec.get("enroll_number", 0),
            "employee_name": rec.get("employee_name", ""),
            "record_date": rec.get("record_date", ""),
            "check_in": check_in or "",
            "check_out": check_out or "",
            "verify_mode_in": rec.get("verify_mode_in") or "",
            "verify_mode_in_name": vin,
            "verify_mode_out": rec.get("verify_mode_out") or "",
            "verify_mode_out_name": vout,
            "check_in_method": vin,
            "check_out_method": vout,
            "attendance_status": _compute_status(check_in, check_out),
            "hours_worked": f"{hrs:.4f}" if hrs is not None else "",
        })
    return rows


def _merge_records(existing: list[dict], new_rows: list[dict]) -> list[dict]:
    """Merge new rows into existing, keyed by (device_id, enroll_number, record_date).
    New rows win on conflict."""
    index = {}
    for row in existing:
        key = (row.get("device_id", ""), str(row.get("enroll_number", "")),
               row.get("record_date", ""))
        index[key] = row
    for row in new_rows:
        key = (row["device_id"], str(row["enroll_number"]), row["record_date"])
        index[key] = row
    return list(index.values())


def _write_csv(path: str, rows: list[dict]):
    """Write rows as CSV with CR/LF line endings (LINE SEQUENTIAL format)."""
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, lineterminator="\r\n")
        writer.writeheader()
        writer.writerows(rows)


def _fmt_fixed(value: str, width: int) -> str:
    """Format a value as fixed-width, left-justified."""
    s = str(value)
    return s[:width].ljust(width)


def _write_fixedwidth(path: str, rows: list[dict]):
    """Write rows as fixed-width records with CR/LF line endings."""
    field_order = FIELDNAMES
    widths = FIELD_WIDTHS
    with open(path, "w", newline="") as f:
        # Header record
        header = "".join(_fmt_fixed(h, widths[h]) for h in field_order)
        f.write(header + "\r\n")
        for row in rows:
            line = "".join(
                _fmt_fixed(str(row.get(h, "")), widths[h])
                for h in field_order
            )
            f.write(line + "\r\n")


def update_from_raw(
    records: list[dict],
    device_id: str = "",
    device_name: str = "",
    device_ip: str = "",
    department: str = "",
    place: str = "",
    cfg: PowerCobolConfig | None = None,
) -> int:
    """Pair raw attendance records and write to the PowerCobol file."""
    if not records:
        return 0
    from attendance_supabase import _pair_records, SupabaseConfig
    scfg = SupabaseConfig(
        device_id=device_id, device_name=device_name,
        device_ip=device_ip, department=department, place=place,
    )
    paired = _pair_records(records, scfg)
    return update_records(paired, cfg)


def update_records(
    paired_records: list[dict],
    cfg: PowerCobolConfig | None = None,
) -> int:
    """Write pre-paired records into the PowerCobol file (CSV or fixed-width).

    Merges with any existing records to avoid duplicates, keyed by
    (device_id, enroll_number, record_date).

    Returns the number of *new* records provided (not total in file).
    """
    if not paired_records:
        return 0
    cfg = cfg or PowerCobolConfig()
    rows = _build_rows(paired_records)
    if not rows:
        return 0

    existing = []
    if os.path.exists(cfg.csv_path):
        try:
            if USE_FIXEDWIDTH:
                with open(cfg.csv_path) as f:
                    lines = f.read().splitlines()
                if lines:
                    lines = lines[1:]  # skip header
                    for line in lines:
                        pos = 0
                        row = {}
                        for name in FIELDNAMES:
                            w = FIELD_WIDTHS[name]
                            row[name] = line[pos:pos + w].rstrip()
                            pos += w
                        existing.append(row)
            else:
                with open(cfg.csv_path, newline="") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        existing.append(row)
        except Exception:
            pass

    merged = _merge_records(existing, rows)

    if USE_FIXEDWIDTH:
        _write_fixedwidth(cfg.csv_path, merged)
    else:
        _write_csv(cfg.csv_path, merged)

    logger.info("PowerCobol: %d records written to %s", len(merged), cfg.csv_path)
    return len(rows)


def query_records(
    cfg: PowerCobolConfig | None = None,
    device_id: str = "",
    date_from: str = "",
    date_to: str = "",
    limit: int = 500,
    offset: int = 0,
) -> list[dict]:
    """Query records from the PowerCobol file."""
    cfg = cfg or PowerCobolConfig()
    if not os.path.exists(cfg.csv_path):
        return []

    all_rows = []
    try:
        if USE_FIXEDWIDTH:
            with open(cfg.csv_path) as f:
                lines = f.read().splitlines()
            if lines:
                lines = lines[1:]
                for line in lines:
                    pos = 0
                    row = {}
                    for name in FIELDNAMES:
                        w = FIELD_WIDTHS[name]
                        row[name] = line[pos:pos + w].rstrip()
                        pos += w
                    all_rows.append(row)
        else:
            with open(cfg.csv_path, newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    all_rows.append(row)
    except Exception:
        return []

    filtered = all_rows
    if device_id:
        filtered = [r for r in filtered if r.get("device_id") == device_id]
    if date_from:
        filtered = [r for r in filtered if r.get("record_date", "") >= date_from]
    if date_to:
        filtered = [r for r in filtered if r.get("record_date", "") <= date_to]

    return filtered[offset:offset + limit]
