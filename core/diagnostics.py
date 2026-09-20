#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
 CachyOS Control Center — Diagnostic & Hardware Audit Core Engine
 Hardware-Snapshots, Boot-Parameter (/proc/cmdline), Kernel-Logs (dmesg/journal),
 Systemstart-Analyse (systemd-analyze) & Netzwerk-Audits
===============================================================================
"""

from __future__ import annotations

import json
import os
import platform
import shutil
import socket
import subprocess
import time
import urllib.request
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .system import get_system_telemetry, run_cmd


@dataclass
class DiagnosticItem:
    category: str
    test_name: str
    status: str  # "PASS", "WARN", "FAIL", "INFO"
    metric_value: str
    details: str
    recommendation: str = ""


@dataclass
class DiagnosticResult:
    profile: str
    overall_health: str  # "HEALTHY", "DEGRADED", "CRITICAL"
    items: List[DiagnosticItem] = field(default_factory=list)
    raw_report: str = ""
    duration_seconds: float = 0.0


def get_boot_cmdline() -> str:
    """Liest die aktiven Kernel-Boot-Parameter aus /proc/cmdline."""
    cmdline_file = Path("/proc/cmdline")
    if cmdline_file.exists():
        try:
            return cmdline_file.read_text(encoding="utf-8").strip()
        except Exception:
            pass
    return "N/A"


def get_kernel_logs(max_lines: int = 40) -> List[str]:
    """
    Liest die neuesten Kernel-Logs via journalctl -k oder dmesg.
    Benötigt dank systemd-journal Gruppe keine Root-Rechte.
    """
    logs: List[str] = []
    if shutil.which("journalctl"):
        out, _, code = run_cmd(f"journalctl -k -n {max_lines} --no-pager", timeout=5)
        if code == 0 and out.strip():
            return [line for line in out.splitlines() if line.strip()]

    if shutil.which("dmesg"):
        out, _, code = run_cmd(f"dmesg -T | tail -n {max_lines}", timeout=5)
        if code == 0 and out.strip():
            return [line for line in out.splitlines() if line.strip()]

    return ["Keine Kernel-Logs abrufbar."]


def get_boot_time_analysis() -> Dict[str, str]:
    """Ermittelt Systemstartzeiten über systemd-analyze (Firmware, Loader, Kernel, Initrd, Userspace)."""
    res = {
        "status": "Available",
        "summary": "systemd-analyze nicht verfügbar",
        "firmware": "0s",
        "loader": "0s",
        "kernel": "0s",
        "initrd": "0s",
        "userspace": "0s",
        "total": "0s",
    }
    if not shutil.which("systemd-analyze"):
        res["status"] = "Unavailable/Not Installed"
        res["summary"] = "systemd-analyze fehlt (Bestandteil von systemd)"
        return res

    out, _, code = run_cmd("systemd-analyze time", timeout=6)
    if code == 0 and out.strip():
        first_line = out.splitlines()[0]
        res["summary"] = first_line
        # Parser für Zeiten
        import re
        m = re.search(r"Startup finished in (.+)", first_line)
        if m:
            res["total"] = first_line.split("=")[-1].strip() if "=" in first_line else "N/A"
    return res


def get_hardware_snapshot() -> Dict[str, Any]:
    """Erfasst einen vollständigen Hardware-Snapshot (CPU, Board, RAM, Disks, PCI)."""
    snapshot: Dict[str, Any] = {
        "cpu_model": "Unbekannt",
        "cpu_cores": os.cpu_count() or 1,
        "motherboard": "Unbekannt",
        "chassis": "Desktop / PC",
        "disks": [],
        "pci_controllers": [],
    }

    # CPU Modell aus /proc/cpuinfo
    try:
        with open("/proc/cpuinfo", "r") as f:
            for line in f:
                if line.startswith("model name"):
                    snapshot["cpu_model"] = line.split(":", 1)[1].strip()
                    break
    except Exception:
        pass

    # Motherboard & DMI (falls lesbar in sysfs)
    try:
        board_vendor = Path("/sys/devices/virtual/dmi/id/board_vendor")
        board_name = Path("/sys/devices/virtual/dmi/id/board_name")
        if board_vendor.exists() and board_name.exists():
            v = board_vendor.read_text(encoding="utf-8").strip()
            n = board_name.read_text(encoding="utf-8").strip()
            snapshot["motherboard"] = f"{v} {n}"
    except Exception:
        pass

    # Block Devices / Disks via lsblk
    if shutil.which("lsblk"):
        out, _, code = run_cmd("lsblk -d -n -o NAME,SIZE,TYPE,MODEL", timeout=5)
        if code == 0 and out.strip():
            for l in out.splitlines():
                parts = l.split(maxsplit=3)
                if len(parts) >= 3 and parts[2] in ["disk", "nvme"]:
                    model = parts[3] if len(parts) > 3 else "Storage Device"
                    snapshot["disks"].append(f"/dev/{parts[0]} ({parts[1]}, {model})")

    # PCI Controller Auszug
    if shutil.which("lspci"):
        out, _, code = run_cmd("lspci | grep -E 'VGA|Audio|Network|Ethernet|Non-Volatile'", timeout=5)
        if code == 0 and out.strip():
            snapshot["pci_controllers"] = [line.split(":", 1)[-1].strip() for line in out.splitlines() if line.strip()]

    return snapshot


def _check_ping(target: str, count: int = 2, timeout: int = 3) -> Tuple[bool, str]:
    """Pinget ein Ziel an und liefert Latenz oder Fehler."""
    out, err, code = run_cmd(f"ping -c {count} -W {timeout} {target}", timeout=timeout + 2)
    if code == 0:
        for line in out.splitlines():
            if "rtt min/avg/max" in line or "round-trip min/avg/max" in line:
                stats = line.split("=")[1].strip().split("/")[1]
                return True, f"{stats} ms"
        return True, "Erreichbar"
    return False, "Keine Antwort / Paketverlust"


def _check_dns(domain: str, server: Optional[str] = None) -> Tuple[bool, str]:
    """Prüft DNS-Auflösung via dig oder socket."""
    if server and shutil.which("dig"):
        out, err, code = run_cmd(f"dig +short +time=2 +tries=1 @{server} {domain}")
        if code == 0 and out.strip():
            first_ip = out.strip().splitlines()[0]
            return True, first_ip
        return False, "Auflösung fehlgeschlagen"
    else:
        try:
            ip = socket.gethostbyname(domain)
            return True, ip
        except Exception:
            return False, "Auflösung fehlgeschlagen"


def _check_http(url: str = "http://connectivitycheck.gstatic.com/generate_204", timeout: int = 3) -> Tuple[bool, str]:
    """Prüft HTTP Internetverbindung / Captive Portal."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "CachyOS-Control-Center/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.status == 204 or response.status == 200:
                return True, "Online (HTTP 204 OK)"
            return False, f"HTTP Status {response.status}"
    except Exception as exc:
        return False, f"Offline ({exc})"


