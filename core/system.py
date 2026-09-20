#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
 CachyOS Control Center — Core System & Telemetry Engine
 Low-Level System Metriken, Service-Audits & Hardware-Monitoring
===============================================================================
"""

from __future__ import annotations

import os
import platform
import re
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def run_cmd(cmd: str, timeout: int = 20) -> Tuple[str, str, int]:
    """
    Führt Shell-Befehle sicher mit Timeout und Exit-Code-Rückgabe aus.
    Erkennt automatisch bestehende Root-Rechte (entfernt pkexec) und fängt
    Timeouts sowie Berechtigungsfehler defensiv ab.
    """
    if os.geteuid() == 0 and cmd.startswith("pkexec "):
        cmd = cmd[7:].strip()

    try:
        res = subprocess.run(
            cmd,
            shell=True,
            text=True,
            capture_output=True,
            timeout=timeout,
        )
        out = res.stdout.strip()
        err = res.stderr.strip()

        # Polkit / pkexec Abbruch abfangen
        if res.returncode == 126 or "not authorized" in err.lower() or "dismissed" in err.lower():
            err = "Aktion abgebrochen: Root-Authentifizierung (Polkit) wurde abgewiesen oder nicht bestätigt."

        return out, err, res.returncode
    except subprocess.TimeoutExpired:
        return "", f"Zeitüberschreitung: Befehl nach {timeout}s abgebrochen.", 124
    except Exception as exc:
        return "", f"Systemfehler bei Befehlsausführung: {exc}", 1


@dataclass
class ServiceStatus:
    name: str
    active: bool
    status_text: str
    substate: str = ""
    enabled: bool = False


@dataclass
class SystemTelemetry:
    hostname: str
    os_name: str
    kernel: str
    architecture: str
    uptime_str: str
    cpu_percent: float
    cpu_cores: int
    ram_total_gb: float
    ram_used_gb: float
    ram_percent: float
    disk_total_gb: float
    disk_used_gb: float
    disk_percent: float
    is_btrfs: bool
    failed_system_units: int
    failed_user_units: int
    failed_unit_names: List[str] = field(default_factory=list)
    timestamp: str = ""


_last_cpu_times: Optional[Tuple[float, float]] = None


def _get_cpu_usage_proc() -> float:
    """Berechnet die CPU-Auslastung präzise über zwei Ticks aus /proc/stat."""
    global _last_cpu_times
    try:
        with open("/proc/stat", "r") as f:
            first_line = f.readline()
        fields = [float(x) for x in first_line.strip().split()[1:]]
        idle_time = fields[3] + fields[4]  # idle + iowait
        total_time = sum(fields)

        if _last_cpu_times is None:
            _last_cpu_times = (idle_time, total_time)
            time.sleep(0.05)
            with open("/proc/stat", "r") as f:
                first_line = f.readline()
            fields = [float(x) for x in first_line.strip().split()[1:]]
            idle_time = fields[3] + fields[4]
            total_time = sum(fields)

        last_idle, last_total = _last_cpu_times
        delta_idle = idle_time - last_idle
        delta_total = total_time - last_total
        _last_cpu_times = (idle_time, total_time)

        if delta_total > 0:
            usage = 100.0 * (1.0 - (delta_idle / delta_total))
            return max(0.0, min(100.0, round(usage, 1)))
        return 0.0
    except Exception:
        return 0.0


def _get_ram_info() -> Tuple[float, float, float]:
    """Ermittelt RAM Gesamt, Belegt und Prozentwert via /proc/meminfo."""
    try:
        meminfo: Dict[str, int] = {}
        with open("/proc/meminfo", "r") as f:
            for line in f:
                parts = line.split(":")
                if len(parts) == 2:
                    key = parts[0].strip()
                    val_str = parts[1].strip().split()[0]
                    if val_str.isdigit():
                        meminfo[key] = int(val_str)

        total_kb = meminfo.get("MemTotal", 0)
        avail_kb = meminfo.get("MemAvailable", meminfo.get("MemFree", 0))
        used_kb = max(0, total_kb - avail_kb)

        total_gb = round(total_kb / (1024 * 1024), 2)
        used_gb = round(used_kb / (1024 * 1024), 2)
        pct = round((used_kb / total_kb * 100.0), 1) if total_kb > 0 else 0.0
        return total_gb, used_gb, pct
    except Exception:
        return 0.0, 0.0, 0.0


def _get_uptime_string() -> str:
    """Liest Uptime aus /proc/uptime und formatiert in Tage, Stunden, Minuten."""
    try:
        with open("/proc/uptime", "r") as f:
            up_secs = float(f.readline().split()[0])
        mins, _ = divmod(int(up_secs), 60)
        hours, mins = divmod(mins, 60)
        days, hours = divmod(hours, 24)
        if days > 0:
            return f"{days}d {hours}h {mins}m"
        return f"{hours}h {mins}m"
    except Exception:
        return "N/A"


def _check_is_btrfs() -> bool:
    """Prüft, ob das Root-Dateisystem Btrfs ist."""
    try:
        out, _, _ = run_cmd("stat -f -c %T /")
        return "btrfs" in out.lower()
    except Exception:
        return False


def get_system_telemetry() -> SystemTelemetry:
    """Erfasst den vollständigen System- und Hardwarereport."""
    hostname = platform.node() or "cachyos-host"
    kernel = platform.release() or "Linux"
    arch = platform.machine() or "x86_64"

    # Distro Name
    os_name = "CachyOS Linux"
    try:
        if Path("/etc/os-release").exists():
            with open("/etc/os-release") as f:
                for line in f:
                    if line.startswith("PRETTY_NAME="):
                        os_name = line.split("=", 1)[1].strip().strip('"')
                        break
    except Exception:
        pass

    uptime_str = _get_uptime_string()
    cpu_pct = _get_cpu_usage_proc()
    cpu_cores = os.cpu_count() or 1
    ram_tot, ram_use, ram_pct = _get_ram_info()

    # Disk Info für /
    try:
        du = shutil.disk_usage("/")
        disk_tot = round(du.total / (1024**3), 2)
        disk_use = round(du.used / (1024**3), 2)
        disk_pct = round((du.used / du.total * 100.0), 1) if du.total > 0 else 0.0
    except Exception:
        disk_tot, disk_use, disk_pct = 0.0, 0.0, 0.0

    is_btrfs = _check_is_btrfs()

    sys_fail_out, _, _ = run_cmd("systemctl --failed --no-legend")
    usr_fail_out, _, _ = run_cmd("systemctl --user --failed --no-legend")

    def _parse_failed(output: str) -> List[str]:
        units = []
        for line in output.splitlines():
            parts = line.split()
            if not parts:
                continue
            unit_name = parts[1] if parts[0] in ("●", "*", "-") and len(parts) > 1 else parts[0]
            units.append(unit_name)
        return units

    sys_failed = _parse_failed(sys_fail_out)
    usr_failed = _parse_failed(usr_fail_out)

    all_failed = sys_failed + [f"[user] {u}" for u in usr_failed]

    return SystemTelemetry(
        hostname=hostname,
        os_name=os_name,
        kernel=kernel,
        architecture=arch,
        uptime_str=uptime_str,
        cpu_percent=cpu_pct,
        cpu_cores=cpu_cores,
        ram_total_gb=ram_tot,
        ram_used_gb=ram_use,
        ram_percent=ram_pct,
        disk_total_gb=disk_tot,
        disk_used_gb=disk_use,
        disk_percent=disk_pct,
        is_btrfs=is_btrfs,
        failed_system_units=len(sys_failed),
        failed_user_units=len(usr_failed),
        failed_unit_names=all_failed,
        timestamp=time.strftime("%H:%M:%S"),
    )


def get_services_status(service_names: Optional[List[str]] = None) -> List[ServiceStatus]:
    """Prüft den Live-Status definierter Systemd-Dienste."""
    if service_names is None:
        service_names = ["sshd", "NetworkManager", "tailscaled", "syncthing", "docker", "bluetooth"]

    results: List[ServiceStatus] = []
    for s_name in service_names:
        state_out, _, code = run_cmd(f"systemctl is-active {s_name}")
        is_act = state_out == "active"
        sub_out, _, _ = run_cmd(f"systemctl show -p SubState --value {s_name}")
        en_out, _, _ = run_cmd(f"systemctl is-enabled {s_name}")
        is_en = en_out == "enabled"

        results.append(
            ServiceStatus(
                name=s_name,
                active=is_act,
                status_text=state_out or "inactive",
                substate=sub_out or "dead",
                enabled=is_en,
            )
        )
    return results
