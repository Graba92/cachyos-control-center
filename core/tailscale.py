#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
 CachyOS Control Center — Tailscale Mesh VPN Engine
 Peer-Topology, Exit-Node-Routing, Direct Latency Pings & Daemon-Control
===============================================================================
"""

from __future__ import annotations

import json
import os
import shutil
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from .system import run_cmd


@dataclass
class TailscaleNode:
    ip: str
    hostname: str
    os_name: str
    online: bool
    is_self: bool = False
    is_exit_node: bool = False
    exit_node_option: bool = False
    rx_bytes: int = 0
    tx_bytes: int = 0


@dataclass
class TailscaleMeshStatus:
    available: bool
    running: bool
    backend_state: str
    self_node: Optional[TailscaleNode] = None
    peers: List[TailscaleNode] = field(default_factory=list)
    active_exit_node: Optional[str] = None
    error_message: str = ""


def get_tailscale_status() -> TailscaleMeshStatus:
    """Parst die Tailscale-Topologie via tailscale status --json."""
    if not shutil.which("tailscale"):
        return TailscaleMeshStatus(
            available=False,
            running=False,
            backend_state="Not Installed",
            error_message="Tailscale Binary nicht im PATH gefunden.",
        )

    out, err, code = run_cmd("tailscale status --json", timeout=10)
    if code != 0 or not out:
        return TailscaleMeshStatus(
            available=True,
            running=False,
            backend_state="Stopped / Inactive",
            error_message=err or "Tailscale Daemon antwortet nicht.",
        )

    try:
        data = json.loads(out)
        b_state = data.get("BackendState", "Unknown")
        running = b_state.lower() == "running"

        # Self Node
        self_data = data.get("Self", {})
        self_node = None
        if self_data:
            s_ips = self_data.get("TailscaleIPs", ["-"])
            s_ip = s_ips[0] if s_ips else "-"
            self_node = TailscaleNode(
                ip=s_ip,
                hostname=self_data.get("HostName", "Lokales System"),
                os_name=self_data.get("OS", "Linux"),
                online=True,
                is_self=True,
            )

        peers: List[TailscaleNode] = []
        active_exit: Optional[str] = None

        raw_peers = data.get("Peer", {})
        for _, p in raw_peers.items():
            p_ips = p.get("TailscaleIPs", ["-"])
            p_ip = p_ips[0] if p_ips else "-"
            is_exit = p.get("ExitNode", False)
            can_exit = p.get("ExitNodeOption", False)
            if is_exit:
                active_exit = p.get("HostName", p_ip)

            node = TailscaleNode(
                ip=p_ip,
                hostname=p.get("HostName", "Unbekannt"),
                os_name=p.get("OS", "-"),
                online=p.get("Online", False),
                is_self=False,
                is_exit_node=is_exit,
                exit_node_option=can_exit,
                rx_bytes=p.get("RxBytes", 0),
                tx_bytes=p.get("TxBytes", 0),
            )
            peers.append(node)

        # Sortiere Peers: Online zuerst, dann Hostname
        peers.sort(key=lambda x: (not x.online, x.hostname.lower()))

        return TailscaleMeshStatus(
            available=True,
            running=running,
            backend_state=b_state,
            self_node=self_node,
            peers=peers,
            active_exit_node=active_exit,
        )

    except Exception as exc:
        return TailscaleMeshStatus(
            available=True,
            running=False,
            backend_state="Parse Error",
            error_message=f"JSON Parse-Fehler: {exc}",
        )


def toggle_tailscale(up: bool, operator_user: Optional[str] = None) -> Tuple[bool, str]:
    """Startet oder beendet die Tailscale Mesh-Verbindung."""
    user = operator_user or os.environ.get("USER", "graba")
    if up:
        cmd = f"pkexec tailscale up --operator={user} --reset=false"
        out, err, code = run_cmd(cmd, timeout=25)
        if code == 0:
            return True, "Tailscale erfolgreich verbunden."
        return False, f"Fehler bei tailscale up: {err or out}"
    else:
        cmd = "pkexec tailscale down"
        out, err, code = run_cmd(cmd, timeout=15)
        if code == 0:
            return True, "Tailscale getrennt."
        return False, f"Fehler bei tailscale down: {err or out}"


def set_exit_node(node_target: str) -> Tuple[bool, str]:
    """Setzt einen Exit-Node im Mesh-Netzwerk."""
    target = node_target.strip()
    if not target:
        return False, "Zielknoten darf nicht leer sein."
    cmd = f"pkexec tailscale set --exit-node={target}"
    out, err, code = run_cmd(cmd, timeout=15)
    if code == 0:
        return True, f"Exit-Node erfolgreich auf '{target}' gesetzt."
    return False, f"Fehler beim Setzen des Exit-Nodes: {err or out}"


def disable_exit_node() -> Tuple[bool, str]:
    """Entfernt den aktiven Exit-Node und routet wieder lokal."""
    cmd = "pkexec tailscale set --exit-node="
    out, err, code = run_cmd(cmd, timeout=15)
    if code == 0:
        return True, "Exit-Node deaktiviert. Lokales Gateway wiederhergestellt."
    return False, f"Fehler beim Deaktivieren des Exit-Nodes: {err or out}"


def ping_tailscale_peer(peer_target: str) -> Tuple[bool, str]:
    """Führt einen direkten Tailscale Ping (Layer 3 Mesh Ping) aus."""
    target = peer_target.strip()
    if not target:
        return False, "Kein Ziel für Ping angegeben."
    cmd = f"tailscale ping -c 3 {target}"
    out, err, code = run_cmd(cmd, timeout=10)
    if code == 0:
        return True, out
    return False, err or out or "Ping fehlgeschlagen."
