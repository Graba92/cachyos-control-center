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
from dataclasses import dataclass
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


@dataclass
class MaintenanceTimer:
    name: str
    service: str
    active: bool
    enabled: bool
    description: str
    next_trigger: str = "-"
    last_trigger: str = "-"


def vacuum_journal(size: str = "50M") -> Tuple[bool, str]:
    """Trimmt Systemd-Journal Logs auf die angegebene Maximalgröße."""
    clean_sz = size.strip()
    if not clean_sz.isalnum():
        clean_sz = "50M"
    ok, msg, _ = run_polkit_cmd(["journalctl", f"--vacuum-size={clean_sz}"], timeout=25)
    return ok, msg


def find_pacnew_files() -> List[str]:
    """Sucht nach ungemergten .pacnew Dateien unter /etc."""
    pacnews: List[str] = []
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
    sys_ok, sys_msg, _ = run_polkit_cmd(["systemctl", "reset-failed"], timeout=10)
    usr_res = subprocess.run(["systemctl", "--user", "reset-failed"], capture_output=True, text=True)
    msg = f"Systemd Reset abgeschlossen.\nSystem: {sys_msg}\nUser: {usr_res.stdout.strip() or 'OK'}"
    return True, msg


def run_fstrim() -> Tuple[bool, str]:
    """Führt SSD TRIM auf allen gemounteten Dateisystemen aus."""
    ok, msg, _ = run_polkit_cmd(["fstrim", "-av"], timeout=60)
    return ok, msg


def get_maintenance_timers() -> List[MaintenanceTimer]:
    """
    Überwacht automatische Systemd-Wartungs-Timer (fstrim.timer, paccache.timer, plocate-updatedb.timer).
    Echte Systempflege läuft über automatisierte Hintergrund-Timer.
    """
    timer_definitions = [
        ("fstrim.timer", "fstrim.service", "Wöchentlicher automatischer SSD TRIM"),
        ("paccache.timer", "paccache.service", "Wöchentliche Pacman-Cache-Bereinigung"),
        ("plocate-updatedb.timer", "plocate-updatedb.service", "Tägliche Datei-Indexierung"),
        ("shadow.timer", "shadow.service", "Regelmäßige Passwort-/Account-Integritätsprüfung"),
    ]

    timers: List[MaintenanceTimer] = []
    for t_name, s_name, desc in timer_definitions:
        res_act = subprocess.run(["systemctl", "is-active", t_name], capture_output=True, text=True)
        is_active = res_act.stdout.strip() == "active"

        res_en = subprocess.run(["systemctl", "is-enabled", t_name], capture_output=True, text=True)
        is_enabled = res_en.stdout.strip() == "enabled"

        next_trig = "-"
        last_trig = "-"
        # Timer details aus systemctl show auslesen
        res_show = subprocess.run(
            ["systemctl", "show", t_name, "-p", "NextElapseUSecRealtime", "-p", "LastTriggerUSec"],
            capture_output=True,
            text=True,
        )
        if res_show.returncode == 0:
            for l in res_show.stdout.splitlines():
                if l.startswith("NextElapseUSecRealtime=") and not l.endswith("=0"):
                    val = l.split("=", 1)[1].strip()
                    if val and val != "N/A":
                        next_trig = "Aktiviert / Geplant"
                elif l.startswith("LastTriggerUSec=") and not l.endswith("=0"):
                    val = l.split("=", 1)[1].strip()
                    if val and val != "N/A":
                        last_trig = "Kürzlich ausgeführt"

        timers.append(
            MaintenanceTimer(
                name=t_name,
                service=s_name,
                active=is_active,
                enabled=is_enabled,
                description=desc,
                next_trigger=next_trig,
                last_trigger=last_trig,
            )
        )
    return timers


def toggle_maintenance_timer(timer_name: str, enable: bool) -> Tuple[bool, str]:
    """
    Aktiviert oder deaktiviert einen Systemd-Hintergrund-Wartungstimer (z. B. fstrim.timer, paccache.timer).
    """
    clean_timer = timer_name.strip()
    if not clean_timer.endswith(".timer") or not clean_timer.replace(".", "").replace("-", "").replace("_", "").isalnum():
        return False, f"Ungültiger Timer-Name: {timer_name}"

    action = "enable" if enable else "disable"
    cmd = ["systemctl", action, "--now", clean_timer]
    ok, msg, _ = run_polkit_cmd(cmd, timeout=20)
    status_str = "aktiviert und gestartet" if enable else "deaktiviert und gestoppt"
    return ok, f"Timer '{clean_timer}' erfolgreich {status_str}." if ok else msg


def check_available_updates(timeout: int = 10) -> Tuple[int, str]:
    """
    Prüft auf anstehende Systemupdates ohne Installation.
    Fängt Timeouts und korrupte /tmp/checkup-db Verzeichnisse defensiv ab.
    """
    if not shutil.which("checkupdates"):
        return 0, "checkupdates nicht gefunden (pacman-contrib fehlt)."

    try:
        res = subprocess.run(["checkupdates"], capture_output=True, text=True, timeout=timeout)
        if res.returncode == 0 and res.stdout.strip():
            lines = res.stdout.strip().splitlines()
            return len(lines), f"{len(lines)} Pakete können aktualisiert werden."
        elif res.returncode == 0:
            return 0, "System ist auf dem aktuellsten Stand."
        else:
            # Bei Fehlern (z. B. korruptes Archiv im temporären checkup-db) Bereinigung durchführen
            try:
                uid = os.getuid()
                tmp_db = Path(f"/tmp/checkup-db-{uid}")
                if tmp_db.exists():
                    shutil.rmtree(tmp_db, ignore_errors=True)
            except Exception:
                pass
            return 0, "Updateprüfung: Temporärer Fehler (Cache bereinigt)."
    except subprocess.TimeoutExpired:
        # Bei Timeout temporäre DB ebenfalls aufräumen
        try:
            uid = os.getuid()
            tmp_db = Path(f"/tmp/checkup-db-{uid}")
            if tmp_db.exists():
                shutil.rmtree(tmp_db, ignore_errors=True)
        except Exception:
            pass
        return 0, "Updateprüfung: Zeitüberschreitung (Spiegelserver prüfen)."
    except Exception:
        return 0, "Fehler bei der Updateprüfung."

