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
  department TEXT,
  place TEXT,
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
  department TEXT,
  place TEXT,
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
        department: str | None = None,
        place: str | None = None,
    ):
        self.url = url or os.environ.get("SUPABASE_URL", "")
        self.key = key or os.environ.get("SUPABASE_KEY", "")
        self.table_raw = table_raw or os.environ.get("SUPABASE_TABLE_RAW", TABLE_RAW)
        self.table_paired = table_paired or os.environ.get("SUPABASE_TABLE_PAIRED", TABLE_PAIRED)
        self.device_id = device_id or ""
        self.device_name = device_name or ""
        self.device_ip = device_ip or ""
        self.department = department or ""
        self.place = place or device_name or ""

    @property
    def enabled(self) -> bool:
        return bool(self.url and self.key)


# ── Attendance Record Helpers ──────────────────────────────────────────

def _infer_event_type(record: dict) -> str:
    """Determine event type from a record.

    Uses attend_status as primary signal, verify mode name as fallback:
      Check-in:  0 (Duty On), 2 (Overtime On), 4 (Go In)
      Check-out: 1 (Duty Off), 3 (Overtime Off), 5 (Go Out)

    Falls back to verifying mode name suffix (In)/(Out) or raw verify code.
    """
    status = record.get("attend_status")
    mode_name = record.get("verify_mode_name", "")
    verify = record.get("verify_mode")

    # Primary: attend_status codes
    if status in (0, 2, 4):
        return "check_in"
    if status in (1, 3, 5):
        return "check_out"

    # Fallback: verify mode name suffix
    if "(In)" in mode_name:
        return "check_in"
    if "(Out)" in mode_name:
        return "check_out"

    # Fallback: raw verify mode codes with implied direction
    if verify is not None:
        if verify in (51, 52, 53, 54, 55, 56, 57, 80, 81, 82, 83, 84):
            return "check_in"
        if verify in (101, 102, 103, 104, 105, 106, 107, 130, 131, 132, 133, 134):
            return "check_out"

    return "unknown"


def _parse_timestamp(record: dict) -> tuple[datetime.datetime | None, str | None]:
    """Extract datetime and date string from a record.

    Returns a timezone-aware datetime (UTC if no timezone in input)
    and a date string in YYYY-MM-DD format.
    """
    ts = record.get("timestamp")
    if ts:
        try:
            dt = datetime.datetime.fromisoformat(ts)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=datetime.timezone.utc)
            return dt, dt.strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            pass

    try:
        dt = datetime.datetime(
            int(record["year"]), int(record["month"]), int(record["day"]),
            int(record.get("hour", 0)), int(record.get("minute", 0)),
            int(record.get("second", 0)),
            tzinfo=datetime.timezone.utc,
        )
        return dt, dt.strftime("%Y-%m-%d")
    except (KeyError, ValueError, TypeError):
        return None, None


