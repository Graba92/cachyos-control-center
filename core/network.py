#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
 CachyOS Control Center — Network & Wi-Fi Engine
 Hardware-Schnittstellen, Monitor-Mode Injection, AP-Scans & Stack-Steuerung
===============================================================================
"""

from __future__ import annotations

import json
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .system import run_cmd
from .polkit import run_polkit_cmd


@dataclass
class NetworkInterface:
    name: str
    is_wireless: bool
    mode: str
    mac: str
    driver: str
    state: str
    ip4: str = "-"
    ip6: str = "-"


@dataclass
class WifiAccessPoint:
    ssid: str
    bssid: str
    channel: str
    signal: int
    bars: str
    security: str


def get_network_interfaces() -> List[NetworkInterface]:
    """Ermittelt alle physischen und drahtlosen Netzwerkschnittstellen."""
    interfaces: List[NetworkInterface] = []

    # Schnelle Erkennung über /sys/class/net
    net_path = Path("/sys/class/net")
    if not net_path.exists():
        return interfaces

    for if_entry in sorted(net_path.iterdir()):
        name = if_entry.name
        if name == "lo":
            continue

        is_wireless = (if_entry / "wireless").exists() or (if_entry / "phy80211").exists() or name.startswith("wl")

        # MAC
        mac = "-"
        try:
            mac_file = if_entry / "address"
            if mac_file.exists():
                mac = mac_file.read_text().strip()
        except Exception:
            pass

        # Operstate
        state = "DOWN"
        try:
            st_file = if_entry / "operstate"
            if st_file.exists():
                state = st_file.read_text().strip().upper()
        except Exception:
            pass

        # Driver
        driver = "unknown"
        try:
            drv_link = if_entry / "device" / "driver"
            if drv_link.exists():
                driver = drv_link.resolve().name
        except Exception:
            pass

        # Mode (für WLAN)
        mode = "Ethernet"
        if is_wireless:
            mode = "Managed"
            mode_out, _, _ = run_cmd(["iw", "dev", name, "info"], timeout=3)
            for m_line in mode_out.splitlines():
                if "type" in m_line:
                    m_parts = m_line.split()
                    if len(m_parts) >= 2 and m_parts[0] == "type":
                        mode = m_parts[1].capitalize()
                        break

        # IP-Adressen
        ip4 = "-"
        ip4_out, _, _ = run_cmd(["ip", "-4", "-o", "addr", "show", name], timeout=3)
        if ip4_out.strip():
            parts = ip4_out.splitlines()[0].split()
            if len(parts) >= 4:
                ip4 = parts[3]

        ip6 = "-"
        ip6_out, _, _ = run_cmd(["ip", "-6", "-o", "addr", "show", name, "scope", "global"], timeout=3)
        if ip6_out.strip():
            parts = ip6_out.splitlines()[0].split()
            if len(parts) >= 4:
                ip6 = parts[3]

        interfaces.append(
            NetworkInterface(
                name=name,
                is_wireless=is_wireless,
                mode=mode,
                mac=mac,
                driver=driver,
                state=state,
                ip4=ip4,
                ip6=ip6,
            )
        )

    return interfaces


def scan_wifi_networks(iface: Optional[str] = None) -> List[WifiAccessPoint]:
    """Scannt die Funkumgebung nach verfügbaren WLAN Access Points."""
    networks: List[WifiAccessPoint] = []

    # Primär über nmcli, da dies keine Root-Rechte erzwingt und bereits im Hintergrund scannt
    if shutil.which("nmcli"):
        cmd = ["nmcli", "-t", "-f", "SSID,BSSID,CHAN,SIGNAL,BARS,SECURITY", "dev", "wifi", "list", "--rescan", "yes"]
        out, _, _ = run_cmd(cmd, timeout=12)
        if not out:
            # Fallback ohne expliziten Rescan
            out, _, _ = run_cmd(["nmcli", "-t", "-f", "SSID,BSSID,CHAN,SIGNAL,BARS,SECURITY", "dev", "wifi", "list"])

        for line in out.splitlines():
            parts = line.strip().split(":")
            if len(parts) >= 6:
                ssid = parts[0] or "<Versteckt>"
                sub = line.split(":")
                sig_val = 0
                for item in sub:
                    if item.isdigit() and 0 <= int(item) <= 100:
                        sig_val = int(item)
                        break

                bssid = ":".join(parts[1:7]) if len(parts) >= 7 else parts[1]
                chan = parts[-4] if len(parts) >= 6 else "-"
                bars = parts[-2] if len(parts) >= 6 else "▂▄▆█"
                sec = parts[-1] if len(parts) >= 6 else "WPA2"

                networks.append(
                    WifiAccessPoint(
                        ssid=ssid,
                        bssid=bssid,
                        channel=chan,
                        signal=sig_val,
                        bars=bars,
                        security=sec,
                    )
                )
        if networks:
            return networks

    # Fallback via iw dev scan falls nmcli keine Daten liefert
    if iface and shutil.which("iw"):
        ok, out, _ = run_polkit_cmd(["iw", "dev", iface, "scan"], timeout=10)
        curr_bssid = ""
        curr_ssid = ""
        for line in out.splitlines():
            line = line.strip()
            if line.startswith("BSS "):
                curr_bssid = line.split()[1].split("(")[0]
            elif line.startswith("SSID:"):
                curr_ssid = line.split("SSID:", 1)[1].strip() or "<Versteckt>"
                if curr_bssid:
                    networks.append(
                        WifiAccessPoint(
                            ssid=curr_ssid,
                            bssid=curr_bssid,
                            channel="-",
                            signal=50,
                            bars="▂▄▆_",
                            security="WPA/WPA2",
                        )
                    )
    return networks


def set_interface_mode(iface: str, target_mode: str) -> Tuple[bool, str]:
    """
    Wechselt den Betriebsmodus der WLAN-Schnittstelle (monitor oder managed).
    Verwendet airmon-ng mit Fallback auf native iw/ip Befehle via Polkit.
    """
    if target_mode.lower() == "monitor":
        if shutil.which("airmon-ng"):
            ok, out, _ = run_polkit_cmd(["airmon-ng", "start", iface])
            if ok:
                return True, f"Monitor-Modus für {iface} via airmon-ng aktiviert.\n{out}"
        # Fallback iw
        ok1, _, _ = run_polkit_cmd(["ip", "link", "set", iface, "down"])
        ok2, _, _ = run_polkit_cmd(["iw", iface, "set", "type", "monitor"])
        ok3, _, _ = run_polkit_cmd(["ip", "link", "set", iface, "up"])
        if ok1 and ok2 and ok3:
            return True, f"Monitor-Modus für {iface} via iw aktiviert."
        return False, f"Fehler beim Setzen auf Monitor-Modus für {iface}."

    else:  # managed
        if shutil.which("airmon-ng"):
            ok, out, _ = run_polkit_cmd(["airmon-ng", "stop", iface])
            if ok:
                return True, f"Managed-Modus für {iface} via airmon-ng wiederhergestellt."
        ok1, _, _ = run_polkit_cmd(["ip", "link", "set", iface, "down"])
        ok2, _, _ = run_polkit_cmd(["iw", iface, "set", "type", "managed"])
        ok3, _, _ = run_polkit_cmd(["ip", "link", "set", iface, "up"])
        if ok1 and ok2 and ok3:
            return True, f"Managed-Modus für {iface} via iw wiederhergestellt."
        return False, f"Fehler beim Setzen auf Managed-Modus für {iface}."


def kill_wifi_conflicts() -> Tuple[bool, str]:
    """Beendet störende Daemon-Prozesse (wpa_supplicant, NetworkManager) für Injection/Monitor."""
    if shutil.which("airmon-ng"):
        ok, out, _ = run_polkit_cmd(["airmon-ng", "check", "kill"])
        if ok:
            return True, f"Störprozesse eliminiert:\n{out}"
        return False, f"airmon-ng check kill fehlgeschlagen: {out}"
    return False, "airmon-ng ist auf dem System nicht installiert (aircrack-ng Paket fehlt)."


def restart_network_stack() -> Tuple[bool, str]:
    """Startet den NetworkManager Dienst neu via Polkit."""
    ok, out, _ = run_polkit_cmd(["systemctl", "restart", "NetworkManager"])
    if ok:
        return True, "NetworkManager erfolgreich neu gestartet."
    return False, f"Fehler beim Neustart des NetworkManagers: {out}"
