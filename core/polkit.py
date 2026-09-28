#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
 CachyOS Control Center — Polkit & Privilege Isolation Engine
 Führt administrative Aufgaben strikt isoliert über pkexec / Polkit-Aktionen aus.
 UI läuft uneingeschränkt unprivilegiert als normaler Nutzer.
===============================================================================
"""

from __future__ import annotations

import glob
import os
import shlex
import shutil
import subprocess
import time
from pathlib import Path
from typing import List, Optional, Tuple, Union

from .i18n import t


PACMAN_LOCK_FILE = Path("/var/lib/pacman/db.lck")


def is_pacman_locked() -> bool:
    """Prüft, ob die Pacman-Datenbank aktuell durch einen anderen Prozess gesperrt ist."""
    return PACMAN_LOCK_FILE.exists()


def run_polkit_cmd(
    cmd: Union[str, List[str]],
    timeout: int = 45,
    check_pacman_lock: bool = False,
    input_data: Optional[str] = None,
) -> Tuple[bool, str, int]:
    """
    Führt einen administrativen Befehl defensiv mit pkexec aus.
    Verwendet strikt shell=False und tokenisierte Argumentlisten,
    um Command-Injection in den Root-Bereich absolut auszuschließen.
    Rückgabe: (erfolgreich: bool, ausgabe/fehlermeldung: str, returncode: int)
    """
    # Wenn Pacman-Befehl und db.lck existiert, sofort warnen
    if check_pacman_lock and is_pacman_locked():
        return False, t("db_lock_warn"), 1

    # Argumente als Liste sicherstellen (kein shell=True)
    if isinstance(cmd, str):
        args = shlex.split(cmd)
    else:
        args = [str(a) for a in cmd]

    if not args:
        return False, "Leerer Befehl übergeben.", 1

    # Wenn bereits Root (z. B. CLI als sudo), kein pkexec voranstellen
    if os.geteuid() == 0:
        full_cmd = args
    else:
        if not shutil.which("pkexec"):
            return False, "Fehler: 'pkexec' ist nicht installiert oder im PATH nicht verfügbar.", 127
        full_cmd = ["pkexec"] + args

    try:
        res = subprocess.run(
            full_cmd,
            shell=False,
            text=True,
            input=input_data,
            capture_output=True,
            timeout=timeout,
        )
        out = res.stdout.strip()
        err = res.stderr.strip()

        # Polkit Abbruch durch Nutzer (Exit 126 oder stderr Text)
        if res.returncode == 126 or "dismissed" in err.lower() or "not authorized" in err.lower():
            return False, t("polkit_dismissed"), 126

        if res.returncode != 0:
            err_msg = err or out or f"Befehl mit Exit-Code {res.returncode} beendet."
            return False, f"Fehler: {err_msg}", res.returncode

        return True, out or t("polkit_success"), 0

    except subprocess.TimeoutExpired:
        return False, t("polkit_timeout"), 124
    except Exception as exc:
        return False, f"Systemfehler bei Polkit-Ausführung: {exc}", 1


# Granulare Standard-Aktionen
def polkit_clean_cache(keep_versions: int = 2) -> Tuple[bool, str]:
    """Bereinigt den Pacman Paket-Cache via paccache oder pacman -Sc."""
    if is_pacman_locked():
        return False, t("db_lock_warn")

    if shutil.which("paccache"):
        cmd = ["paccache", "-r", "-k", str(int(keep_versions))]
        ok, msg, _ = run_polkit_cmd(cmd, timeout=30, check_pacman_lock=True)
        if ok:
            return True, f"Pacman Cache erfolgreich bereinigt (k={keep_versions}):\n{msg}"

    cmd = ["pacman", "-Sc", "--noconfirm"]
    ok, msg, _ = run_polkit_cmd(cmd, timeout=30, check_pacman_lock=True)
    return ok, msg


def polkit_remove_orphans(orphan_list: list[str]) -> Tuple[bool, str]:
    """Entfernt verwaiste Pakete über pacman -Rns."""
    if not orphan_list:
        return True, t("no_orphans_found")

    if is_pacman_locked():
        return False, t("db_lock_warn")

    # Nur saubere Paketnamen ohne Sonderzeichen erlauben
    clean_pkgs = [p.strip() for p in orphan_list if p.strip().replace("-", "").replace("_", "").replace(".", "").isalnum()]
    if not clean_pkgs:
        return False, "Keine gültigen Paketnamen zum Entfernen angegeben."

    cmd = ["pacman", "-Rns", "--noconfirm"] + clean_pkgs
    ok, msg, _ = run_polkit_cmd(cmd, timeout=60, check_pacman_lock=True)
    return ok, msg


def polkit_service_action(service_name: str, action: str) -> Tuple[bool, str]:
    """
    Steuert Systemd-Dienste (start, stop, restart, enable, disable).
    Validiert Service-Namen gegen Injection.
    """
    allowed_actions = {"start", "stop", "restart", "enable", "disable", "reload"}
    if action not in allowed_actions:
        return False, f"Ungültige Service-Aktion: {action}"

    # Bereinigung des Servicenamens
    clean_srv = service_name.strip()
    if not clean_srv.replace(".", "").replace("-", "").replace("@", "").replace("_", "").isalnum():
        return False, f"Ungültiger Service-Name: {service_name}"

    cmd = ["systemctl", action, clean_srv]
    ok, msg, _ = run_polkit_cmd(cmd, timeout=20)
    return ok, msg


def polkit_set_cpu_governor(governor: str) -> Tuple[bool, str]:
    """
    Setzt den CPU Governor für alle Kerne.
    Nutzt 'tee' ohne Shell-Interpolation (kein sh -c / shell=True).
    """
    clean_gov = governor.strip()
    if not clean_gov.replace("_", "").isalnum():
        return False, f"Ungültiger Governor: {governor}"

    paths = sorted(glob.glob("/sys/devices/system/cpu/cpu*/cpufreq/scaling_governor"))
    if not paths:
        return False, "Keine CPU cpufreq scaling_governor Schnittstellen gefunden."

    cmd = ["tee"] + paths
    ok, msg, _ = run_polkit_cmd(cmd, timeout=10, input_data=f"{clean_gov}\n")
    return ok, f"Governor '{clean_gov}' für {len(paths)} Kerne gesetzt." if ok else msg


def polkit_set_epp_preference(preference: str) -> Tuple[bool, str]:
    """
    Setzt das Energy Performance Preference (EPP) Profil für alle Cores.
    Nutzt 'tee' ohne Shell-Interpolation (kein sh -c / shell=True).
    """
    clean_pref = preference.strip()
    if not clean_pref.replace("_", "").isalnum():
        return False, f"Ungültige EPP-Präferenz: {preference}"

    paths = sorted(glob.glob("/sys/devices/system/cpu/cpu*/cpufreq/energy_performance_preference"))
    if not paths:
        return False, "Keine CPU EPP Schnittstellen gefunden."

    cmd = ["tee"] + paths
    ok, msg, _ = run_polkit_cmd(cmd, timeout=10, input_data=f"{clean_pref}\n")
    return ok, f"EPP '{clean_pref}' für {len(paths)} Kerne gesetzt." if ok else msg


def polkit_run_mirror_bench() -> Tuple[bool, str]:
    """Führt CachyOS Mirror Ranking über cachyos-rate-mirrors oder rate-mirrors aus."""
    if is_pacman_locked():
        return False, t("db_lock_warn")

    if shutil.which("cachyos-rate-mirrors"):
        cmd = ["cachyos-rate-mirrors"]
        ok, msg, _ = run_polkit_cmd(cmd, timeout=120, check_pacman_lock=True)
        return ok, msg
    elif shutil.which("rate-mirrors"):
        cmd = ["rate-mirrors", "--save=/etc/pacman.d/cachyos-mirrorlist", "cachyos"]
        ok, msg, _ = run_polkit_cmd(cmd, timeout=120, check_pacman_lock=True)
        return ok, msg
    else:
        return False, "Weder 'cachyos-rate-mirrors' noch 'rate-mirrors' gefunden. Bitte installieren mit: sudo pacman -S cachyos-rate-mirrors"

