#!/usr/bin/env python3
"""Attendance Device GUI — Tkinter frontend for attendance_device.py"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import sys
import io
import os
import json
import time
import datetime
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from attendance_device import AttendanceDevice, StatusIndicator

THEME_BG = "#f0f0f0"
THEME_FG = "#1a1a1a"
ACCENT = "#2563eb"
ACCENT_HOVER = "#1d4ed8"
SUCCESS = "#16a34a"
ERROR_COL = "#dc2626"
FIELD_BG = "#ffffff"
CARD_BG = "#ffffff"
BORDER = "#d1d5db"

PROFILES_PATH = os.path.expanduser("~/.attendance_devices.json")
SUPABASE_CONFIG_PATH = os.path.expanduser("~/.attendance_supabase.json")


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


class TextRedirector(io.StringIO):
    def __init__(self, widget: tk.Text, tag: str = ""):
        super().__init__()
        self.widget = widget
        self.tag = tag

    def write(self, s: str):
        self.widget.insert(tk.END, s, (self.tag,))
        self.widget.see(tk.END)
        self.widget.update_idletasks()

    def flush(self):
        pass


class GuiStatus(StatusIndicator):
    def __init__(self, log_widget: tk.Text, log_file: str | None = None):
        super().__init__(log_file=log_file)
        self._log = log_widget
        self._log.tag_configure("info", foreground="#2563eb")
        self._log.tag_configure("ok", foreground="#16a34a")
        self._log.tag_configure("err", foreground="#dc2626")
        self._log.tag_configure("step", foreground="#888888")
        self._log.tag_configure("timer", foreground="#a0a0a0")

    def _fmt_elapsed(self, secs: int) -> str:
        if secs >= 3600:
            return f"{secs//3600:02d}:{(secs%3600)//60:02d}:{secs%60:02d}"
        return f"{secs//60:02d}:{secs%60:02d}"

    def _now_tag(self) -> str:
        if self._global_start:
            e = int(time.time() - self._global_start)
            return f"  [{self._fmt_elapsed(e)}]"
        return ""

    def _write_log(self, msg: str, tag: str = ""):
        self._log.insert(tk.END, msg + "\n", (tag,))
        self._log.see(tk.END)
        self._log.update_idletasks()

    def step(self, msg: str):
        now = time.time()
        if self._global_start == 0:
            self._global_start = now
        self._phase += 1
        self._step_start = now
        self._current = msg
        self._write_log(f"  {msg} ...", "step")

    def tick(self, msg: str | None = None):
        if msg:
            self._current = msg
        elapsed = int(time.time() - self._global_start) if self._global_start else 0
        tag = self._fmt_elapsed(elapsed)
        self._write_log(f"  [{tag}] {self._current}", "step")

    def ok(self, msg: str | None = None):
        label = msg if msg else self._current
        tag = self._now_tag()
        self._write_log(f"\u2713 {label}{tag}", "ok")
        self._current = ""
        self._step_start = 0.0

    def fail(self, msg: str | None = None):
        label = msg if msg else self._current
        tag = self._now_tag()
        self._write_log(f"\u2717 {label}{tag}", "err")
        self._current = ""
        self._step_start = 0.0

    def write(self, msg: str):
        tag = self._now_tag()
        self._write_log(f"{msg}{tag}", "info")

    def waiting(self, msg: str):
        tag = self._now_tag()
        self._write_log(f"  \u23F3 {msg}{tag}", "step")

    def startup(self, msg: str):
        self._write_log(f"\u25B6 {msg}", "info")


class AttendanceGUI:

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Attendance Device Utility")
        self.root.geometry("760x740")
        self.root.minsize(640, 600)
        self.root.configure(bg=THEME_BG)

        self._profiles: dict = load_profiles()
        self._last_records = None
        self._running = False
        self._dirty = False
        self._timer_running = False
        self._timer_seconds = 0
        self._supabase_cfg = load_supabase_config()
        self._log_file = self._init_log_file()

        self._build_ui()

    @staticmethod
    def _init_log_file() -> str | None:
        log_dir = os.path.expanduser("~/.attendance_logs")
        os.makedirs(log_dir, exist_ok=True)
        ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        path = os.path.join(log_dir, f"attendance_{ts}.log")
        try:
            fh = logging.FileHandler(path)
            fh.setLevel(logging.DEBUG)
            logging.getLogger().addHandler(fh)
            logging.info("Session log: %s", path)
            return path
        except OSError:
            return None
        self._refresh_device_list()
        self._on_select_device(None)

    # ── Timer ──────────────────────────────────────────────────────────

    def _start_timer(self):
        self._timer_seconds = 0
        self._timer_running = True
        self._timer_label.config(text="⏱  00:00:00")
        self._update_timer()

    def _stop_timer(self):
        self._timer_running = False

    def _update_timer(self):
        if not self._timer_running:
            return
        self._timer_seconds += 1
        h = self._timer_seconds // 3600
        m = (self._timer_seconds % 3600) // 60
        s = self._timer_seconds % 60
        self._timer_label.config(text=f"⏱  {h:02d}:{m:02d}:{s:02d}")
        self.root.after(1000, self._update_timer)

    # ── UI Build ────────────────────────────────────────────────────────

    def _make_entry(self, parent, **kw) -> tk.Entry:
        ent = tk.Entry(
            parent, font=("Segoe UI", 12), bg=FIELD_BG, fg=THEME_FG,
            relief=tk.FLAT, highlightthickness=1,
            highlightcolor=ACCENT, highlightbackground=BORDER,
            **kw,
        )
        # Enable paste on macOS (right-click / Ctrl+click context menu)
        if sys.platform == "darwin":
            paste_menu = tk.Menu(ent, tearoff=0)
            paste_menu.add_command(label="Paste", command=lambda e=ent: e.event_generate("<<Paste>>"))
            ent.bind("<Button-2>", lambda e, m=paste_menu: m.tk_popup(e.x_root, e.y_root))
            ent.bind("<Control-Button-1>", lambda e, m=paste_menu: m.tk_popup(e.x_root, e.y_root))
        return ent

    def _make_label(self, parent, text: str, **kw) -> tk.Label:
        return tk.Label(
            parent, text=text, bg=THEME_BG, fg=THEME_FG,
            font=("Segoe UI", 10), anchor="w", **kw,
        )

    def _make_card(self, parent, title: str = "") -> tk.Frame:
        frame = tk.Frame(parent, bg=CARD_BG, highlightbackground=BORDER,
                         highlightthickness=1, padx=20, pady=16)
        if title:
            tk.Label(frame, text=title, bg=CARD_BG, fg=THEME_FG,
                     font=("Segoe UI", 11, "bold"), anchor="w"
                     ).pack(fill=tk.X, pady=(0, 12))
        return frame

    def _build_ui(self):
        root = self.root

        # ── Header ────────────────────────────────────────────────────
        header = tk.Frame(root, bg=ACCENT, height=56)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(header, text="Attendance Device Utility",
                 fg="white", bg=ACCENT, font=("Segoe UI", 16, "bold")
                 ).pack(side=tk.LEFT, padx=20, pady=12)
        self._timer_label = tk.Label(
            header, text="⏱  00:00:00",
            fg="#bfdbfe", bg=ACCENT, font=("Segoe UI", 12),
        )
        self._timer_label.pack(side=tk.RIGHT, padx=20, pady=12)

        # ── Scrollable body ───────────────────────────────────────────
        canvas = tk.Canvas(root, bg=THEME_BG, highlightthickness=0)
        scrollbar = tk.Scrollbar(root, orient=tk.VERTICAL, command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=THEME_BG)
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        body = scroll_frame

        # ── Device Selector Card ───────────────────────────────────────
        sel_card = self._make_card(body, "Saved Devices")
        sel_card.pack(fill=tk.X, padx=24, pady=(20, 0))

        sel_row = tk.Frame(sel_card, bg=CARD_BG)
        sel_row.pack(fill=tk.X)

        self.device_selector = ttk.Combobox(
            sel_row, state="readonly", font=("Segoe UI", 12),
        )
        self.device_selector.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4)
        self.device_selector.bind("<<ComboboxSelected>>", self._on_select_device)

        self.del_btn = tk.Button(
            sel_row, text="\u2716  Delete", font=("Segoe UI", 10),
            bg="#fee2e2", fg="#991b1b", relief=tk.FLAT, padx=14, pady=6,
            activebackground="#fecaca", cursor="hand2",
            command=self._on_delete_device,
        )
        self.del_btn.pack(side=tk.LEFT, padx=(10, 0))

        # ── Device Details Card ────────────────────────────────────────
        det_card = self._make_card(body, "Device Details")
        det_card.pack(fill=tk.X, padx=24, pady=(12, 0))

        grid = tk.Frame(det_card, bg=CARD_BG)
        grid.pack(fill=tk.X)
        grid.columnconfigure(1, weight=1)

        labels = [
            ("Device Name", "name_var", "Main Office"),
            ("Hostname", "hostname_var", ""),
            ("IP Address", "ip_var", "192.168.1.224"),
            ("Port", "port_var", "5005"),
            ("Password", "pw_var", "0"),
            ("Device ID (Machine #)", "machine_var", "1"),
        ]

        self._entry_vars = {}
        for i, (label_text, var_name, default) in enumerate(labels):
            self._make_label(grid, label_text
                             ).grid(row=i, column=0, sticky="w", pady=(0, 2))
            v = tk.StringVar(value=default)
            setattr(self, var_name, v)
            self._entry_vars[var_name] = v
            ent = self._make_entry(grid, textvariable=v)
            ent.grid(row=i, column=1, sticky="ew", padx=(8, 0), pady=(0, 10), ipady=6)
            # Bind changes to mark dirty
            v.trace_add("write", lambda *a: setattr(self, '_dirty', True))

        # Save buttons
        btn_row = tk.Frame(det_card, bg=CARD_BG)
        btn_row.pack(fill=tk.X, pady=(4, 0))

        self.save_new_btn = tk.Button(
            btn_row, text="\u2795  Save As New", font=("Segoe UI", 11),
            bg=ACCENT, fg="white", relief=tk.FLAT, padx=20, pady=7,
            activebackground=ACCENT_HOVER, activeforeground="white",
            cursor="hand2", command=self._on_save_as_new,
        )
        self.save_new_btn.pack(side=tk.LEFT, padx=(0, 8))

        self.save_btn = tk.Button(
            btn_row, text="\U0001F4BE  Save", font=("Segoe UI", 11),
            bg="#e5e7eb", fg=THEME_FG, relief=tk.FLAT, padx=20, pady=7,
            activebackground="#d1d5db", cursor="hand2",
            state=tk.DISABLED, command=self._on_save,
        )
        self.save_btn.pack(side=tk.LEFT)

        # ── Operation Card ─────────────────────────────────────────────
        op_card = self._make_card(body, "Operation")
        op_card.pack(fill=tk.X, padx=24, pady=(12, 0))

        op_row = tk.Frame(op_card, bg=CARD_BG)
        op_row.pack(fill=tk.X)

        self.op_var = tk.StringVar(value="read-glogs")
        op_menu = ttk.Combobox(
            op_row, textvariable=self.op_var, state="readonly",
            font=("Segoe UI", 12),
            values=[
                ("read-glogs", "Read Attendance Logs"),
                ("read-slogs", "Read Management Logs"),
                ("users",      "List Enrolled Users"),
                ("info",       "Device Information"),
                ("time",       "Device Date/Time"),
            ],
        )
        op_menu.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4)

        self.run_btn = tk.Button(
            op_row, text="\u25b6  Execute", font=("Segoe UI", 12, "bold"),
            bg=ACCENT, fg="white", relief=tk.FLAT, padx=28, pady=8,
            activebackground=ACCENT_HOVER, activeforeground="white",
            cursor="hand2", command=self._on_execute,
        )
        self.run_btn.pack(side=tk.LEFT, padx=(10, 0))

        self.export_btn = tk.Button(
            op_row, text="\U0001F4BE  Export CSV", font=("Segoe UI", 11),
            bg="#e5e7eb", fg=THEME_FG, relief=tk.FLAT, padx=20, pady=8,
            activebackground="#d1d5db", cursor="hand2",
            state=tk.DISABLED, command=self._on_export_csv,
        )
        self.export_btn.pack(side=tk.LEFT, padx=(8, 0))

        self.exit_btn = tk.Button(
            op_row, text="\u2716  Exit", font=("Segoe UI", 11),
            bg="#e5e7eb", fg=THEME_FG, relief=tk.FLAT, padx=20, pady=8,
            activebackground="#d1d5db", cursor="hand2",
            command=self.root.destroy,
        )
        self.exit_btn.pack(side=tk.RIGHT, padx=(0, 0))

        # ── Supabase Card ──────────────────────────────────────────────
        sup_card = self._make_card(body, "Supabase Integration")
        sup_card.pack(fill=tk.X, padx=24, pady=(12, 0))

        self._supabase_enabled = tk.BooleanVar(value=self._supabase_cfg.get("enabled", False))
        sup_row1 = tk.Frame(sup_card, bg=CARD_BG)
        sup_row1.pack(fill=tk.X)
        tk.Checkbutton(
            sup_row1, text="Upload records to Supabase", variable=self._supabase_enabled,
            bg=CARD_BG, fg=THEME_FG, font=("Segoe UI", 10, "bold"),
            selectcolor=CARD_BG, activebackground=CARD_BG,
        ).pack(side=tk.LEFT)

        sup_grid = tk.Frame(sup_card, bg=CARD_BG)
        sup_grid.pack(fill=tk.X, pady=(8, 0))
        sup_grid.columnconfigure(1, weight=1)

        sup_fields = [
            ("Project URL", "supabase_url", self._supabase_cfg.get("url", "")),
            ("API Key", "supabase_key", self._supabase_cfg.get("key", "")),
            ("Device ID", "supabase_devid", self._supabase_cfg.get("device_id", "")),
            ("Device Name", "supabase_devname", self._supabase_cfg.get("device_name", "")),
        ]
        self._supabase_vars = {}
        for i, (label_text, var_name, default) in enumerate(sup_fields):
            self._make_label(sup_grid, label_text
                             ).grid(row=i, column=0, sticky="w", pady=(0, 2))
            v = tk.StringVar(value=default)
            self._supabase_vars[var_name] = v
            ent = self._make_entry(sup_grid, textvariable=v)
            ent.grid(row=i, column=1, sticky="ew", padx=(8, 0), pady=(0, 6), ipady=4)

        sup_btn_row = tk.Frame(sup_card, bg=CARD_BG)
        sup_btn_row.pack(fill=tk.X, pady=(4, 0))
        tk.Button(
            sup_btn_row, text="Save Supabase Settings", font=("Segoe UI", 10),
            bg=ACCENT, fg="white", relief=tk.FLAT, padx=16, pady=5,
            activebackground=ACCENT_HOVER, activeforeground="white",
            cursor="hand2", command=self._on_save_supabase,
        ).pack(side=tk.LEFT)

        # ── Log Output ─────────────────────────────────────────────────
        log_frame = tk.Frame(body, bg=THEME_BG)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=24, pady=(16, 24))

        tk.Label(log_frame, text="Output Log", bg=THEME_BG, fg=THEME_FG,
                 font=("Segoe UI", 10, "bold"), anchor="w"
                 ).pack(fill=tk.X, pady=(0, 4))

        text_frame = tk.Frame(log_frame, bg=THEME_BG)
        text_frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = tk.Text(
            text_frame, font=("Consolas", 10), bg="#1e1e2e", fg="#cdd6f4",
            relief=tk.FLAT, borderwidth=0, padx=12, pady=12,
            wrap=tk.WORD, state=tk.NORMAL,
        )
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(text_frame, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)

        # ── Bindings ───────────────────────────────────────────────────
        root.bind("<Return>", lambda e: self._on_execute())

    # ── Device Profile Management ──────────────────────────────────────

    def _refresh_device_list(self):
        names = sorted(self._profiles.keys())
        self.device_selector["values"] = names
        if names:
            if not self.device_selector.get():
                self.device_selector.set(names[0])
            self.del_btn.config(state=tk.NORMAL)
        else:
            self.device_selector.set("")
            self.del_btn.config(state=tk.DISABLED)

    def _refresh_and_select(self, name: str):
        """Refresh the dropdown list and select *name*, then load its fields."""
        self._refresh_device_list()
        self.device_selector.set(name)
        self._load_device_fields(name)

    def _load_device_fields(self, name: str):
        """Load field values for a known profile name."""
        if name and name in self._profiles:
            p = self._profiles[name]
            self.name_var.set(name)
            self.hostname_var.set(p.get("hostname", ""))
            self.ip_var.set(p.get("ip", ""))
            self.port_var.set(str(p.get("port", 5005)))
            self.pw_var.set(str(p.get("password", 0)))
            self.machine_var.set(str(p.get("machine_id", 1)))
            self.save_btn.config(state=tk.NORMAL)
            self._dirty = False
        else:
            self.save_btn.config(state=tk.DISABLED)

    def _on_select_device(self, event=None):
        self._load_device_fields(self.device_selector.get())

    def _on_delete_device(self):
        name = self.device_selector.get()
        if not name or name not in self._profiles:
            return
        if messagebox.askyesno("Delete Device",
                               f"Delete saved device \"{name}\"?"):
            del self._profiles[name]
            save_profiles(self._profiles)
            self._refresh_device_list()
            if self._profiles:
                first = sorted(self._profiles.keys())[0]
                self._refresh_and_select(first)
            else:
                self.device_selector.set("")
                self.del_btn.config(state=tk.DISABLED)
                self.save_btn.config(state=tk.DISABLED)
                self.name_var.set("")

    def _on_save_as_new(self):
        name = self.name_var.get().strip()
        if not name:
            messagebox.showerror("Error", "Device Name is required.")
            return
        if name in self._profiles:
            if not messagebox.askyesno("Overwrite?",
                                       f"Device \"{name}\" already exists. Overwrite?"):
                return
        self._save_current(name)
        self._refresh_and_select(name)

    def _on_save(self):
        name = self.device_selector.get()
        if not name:
            return
        self._save_current(name)
        self._refresh_device_list()
        self._dirty = False

    def _save_current(self, name: str):
        try:
            port = int(self.port_var.get())
        except ValueError:
            port = 5005
        try:
            password = int(self.pw_var.get())
        except ValueError:
            password = 0
        try:
            machine_id = int(self.machine_var.get())
        except ValueError:
            machine_id = 1

        self._profiles[name] = {
            "ip": self.ip_var.get().strip(),
            "hostname": self.hostname_var.get().strip(),
            "port": port,
            "password": password,
            "machine_id": machine_id,
        }
        save_profiles(self._profiles)

    # ── Execution ──────────────────────────────────────────────────────

    def _on_execute(self):
        if self._running:
            return

        # Prompt to save if dirty
        if self._dirty:
            ans = messagebox.askyesnocancel(
                "Unsaved Changes",
                "Device details have changed. Save before running?",
            )
            if ans is True:
                current_name = self.name_var.get().strip()
                if current_name:
                    self._save_current(current_name)
                    self._refresh_device_list()
                    self.device_selector.set(current_name)
                    self._dirty = False
                else:
                    self._on_save_as_new()
            elif ans is None:
                return

        self._running = True
        self.run_btn.config(state=tk.DISABLED, text="\u23f3  Running ...")
        self.export_btn.config(state=tk.DISABLED)
        self.log_text.delete("1.0", tk.END)
        self._last_records = None

        ip = self.ip_var.get().strip()
        hostname = self.hostname_var.get().strip()
        port_str = self.port_var.get().strip()
        pw_str = self.pw_var.get().strip()
        machine_str = self.machine_var.get().strip()
        command = self.op_var.get()

        errors = []
        if not ip and not hostname:
            errors.append("IP Address or Hostname is required")
        try:
            port = int(port_str)
        except ValueError:
            errors.append("Port must be a number")
        try:
            password = int(pw_str)
        except ValueError:
            errors.append("Password must be a number")
        try:
            machine = int(machine_str)
        except ValueError:
            errors.append("Device ID must be a number")

        if errors:
            messagebox.showerror("Input Error", "\n".join(errors))
            self._running = False
            self.run_btn.config(state=tk.NORMAL, text="\u25b6  Execute")
            return

        threading.Thread(
            target=self._run_task,
            args=(ip, hostname, port, password, machine, command),
            daemon=True,
        ).start()

    def _run_task(self, ip: str, hostname: str, port: int, password: int,
                  machine: int, command: str):
        try:
            self.root.after(0, self._start_timer)
            status = GuiStatus(self.log_text, log_file=self._log_file)

            status.startup(f"Initializing device interface for {ip}:{port}")
            dev = AttendanceDevice(
                ip=ip, port=port, password=password,
                machine_id=machine, timeout=10.0,
                hostname=self.hostname_var.get().strip() or None,
                status=status,
            )
            status.ok("Device interface loaded")

            status.write("---")
            status.step("Opening TCP connection")
            dev.connect()
            status.ok("TCP handshake complete")

            if password:
                status.step("Authenticating with device")
                status.ok("Authentication successful")
                status.write("---")

            status.write(f"Executing operation: {command}")
            records = []

            if command == "read-glogs":
                status.step("Requesting attendance log data from device")
                status.waiting("Waiting for device to prepare log data ...")
                records = dev.read_attendance_logs(all_logs=True)
                if records:
                    status.write(f"Total: {len(records)} attendance records retrieved")
                else:
                    status.write("No attendance records found")

            elif command == "read-slogs":
                status.step("Requesting management log data from device")
                status.waiting("Waiting for device to prepare management logs ...")
                records = dev.read_management_logs(all_logs=True)
                if records:
                    status.write(f"Total: {len(records)} management records retrieved")
                else:
                    status.write("No management records found")

            elif command == "users":
                status.step("Fetching enrolled user list from device")
                status.waiting("Waiting for device to transmit user data ...")
                records = dev.read_users()
                if records:
                    status.write(f"Total: {len(records)} users found")
                else:
                    status.write("No users found")

            elif command == "info":
                status.step("Retrieving device information")
                status.waiting("Querying device serial number ...")
                serial = dev.get_serial_number()
                status.write(f"  Serial Number: {serial or 'N/A'}")
                status.waiting("Querying device date/time ...")
                dt = dev.get_device_time()
                if dt:
                    status.write(f"  Device Time: {dt['year']:04d}-{dt['month']:02d}-{dt['day']:02d}"
                                 f" {dt['hour']:02d}:{dt['minute']:02d}:{dt['second']:02d}")
                status.ok("Device information retrieved")

            elif command == "time":
                status.step("Reading device date/time")
                status.waiting("Querying device clock ...")
                dt = dev.get_device_time()
                if dt:
                    status.write(f"Device Time: {dt['year']:04d}-{dt['month']:02d}-{dt['day']:02d}"
                                 f" {dt['hour']:02d}:{dt['minute']:02d}:{dt['second']:02d}")
                    status.ok("Device time retrieved")
                else:
                    status.fail("Failed to read device time")

            status.write("---")
            status.step("Closing connection to device")
            dev.disconnect()
            status.ok("Disconnected")

            self._last_records = records if records else None

            if records:
                self.root.after(0, self._enable_export)

            self._upload_to_supabase(records, status, ip, machine)

            status.write("Operation complete")

        except Exception as e:
            self.root.after(0, lambda e=e: self._show_error(str(e)))
        finally:
            self.root.after(0, self._enable_run_button)

    def _enable_run_button(self):
        self._running = False
        self._stop_timer()
        self.run_btn.config(state=tk.NORMAL, text="\u25b6  Execute")

    def _enable_export(self):
        self.export_btn.config(state=tk.NORMAL)

    def _show_error(self, msg: str):
        self.log_text.insert(tk.END, f"\nERROR: {msg}\n", "err")
        self.log_text.see(tk.END)

    # ── Supabase ────────────────────────────────────────────────────────

    def _on_save_supabase(self):
        self._supabase_cfg = {
            "url": self._supabase_vars["supabase_url"].get().strip(),
            "key": self._supabase_vars["supabase_key"].get().strip(),
            "device_id": self._supabase_vars["supabase_devid"].get().strip(),
            "device_name": self._supabase_vars["supabase_devname"].get().strip(),
            "enabled": self._supabase_enabled.get(),
        }
        save_supabase_config(self._supabase_cfg)
        messagebox.showinfo("Supabase", "Supabase settings saved.")

    def _upload_to_supabase(self, records: list[dict], status, ip: str, machine: int):
        cfg = self._supabase_cfg
        if not cfg.get("enabled") or not records:
            return
        url = cfg.get("url", "").strip()
        key = cfg.get("key", "").strip()
        if not url or not key:
            status.write("Supabase enabled but URL or Key missing")
            return
        try:
            from attendance_supabase import SupabaseConfig, upload_to_supabase
        except ImportError:
            status.write("Supabase not installed (pip install supabase)")
            return
        scfg = SupabaseConfig(
            url=url, key=key,
            device_id=cfg.get("device_id", "") or str(machine),
            device_name=cfg.get("device_name", ""),
            device_ip=ip,
        )
        status.step("Uploading to Supabase")
        result = upload_to_supabase(records, scfg, status=status)
        parts = [f"{k}={v}" for k, v in result.items() if v]
        if parts:
            status.ok(f"Supabase upload complete ({', '.join(parts)})")
        else:
            status.fail("Supabase upload failed")

    # ── CSV Export ─────────────────────────────────────────────────────

    def _on_export_csv(self):
        if not self._last_records:
            messagebox.showinfo("No Data", "No records to export. Run an operation first.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            from attendance_device import records_to_csv
            records_to_csv(self._last_records, path)
            messagebox.showinfo("Exported",
                                f"Saved {len(self._last_records)} records to {path}")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))

    # ── Run ────────────────────────────────────────────────────────────

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    AttendanceGUI().run()
