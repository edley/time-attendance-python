#!/usr/bin/env python3
"""Attendance Device Web UI — Flask + SSE frontend for attendance_device.py"""

import json
import os
import queue
import sys
import threading
import time
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from flask import Flask, request, jsonify, Response, render_template_string
except ImportError:
    print("Flask is required. Install with: pip install flask")
    sys.exit(1)

from attendance_device import AttendanceDevice, StatusIndicator

PROFILES_PATH = os.path.expanduser("~/.attendance_devices.json")
SUPABASE_CONFIG_PATH = os.path.expanduser("~/.attendance_supabase.json")
TASKS: dict[str, dict] = {}
_LOG_FILE: str | None = None


# ── Queue-based StatusIndicator for SSE streaming ───────────────────────

class QueueStatus(StatusIndicator):
    def __init__(self, task_id: str, log_file: str | None = None):
        super().__init__(log_file=log_file)
        self._task_id = task_id
        self._queue: queue.Queue = queue.Queue()
        self._global_start = time.time()
        # Register queue so SSE endpoint can find it
        if task_id in TASKS:
            TASKS[task_id]["queue"] = self._queue

    def _send(self, event: str, data: dict):
        self._queue.put({"event": event, "data": data})

    def step(self, msg: str):
        super().step(msg)
        self._send("step", {"msg": msg, "elapsed": self._elapsed(self._global_start)})

    def tick(self, msg: str | None = None):
        if msg:
            self._current = msg
        self._send("tick", {"msg": self._current, "elapsed": self._elapsed(self._global_start)})

    def ok(self, msg: str | None = None):
        label = msg if msg else self._current
        super().ok(label)
        self._send("ok", {"msg": label, "elapsed": self._elapsed(self._global_start)})

    def fail(self, msg: str | None = None):
        label = msg if msg else self._current
        super().fail(label)
        self._send("fail", {"msg": label, "elapsed": self._elapsed(self._global_start)})

    def write(self, msg: str):
        self._send("info", {"msg": msg, "elapsed": self._elapsed(self._global_start)})

    def waiting(self, msg: str):
        self._send("step", {"msg": f"\u23F3 {msg}", "elapsed": self._elapsed(self._global_start)})

    def startup(self, msg: str):
        self._send("info", {"msg": msg, "elapsed": self._elapsed(self._global_start)})

    def result(self, data: list | None):
        self._send("result", {"count": len(data) if data else 0, "data": data})

    def iter_events(self, timeout=0.5):
        while True:
            try:
                yield self._queue.get(timeout=timeout)
            except queue.Empty:
                if not TASKS.get(self._task_id, {}).get("running", False):
                    break
                yield {"event": "heartbeat", "data": {}}


# ── Device Profile I/O ──────────────────────────────────────────────────

def load_profiles() -> dict:
    if os.path.exists(PROFILES_PATH):
        try:
            with open(PROFILES_PATH) as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_profiles(profiles: dict):
    with open(PROFILES_PATH, "w") as f:
        json.dump(profiles, f, indent=2)


def load_supabase_config() -> dict:
    if os.path.exists(SUPABASE_CONFIG_PATH):
        try:
            with open(SUPABASE_CONFIG_PATH) as f:
                return json.load(f)
        except Exception:
            pass
    return {"url": "", "key": "", "device_id": "", "device_name": "", "enabled": False}


def save_supabase_config(cfg: dict):
    with open(SUPABASE_CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)


# ── Flask App ───────────────────────────────────────────────────────────

app = Flask(__name__)

