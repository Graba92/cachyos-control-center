#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
 CachyOS Control Center — Diagnostic Core Engine
 Evidenzbasierte Netzwerkprüfungen, Latenzmessungen, DNSSEC & Route-Audits
===============================================================================
"""

from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import time
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .system import run_cmd


@dataclass
class DiagnosticItem:
    category: str
    test_name: str
    status: str  # "PASS", "WARN", "FAIL"
    metric_value: str
    details: str
    recommendation: str = ""


@dataclass
class DiagnosticResult:
    profile: str
    overall_health: str  # "HEALTHY", "DEGRADED", "CRITICAL"
    items: List[DiagnosticItem] = field(default_factory=list)
    raw_report: str = ""
    duration_seconds: float = 0.0


def _check_ping(target: str, count: int = 2, timeout: int = 3) -> Tuple[bool, str]:
    """Pinget ein Ziel an und liefert Latenz oder Fehler."""
    out, err, code = run_cmd(f"ping -c {count} -W {timeout} {target}", timeout=timeout + 2)
    if code == 0:
        # Extrahiere rtt min/avg/max
        for line in out.splitlines():
            if "rtt min/avg/max" in line or "round-trip min/avg/max" in line:
                stats = line.split("=")[1].strip().split("/")[1]
                return True, f"{stats} ms"
        return True, "Erreichbar"
    return False, "Keine Antwort / Paketverlust"


def _check_dns(domain: str, server: Optional[str] = None) -> Tuple[bool, str]:
    """Prüft DNS-Auflösung via dig oder socket."""
    if server and shutil.which("dig"):
        out, err, code = run_cmd(f"dig +short +time=2 +tries=1 @{server} {domain}")
        if code == 0 and out.strip():
            first_ip = out.strip().splitlines()[0]
            return True, first_ip
        return False, "Auflösung fehlgeschlagen"
    else:
        try:
            start = time.time()
            ip = socket.gethostbyname(domain)
            lat = round((time.time() - start) * 1000, 1)
            return True, f"{ip} ({lat}ms)"
        except Exception as e:
            return False, str(e)


def _check_http(url: str = "http://connectivitycheck.gstatic.com/generate_204", timeout: int = 3) -> Tuple[bool, str]:
    """Prüft HTTP-Konnektivität gegen 204 Captive Portal Endpunkte."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "CachyOS-Center/1.0"})
        start = time.time()
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            code = resp.getcode()
            lat = round((time.time() - start) * 1000, 1)
            if code in (200, 204):
                return True, f"HTTP {code} ({lat}ms)"
            return False, f"Unerwarteter Status: HTTP {code}"
    except Exception as e:
        return False, f"Verbindungsabbruch: {e}"


