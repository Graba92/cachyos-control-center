#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
 CachyOS Control Center — Localization (i18n) Engine
 Vollständige zweisprachige Lokalisierung (Deutsch de_DE & Englisch en_US)
 Dynamisches Umschalten zur Laufzeit für alle Dialoge, Panels & CLI
===============================================================================
"""

from __future__ import annotations

import os
from typing import Dict, Any


_STRINGS: Dict[str, Dict[str, str]] = {
    "de": {
        # App & Navigation
        "app_title": "CACHYOS CONTROL CENTER & SYSTEM ARCHITECT",
        "app_subtitle": "Professional Edition │ CachyOS Linux x86_64",
        "tab_cockpit": "1. Cockpit",
        "tab_kernel": "2. Kernel & Treiber",
        "tab_power": "3. Hardware & Power",
        "tab_maint": "4. Systemwartung",
        "tab_services": "5. Dienste",
        "tab_diag": "6. Diagnose & Logs",
        "tab_network": "7. Netzwerk & Tools",
        "btn_refresh": "Aktualisieren",
        "btn_lang_toggle": "Sprache: DE (Taste L)",
        "btn_quit": "Beenden",
        "status_ready": "Bereit",
        "status_running": "Wird ausgeführt...",
        "status_done": "Abgeschlossen",
        "status_error": "Fehlgeschlagen",
        "close": "Schließen",
        "cancel": "Abbrechen",
        "confirm": "Bestätigen",
        "apply": "Anwenden",

        # Cockpit KPI Cards
        "kpi_cpu_title": "PROZESSOR (CPU)",
        "kpi_ram_title": "ARBEITSSPEICHER (RAM)",
        "kpi_disk_title": "SYSTEMSPEICHER (/)",
        "kpi_kernel_title": "AKTIVER KERNEL",
        "kpi_health_title": "SYSTEMINTEGRITÄT",
        "kpi_cores": "{cores} Kerne",
        "kpi_used": "{used} / {total} GB belegt",
        "kpi_disk_btrfs": "BTRFS Aktiv",
        "kpi_disk_standard": "Standard FS",
        "kpi_failed_units": "{count} fehlgeschlagene Units",
        "kpi_all_clean": "Alle Einheiten fehlerfrei",
        "quick_actions": "Schnellaktionen",
        "action_cache_clean": "Paket-Cache leeren",
        "action_orphan_remove": "Waisenpakete entfernen",
        "action_trim": "SSD TRIM ausführen",
        "action_rate_mirrors": "Mirrors benchmarken",
        "action_reset_failed": "Failed Units zurücksetzen",
        "telemetry_details": "System-Telemetrie & Hardware-Zusammenfassung",
        "hostname": "Hostname",
        "os_version": "Betriebssystem",
        "uptime": "Betriebszeit",
        "arch": "Architektur",
        "db_lock_warn": "Achtung: Pacman-Datenbank ist gesperrt (/var/lib/pacman/db.lck)!",

        # Kernel & Drivers
        "kernel_mgmt_title": "CachyOS Kernel- & Treibermatrix",
        "kernel_installed": "Installierte Kernel",
        "kernel_available": "Verfügbare CachyOS Kernel (BORE, LTO, RT, BMQ)",
        "kernel_variant": "Variante",
        "kernel_status": "Status",
        "kernel_version": "Version",
        "kernel_desc": "Optimierung",
        "col_component": "Komponente",
        "col_driver": "Aktiver Treiber",
        "col_type": "Typ",
        "col_hardware": "Hardware",
        "gpu_drivers_title": "Grafikkarten & Treiberschnittstellen",
        "gpu_power_state": "Power State",
        "gpu_temp": "Temperatur",
        "gpu_power_draw": "Leistungsaufnahme",
        "action_install_kernel": "Kernel installieren",
        "action_remove_kernel": "Kernel deinstallieren",
        "active_running": "Aktiv (Laufend)",
        "installed": "Installiert",
        "available": "Verfügbar",
        "not_installed": "Nicht installiert",
        "proprietary": "Proprietär",
        "open_source": "Open Source",

        # Hardware & Power Profiles
        "power_mgmt_title": "Hardware-Tuning & Energie-Gouverneure",
        "cpu_scaling_title": "CPU Frequenz- & EPP-Steuerung",
        "current_governor": "Aktueller Governor",
        "available_governors": "Verfügbare Governors",
        "current_epp": "Aktuelles EPP-Profil",
        "available_epp": "Verfügbare EPP-Profile",
        "btn_set_gov_perf": "Performance Governor",
        "btn_set_gov_sched": "Schedutil (Standard)",
        "btn_set_gov_powersave": "Powersave Governor",
        "btn_set_epp_perf": "EPP: Performance",
        "btn_set_epp_balance": "EPP: Balance-Performance",
        "btn_set_epp_power": "EPP: Power",
        "thermal_title": "Thermisches Monitoring & Drosselstatus",
        "thermal_zone": "Thermal Zone",
        "thermal_temp": "Temperatur",
        "throttle_status": "Drosselstatus (Thermal Throttling)",
        "throttle_ok": "Keine thermische Drosselung aktiv",
        "throttle_warning": "Drosselung erkannt! Lüfterkühlung prüfen",
        "gpu_power_title": "GPU Power-Management & DPM",
        "gpu_profile_auto": "Auto",
        "gpu_profile_high": "Höchstleistung (High)",
        "gpu_profile_low": "Stromsparend (Low)",

        # System Maintenance
        "maint_title": "Paketmanagement, Hygiene & Spiegelserver",
        "mirror_bench_title": "Mirror Benchmarking & Repositories",
        "btn_run_mirror_bench": "Mirrors testen & aktualisieren",
        "pkg_cache_title": "Paket-Cache & Waisenpakete (Orphans)",
        "cache_size_label": "Aktueller Cache-Verbrauch",
        "btn_clean_cache": "Cache leeren (paccache)",
        "orphan_count_label": "Ungewollte Abhängigkeiten",
        "btn_remove_orphans": "Waisen entfernen (pacman -Rns)",
        "pacnew_audit_title": "Ungemergte Konfigurationsdateien (.pacnew)",
        "btn_audit_pacnew": "Nach .pacnew suchen",
        "btn_fstrim": "SSD TRIM (fstrim -av)",
        "journal_vacuum_title": "Systemd Journal Bereinigung",
        "btn_journal_vacuum": "Journal auf 50MB trimmen",
        "no_orphans_found": "Keine unbenutzten Waisenpakete gefunden.",
        "no_pacnews_found": "Alle Konfigurationen aktuell, keine .pacnew Dateien vorhanden.",
        "confirm_clean": "Möchten Sie die Bereinigung wirklich durchführen?",

        # Services
        "services_title": "Systemd Dienste & Daemon-Kontrollzentrum",
        "col_service": "Dienstname",
        "col_state": "Status",
        "col_substate": "Substatus",
        "col_enabled": "Autostart (Enabled)",
        "btn_start_service": "Starten",
        "btn_stop_service": "Stoppen",
        "btn_restart_service": "Neustarten",
        "btn_enable_service": "Aktivieren",
        "btn_disable_service": "Deaktivieren",
        "btn_reload_services": "Liste aktualisieren",

        # Diagnostics & Logs
        "diag_title": "Tiefendiagnose, Boot-Parameter & Kernel-Logs",
        "boot_cmdline_title": "Aktive Kernel-Boot-Parameter (/proc/cmdline)",
        "kernel_logs_title": "Aktuelle Kernel-Meldungen (dmesg / journalctl -k)",
        "boot_analyze_title": "Systemstart-Analyse (systemd-analyze)",
        "hardware_specs_title": "Erweiterte Hardware-Spezifikationen",
        "btn_run_diag": "Vollständige Diagnose ausführen",
        "btn_save_report": "Diagnosebericht exportieren",

        # Privilege & Polkit
        "polkit_auth_required": "Root-Berechtigung erforderlich",
        "polkit_dismissed": "Aktion abgebrochen: Root-Authentifizierung (Polkit) wurde abgewiesen.",
        "polkit_timeout": "Zeitüberschreitung bei der Authentifizierung.",
        "polkit_success": "Aktion erfolgreich mit Administratorrechten ausgeführt.",

        # CLI
        "cli_overview": "=== CachyOS Control Center — Systemübersicht ===",
        "cli_active_kernel": "Aktiver Kernel",
        "cli_mirror_status": "Mirror-Zustand",
        "cli_cleaning": "Starte automatische Systemhygiene...",
        "cli_clean_success": "Systemhygiene erfolgreich abgeschlossen.",
    },
    "en": {
        # App & Navigation
        "app_title": "CACHYOS CONTROL CENTER & SYSTEM ARCHITECT",
        "app_subtitle": "Professional Edition │ CachyOS Linux x86_64",
        "tab_cockpit": "1. Cockpit",
        "tab_kernel": "2. Kernels & Drivers",
        "tab_power": "3. Hardware & Power",
        "tab_maint": "4. Maintenance",
        "tab_services": "5. Services",
        "tab_diag": "6. Diagnostics & Logs",
        "tab_network": "7. Network & Tools",
        "btn_refresh": "Refresh",
        "btn_lang_toggle": "Language: EN (Key L)",
        "btn_quit": "Quit",
        "status_ready": "Ready",
        "status_running": "Running...",
        "status_done": "Completed",
        "status_error": "Failed",
        "close": "Close",
        "cancel": "Cancel",
        "confirm": "Confirm",
        "apply": "Apply",

        # Cockpit KPI Cards
        "kpi_cpu_title": "PROCESSOR (CPU)",
        "kpi_ram_title": "MEMORY (RAM)",
        "kpi_disk_title": "SYSTEM STORAGE (/)",
        "kpi_kernel_title": "ACTIVE KERNEL",
        "kpi_health_title": "SYSTEM INTEGRITY",
        "kpi_cores": "{cores} Cores",
        "kpi_used": "{used} / {total} GB used",
        "kpi_disk_btrfs": "BTRFS Active",
        "kpi_disk_standard": "Standard FS",
        "kpi_failed_units": "{count} failed units",
        "kpi_all_clean": "All units operating normally",
        "quick_actions": "Quick Actions",
        "action_cache_clean": "Clean Package Cache",
        "action_orphan_remove": "Remove Orphan Packages",
        "action_trim": "Execute SSD TRIM",
        "action_rate_mirrors": "Benchmark Mirrors",
        "action_reset_failed": "Reset Failed Units",
        "telemetry_details": "System Telemetry & Hardware Summary",
        "hostname": "Hostname",
        "os_version": "Operating System",
        "uptime": "Uptime",
        "arch": "Architecture",
        "db_lock_warn": "Warning: Pacman database is locked (/var/lib/pacman/db.lck)!",

        # Kernel & Drivers
        "kernel_mgmt_title": "CachyOS Kernel & Driver Matrix",
        "kernel_installed": "Installed Kernels",
        "kernel_available": "Available CachyOS Kernels (BORE, LTO, RT, BMQ)",
        "kernel_variant": "Variant",
        "kernel_status": "Status",
        "kernel_version": "Version",
        "kernel_desc": "Optimization Profile",
        "col_component": "Component",
        "col_driver": "Active Driver",
        "col_type": "Type",
        "col_hardware": "Hardware",
        "gpu_drivers_title": "Graphics Adapters & Driver Interfaces",
        "gpu_power_state": "Power State",
        "gpu_temp": "Temperature",
        "gpu_power_draw": "Power Draw",
        "action_install_kernel": "Install Kernel",
        "action_remove_kernel": "Uninstall Kernel",
        "active_running": "Active (Running)",
        "installed": "Installed",
        "available": "Available",
        "not_installed": "Not Installed",
        "proprietary": "Proprietary",
        "open_source": "Open Source",

        # Hardware & Power Profiles
        "power_mgmt_title": "Hardware Tuning & Energy Governors",
        "cpu_scaling_title": "CPU Frequency & EPP Control",
        "current_governor": "Current Governor",
        "available_governors": "Available Governors",
        "current_epp": "Current EPP Profile",
        "available_epp": "Available EPP Profiles",
        "btn_set_gov_perf": "Performance Governor",
        "btn_set_gov_sched": "Schedutil (Default)",
        "btn_set_gov_powersave": "Powersave Governor",
        "btn_set_epp_perf": "EPP: Performance",
        "btn_set_epp_balance": "EPP: Balance-Performance",
        "btn_set_epp_power": "EPP: Power",
        "thermal_title": "Thermal Monitoring & Throttling Status",
        "thermal_zone": "Thermal Zone",
        "thermal_temp": "Temperature",
        "throttle_status": "Throttling Status",
        "throttle_ok": "No thermal throttling active",
        "throttle_warning": "Thermal throttling detected! Check fan cooling",
        "gpu_power_title": "GPU Power Management & DPM",
        "gpu_profile_auto": "Auto",
        "gpu_profile_high": "Maximum Performance (High)",
        "gpu_profile_low": "Power Saving (Low)",

        # System Maintenance
        "maint_title": "Package Management, Hygiene & Mirrors",
        "mirror_bench_title": "Mirror Benchmarking & Repositories",
        "btn_run_mirror_bench": "Test & Optimize Mirrors",
        "pkg_cache_title": "Package Cache & Orphan Packages",
        "cache_size_label": "Current Cache Usage",
        "btn_clean_cache": "Clean Cache (paccache)",
        "orphan_count_label": "Unneeded Dependencies",
        "btn_remove_orphans": "Remove Orphans (pacman -Rns)",
        "pacnew_audit_title": "Unmerged Configuration Files (.pacnew)",
        "btn_audit_pacnew": "Scan for .pacnew",
        "btn_fstrim": "SSD TRIM (fstrim -av)",
        "journal_vacuum_title": "Systemd Journal Maintenance",
        "btn_journal_vacuum": "Trim Journal to 50MB",
        "no_orphans_found": "No unused orphan packages found.",
        "no_pacnews_found": "All configuration files are clean, no .pacnew found.",
        "confirm_clean": "Do you really want to proceed with maintenance cleanup?",

        # Services
        "services_title": "Systemd Services & Daemon Control Center",
        "col_service": "Service Name",
        "col_state": "State",
        "col_substate": "Substate",
        "col_enabled": "Autostart (Enabled)",
        "btn_start_service": "Start",
        "btn_stop_service": "Stop",
        "btn_restart_service": "Restart",
        "btn_enable_service": "Enable",
        "btn_disable_service": "Disable",
        "btn_reload_services": "Refresh List",

        # Diagnostics & Logs
        "diag_title": "Deep Diagnostics, Boot Parameters & Kernel Logs",
        "boot_cmdline_title": "Active Kernel Boot Command Line (/proc/cmdline)",
        "kernel_logs_title": "Kernel Log Feed (dmesg / journalctl -k)",
        "boot_analyze_title": "Boot Performance Analysis (systemd-analyze)",
        "hardware_specs_title": "Extended Hardware Specifications",
        "btn_run_diag": "Run Full Diagnostics",
        "btn_save_report": "Export Diagnostic Report",

        # Privilege & Polkit
        "polkit_auth_required": "Root privileges required",
        "polkit_dismissed": "Action canceled: Polkit root authentication was dismissed or denied.",
        "polkit_timeout": "Authentication request timed out.",
        "polkit_success": "Action successfully completed with administrative privileges.",

        # CLI
        "cli_overview": "=== CachyOS Control Center — System Overview ===",
        "cli_active_kernel": "Active Kernel",
        "cli_mirror_status": "Mirror Status",
        "cli_cleaning": "Starting automated system cleanup...",
        "cli_clean_success": "System hygiene completed successfully.",
    },
}

_current_lang = "de"


def set_language(lang: str) -> None:
    """Setzt die aktive Sprache ('de' oder 'en')."""
    global _current_lang
    if lang.lower().startswith("en"):
        _current_lang = "en"
    else:
        _current_lang = "de"


def get_language() -> str:
    """Gibt den aktuellen Sprachcode ('de' oder 'en') zurück."""
    return _current_lang


def toggle_language() -> str:
    """Wechselt zwischen Deutsch und Englisch."""
    global _current_lang
    _current_lang = "en" if _current_lang == "de" else "de"
    return _current_lang


def t(key: str, **kwargs: Any) -> str:
    """
    Übersetzt einen Schlüssel in die aktuell aktive Sprache.
    Unterstützt dynamische String-Formatierung ({name}).
    """
    lang_dict = _STRINGS.get(_current_lang, _STRINGS["en"])
    text = lang_dict.get(key)
    if text is None:
        # Fallback auf Englisch
        text = _STRINGS["en"].get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except Exception:
            return text
    return text
