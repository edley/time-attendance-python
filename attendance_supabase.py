"""Supabase integration for attendance records.

Pushes attendance log data to a Supabase PostgreSQL database.
Supports both raw log storage and paired check-in/check-out records.

Environment variables:
  SUPABASE_URL     - Project URL (e.g. https://xyz.supabase.co)
  SUPABASE_KEY     - Service role or anon key
  SUPABASE_TABLE   - Table name (default: attendance_logs)

Schema (run in Supabase SQL editor):
  See schema.sql or the create_schema() function below.
"""

import json
import logging
import os
import datetime
from typing import Any

logger = logging.getLogger("attendance_supabase")

TABLE_RAW = "attendance_logs"
TABLE_PAIRED = "attendance_records"

SCHEMA_SQL = """
-- Raw attendance log entries (one row per clock event)
CREATE TABLE IF NOT EXISTS attendance_logs (
  id BIGSERIAL PRIMARY KEY,
  device_id TEXT NOT NULL,
  device_name TEXT,
  device_ip TEXT,
  enroll_number INTEGER NOT NULL,
  employee_name TEXT,
  record_timestamp TIMESTAMPTZ NOT NULL,
  record_date DATE NOT NULL,
  verify_mode INTEGER,
  verify_mode_name TEXT,
  attend_status INTEGER,
  attend_status_name TEXT,
  event_type TEXT,
  raw_json JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_logs_device ON attendance_logs(device_id);
CREATE INDEX IF NOT EXISTS idx_logs_date ON attendance_logs(record_date);
CREATE INDEX IF NOT EXISTS idx_logs_employee ON attendance_logs(enroll_number);
CREATE INDEX IF NOT EXISTS idx_logs_device_date ON attendance_logs(device_id, record_date);

-- Paired check-in / check-out records (one row per employee per day)
CREATE TABLE IF NOT EXISTS attendance_records (
  id BIGSERIAL PRIMARY KEY,
  device_id TEXT NOT NULL,
  device_name TEXT,
  device_ip TEXT,
  enroll_number INTEGER NOT NULL,
  employee_name TEXT,
  record_date DATE NOT NULL,
  check_in TIMESTAMPTZ,
  check_out TIMESTAMPTZ,
  verify_mode_in INTEGER,
  verify_mode_in_name TEXT,
  verify_mode_out INTEGER,
  verify_mode_out_name TEXT,
  raw_log_ids BIGINT[],
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(device_id, enroll_number, record_date)
);

CREATE INDEX IF NOT EXISTS idx_records_device ON attendance_records(device_id);
CREATE INDEX IF NOT EXISTS idx_records_date ON attendance_records(record_date);
CREATE INDEX IF NOT EXISTS idx_records_employee ON attendance_records(enroll_number);
"""


# ── Config ──────────────────────────────────────────────────────────────

class SupabaseConfig:
    def __init__(
        self,
        url: str | None = None,
        key: str | None = None,
        table_raw: str | None = None,
        table_paired: str | None = None,
        device_id: str | None = None,
        device_name: str | None = None,
        device_ip: str | None = None,
    ):
        self.url = url or os.environ.get("SUPABASE_URL", "")
        self.key = key or os.environ.get("SUPABASE_KEY", "")
        self.table_raw = table_raw or os.environ.get("SUPABASE_TABLE_RAW", TABLE_RAW)
        self.table_paired = table_paired or os.environ.get("SUPABASE_TABLE_PAIRED", TABLE_PAIRED)
        self.device_id = device_id or ""
        self.device_name = device_name or ""
        self.device_ip = device_ip or ""

    @property
    def enabled(self) -> bool:
        return bool(self.url and self.key)


# ── Attendance Record Helpers ──────────────────────────────────────────

def _infer_event_type(record: dict) -> str:
    """Determine event type from a record."""
    status = record.get("attend_status")
    status_name = record.get("attend_status_name", "")
    mode_name = record.get("verify_mode_name", "")

    if status == 4 or status_name == "Go In" or "(In)" in mode_name:
        return "check_in"
    if status == 5 or status_name == "Go Out" or "(Out)" in mode_name:
        return "check_out"
    if status == 0 or status_name == "Duty On":
        return "check_in"
    if status == 1 or status_name == "Duty Off":
        return "check_out"
    return "unknown"


def _parse_timestamp(record: dict) -> tuple[datetime.datetime | None, str | None]:
    """Extract datetime and date string from a record."""
    ts = record.get("timestamp")
    if ts:
        try:
            dt = datetime.datetime.fromisoformat(ts)
            return dt, dt.strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            pass

    try:
        dt = datetime.datetime(
            int(record["year"]), int(record["month"]), int(record["day"]),
            int(record.get("hour", 0)), int(record.get("minute", 0)),
            int(record.get("second", 0)),
        )
        return dt, dt.strftime("%Y-%m-%d")
    except (KeyError, ValueError, TypeError):
        return None, None


def _build_raw_record(rec: dict, cfg: SupabaseConfig) -> dict:
    """Convert an attendance log dict into a Supabase row."""
    dt, date_str = _parse_timestamp(rec)
    return {
        "device_id": cfg.device_id or cfg.device_ip or "unknown",
        "device_name": cfg.device_name or "",
        "device_ip": cfg.device_ip or "",
        "enroll_number": rec.get("enroll_number", 0),
        "employee_name": rec.get("name", ""),
        "record_timestamp": dt.isoformat() if dt else None,
        "record_date": date_str,
        "verify_mode": rec.get("verify_mode"),
        "verify_mode_name": rec.get("verify_mode_name", ""),
        "attend_status": rec.get("attend_status"),
        "attend_status_name": rec.get("attend_status_name", ""),
        "event_type": _infer_event_type(rec),
        "raw_json": json.dumps(rec, default=str),
    }


