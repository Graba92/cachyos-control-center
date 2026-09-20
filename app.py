#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
 CACHYOS CONTROL CENTER — Standard Entry Point & Automation CLI
 Führt das interaktive TUI-Cockpit oder Headless-Subcommands aus:
 --status, --clean, --json, --diag, --lang
===============================================================================
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# Pfade zur Laufzeit hinzufügen
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from core.i18n import t, set_language, get_language
from core.config import load_config, save_user_config
from core.system import get_system_telemetry
from core.kernel_driver import get_running_kernel, list_cachyos_kernels, detect_gpu_devices
from core.hardware_power import get_complete_power_profile
from core.maintenance import clean_pacman_cache, remove_orphan_packages, run_fstrim, get_pacman_cache_size, get_orphan_packages, check_available_updates
from core.diagnostics import run_diagnostic_profile, generate_full_audit_json, get_boot_time_analysis


def handle_cli_status() -> int:
    """Gibt einen formatierten System-, Kernel- und Hardwareüberblick im Terminal aus."""
    t_data = get_system_telemetry()
    running_k = get_running_kernel()
    gpus = detect_gpu_devices()
    power = get_complete_power_profile()
    cache_sz = get_pacman_cache_size()
    orphans = get_orphan_packages()
    boot_time = get_boot_time_analysis()
    up_count, up_msg = check_available_updates()

    print("\n" + "=" * 70)
    print(f" {t('cli_header_telemetry')}")
    print("=" * 70)
    print(f" {t('hostname')}:       {t_data.hostname}")
    print(f" {t('cli_os')}: {t_data.os_name} ({t_data.architecture})")
    print(f" {t('cli_active_kernel')}: {running_k}")
    print(f" {t('cli_uptime')}:   {t_data.uptime_str}")
    print(f" {t('cli_boot_time')}:     {boot_time.get('summary', 'N/A')}")
    print("-" * 70)
    print(f" {t('cli_cpu_usage')}: {t_data.cpu_percent}% ({t_data.cpu_cores} {t('cli_cores')})")
    print(f" {t('cli_cpu_gov')}:   {power.cpu.current_governor} ({t('cli_available')}: {', '.join(power.cpu.available_governors)})")
    if power.cpu.current_epp:
        print(f" {t('cli_epp')}:     {power.cpu.current_epp}")
    throttling_str = t('cli_throttling_no') if not power.is_throttled else f"{t('cli_throttling_yes')} - {power.throttle_message}"
    print(f" {t('cli_throttling')}:     {throttling_str}")
    print("-" * 70)
    print(f" {t('cli_ram')}:            {t_data.ram_used_gb} / {t_data.ram_total_gb} GB ({t_data.ram_percent}%)")
    print(f" {t('cli_root_storage')}:  {t_data.disk_used_gb} / {t_data.disk_total_gb} GB ({t_data.disk_percent}%) [BTRFS: {t_data.is_btrfs}]")
    print("-" * 70)
    print(f" {t('cli_pacman_cache')}:   {cache_sz}")
    print(f" {t('cli_orphan_pkgs')}:   {len(orphans)} {t('cli_orphan_unused')}")
    print(f" {t('cli_pkg_updates')}:  {up_msg}")
    print(f" {t('cli_failed_units')}:   System={t_data.failed_system_units}, User={t_data.failed_user_units}")
    if gpus:
        print("-" * 70)
        print(f" {t('cli_gpus')}:")
        for g in gpus:
            extra = []
            if g.temperature_c is not None:
                extra.append(f"{g.temperature_c}°C")
            if g.power_draw_w is not None:
                extra.append(f"{g.power_draw_w}W")
            extra_str = f" [{', '.join(extra)}]" if extra else ""
            driver_type = t('cli_proprietary') if g.is_proprietary else t('cli_open')
            print(f"  • {g.device_name} ({t('cli_driver')}: {g.active_driver}, {driver_type}){extra_str}")
    print("=" * 70 + "\n")
    return 0


