#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
 CachyOS Control Center — Maintenance & System Care Engine
 CachyOS / Arch Linux Hygiene, Pacnew Audits, Cache Trimming & Unit Resets
===============================================================================
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .system import run_cmd


def clean_pacman_cache() -> Tuple[bool, str]:
    """Bereinigt den Pacman Paket-Cache via paccache oder pacman -Sc."""
    if shutil.which("paccache"):
        out, err, code = run_cmd("pkexec paccache -r -k 2")
        if code == 0:
            return True, f"Pacman Cache erfolgreich bereinigt (2 Versionen behalten):\n{out}"
    out, err, code = run_cmd("pkexec pacman -Sc --noconfirm")
    if code == 0:
        return True, f"Pacman Cache bereinigt:\n{out}"
    return False, f"Fehler bei Cache-Bereinigung: {err or out}"


def vacuum_journal(size: str = "50M") -> Tuple[bool, str]:
    """Trimmt Systemd-Journal Logs auf die angegebene Maximalgröße."""
    out, err, code = run_cmd(f"pkexec journalctl --vacuum-size={size}")
    if code == 0:
        return True, f"Journal erfolgreich auf {size} getrimmt:\n{out}"
    return False, f"Fehler beim Trimmen des Journals: {err or out}"


def find_pacnew_files() -> List[str]:
    """Sucht nach ungemergten .pacnew Dateien unter /etc."""
    pacnews: List[str] = []
    out, _, code = run_cmd("pacdiff -o 2>/dev/null || find /etc -name '*.pacnew' 2>/dev/null", timeout=10)
    for line in out.splitlines():
        line = line.strip()
        if line and line.endswith(".pacnew"):
            pacnews.append(line)
    return sorted(list(set(pacnews)))


def reset_failed_units() -> Tuple[bool, str]:
    """Setzt fehlgeschlagene System- und User-Systemd-Units zurück."""
    sys_out, sys_err, sys_code = run_cmd("pkexec systemctl reset-failed")
    usr_out, usr_err, usr_code = run_cmd("systemctl --user reset-failed")

    msg = f"Systemd Reset abgeschlossen.\nSystem: {sys_out or 'OK'}\nUser: {usr_out or 'OK'}"
    return True, msg


def run_fstrim() -> Tuple[bool, str]:
    """Führt SSD TRIM auf allen gemounteten Dateisystemen aus."""
    out, err, code = run_cmd("pkexec fstrim -av")
    if code == 0:
        return True, f"SSD TRIM erfolgreich ausgeführt:\n{out}"
    return False, f"Fehler bei fstrim: {err or out}"


def check_available_updates() -> Tuple[int, str]:
    """Prüft auf anstehende Systemupdates ohne Installation."""
    if shutil.which("checkupdates"):
        out, err, code = run_cmd("checkupdates", timeout=25)
        if code == 0 and out.strip():
            count = len(out.strip().splitlines())
            return count, f"{count} Pakete können aktualisiert werden."
        return 0, "System ist auf dem aktuellsten Stand."
    return 0, "checkupdates nicht gefunden (pacman-contrib fehlt)."