def run_diagnostic_profile(profile: str = "quick") -> DiagnosticResult:
    """Führt ein Diagnostik-Profil nativ aus und sammelt standardisierte Items."""
    start_time = time.time()
    items: List[DiagnosticItem] = []
    profile = profile.lower()

    # 1. Gateway
    gw_out, _, _ = run_cmd("ip route | awk '/default/ {print $3}' | head -n 1")
    gw_ip = gw_out.strip()
    if gw_ip:
        ok, lat = _check_ping(gw_ip)
        items.append(
            DiagnosticItem(
                category="Gateway & Routing",
                test_name="Default Gateway Ping",
                status="PASS" if ok else "FAIL",
                metric_value=lat,
                details=f"Gateway IP: {gw_ip}",
                recommendation="" if ok else "Prüfe Router-Kabel, WLAN-Verbindung oder DHCP-Zuweisung.",
            )
        )
    else:
        items.append(
            DiagnosticItem(
                category="Gateway & Routing",
                test_name="Default Route",
                status="FAIL",
                metric_value="Fehlt",
                details="Keine Standardroute in der Kernel-Routing-Tabelle vorhanden.",
                recommendation="Starte NetworkManager neu oder verbinde die Schnittstelle.",
            )
        )

    # 2. DNS
    dns_ok, dns_res = _check_dns("cachyos.org")
    items.append(
        DiagnosticItem(
            category="DNS Resolution",
            test_name="System DNS (cachyos.org)",
            status="PASS" if dns_ok else "FAIL",
            metric_value=dns_res,
            details="Standard-Resolver des Systems",
            recommendation="" if dns_ok else "Überprüfe /etc/resolv.conf oder systemd-resolved.",
        )
    )

    # 3. Cloudflare & Quad9 External DNS
    cf_ok, cf_lat = _check_ping("1.1.1.1")
    items.append(
        DiagnosticItem(
            category="Internet WAN",
            test_name="Cloudflare Anycast (1.1.1.1)",
            status="PASS" if cf_ok else "WARN",
            metric_value=cf_lat,
            details="Globaler DNS & WAN-Latenz-Indikator",
            recommendation="" if cf_ok else "WAN-Routing eingeschränkt oder ICMP gefiltert.",
        )
    )

    # 4. HTTP 204 Captive Portal
    http_ok, http_res = _check_http()
    items.append(
        DiagnosticItem(
            category="Internet WAN",
            test_name="HTTP Connectivity (Captive Check)",
            status="PASS" if http_ok else "FAIL",
            metric_value=http_res,
            details="Prüfung auf transparente Proxys & Port-80/443 Freigabe",
            recommendation="" if http_ok else "Möglicherweise Anmeldeseite (Captive Portal) im WLAN aktiv.",
        )
    )

    # 5. Tailscale Mesh L3
    if shutil.which("tailscale"):
        ts_out, _, ts_code = run_cmd("tailscale status --json | grep -o '\"BackendState\":\"[^\"]*\"'")
        ts_state = ts_out.split(":")[-1].replace('"', '') if ts_out else "Inaktiv"
        items.append(
            DiagnosticItem(
                category="Tailscale Mesh",
                test_name="Daemon State",
                status="PASS" if ts_state.lower() == "running" else "WARN",
                metric_value=ts_state or "Stopped",
                details="Tailscale Service & WireGuard Virtual Interface",
                recommendation="" if ts_state.lower() == "running" else "tailscale up ausführen falls Mesh gewünscht.",
            )
        )

    # Erweiterte Prüfungen für Standard & Deep
    if profile in ("standard", "deep"):
        # DNSSEC
        if shutil.which("delv"):
            delv_out, _, d_code = run_cmd("delv @1.1.1.1 cloudflare.com")
            sec_ok = "fully validated" in delv_out.lower()
            items.append(
                DiagnosticItem(
                    category="DNS Resolution",
                    test_name="DNSSEC Validation",
                    status="PASS" if sec_ok else "WARN",
                    metric_value="Validiert" if sec_ok else "Unvalidiert",
                    details=delv_out.splitlines()[0] if delv_out else "-",
                )
            )

        # Lokale Listening Ports
        ports_out, _, _ = run_cmd("ss -tulpn | grep LISTEN | wc -l")
        p_count = ports_out.strip() or "0"
        items.append(
            DiagnosticItem(
                category="Lokale Dienste",
                test_name="Offene Listening Ports",
                status="PASS",
                metric_value=f"{p_count} Ports",
                details="Lokale TCP/UDP Daemons",
            )
        )

    if profile == "deep":
        # MTU Discovery
        mtu_out, _, _ = run_cmd("ip route show default | grep -o 'mtu [0-9]*'")
        items.append(
            DiagnosticItem(
                category="Schnittstellen & MTU",
                test_name="Default Interface MTU",
                status="PASS",
                metric_value=mtu_out.replace("mtu ", "") if mtu_out else "1500 (Standard)",
                details="Maximum Transmission Unit",
            )
        )

        # CGNAT Check (RFC 6598: 100.64.0.0/10)
        wan_ip_out, _, _ = run_cmd("curl -s --max-time 3 https://api.ipify.org 2>/dev/null")
        wan_ip = wan_ip_out.strip() or "N/A"
        is_cgnat = wan_ip.startswith("100.")
        items.append(
            DiagnosticItem(
                category="WAN & IP Topology",
                test_name="Öffentliche IP / CGNAT",
                status="WARN" if is_cgnat else "PASS",
                metric_value=wan_ip,
                details="CGNAT erkannt (RFC 6598)" if is_cgnat else "Direkte WAN-Adresse",
                recommendation="Carrier-Grade NAT behindert Portfreigaben; Tailscale empfohlen." if is_cgnat else "",
            )
        )

    # Health Ermittlung
    fails = sum(1 for it in items if it.status == "FAIL")
    warns = sum(1 for it in items if it.status == "WARN")

    if fails > 0:
        health = "CRITICAL"
    elif warns > 0:
        health = "DEGRADED"
    else:
        health = "HEALTHY"

    duration = round(time.time() - start_time, 2)
    return DiagnosticResult(
        profile=profile,
        overall_health=health,
        items=items,
        duration_seconds=duration,
    )