def _build_raw_record(rec: dict, cfg: SupabaseConfig) -> dict:
    """Convert an attendance log dict into a Supabase row.

    Department and place are taken from the record if available
    (e.g. enriched externally), falling back to the SupabaseConfig
    values (set via --supabase-department/--supabase-place or UI).
    """
    dt, date_str = _parse_timestamp(rec)
    return {
        "device_id": cfg.device_id or cfg.device_ip or "unknown",
        "device_name": cfg.device_name or "",
        "device_ip": cfg.device_ip or "",
        "enroll_number": rec.get("enroll_number", 0),
        "employee_name": rec.get("name", ""),
        "department": rec.get("department") or cfg.department or "",
        "place": rec.get("place") or cfg.place or "",
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
                "department": rec.get("department") or cfg.department or "",
                "place": rec.get("place") or cfg.place or "",
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
    """Uploads attendance data to Supabase via the PostgREST API."""

    def __init__(self, config: SupabaseConfig, status=None):
        self.config = config
        self._status = status
        # Strip /rest/v1 if user already included it in the URL
        raw_url = config.url.rstrip("/")
        if raw_url.endswith("/rest/v1"):
            raw_url = raw_url[:-8]
        self._base = raw_url + "/rest/v1"

    def _headers(self) -> dict:
        url = self.config.url.rstrip("/")
        if not url.startswith("http"):
            self._log(f"WARNING: Supabase URL should start with https:// (got: {url})")
        return {
            "apikey": self.config.key,
            "Authorization": f"Bearer {self.config.key}",
            "Content-Type": "application/json",
        }

    def _log(self, msg: str):
        if self._status:
            self._status.write(msg)
        logger.info(msg)

    def _request(self, method: str, table: str, json_body=None,
                 params: dict | None = None,
                 extra_headers: dict | None = None) -> tuple[int, list | dict]:
        """Make a PostgREST API request. Returns (status_code, parsed_json)."""
        import urllib.request
        import urllib.error
        import urllib.parse
        import ssl

        # Build SSL context with certifi if available (fixes macOS cert issues)
        ssl_ctx = None
        try:
            import certifi
            ssl_ctx = ssl.create_default_context(cafile=certifi.where())
        except ImportError:
            try:
                ssl_ctx = ssl.create_default_context()
            except Exception:
                ssl_ctx = ssl._create_unverified_context()

        url = f"{self._base}/{table}"
        if params:
            if isinstance(params, dict):
                items = list(params.items())
            else:
                items = list(params)
            qs = "&".join(f"{k}={urllib.parse.quote(str(v))}" for k, v in items)
            url += f"?{qs}"

        body = json.dumps(json_body).encode("utf-8") if json_body is not None else None
        headers = self._headers()
        if extra_headers:
            headers.update(extra_headers)
        req = urllib.request.Request(url, data=body, method=method, headers=headers)

        self._log(f"Supabase {method} {url}")
        logger.debug("Supabase %s %s", method, url)
        if body:
            logger.debug("Supabase request body: %s", body[:500])

        try:
            with urllib.request.urlopen(req, timeout=15, context=ssl_ctx) as resp:
                raw = resp.read()
                logger.debug("Supabase response HTTP %d: %s", resp.status, raw[:1000])
                decoded = json.loads(raw) if raw else []
                return resp.status, decoded
        except urllib.error.HTTPError as e:
            raw = e.read()
            detail = ""
            try:
                err_json = json.loads(raw)
                detail = err_json.get("message", str(e))
                logger.error("Supabase HTTP %d: full response=%s", e.code, raw[:1000])
            except Exception:
                detail = str(e)
                logger.error("Supabase HTTP %d: raw=%s", e.code, raw[:500])
            return e.code, {"error": detail}
        except urllib.error.URLError as e:
            logger.error("Supabase network error: %s", e.reason)
            return 0, {"error": f"Network error: {e.reason}"}

    def upload_raw(self, records: list[dict]) -> int:
        """Insert raw log records into Supabase. Returns count inserted."""
        if not records:
            return 0
        rows = [_build_raw_record(r, self.config) for r in records]
        self._log(f"Uploading {len(rows)} raw log entries to {self.config.table_raw} ...")
        status, data = self._request("POST", self.config.table_raw, rows,
                                     params={"columns": ",".join(rows[0].keys())}
                                     if rows else None)
        if 200 <= status < 300:
            self._log(f"Uploaded {len(rows)} raw log entries to Supabase")
            return len(rows)
        self._log(f"Supabase raw upload failed (HTTP {status})")
        # Log full URL so user can verify
        self._log(f"  URL: {self._base}/{self.config.table_raw}")
        return 0

    def upload_paired(self, records: list[dict]) -> int:
        """Pair records into check-in/check-out and upsert them."""
        if not records:
            return 0
        paired = _pair_records(records, self.config)
        self._log(f"Upserting {len(paired)} paired records to {self.config.table_paired} ...")
        if not paired:
            return 0
        params = {
            "on_conflict": "device_id,enroll_number,record_date",
        }
        status, data = self._request("POST", self.config.table_paired, paired,
                                     params=params,
                                     extra_headers={"Prefer": "resolution=merge-duplicates"})
        if 200 <= status < 300:
            self._log(f"Uploaded {len(paired)} paired records to Supabase")
            return len(paired)
        err = data.get("error", str(data)) if isinstance(data, dict) else str(data)
        self._log(f"Supabase paired upload failed (HTTP {status}): {err}")
        return 0

    def verify_connection(self) -> bool:
        """Test that Supabase connection works."""
        status, data = self._request("GET", self.config.table_raw,
                                     params={"select": "id", "limit": "1"})
        if 200 <= status < 300:
            self._log("Supabase connection OK")
            return True
        err = data.get("error", str(data)) if isinstance(data, dict) else str(data)
        self._log(f"Supabase connection failed (HTTP {status}): {err}")
        return False

    def query_table(self, table: str, device_id: str = "",
                    date_from: str = "", date_to: str = "",
                    limit: int = 500, offset: int = 0) -> tuple[int, list | dict]:
        """Query records from a Supabase table with optional filters.

        Returns (status_code, records_or_error_dict).
        """
        params = [("select", "*"), ("limit", str(limit)), ("offset", str(offset))]
        if device_id:
            params.append(("device_id", f"eq.{device_id}"))
        date_col = "record_date"
        if date_from:
            params.append((date_col, f"gte.{date_from}"))
        if date_to:
            params.append((date_col, f"lte.{date_to}"))
        return self._request("GET", table, params=params)

    def create_tables(self) -> bool:
        """Create the attendance_logs and attendance_records tables via
        the built-in pg_query RPC.  Requires a **service_role** key.

        On failure the full schema SQL is logged so the user can run it
        manually in the Supabase SQL editor (https://app.supabase.com).
        """
        import urllib.request
        import urllib.error
        import ssl as ssl_mod

        ssl_ctx = None
        try:
            import certifi
            ssl_ctx = ssl_mod.create_default_context(cafile=certifi.where())
        except ImportError:
            try:
                ssl_ctx = ssl_mod.create_default_context()
            except Exception:
                ssl_ctx = ssl_mod._create_unverified_context()

        url = f"{self._base}/rpc/pg_query"
        body = json.dumps({"query_text": SCHEMA_SQL}).encode("utf-8")
        headers = self._headers()
        req = urllib.request.Request(url, data=body, method="POST", headers=headers)

        try:
            with urllib.request.urlopen(req, timeout=30, context=ssl_ctx) as resp:
                self._log(f"Tables created (HTTP {resp.status})")
                return True
        except urllib.error.HTTPError as e:
            raw = e.read()
            detail = ""
            try:
                err_json = json.loads(raw)
                detail = err_json.get("message", str(e))
            except Exception:
                detail = str(e)
            self._log(
                f"Could not create tables via API (HTTP {e.code}: {detail}).\n"
                f"Run this SQL in your Supabase SQL Editor (app.supabase.com):")
            for line in SCHEMA_SQL.strip().split("\n"):
                self._log(line)
            return False
        except urllib.error.URLError as e:
            self._log(f"Network error creating tables: {e.reason}")
            return False


# ── Convenience ────────────────────────────────────────────────────────

def query_supabase(
    config: SupabaseConfig,
    table: str = "attendance_logs",
    device_id: str = "",
    date_from: str = "",
    date_to: str = "",
    limit: int = 500,
    offset: int = 0,
    status=None,
) -> tuple[int, list | dict]:
    """Query Supabase table with filters. Returns (status_code, records)."""
    uploader = SupabaseUploader(config, status=status)
    return uploader.query_table(table, device_id=device_id,
                                date_from=date_from, date_to=date_to,
                                limit=limit, offset=offset)


def query_active_employees(
    config: SupabaseConfig,
    device_id: str = "",
    record_date: str = "",
    status=None,
) -> tuple[int, list | dict]:
    """Query employees who checked in but haven't checked out yet."""
    uploader = SupabaseUploader(config, status=status)
    params = [
        ("select", "id,device_id,device_name,enroll_number,employee_name,record_date,check_in,verify_mode_in_name"),
        ("check_out", "is.null"),
        ("order", "check_in.asc"),
    ]
    if device_id:
        params.append(("device_id", f"eq.{device_id}"))
    if record_date:
        params.append(("record_date", f"eq.{record_date}"))
    status_code, data = uploader._request("GET", config.table_paired, params=params)
    return status_code, data


def create_schema_tables(
    config: SupabaseConfig,
    status=None,
) -> bool:
    """Create attendance_logs and attendance_records tables in Supabase."""
    uploader = SupabaseUploader(config, status=status)
    return uploader.create_tables()


def upload_to_supabase(
    records: list[dict],
    config: SupabaseConfig,
    status=None,
    upload_raw: bool = True,
    upload_paired: bool = True,
) -> dict[str, int]:
    """Upload attendance records to Supabase.

    Returns dict with upload counts (negative = error, 0 = ok/no-new, >0 = uploaded).
    """
    if not config.enabled:
        logger.warning("Supabase not configured (set SUPABASE_URL and SUPABASE_KEY)")
        return {"raw": -2, "paired": -2, "error": "not configured"}

    uploader = SupabaseUploader(config, status=status)
    result = {}

    if upload_raw:
        result["raw"] = uploader.upload_raw(records)

    if upload_paired:
        result["paired"] = uploader.upload_paired(records)

    return result