def run_diagnostic_profile(profile: str = "quick") -> DiagnosticResult:
    """Führt ein Diagnoseprofil (quick, standard, deep) aus."""
    start_time = time.time()
    items: List[DiagnosticItem] = []

    # 1. Gateway Ping
    gw_out, _, _ = run_cmd("ip route show default | awk '{print $3}' | head -n1")
    gateway = gw_out.strip()
    if gateway:
        gw_ok, gw_lat = _check_ping(gateway)
        items.append(
            DiagnosticItem(
                category="Lokales Netzwerk (LAN)",
                test_name="Default Gateway RTT",
                status="PASS" if gw_ok else "FAIL",
                metric_value=gw_lat,
                details=f"Gateway IP: {gateway}",
                recommendation="" if gw_ok else "LAN-Kabel oder WLAN-Verbindung zum Router prüfen.",
            )
        )
    else:
        items.append(
            DiagnosticItem(
                category="Lokales Netzwerk (LAN)",
                test_name="Default Gateway RTT",
                status="FAIL",
                metric_value="Keine Route",
                details="Kein Standard-Gateway konfiguriert",
                recommendation="Netzwerkverbindung aktivieren.",
            )
        )

    # 2. DNS Auflösung
    dns_ok, dns_val = _check_dns("archlinux.org")
    items.append(
        DiagnosticItem(
            category="DNS Resolution",
            test_name="System DNS Resolver",
            status="PASS" if dns_ok else "FAIL",
            metric_value=dns_val,
            details="Abfrage von archlinux.org",
            recommendation="" if dns_ok else "DNS-Konfiguration in /etc/resolv.conf prüfen.",
        )
    )

    # 3. Internet Connectivity
    http_ok, http_res = _check_http()
    items.append(
        DiagnosticItem(
            category="Internet WAN",
            test_name="HTTP Connectivity",
            status="PASS" if http_ok else "FAIL",
            metric_value=http_res,
            details="Google 204 Connectivity Check",
            recommendation="" if http_ok else "Prüfen ob Internetverbindung oder Captive Portal aktiv ist.",
        )
    )

    # 4. Tailscale State
    if shutil.which("tailscale"):
        ts_out, _, ts_code = run_cmd("tailscale status --json | grep -o '\"BackendState\":\"[^\"]*\"'")
        ts_state = ts_out.split(":")[-1].replace('"', '') if ts_out else "Inaktiv"
        items.append(
            DiagnosticItem(
                category="Tailscale Mesh",
                test_name="Daemon State",
                status="PASS" if ts_state.lower() == "running" else "WARN",
                metric_value=ts_state or "Stopped",
                details="WireGuard Virtual Interface",
                recommendation="" if ts_state.lower() == "running" else "tailscale up ausführen falls Mesh gewünscht.",
            )
        )

    fails = sum(1 for it in items if it.status == "FAIL")
    warns = sum(1 for it in items if it.status == "WARN")
    health = "CRITICAL" if fails > 0 else ("DEGRADED" if warns > 0 else "HEALTHY")

    return DiagnosticResult(
        profile=profile,
        overall_health=health,
        items=items,
        duration_seconds=round(time.time() - start_time, 2),
    )