def handle_cli_clean() -> int:
    """Triggert die headless Cache- und Waisenpaket-Bereinigung."""
    print("\n[INFO] Starte autonome Systemhygiene...")
    cache_before = get_pacman_cache_size()
    orphans_before = get_orphan_packages()
    print(f" • Pacman Cache vor Bereinigung: {cache_before}")
    print(f" • Waisenpakete vor Bereinigung: {len(orphans_before)}")

    print("\n1. Bereinige Pacman Paket-Cache (paccache -r -k 2)...")
    ok_cache, msg_cache = clean_pacman_cache(keep_versions=2)
    print(f"   Status: {'[ERFOLG]' if ok_cache else '[FEHLER]'} {msg_cache}")

    print("\n2. Entferne Waisenpakete (pacman -Rns)...")
    ok_orph, msg_orph = remove_orphan_packages()
    print(f"   Status: {'[ERFOLG]' if ok_orph else '[FEHLER]'} {msg_orph}")

    print("\n3. Führe SSD TRIM (fstrim -av) aus...")
    ok_trim, msg_trim = run_fstrim()
    print(f"   Status: {'[ERFOLG]' if ok_trim else '[FEHLER]'} {msg_trim}")

    print("\n[FERTIG] Systemhygiene abgeschlossen.\n")
    return 0 if (ok_cache and ok_orph and ok_trim) else 1


def handle_cli_json() -> int:
    """Gibt den vollständigen Systemaudit im maschinenlesbaren JSON-Format aus."""
    audit_data = generate_full_audit_json()
    print(json.dumps(audit_data, indent=2, ensure_ascii=False))
    return 0


def handle_cli_diag(profile: str) -> int:
    """Führt die direkte Netzwerk- und Latenzdiagnose aus."""
    print(f"\n=== CachyOS System- & Netzwerkdiagnose (Profil: {profile}) ===")
    res = run_diagnostic_profile(profile)
    print(f"Gesamtzustand: {res.overall_health} (Dauer: {res.duration_seconds}s)\n")
    for item in res.items:
        print(f"[{item.status}] {item.category} -> {item.test_name}: {item.metric_value}")
        if item.details:
            print(f"     Details: {item.details}")
        if item.recommendation:
            print(f"     Tipp:    {item.recommendation}")
    print()
    return 0 if res.overall_health == "HEALTHY" else 1


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="cachyos-control-center",
        description="CachyOS Control Center & Unified System Administrator (TUI & Headless CLI)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  cachyos-control-center              # Startet das interaktive TUI-Cockpit
  cachyos-control-center --status     # Schnelle Systemübersicht im Terminal
  cachyos-control-center --clean      # Führt Cache- & Waisenbereinigung via Polkit aus
  cachyos-control-center --json       # Vollständiger Systemaudit als JSON
  cachyos-control-center --diag quick # Führt Netzwerk- & Latenztests durch
  cachyos-control-center --lang de    # Setzt die Standardsprache auf Deutsch
        """,
    )
    parser.add_argument("--status", action="store_true", help="Zeigt System-Telemetrie, Kernel und Hardware als CLI-Übersicht")
    parser.add_argument("--clean", action="store_true", help="Führt Cache-Bereinigung und Waisenpaket-Entfernung headless aus")
    parser.add_argument("--json", action="store_true", help="Gibt einen vollständigen Systemaudit als JSON aus")
    parser.add_argument("--diag", choices=["quick", "standard", "deep"], help="Führt eine direkte CLI-Netzwerkdiagnose durch")
    parser.add_argument("--lang", choices=["de", "en"], help="Setzt die bevorzugte Sprache (de_DE oder en_US)")
    parser.add_argument("--version", action="version", version="CachyOS Control Center 1.0.0 (Unified 2026 Edition)")

    args = parser.parse_args()

    cfg = load_config()

    if args.lang:
        set_language(args.lang)
        cfg.setdefault("general", {})["language"] = args.lang
        save_user_config(cfg)
        if not (args.status or args.clean or args.json or args.diag):
            print(f"[OK] Sprache dauerhaft auf '{args.lang}' gesetzt.")
            sys.exit(0)
    else:
        # Sprache aus Config anwenden
        set_language(cfg.get("general", {}).get("language", "de"))

    if args.status:
        sys.exit(handle_cli_status())
    elif args.clean:
        sys.exit(handle_cli_clean())
    elif args.json:
        sys.exit(handle_cli_json())
    elif args.diag:
        sys.exit(handle_cli_diag(args.diag))
    else:
        # TUI App starten
        from cachyos_center import CachyOSCenterApp
        app = CachyOSCenterApp()
        app.run()


if __name__ == "__main__":
    main()
