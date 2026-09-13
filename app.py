#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
 CACHYOS CONTROL CENTER — Standard Entry Point
 Startet das modulare TUI-Kontrollzentrum oder Standalone CLI-Funktionen.
===============================================================================
"""

import sys
import argparse
from pathlib import Path

# Pfade hinzufügen
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from cachyos_center import CachyOSCenterApp
from core.diagnostics import run_diagnostic_profile
from core.system import get_system_telemetry


def main() -> None:
    parser = argparse.ArgumentParser(
        description="CachyOS Ultimate Control Center & System Architect",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--diag", choices=["quick", "standard", "deep"], help="Führt eine direkte CLI-Netzwerkdiagnose durch")
    parser.add_argument("--status", action="store_true", help="Zeigt System-Telemetrie und Hardwaredaten als CLI-Ausgabe")
    parser.add_argument("--maint", action="store_true", help="Führt eine schnelle CLI-Wartungs- und Pacnew-Prüfung durch")
    parser.add_argument("--version", action="version", version="CachyOS Control Center 10.0.0 (Masterpiece Edition 2026)")

    args = parser.parse_args()

    if args.diag:
        print(f"=== CachyOS Netzwerkdiagnose ({args.diag}) ===")
        res = run_diagnostic_profile(args.diag)
        print(f"Gesamtzustand: {res.overall_health} ({res.duration_seconds}s)")
        for item in res.items:
            print(f"[{item.status}] {item.category} -> {item.test_name}: {item.metric_value}")
            if item.recommendation:
                print(f"     Tipp: {item.recommendation}")
    elif args.maint:
        from core.maintenance import find_pacnew_files, check_available_updates
        print("=== CachyOS Systemhygiene & Wartungsprüfung ===")
        pacnews = find_pacnew_files()
        print(f".pacnew Konflikte in /etc: {len(pacnews)}")
        for p in pacnews:
            print(f"  • {p}")
        count, msg = check_available_updates()
        print(f"Paket-Updates: {msg}")
    elif args.status:
        t = get_system_telemetry()
        print(f"Host:    {t.hostname} ({t.os_name} {t.architecture})")
        print(f"Kernel:  {t.kernel}")
        print(f"Uptime:  {t.uptime_str}")
        print(f"CPU:     {t.cpu_percent}% ({t.cpu_cores} Kerne)")
        print(f"RAM:     {t.ram_used_gb} / {t.ram_total_gb} GB ({t.ram_percent}%)")
        print(f"Disk:    {t.disk_used_gb} / {t.disk_total_gb} GB ({t.disk_percent}%) [BTRFS: {t.is_btrfs}]")
        print(f"Failed Units: System={t.failed_system_units}, User={t.failed_user_units}")
    else:
        app = CachyOSCenterApp()
        app.run()


if __name__ == "__main__":
    main()
