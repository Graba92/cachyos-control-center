#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
 CachyOS Control Center — XDG-konforme Konfigurationsverwaltung
 Verwaltet Einstellungen, Module, Refresh-Raten & Standardwerte nach XDG Base Dir
===============================================================================
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict

# Python 3.11+ integriertes tomllib oder Fallback
try:
    import tomllib  # type: ignore
except ImportError:
    try:
        import tomli as tomllib  # type: ignore
    except ImportError:
        tomllib = None  # type: ignore


DEFAULT_CONFIG: Dict[str, Any] = {
    "general": {
        "language": "de",
        "theme": "cachyos-emerald",
        "refresh_interval_seconds": 3,
        "aur_helper": "auto",  # 'auto', 'yay', 'paru'
    },
    "modules": {
        "cockpit": True,
        "kernel_driver": True,
        "hardware_power": True,
        "maintenance": True,
        "services": True,
        "diagnostics": True,
        "network": True,
    },
    "maintenance": {
        "keep_cache_versions": 2,
        "journal_vacuum_size": "50M",
        "prefer_cachyos_mirrors": True,
    },
    "services": {
        "monitored": [
            "NetworkManager",
            "bluetooth",
            "tailscaled",
            "sshd",
            "ananicy-cpp",
            "systemd-resolved",
            "ufw",
            "firewalld",
            "docker",
            "syncthing",
        ]
    },
}


def get_xdg_config_dir() -> Path:
    """Ermittelt das Standard XDG-Konfigurationsverzeichnis."""
    xdg_config_home = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config_home:
        return Path(xdg_config_home) / "cachyos-control-center"
    return Path.home() / ".config" / "cachyos-control-center"


def get_xdg_cache_dir() -> Path:
    """Ermittelt das Standard XDG-Cache-Verzeichnis."""
    xdg_cache_home = os.environ.get("XDG_CACHE_HOME")
    if xdg_cache_home:
        return Path(xdg_cache_home) / "cachyos-control-center"
    return Path.home() / ".cache" / "cachyos-control-center"


def get_xdg_state_dir() -> Path:
    """Ermittelt das Standard XDG-State-Verzeichnis (Logs/Historie)."""
    xdg_state_home = os.environ.get("XDG_STATE_HOME")
    if xdg_state_home:
        return Path(xdg_state_home) / "cachyos-control-center"
    return Path.home() / ".local" / "state" / "cachyos-control-center"


def get_config_file_path() -> Path:
    """Sucht nach existierender Konfigurationsdatei (User XDG -> System /etc)."""
    user_conf = get_xdg_config_dir() / "config.toml"
    if user_conf.exists():
        return user_conf
    sys_conf = Path("/etc/cachyos-control-center/config.toml")
    if sys_conf.exists():
        return sys_conf
    return user_conf


def load_config() -> Dict[str, Any]:
    """Lädt Konfiguration aus Datei oder gibt Standardwerte zurück."""
    conf = DEFAULT_CONFIG.copy()
    conf_path = get_config_file_path()

    if conf_path.exists() and tomllib is not None:
        try:
            with open(conf_path, "rb") as f:
                loaded = tomllib.load(f)
            # Tiefes Zusammenführen mit Standardwerten
            for section, values in loaded.items():
                if section in conf and isinstance(values, dict):
                    conf[section].update(values)
                else:
                    conf[section] = values
        except Exception:
            pass  # Defensiver Fallback auf DEFAULT_CONFIG
    return conf


def save_user_config(config_data: Dict[str, Any]) -> bool:
    """Speichert Konfiguration im Benutzerverzeichnis ab."""
    try:
        cfg_dir = get_xdg_config_dir()
        cfg_dir.mkdir(parents=True, exist_ok=True)
        conf_file = cfg_dir / "config.toml"

        lines = [
            "# CachyOS Control Center Konfiguration",
            "# Automatisch generiert oder manuell gepflegt",
            "",
            "[general]",
            f'language = "{config_data.get("general", {}).get("language", "de")}"',
            f'theme = "{config_data.get("general", {}).get("theme", "cachyos-emerald")}"',
            f'refresh_interval_seconds = {config_data.get("general", {}).get("refresh_interval_seconds", 3)}',
            f'aur_helper = "{config_data.get("general", {}).get("aur_helper", "auto")}"',
            "",
            "[modules]",
        ]
        for mod, en in config_data.get("modules", {}).items():
            lines.append(f"{mod} = {'true' if en else 'false'}")

        lines.extend([
            "",
            "[maintenance]",
            f'keep_cache_versions = {config_data.get("maintenance", {}).get("keep_cache_versions", 2)}',
            f'journal_vacuum_size = "{config_data.get("maintenance", {}).get("journal_vacuum_size", "50M")}"',
            f'prefer_cachyos_mirrors = {"true" if config_data.get("maintenance", {}).get("prefer_cachyos_mirrors", True) else "false"}',
            "",
            "[services]",
            f'monitored = {config_data.get("services", {}).get("monitored", [])}',
        ])

        with open(conf_file, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        return True
    except Exception:
        return False