HTML_PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Attendance Device Utility</title>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --bg: #0f172a;
    --surface: #1e293b;
    --surface2: #334155;
    --border: #475569;
    --text: #f1f5f9;
    --text2: #94a3b8;
    --accent: #3b82f6;
    --accent-hover: #2563eb;
    --success: #22c55e;
    --error: #ef4444;
    --warning: #eab308;
    --radius: 8px;
    --font: 'Segoe UI', system-ui, -apple-system, sans-serif;
  }

  html { font-size: 16px; }
  body {
    font-family: var(--font);
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }

  /* ── Header ─────────────────────────────────────────── */
  header {
    background: linear-gradient(135deg, #1e40af, #3b82f6);
    padding: 1rem 1.5rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 0.5rem;
  }
  header h1 { font-size: 1.25rem; font-weight: 700; }
  header .subtitle { font-size: 0.8rem; opacity: 0.8; }

  /* ── Layout ─────────────────────────────────────────── */
  .container { max-width: 960px; margin: 0 auto; padding: 1.25rem; width: 100%; flex: 1; }

  .card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.25rem;
    margin-bottom: 1rem;
  }
  .card-title {
    font-size: 0.85rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--text2);
    margin-bottom: 1rem;
  }

  .row { display: flex; flex-wrap: wrap; gap: 0.75rem; align-items: center; }
  .row.gap-1 { gap: 0.5rem; }
  .fill { flex: 1; min-width: 0; }

  /* ── Form elements ──────────────────────────────────── */
  label {
    display: block;
    font-size: 0.8rem;
    font-weight: 500;
    color: var(--text2);
    margin-bottom: 0.25rem;
  }

  input, select {
    width: 100%;
    padding: 0.6rem 0.75rem;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    color: var(--text);
    font-size: 0.9rem;
    font-family: var(--font);
    transition: border-color 0.15s;
  }
  input:focus, select:focus { outline: none; border-color: var(--accent); }
  select { cursor: pointer; }

  .field { margin-bottom: 0.75rem; }
  .field-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.75rem;
  }

  /* ── Buttons ────────────────────────────────────────── */
  .btn {
    display: inline-flex; align-items: center; gap: 0.4rem;
    padding: 0.55rem 1rem;
    font-size: 0.85rem; font-weight: 600;
    border: none; border-radius: var(--radius);
    cursor: pointer;
    transition: background 0.15s, opacity 0.15s;
    white-space: nowrap;
    font-family: var(--font);
  }
  .btn:disabled { opacity: 0.5; cursor: not-allowed; }

  .btn-primary { background: var(--accent); color: #fff; }
  .btn-primary:hover:not(:disabled) { background: var(--accent-hover); }

  .btn-success { background: var(--success); color: #fff; }
  .btn-success:hover:not(:disabled) { background: #16a34a; }

  .btn-danger { background: var(--error); color: #fff; }
  .btn-danger:hover:not(:disabled) { background: #dc2626; }

  .btn-ghost { background: transparent; color: var(--text2); border: 1px solid var(--border); }
  .btn-ghost:hover:not(:disabled) { background: var(--surface2); }

  .btn-sm { padding: 0.35rem 0.7rem; font-size: 0.78rem; }

  /* ── Dropdown + device actions ──────────────────────── */
  .device-select-row { display: flex; gap: 0.5rem; align-items: center; }
  .device-select-row select { flex: 1; }

  /* ── Progress / Log ─────────────────────────────────── */
  #log {
    background: #0a0f1a;
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 0.75rem;
    height: 260px;
    overflow-y: auto;
    font-family: 'Cascadia Code', 'Fira Code', 'JetBrains Mono', 'Consolas', monospace;
    font-size: 0.82rem;
    line-height: 1.5;
    white-space: pre-wrap;
    word-break: break-all;
  }
  #log .step { color: var(--text2); }
  #log .ok   { color: var(--success); }
  #log .err  { color: var(--error); }
  #log .info { color: var(--accent); }
  #log .timer { color: #52525b; }
  #log .tick { color: var(--text); }

  .progress-bar-container {
    background: var(--bg);
    border-radius: 999px;
    height: 6px;
    overflow: hidden;
    margin-top: 0.5rem;
  }
  .progress-bar-fill {
    height: 100%;
    width: 0%;
    background: linear-gradient(90deg, var(--accent), var(--success));
    transition: width 0.3s;
    border-radius: 999px;
  }

  .status-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    margin-bottom: 0.5rem;
    flex-wrap: wrap;
  }
  .status-row .current-op {
    font-size: 0.85rem;
    color: var(--text2);
  }
  .status-row .elapsed {
    font-size: 0.8rem;
    color: var(--text2);
    font-variant-numeric: tabular-nums;
  }

  /* ── Results table ──────────────────────────────────── */
  .result-table-wrap {
    overflow-x: auto;
    margin-top: 0.75rem;
    max-height: 320px;
    overflow-y: auto;
  }
  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.8rem;
  }
  th, td {
    padding: 0.4rem 0.6rem;
    text-align: left;
    border-bottom: 1px solid var(--border);
    white-space: nowrap;
  }
  th {
    background: var(--surface2);
    color: var(--text2);
    font-weight: 600;
    position: sticky;
    top: 0;
  }
  td { color: var(--text); }
  tr:hover td { background: var(--surface2); }

  .badge {
    display: inline-block;
    padding: 0.15rem 0.45rem;
    border-radius: 999px;
    font-size: 0.7rem;
    font-weight: 600;
  }
  .badge-success { background: #166534; color: #86efac; }
  .badge-count { background: var(--surface2); color: var(--text2); }

  .no-data { color: var(--text2); text-align: center; padding: 2rem; }

  /* ── Responsive ─────────────────────────────────────── */
  @media (max-width: 640px) {
    .container { padding: 0.75rem; }
    .card { padding: 0.9rem; }
    .field-grid { grid-template-columns: 1fr; }
    header h1 { font-size: 1rem; }
    #log { height: 180px; font-size: 0.75rem; }
    .btn { font-size: 0.8rem; padding: 0.45rem 0.8rem; }
    table { font-size: 0.72rem; }
    th, td { padding: 0.3rem 0.4rem; }
  }

  @media (min-width: 768px) {
    .field-grid { grid-template-columns: 1fr 1fr 1fr; }
  }

  /* ── Utility ────────────────────────────────────────── */
  .mt-1 { margin-top: 0.5rem; }
  .mb-1 { margin-bottom: 0.5rem; }
  .flex { display: flex; }
  .flex-wrap { flex-wrap: wrap; }
  .gap-1 { gap: 0.5rem; }
  .hide { display: none !important; }

  /* Scrollbar styling */
  ::-webkit-scrollbar { width: 6px; height: 6px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: var(--surface2); border-radius: 3px; }
</style>
</head>
<body>

<header>
  <div>
    <h1>Attendance Device Utility</h1>
    <div class="subtitle">SBXPC Protocol – Smackbio / Anviz</div>
  </div>
  <div class="row gap-1">
    <span id="headerTimer" style="font-size:0.85rem;font-variant-numeric:tabular-nums;opacity:0.7">00:00</span>
    <button class="btn btn-ghost btn-sm" onclick="location.reload()">⟳ Refresh</button>
  </div>
</header>

<div class="container">

  <!-- Saved Devices -->
  <div class="card">
    <div class="card-title">Saved Devices</div>
    <div class="device-select-row">
      <select id="deviceSelect" onchange="onSelectDevice()">
        <option value="">— Select a device —</option>
      </select>
      <button class="btn btn-danger btn-sm" id="deleteBtn" disabled onclick="deleteDevice()">✕ Delete</button>
    </div>
  </div>

  <!-- Device Details -->
  <div class="card">
    <div class="card-title">Device Details</div>
    <div class="field-grid">
      <div class="field">
        <label for="name">Device Name</label>
        <input id="name" placeholder="e.g. Main Office" value="Main Office">
      </div>
      <div class="field">
        <label for="hostname">Hostname (optional)</label>
        <input id="hostname" placeholder="e.g. device01.local">
      </div>
      <div class="field">
        <label for="ip">IP Address</label>
        <input id="ip" placeholder="192.168.1.224" value="192.168.1.224">
      </div>
      <div class="field">
        <label for="port">Port</label>
        <input id="port" type="number" value="5005">
      </div>
      <div class="field">
        <label for="password">Password</label>
        <input id="password" type="number" value="0">
      </div>
      <div class="field">
        <label for="machineId">Device ID (Machine #)</label>
        <input id="machineId" type="number" value="1">
      </div>
    </div>
    <div class="row mt-1">
      <button class="btn btn-primary" onclick="saveAsNew()">＋ Save As New</button>
      <button class="btn btn-ghost" id="saveBtn" disabled onclick="saveDevice()">💾 Save</button>
    </div>
  </div>

  <!-- Operation -->
  <div class="card">
    <div class="card-title">Operation</div>
    <div class="row">
      <div class="fill">
        <select id="operation">
          <option value="read-glogs">📋 Read Attendance Logs</option>
          <option value="read-slogs">📋 Read Management Logs</option>
          <option value="users">👤 List Enrolled Users</option>
          <option value="info">ℹ️ Device Information</option>
          <option value="time">🕐 Device Date/Time</option>
        </select>
      </div>
      <button class="btn btn-success" id="executeBtn" onclick="execute()">▶ Execute</button>
      <button class="btn btn-ghost" id="exportBtn" disabled onclick="exportCSV()">↓ Export CSV</button>
    </div>
  </div>

  <!-- Supabase Integration -->
  <div class="card">
    <div class="card-title">Supabase Integration</div>
    <div class="row mb-1">
      <label class="flex gap-1" style="align-items:center;cursor:pointer">
        <input type="checkbox" id="supabaseEnabled">
        <span style="font-size:0.85rem;font-weight:600">Upload records automatically</span>
      </label>
    </div>
    <div class="field-grid">
      <div class="field">
        <label for="supabaseUrl">Project URL</label>
        <input id="supabaseUrl" placeholder="https://xyz.supabase.co">
      </div>
      <div class="field">
        <label for="supabaseKey">API Key</label>
        <div style="display:flex;gap:4px">
          <input id="supabaseKey" type="text" placeholder="service_role or anon key" style="flex:1">
          <button type="button" class="btn btn-ghost" style="font-size:0.75rem;padding:2px 8px" onclick="toggleSupabaseKey()" id="supabaseKeyToggle">Hide</button>
        </div>
      </div>
      <div class="field">
        <label for="supabaseDeviceId">Device ID</label>
        <input id="supabaseDeviceId" placeholder="e.g. device-01">
      </div>
      <div class="field">
        <label for="supabaseDeviceName">Device Name</label>
        <input id="supabaseDeviceName" placeholder="e.g. Main Office">
      </div>
    </div>
    <div class="row mt-1">
      <button class="btn btn-ghost" onclick="saveSupabaseConfig()">Save Settings</button>
    </div>
  </div>

  <!-- Progress & Log -->
  <div class="card">
    <div class="card-title">Progress</div>
    <div class="status-row">
      <span class="current-op" id="currentOp">Ready</span>
      <span class="elapsed" id="elapsedTimer">00:00</span>
    </div>
    <div class="progress-bar-container">
      <div class="progress-bar-fill" id="progressFill"></div>
    </div>
    <div id="log" class="mt-1"><span class="step">Ready — configure device and press Execute</span></div>
  </div>

  <!-- Results -->
  <div class="card hide" id="resultsCard">
    <div class="card-title">
      Results
      <span id="resultCount" class="badge badge-count" style="margin-left:0.5rem">0</span>
    </div>
    <div class="result-table-wrap" id="resultTableWrap">
      <table id="resultTable"><thead></thead><tbody></tbody></table>
    </div>
  </div>

</div>

<script>
// ── State ──────────────────────────────────────────────────────────────
let currentTaskId = null;
let lastRecords = null;
let eventSource = null;
let dirty = false;
const fields = ["name","ip","port","password","machineId"];
fields.forEach(f => {
  document.getElementById(f).addEventListener("input", () => { dirty = true; });
});

// ── Device Profiles ────────────────────────────────────────────────────
async function loadDevices() {
  const r = await fetch("/api/devices");
  const devices = await r.json();
  const sel = document.getElementById("deviceSelect");
  sel.innerHTML = '<option value="">— Select a device —</option>';
  Object.keys(devices).sort().forEach(name => {
    const opt = document.createElement("option");
    opt.value = name; opt.textContent = name;
    sel.appendChild(opt);
  });
}

async function saveAsNew() {
  const name = document.getElementById("name").value.trim();
  if (!name) { alert("Device Name is required."); return; }
  const data = getFields();
  const r = await fetch("/api/devices", {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({name, ...data}),
  });
  if (!r.ok) { const e = await r.json(); alert(e.error); return; }
  dirty = false;
  await loadDevices();
  document.getElementById("deviceSelect").value = name;
  document.getElementById("saveBtn").disabled = false;
}

async function saveDevice() {
  const name = document.getElementById("deviceSelect").value;
  if (!name) return;
  const data = getFields();
  await fetch("/api/devices", {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({name, ...data}),
  });
  dirty = false;
  await loadDevices();
  document.getElementById("deviceSelect").value = name;
}

async function deleteDevice() {
  const name = document.getElementById("deviceSelect").value;
  if (!name || !confirm(`Delete "${name}"?`)) return;
  await fetch(`/api/devices/${encodeURIComponent(name)}`, { method: "DELETE" });
  await loadDevices();
  document.getElementById("saveBtn").disabled = true;
  dirty = false;
}

function onSelectDevice() {
  const name = document.getElementById("deviceSelect").value;
  document.getElementById("saveBtn").disabled = !name;
  document.getElementById("deleteBtn").disabled = !name;
  if (!name) return;
  fetch("/api/devices").then(r => r.json()).then(devices => {
    const d = devices[name];
    if (!d) return;
    document.getElementById("name").value = name;
    document.getElementById("ip").value = d.ip || "";
    document.getElementById("port").value = d.port || 5005;
    document.getElementById("password").value = d.password ?? 0;
    document.getElementById("machineId").value = d.machine_id || 1;
    dirty = false;
  });
}

function getFields() {
  return {
    ip: document.getElementById("ip").value.trim(),
    port: parseInt(document.getElementById("port").value) || 5005,
    password: parseInt(document.getElementById("password").value) || 0,
    machine_id: parseInt(document.getElementById("machineId").value) || 1,
  };
}

// ── Execution ──────────────────────────────────────────────────────────
function execute() {
  // Save if dirty
  const selName = document.getElementById("deviceSelect").value;
  if (dirty && selName) {
    if (!confirm("Device details changed. Save before running?")) return;
    saveDevice();
  }

  const ip = document.getElementById("ip").value.trim();
  const hostname = document.getElementById("hostname").value.trim();
  const port = parseInt(document.getElementById("port").value);
  const password = parseInt(document.getElementById("password").value);
  const machine = parseInt(document.getElementById("machineId").value);
  const op = document.getElementById("operation").value;

  if (!ip && !hostname) { alert("IP Address or Hostname is required."); return; }
  if (isNaN(port)) { alert("Port must be a number."); return; }

  // Reset UI
  lastRecords = null;
  document.getElementById("exportBtn").disabled = true;
  document.getElementById("executeBtn").disabled = true;
  document.getElementById("executeBtn").textContent = "⏳ Running ...";
  document.getElementById("log").innerHTML = "";
  document.getElementById("progressFill").style.width = "0%";
  document.getElementById("resultsCard").classList.add("hide");
  setCurrentOp("Starting ...");

  // SSE
  if (eventSource) eventSource.close();
  const taskId = crypto.randomUUID();
  currentTaskId = taskId;

  eventSource = new EventSource(`/api/progress/${taskId}`);
  eventSource.addEventListener("step", e => handleSSE("step", e));
  eventSource.addEventListener("tick", e => handleSSE("tick", e));
  eventSource.addEventListener("ok", e => handleSSE("ok", e));
  eventSource.addEventListener("fail", e => handleSSE("fail", e));
  eventSource.addEventListener("info", e => handleSSE("info", e));
  eventSource.addEventListener("result", e => handleSSE("result", e));
  eventSource.addEventListener("error", e => {
    if (e.eventPhase === EventSource.CLOSED) done();
  });

  // Collect Supabase config
  const supabase = {
    enabled: document.getElementById("supabaseEnabled").checked,
    url: document.getElementById("supabaseUrl").value.trim(),
    key: document.getElementById("supabaseKey").value.trim(),
    device_id: document.getElementById("supabaseDeviceId").value.trim(),
    device_name: document.getElementById("supabaseDeviceName").value.trim(),
  };

  // POST execute
  fetch("/api/execute", {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({task_id: taskId, ip, hostname, port, password, machine, command: op, supabase}),
  });
}

function handleSSE(type, e) {
  const d = JSON.parse(e.data);
  const log = document.getElementById("log");

  if (type === "tick" || type === "heartbeat") {
    const bar = document.getElementById("progressFill");
    const w = Math.min(parseFloat(bar.style.width || "0") + 0.5, 85);
    bar.style.width = w + "%";
    setCurrentOp(d.msg || "");
    setElapsed(d.elapsed || "");
  }

  if (type === "step") {
    log.innerHTML += `<div class="step">  ${esc(d.msg)} ...</div>`;
    setCurrentOp(d.msg);
    setElapsed(d.elapsed);
  }
  if (type === "ok") {
    log.innerHTML += `<div class="ok">✓ ${esc(d.msg)}  <span class="timer">[${d.elapsed || ""}]</span></div>`;
    setElapsed(d.elapsed);
  }
  if (type === "fail") {
    log.innerHTML += `<div class="err">✗ ${esc(d.msg)}  <span class="timer">[${d.elapsed || ""}]</span></div>`;
  }
  if (type === "info") {
    log.innerHTML += `<div class="info">${esc(d.msg)}  <span class="timer">[${d.elapsed || ""}]</span></div>`;
  }
  if (type === "result") {
    document.getElementById("progressFill").style.width = "100%";
    document.getElementById("resultCount").textContent = d.count;
    if (d.data && d.data.length > 0) {
      lastRecords = d.data;
      document.getElementById("exportBtn").disabled = false;
      renderTable(d.data);
    }
    done();
  }

  log.scrollTop = log.scrollHeight;
}

function done() {
  document.getElementById("executeBtn").disabled = false;
  document.getElementById("executeBtn").textContent = "▶ Execute";
  if (eventSource) { eventSource.close(); eventSource = null; }
  setCurrentOp("Complete");
}

function setCurrentOp(msg) {
  document.getElementById("currentOp").textContent = msg;
}
function setElapsed(el) {
  document.getElementById("elapsedTimer").textContent = el;
  document.getElementById("headerTimer").textContent = el;
}

function esc(s) {
  const d = document.createElement("div");
  d.textContent = s;
  return d.innerHTML;
}

// ── Table ──────────────────────────────────────────────────────────────
function renderTable(data) {
  if (!data || data.length === 0) return;
  const keys = Object.keys(data[0]);
  const thead = document.querySelector("#resultTable thead");
  const tbody = document.querySelector("#resultTable tbody");
  thead.innerHTML = "<tr>" + keys.map(k => `<th>${esc(k)}</th>`).join("") + "</tr>";
  tbody.innerHTML = data.slice(0, 500).map(row =>
    "<tr>" + keys.map(k => `<td>${esc(String(row[k] ?? ""))}</td>`).join("") + "</tr>"
  ).join("");
  document.getElementById("resultsCard").classList.remove("hide");
}

// ── Supabase Config ────────────────────────────────────────────────────
async function loadSupabaseConfig() {
  const r = await fetch("/api/supabase-config");
  const cfg = await r.json();
  document.getElementById("supabaseEnabled").checked = cfg.enabled || false;
  document.getElementById("supabaseUrl").value = cfg.url || "";
  document.getElementById("supabaseKey").value = cfg.key || "";
  document.getElementById("supabaseDeviceId").value = cfg.device_id || "";
  document.getElementById("supabaseDeviceName").value = cfg.device_name || "";
}

async function saveSupabaseConfig() {
  const cfg = {
    enabled: document.getElementById("supabaseEnabled").checked,
    url: document.getElementById("supabaseUrl").value.trim(),
    key: document.getElementById("supabaseKey").value.trim(),
    device_id: document.getElementById("supabaseDeviceId").value.trim(),
    device_name: document.getElementById("supabaseDeviceName").value.trim(),
  };
  const r = await fetch("/api/supabase-config", {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify(cfg),
  });
  if (r.ok) alert("Supabase settings saved."); else alert("Failed to save Supabase settings.");
}

function toggleSupabaseKey() {
  const inp = document.getElementById("supabaseKey");
  const btn = document.getElementById("supabaseKeyToggle");
  if (inp.type === "password") {
    inp.type = "text";
    btn.textContent = "Hide";
  } else {
    inp.type = "password";
    btn.textContent = "Show";
  }
}

// ── Export CSV ─────────────────────────────────────────────────────────
async function exportCSV() {
  if (!lastRecords || lastRecords.length === 0) { alert("No data to export."); return; }
  const r = await fetch("/api/export-csv", {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({data: lastRecords}),
  });
  const blob = await r.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `attendance_export_${new Date().toISOString().slice(0,19).replace(/[T:]/g,"-")}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}

// ── Init ───────────────────────────────────────────────────────────────
loadDevices();
loadSupabaseConfig();
</script>
</body>
</html>"""


# ── Routes ──────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template_string(HTML_PAGE)


@app.route("/api/devices", methods=["GET", "POST"])
def api_devices():
    profiles = load_profiles()
    if request.method == "GET":
        return jsonify(profiles)

    body = request.get_json()
    name = body.get("name", "").strip()
    if not name:
        return jsonify({"error": "Device name required"}), 400
    profiles[name] = {
        "ip": body.get("ip", ""),
        "port": int(body.get("port", 5005)),
        "password": int(body.get("password", 0)),
        "machine_id": int(body.get("machine_id", 1)),
    }
    save_profiles(profiles)
    return jsonify({"ok": True})


@app.route("/api/devices/<path:name>", methods=["DELETE"])
def api_delete_device(name: str):
    profiles = load_profiles()
    if name in profiles:
        del profiles[name]
        save_profiles(profiles)
    return jsonify({"ok": True})


@app.route("/api/supabase-config", methods=["GET", "POST"])
def api_supabase_config():
    if request.method == "GET":
        return jsonify(load_supabase_config())
    cfg = request.get_json()
    save_supabase_config(cfg)
    return jsonify({"ok": True})


@app.route("/api/execute", methods=["POST"])
def api_execute():
    body = request.get_json()
    task_id = body.get("task_id", str(uuid.uuid4()))
    TASKS[task_id] = {"running": True, "queue": None}

    def _run():
        status = QueueStatus(task_id, log_file=_LOG_FILE)
        try:
            dev = AttendanceDevice(
                ip=body["ip"], port=int(body["port"]),
                password=int(body.get("password", 0)),
                machine_id=int(body.get("machine", 1)),
                timeout=10.0,
                hostname=body.get("hostname") or None,
                status=status,
            )
            status.step("Connecting to device")
            dev.connect()
            status.ok("Connected to device")

            command = body.get("command", "read-glogs")
            records = []

            if command == "read-glogs":
                records = dev.read_attendance_logs(all_logs=True)
            elif command == "read-slogs":
                records = dev.read_management_logs(all_logs=True)
            elif command == "users":
                records = dev.read_users()
            elif command == "info":
                serial = dev.get_serial_number()
                dt = dev.get_device_time()
                parts = []
                if serial: parts.append(f"Serial: {serial}")
                if dt: parts.append(f"Time: {dt['year']:04d}-{dt['month']:02d}-{dt['day']:02d} {dt['hour']:02d}:{dt['minute']:02d}:{dt['second']:02d}")
                status.write(" | ".join(parts) if parts else "No info returned")
                records = [{"serial_number": serial or "N/A", "device_time": str(dt) if dt else "N/A"}]
            elif command == "time":
                dt = dev.get_device_time()
                if dt:
                    ts = f"{dt['year']:04d}-{dt['month']:02d}-{dt['day']:02d} {dt['hour']:02d}:{dt['minute']:02d}:{dt['second']:02d}"
                    status.write(f"Device Time: {ts}")
                    records = [{"device_time": ts}]
                else:
                    status.fail("Failed to read device time")

            dev.disconnect()

            # Upload to Supabase if configured
            supabase_cfg = body.get("supabase", {})
            if supabase_cfg.get("enabled") and supabase_cfg.get("url") and supabase_cfg.get("key"):
                try:
                    from attendance_supabase import SupabaseConfig, upload_to_supabase
                    scfg = SupabaseConfig(
                        url=supabase_cfg["url"], key=supabase_cfg["key"],
                        device_id=supabase_cfg.get("device_id", "") or str(body.get("machine", 1)),
                        device_name=supabase_cfg.get("device_name", ""),
                        device_ip=body.get("ip", ""),
                    )
                    status.step("Uploading to Supabase")
                    result = upload_to_supabase(records, scfg, status=status)
                    parts = [f"{k}={v}" for k, v in result.items() if v]
                    if parts:
                        status.ok(f"Supabase upload complete ({', '.join(parts)})")
                    else:
                        status.fail("Supabase upload failed")
                except ImportError:
                    status.write("Supabase not installed (pip install supabase)")

            if records:
                status.result(records)
                status.ok("Complete")
            else:
                status.write("No data returned")
                status.result([])

        except Exception as e:
            status.fail(str(e))
            status.result([])
        finally:
            TASKS[task_id]["running"] = False

    threading.Thread(target=_run, daemon=True).start()
    return jsonify({"task_id": task_id})


@app.route("/api/progress/<task_id>")
def api_progress(task_id: str):
    """SSE endpoint that streams progress events from the task's queue."""

    def generate():
        q = None
        # Wait up to ~5s for the task to register its queue
        for _ in range(100):
            t = TASKS.get(task_id)
            if t and t.get("queue") is not None:
                q = t["queue"]
                break
            time.sleep(0.05)

        if q is None:
            yield f"event: fail\ndata: {json.dumps({'msg': 'Task not found'})}\n\n"
            return

        while True:
            try:
                ev = q.get(timeout=0.5)
                yield f"event: {ev['event']}\ndata: {json.dumps(ev['data'])}\n\n"
                if ev["event"] in ("result", "fail"):
                    break
            except queue.Empty:
                running = TASKS.get(task_id, {}).get("running", False)
                if not running:
                    break
                yield ": heartbeat\n\n"

        # Drain remaining events
        while True:
            try:
                ev = q.get_nowait()
                yield f"event: {ev['event']}\ndata: {json.dumps(ev['data'])}\n\n"
            except queue.Empty:
                break

    return Response(generate(), mimetype="text/event-stream")


@app.route("/api/export-csv", methods=["POST"])
def api_export_csv():
    body = request.get_json()
    data = body.get("data", [])
    if not data:
        return jsonify({"error": "No data"}), 400
    import csv, io
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(data[0].keys()))
    w.writeheader()
    w.writerows(data)
    mem = io.BytesIO(buf.getvalue().encode("utf-8-sig"))
    return Response(
        mem.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=attendance_export.csv"},
    )


@app.route("/api/progress-v2/<task_id>")
def api_progress_v2(task_id: str):
    """SSE endpoint that reads from the QueueStatus queue stored in TASKS."""

    def generate():
        # Wait for the task to register its queue
        q = None
        for _ in range(100):
            t = TASKS.get(task_id)
            if t and "queue" in t:
                q = t["queue"]
                break
            time.sleep(0.05)

        if q is None:
            yield f"event: fail\ndata: {json.dumps({'msg': 'Task not found'})}\n\n"
            return

        while True:
            try:
                ev = q.get(timeout=0.5)
                yield f"event: {ev['event']}\ndata: {json.dumps(ev['data'])}\n\n"
                if ev["event"] in ("result", "fail"):
                    break
            except queue.Empty:
                running = TASKS.get(task_id, {}).get("running", False)
                if not running:
                    break
                yield ": heartbeat\n\n"

        # Drain remaining
        while True:
            try:
                ev = q.get_nowait()
                yield f"event: {ev['event']}\ndata: {json.dumps(ev['data'])}\n\n"
            except queue.Empty:
                break

    return Response(generate(), mimetype="text/event-stream")


# ── Main ────────────────────────────────────────────────────────────────

def _setup_logging():
    global _LOG_FILE
    log_dir = os.path.expanduser("~/.attendance_logs")
    os.makedirs(log_dir, exist_ok=True)
    ts = time.strftime("%Y%m%d-%H%M%S")
    _LOG_FILE = os.path.join(log_dir, f"attendance_web_{ts}.log")
    handlers = [
        logging.StreamHandler(),
        logging.FileHandler(_LOG_FILE),
    ]
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
        handlers=handlers,
    )
    logging.info("Session log: %s", _LOG_FILE)


if __name__ == "__main__":
    _setup_logging()
    print("=" * 56)
    print("  Attendance Device Web UI")
    print("  Open:  http://127.0.0.1:5000")
    print("  Quit:  Ctrl+C")
    print(f"  Log:   {_LOG_FILE}")
    print("=" * 56)
    app.run(host="127.0.0.1", port=5000, debug=False, threaded=True)
