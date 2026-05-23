-- ===============================================================
-- Supabase Schema for Attendance Device Utility
-- Run this in the Supabase SQL Editor (https://app.supabase.com)
-- ===============================================================

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
  created_at TIMESTAMPTZ DEFAULT NOW(),
  raw_log_ids BIGINT[] DEFAULT '{}',
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(device_id, enroll_number, record_date)
);

CREATE INDEX IF NOT EXISTS idx_records_device ON attendance_records(device_id);
CREATE INDEX IF NOT EXISTS idx_records_date ON attendance_records(record_date);
CREATE INDEX IF NOT EXISTS idx_records_employee ON attendance_records(enroll_number);

-- View: daily attendance summary
CREATE OR REPLACE VIEW attendance_daily AS
SELECT
  ar.device_id,
  ar.device_name AS place,
  ar.department,
  ar.enroll_number,
  ar.employee_name,
  ar.record_date,
  ar.check_in,
  ar.check_out,
  ar.verify_mode_in,
  ar.verify_mode_in_name,
  ar.verify_mode_out,
  ar.verify_mode_out_name,
  ar.verify_mode_in_name AS check_in_method,
  ar.verify_mode_out_name AS check_out_method,
  CASE
    WHEN ar.check_in IS NULL AND ar.check_out IS NULL THEN 'missing_both'
    WHEN ar.check_in IS NULL THEN 'missing_check_in'
    WHEN ar.check_out IS NULL THEN 'missing_check_out'
    ELSE 'complete'
  END AS attendance_status,
  EXTRACT(EPOCH FROM (ar.check_out - ar.check_in)) / 3600 AS hours_worked
FROM attendance_records ar
ORDER BY ar.record_date DESC, ar.enroll_number;

-- View: employees currently on premises (checked in, not checked out)
CREATE OR REPLACE VIEW attendance_active AS
SELECT *
FROM attendance_records
WHERE check_in IS NOT NULL AND check_out IS NULL
ORDER BY record_date DESC, check_in;