def _pair_records(records: list[dict], cfg: SupabaseConfig) -> list[dict]:
    """Group raw records by (device, employee, date) and pair check-in/out.

    Returns a list of paired record dicts ready for upsert into attendance_records.
    """
    groups: dict[tuple, dict] = {}

    for rec in records:
        dt, date_str = _parse_timestamp(rec)
        if not date_str:
            continue
        key = (cfg.device_id or cfg.device_ip or "unknown", rec.get("enroll_number"), date_str)

        if key not in groups:
            groups[key] = {
                "device_id": key[0],
                "device_name": cfg.device_name or "",
                "device_ip": cfg.device_ip or "",
                "enroll_number": rec.get("enroll_number", 0),
                "employee_name": rec.get("name", ""),
                "record_date": date_str,
                "check_in": None,
                "check_out": None,
                "verify_mode_in": None,
                "verify_mode_in_name": "",
                "verify_mode_out": None,
                "verify_mode_out_name": "",
                "raw_log_ids": [],
            }

        g = groups[key]
        event = _infer_event_type(rec)
        ts = dt.isoformat() if dt else None

        if event == "check_in":
            if g["check_in"] is None or (ts and ts < g["check_in"]):
                g["check_in"] = ts
                g["verify_mode_in"] = rec.get("verify_mode")
                g["verify_mode_in_name"] = rec.get("verify_mode_name", "")
        elif event == "check_out":
            if g["check_out"] is None or (ts and ts > g["check_out"]):
                g["check_out"] = ts
                g["verify_mode_out"] = rec.get("verify_mode")
                g["verify_mode_out_name"] = rec.get("verify_mode_name", "")
        else:
            if g["check_in"] is None:
                g["check_in"] = ts
                g["verify_mode_in"] = rec.get("verify_mode")
                g["verify_mode_in_name"] = rec.get("verify_mode_name", "")
            else:
                g["check_out"] = ts
                g["verify_mode_out"] = rec.get("verify_mode")
                g["verify_mode_out_name"] = rec.get("verify_mode_name", "")

    return list(groups.values())


# ── Supabase Client ────────────────────────────────────────────────────

class SupabaseUploader:
    """Uploads attendance data to Supabase."""

    def __init__(self, config: SupabaseConfig, status=None):
        self.config = config
        self._status = status
        self._client = None

    def _get_client(self):
        if self._client is not None:
            return self._client
        try:
            from supabase import create_client
        except ImportError:
            raise ImportError(
                "Supabase package required. Install with: pip install supabase"
            )
        self._client = create_client(self.config.url, self.config.key)
        return self._client

    def _log(self, msg: str):
        if self._status:
            self._status.write(msg)
        logger.info(msg)

    def upload_raw(self, records: list[dict]) -> int:
        """Insert raw log records into Supabase. Returns count inserted."""
        if not records:
            return 0
        client = self._get_client()
        rows = [_build_raw_record(r, self.config) for r in records]
        self._log(f"Uploading {len(rows)} raw log entries to {self.config.table_raw} ...")
        try:
            resp = client.table(self.config.table_raw).insert(rows).execute()
            inserted = len(resp.data) if resp.data else 0
            self._log(f"Uploaded {inserted} raw log entries to Supabase")
            return inserted
        except Exception as e:
            self._log(f"Supabase raw upload failed: {e}")
            return 0

    def upload_paired(self, records: list[dict]) -> int:
        """Pair records into check-in/check-out and upsert them."""
        if not records:
            return 0
        client = self._get_client()
        paired = _pair_records(records, self.config)
        self._log(f"Upserting {len(paired)} paired records to {self.config.table_paired} ...")
        count = 0
        for row in paired:
            try:
                resp = (
                    client.table(self.config.table_paired)
                    .upsert(row, on_conflict="device_id,enroll_number,record_date")
                    .execute()
                )
                if resp.data:
                    count += 1
            except Exception as e:
                self._log(f"Supabase upsert failed for {row.get('enroll_number')} "
                          f"on {row.get('record_date')}: {e}")
        self._log(f"Uploaded {count} paired records to Supabase")
        return count

    def verify_connection(self) -> bool:
        """Test that Supabase connection works."""
        try:
            client = self._get_client()
            resp = client.table(self.config.table_raw).select("id").limit(1).execute()
            self._log("Supabase connection OK")
            return True
        except Exception as e:
            self._log(f"Supabase connection failed: {e}")
            return False


# ── Convenience ────────────────────────────────────────────────────────

def upload_to_supabase(
    records: list[dict],
    config: SupabaseConfig,
    status=None,
    upload_raw: bool = True,
    upload_paired: bool = True,
) -> dict[str, int]:
    """Upload attendance records to Supabase.

    Returns dict with counts of uploaded records.
    """
    if not config.enabled:
        logger.warning("Supabase not configured (set SUPABASE_URL and SUPABASE_KEY)")
        return {"raw": 0, "paired": 0}

    uploader = SupabaseUploader(config, status=status)
    result = {}

    if upload_raw:
        result["raw"] = uploader.upload_raw(records)

    if upload_paired:
        result["paired"] = uploader.upload_paired(records)

    return result
