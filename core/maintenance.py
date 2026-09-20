#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
 CachyOS Control Center — Maintenance & System Care Engine
 Pacman/Paru/Yay Mirror-Benchmarking, Cache-Cleaning, Waisen-Entfernung,
 .pacnew Audits, SSD-TRIM & Systemd Journal Management
===============================================================================
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import List, Tuple

from .i18n import t
from .polkit import (
    is_pacman_locked,
    polkit_clean_cache,
    polkit_remove_orphans,
    polkit_run_mirror_bench,
    run_polkit_cmd,
)


def get_pacman_cache_size() -> str:
    """Ermittelt den aktuellen Festplattenverbrauch des Pacman-Paketcaches."""
    cache_path = Path("/var/cache/pacman/pkg")
    if not cache_path.exists():
        return "0 MB"
    try:
        res = subprocess.run(["du", "-sh", str(cache_path)], capture_output=True, text=True, timeout=5)
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout.split()[0]
    except Exception:
        pass
    return "N/A"


def clean_pacman_cache(keep_versions: int = 2) -> Tuple[bool, str]:
    """Bereinigt den Pacman Paket-Cache via Polkit."""
    return polkit_clean_cache(keep_versions)


def get_orphan_packages() -> List[str]:
    """Sucht nach unbenutzten verwaisten Paketen (pacman -Qtdq)."""
    try:
        res = subprocess.run(["pacman", "-Qtdq"], capture_output=True, text=True, timeout=10)
        # pacman gibt Exitcode 1 zurück, wenn keine Waisen gefunden werden
        if res.returncode == 0 and res.stdout.strip():
            return [pkg.strip() for pkg in res.stdout.splitlines() if pkg.strip()]
    except Exception:
        pass
    return []


def remove_orphan_packages() -> Tuple[bool, str]:
    """Entfernt alle verwaisten Pakete rückstandslos via Polkit."""
    orphans = get_orphan_packages()
    if not orphans:
        return True, t("no_orphans_found")
    return polkit_remove_orphans(orphans)


def benchmark_mirrors() -> Tuple[bool, str]:
    """Führt ein Mirror-Benchmarking für schnellste Download-Raten durch."""
    return polkit_run_mirror_bench()


def vacuum_journal(size: str = "50M") -> Tuple[bool, str]:
    """Trimmt Systemd-Journal Logs auf die angegebene Maximalgröße."""
    ok, msg, _ = run_polkit_cmd(f"journalctl --vacuum-size={size}", timeout=25)
    return ok, msg


def find_pacnew_files() -> List[str]:
    """Sucht nach ungemergten .pacnew Dateien unter /etc."""
    pacnews: List[str] = []
    # Schneller pacdiff Check oder defensiver find
    try:
        if shutil.which("pacdiff"):
            res = subprocess.run(["pacdiff", "-o"], capture_output=True, text=True, timeout=8)
            if res.returncode == 0 and res.stdout.strip():
                for line in res.stdout.splitlines():
                    if line.strip():
                        pacnews.append(line.strip())
        if not pacnews:
            res2 = subprocess.run(["find", "/etc", "-name", "*.pacnew"], capture_output=True, text=True, timeout=8)
            if res2.returncode == 0 and res2.stdout.strip():
                for line in res2.stdout.splitlines():
                    if line.strip():
                        pacnews.append(line.strip())
    except Exception:
        pass
    return sorted(list(set(pacnews)))


def reset_failed_units() -> Tuple[bool, str]:
    """Setzt fehlgeschlagene System- und User-Systemd-Units zurück."""
    sys_ok, sys_msg, _ = run_polkit_cmd("systemctl reset-failed", timeout=10)
    usr_res = subprocess.run(["systemctl", "--user", "reset-failed"], capture_output=True, text=True)
    msg = f"Systemd Reset abgeschlossen.\nSystem: {sys_msg}\nUser: {usr_res.stdout.strip() or 'OK'}"
    return True, msg


def run_fstrim() -> Tuple[bool, str]:
    """Führt SSD TRIM auf allen gemounteten Dateisystemen aus."""
    ok, msg, _ = run_polkit_cmd("fstrim -av", timeout=60)
    return ok, msg


def check_available_updates() -> Tuple[int, str]:
    """Prüft auf anstehende Systemupdates ohne Installation."""
    if shutil.which("checkupdates"):
        try:
            res = subprocess.run(["checkupdates"], capture_output=True, text=True, timeout=25)
            if res.returncode == 0 and res.stdout.strip():
                lines = res.stdout.strip().splitlines()
                return len(lines), f"{len(lines)} Pakete können aktualisiert werden."
            return 0, "System ist auf dem aktuellsten Stand."
        except Exception:
            return 0, "Fehler bei der Updateprüfung."
    return 0, "checkupdates nicht gefunden (pacman-contrib fehlt)."