def generate_full_audit_json() -> Dict[str, Any]:
    """Generiert einen vollständigen System-Audit-Bericht als strukturiertes JSON."""
    from .kernel_driver import detect_gpu_devices, list_cachyos_kernels
    from .hardware_power import get_complete_power_profile
    from .maintenance import find_pacnew_files, get_orphan_packages, get_pacman_cache_size, check_available_updates

    telemetry = get_system_telemetry()
    installed_k, available_k = list_cachyos_kernels()
    gpus = detect_gpu_devices()
    power = get_complete_power_profile()
    diag = run_diagnostic_profile("quick")
    boot_time = get_boot_time_analysis()
    hw_snap = get_hardware_snapshot()
    update_count, update_msg = check_available_updates()

    return {
        "timestamp": telemetry.timestamp,
        "system": {
            "hostname": telemetry.hostname,
            "os_name": telemetry.os_name,
            "kernel": telemetry.kernel,
            "architecture": telemetry.architecture,
            "uptime": telemetry.uptime_str,
            "cpu_cores": telemetry.cpu_cores,
            "cpu_usage_percent": telemetry.cpu_percent,
            "ram_total_gb": telemetry.ram_total_gb,
            "ram_used_gb": telemetry.ram_used_gb,
            "ram_percent": telemetry.ram_percent,
            "disk_total_gb": telemetry.disk_total_gb,
            "disk_used_gb": telemetry.disk_used_gb,
            "disk_percent": telemetry.disk_percent,
            "is_btrfs": telemetry.is_btrfs,
            "failed_system_units": telemetry.failed_system_units,
            "failed_user_units": telemetry.failed_user_units,
            "failed_unit_names": telemetry.failed_unit_names,
        },
        "hardware": hw_snap,
        "boot": {
            "cmdline": get_boot_cmdline(),
            "boot_time": boot_time,
        },
        "kernels": {
            "running": telemetry.kernel,
            "installed": [asdict(k) for k in installed_k],
            "available": [asdict(k) for k in available_k],
        },
        "gpus": [asdict(g) for g in gpus],
        "power_and_thermals": {
            "governor": power.cpu.current_governor,
            "available_governors": power.cpu.available_governors,
            "epp": power.cpu.current_epp,
            "available_epp": power.cpu.available_epp,
            "is_throttled": power.is_throttled,
            "throttle_message": power.throttle_message,
            "thermal_zones": [asdict(z) for z in power.thermals],
        },
        "maintenance": {
            "cache_size": get_pacman_cache_size(),
            "orphan_packages": get_orphan_packages(),
            "pacnew_files": find_pacnew_files(),
            "available_updates": update_count,
            "update_message": update_msg,
        },
        "network_diagnostics": {
            "health": diag.overall_health,
            "items": [asdict(it) for it in diag.items],
        },
    }
