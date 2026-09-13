#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
NET-DIAGNOSE 2.2 FINAL
Professional Linux Network Diagnostics

Read-only network diagnostics with:
- IPv4 / IPv6
- LAN / WLAN
- DNS / DNSSEC
- Internet / HTTPS
- TCP / UDP / NTP
- traceroute / MTR
- local listening ports
- CGNAT / Tailscale detection
- structured JSON
- Markdown reports
- monitoring-friendly exit codes
- polished Rich terminal UI

Exit codes:
  0 HEALTHY
  1 WARNING / DEGRADED
  2 CRITICAL
  3 TOOL ERROR
  130 USER ABORT
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import socket
import statistics
import struct
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from ipaddress import ip_address, ip_network
from typing import Any, Optional

APP_NAME = "NET-DIAGNOSE"
APP_VERSION = "2.2.0"
APP_EDITION = "Professional Linux Network Diagnostics"
USER_AGENT = f"{APP_NAME}/{APP_VERSION}"

EXIT_HEALTHY = 0
EXIT_WARNING = 1
EXIT_CRITICAL = 2
EXIT_TOOL_ERROR = 3
EXIT_ABORTED = 130

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    psutil = None
    HAS_PSUTIL = False

try:
    from rich.console import Console, Group
    from rich.panel import Panel
    from rich.table import Table
    from rich.align import Align
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.text import Text
    from rich import box
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

console = Console() if HAS_RICH else None


@dataclass
class Finding:
    level: str
    category: str
    title: str
    evidence: str
    recommendation: str
    confidence: str = "MEDIUM"


@dataclass
class TestResult:
    success: bool
    status: str
    elapsed_ms: float = 0.0
    detail: str = ""
    error: Optional[str] = None


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def command_exists(command: str) -> bool:
    return shutil.which(command) is not None


def elapsed_ms(start: float) -> float:
    return round((time.monotonic() - start) * 1000, 2)


def run_command(command: list[str], timeout: int = 5) -> Optional[subprocess.CompletedProcess]:
    try:
        return subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return None


def print_message(message: str, level: str = "INFO") -> None:
    if HAS_RICH:
        styles = {
            "INFO": ("cyan", "›"),
            "SUCCESS": ("green", "✓"),
            "WARNING": ("yellow", "△"),
            "ERROR": ("red", "✕"),
        }
        color, symbol = styles.get(level, ("white", "•"))
        console.print(f"[{color}]{symbol}[/{color}] {message}")
    else:
        symbols = {"INFO": "[i]", "SUCCESS": "[+]", "WARNING": "[!]", "ERROR": "[-]"}
        print(f"{symbols.get(level, '[*]')} {message}")


def section(title: str) -> None:
    if HAS_RICH:
        console.print()
        console.rule(f"[bold cyan]{title}[/bold cyan]", style="dim")
    else:
        print(f"\n{'─' * 18} {title} {'─' * 18}")


def get_capabilities() -> dict[str, bool]:
    commands = ["ip", "ping", "ping6", "dig", "traceroute", "mtr", "iw", "nmcli", "ethtool", "ss", "getent"]
    result = {cmd: command_exists(cmd) for cmd in commands}
    result["psutil"] = HAS_PSUTIL
    result["rich"] = HAS_RICH
    return result


def get_system_information() -> dict[str, Any]:
    return {
        "hostname": socket.gethostname(),
        "platform": platform.platform(),
        "kernel": platform.release(),
        "architecture": platform.machine(),
        "python": platform.python_version(),
        "uid": os.getuid() if hasattr(os, "getuid") else None,
        "timestamp_utc": now_utc(),
    }


def get_default_gateway() -> tuple[Optional[str], Optional[str]]:
    if command_exists("ip"):
        result = run_command(["ip", "-4", "route", "show", "default"], timeout=2)
        if result and result.stdout:
            for line in result.stdout.splitlines():
                parts = line.split()
                gateway = parts[parts.index("via") + 1] if "via" in parts and parts.index("via") + 1 < len(parts) else None
                interface = parts[parts.index("dev") + 1] if "dev" in parts and parts.index("dev") + 1 < len(parts) else None
                if gateway or interface:
                    return gateway, interface
    try:
        with open("/proc/net/route", encoding="utf-8") as file:
            for line in file:
                parts = line.strip().split()
                if len(parts) >= 3 and parts[1] == "00000000":
                    gateway = socket.inet_ntoa(struct.pack("<L", int(parts[2], 16)))
                    return gateway, parts[0]
    except OSError:
        pass
    return None, None


def get_default_ipv6_gateway() -> tuple[Optional[str], Optional[str]]:
    if not command_exists("ip"):
        return None, None
    result = run_command(["ip", "-6", "route", "show", "default"], timeout=2)
    if not result or not result.stdout:
        return None, None
    for line in result.stdout.splitlines():
        parts = line.split()
        gateway = parts[parts.index("via") + 1] if "via" in parts and parts.index("via") + 1 < len(parts) else None
        interface = parts[parts.index("dev") + 1] if "dev" in parts and parts.index("dev") + 1 < len(parts) else None
        if gateway or interface:
            return gateway, interface
    return None, None


def get_routing_table() -> dict[str, str]:
    routes = {"ipv4": "", "ipv6": ""}
    if not command_exists("ip"):
        return routes
    ipv4 = run_command(["ip", "-4", "route"], timeout=3)
    ipv6 = run_command(["ip", "-6", "route"], timeout=3)
    if ipv4:
        routes["ipv4"] = ipv4.stdout.strip()
    if ipv6:
        routes["ipv6"] = ipv6.stdout.strip()
    return routes


def get_system_dns_servers() -> list[str]:
    servers: list[str] = []
    try:
        with open("/etc/resolv.conf", encoding="utf-8") as file:
            for line in file:
                parts = line.strip().split()
                if len(parts) >= 2 and parts[0] == "nameserver":
                    servers.append(parts[1])
    except OSError:
        pass
    return servers


def get_local_interfaces() -> list[dict[str, Any]]:
    if not HAS_PSUTIL:
        return []
    interfaces: list[dict[str, Any]] = []
    try:
        addresses = psutil.net_if_addrs()
        stats = psutil.net_if_stats()
        for name, addr_list in addresses.items():
            if name == "lo":
                continue
            stat = stats.get(name)
            ipv4: list[str] = []
            ipv6: list[str] = []
            mac = None
            for address in addr_list:
                if address.family == socket.AF_INET:
                    ipv4.append(address.address)
                elif address.family == socket.AF_INET6:
                    value = address.address.split("%")[0]
                    if value:
                        ipv6.append(value)
                elif address.family == getattr(socket, "AF_PACKET", -999) or (
                    hasattr(socket, "AF_LINK") and address.family == socket.AF_LINK
                ):
                    mac = address.address
            if ipv4 or ipv6:
                interfaces.append({
                    "name": name,
                    "status": "UP" if stat and stat.isup else "DOWN",
                    "speed_mbps": stat.speed if stat else 0,
                    "mtu": stat.mtu if stat else 1500,
                    "ipv4": ipv4,
                    "ipv6": ipv6,
                    "mac": mac,
                })
    except Exception:
        pass
    return interfaces


def get_wifi_interfaces() -> list[str]:
    if not command_exists("iw"):
        return []
    proc = run_command(["iw", "dev"], timeout=3)
    if not proc or not proc.stdout:
        return []
    return [
        match.group(1)
        for line in proc.stdout.splitlines()
        if (match := re.match(r"\s*Interface\s+(\S+)", line))
    ]


def frequency_to_channel(frequency: int) -> Optional[int]:
    if 2412 <= frequency <= 2472:
        return (frequency - 2407) // 5
    if frequency == 2484:
        return 14
    if 5000 <= frequency <= 5900:
        return (frequency - 5000) // 5
    if 5955 <= frequency <= 7125:
        return (frequency - 5950) // 5
    return None


def get_wifi_info(interface: Optional[str] = None) -> dict[str, Any]:
    info: dict[str, Any] = {
        "active": False, "interface": None, "ssid": None, "bssid": None,
        "signal_dbm": None, "frequency_mhz": None, "channel": None,
        "bitrate_mbps": None, "source": None,
    }
    candidates = ([interface] if interface else []) + get_wifi_interfaces()
    seen: set[str] = set()
    for iface in candidates:
        if not iface or iface in seen or not command_exists("iw"):
            continue
        seen.add(iface)
        result = run_command(["iw", "dev", iface, "link"], timeout=3)
        if not result or result.returncode != 0 or "Not connected" in result.stdout:
            continue
        output = result.stdout
        info.update({
            "active": True,
            "interface": iface,
            "source": "iw",
        })
        if match := re.search(r"Connected to ([0-9a-fA-F:]+)", output):
            info["bssid"] = match.group(1)
        if match := re.search(r"SSID:\s*(.+)", output):
            info["ssid"] = match.group(1).strip()
        if match := re.search(r"freq:\s*(\d+)", output):
            frequency = int(match.group(1))
            info["frequency_mhz"] = frequency
            info["channel"] = frequency_to_channel(frequency)
        if match := re.search(r"signal:\s*(-?[\d.]+)\s*dBm", output):
            info["signal_dbm"] = float(match.group(1))
        if match := re.search(r"tx bitrate:\s*([\d.]+)\s*MBit/s", output):
            info["bitrate_mbps"] = float(match.group(1))
        return info
    return info


def get_wifi_environment(interface: Optional[str]) -> dict[str, Any]:
    result_data: dict[str, Any] = {"available": False, "networks": [], "channel_counts": {}}
    if not interface or not command_exists("iw"):
        return result_data
    result = run_command(["iw", "dev", interface, "scan"], timeout=15)
    if not result or result.returncode != 0:
        return result_data
    result_data["available"] = True
    current = None
    for raw_line in result.stdout.splitlines():
        line = raw_line.strip()
        if line.startswith("BSS "):
            if current:
                result_data["networks"].append(current)
            current = {
                "bssid": line.split()[1].split("(")[0],
                "ssid": None,
                "frequency_mhz": None,
                "signal_dbm": None,
                "channel": None,
            }
        elif current and line.startswith("SSID:"):
            current["ssid"] = line[5:].strip()
        elif current and line.startswith("freq:"):
            try:
                frequency = int(line.split(":", 1)[1].strip())
                current["frequency_mhz"] = frequency
                current["channel"] = frequency_to_channel(frequency)
            except ValueError:
                pass
        elif current and line.startswith("signal:"):
            if match := re.search(r"(-?[\d.]+)", line):
                current["signal_dbm"] = float(match.group(1))
    if current:
        result_data["networks"].append(current)
    for network in result_data["networks"]:
        channel = network.get("channel")
        if channel is not None:
            result_data["channel_counts"][channel] = result_data["channel_counts"].get(channel, 0) + 1
    return result_data


def get_public_ip() -> dict[str, Any]:
    result = {"ipv4": None, "ipv6": None}
    services = {
        "ipv4": ["https://api.ipify.org", "https://ipv4.icanhazip.com"],
        "ipv6": ["https://api6.ipify.org", "https://ipv6.icanhazip.com"],
    }
    families = {"ipv4": socket.AF_INET, "ipv6": socket.AF_INET6}
    for family_name, urls in services.items():
        for url in urls:
            try:
                request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
                with urllib.request.urlopen(request, timeout=4) as response:
                    value = response.read().decode().strip()
                socket.inet_pton(families[family_name], value)
                result[family_name] = value
                break
            except Exception:
                continue
    return result


def test_system_dns(domain: str) -> TestResult:
    start = time.monotonic()
    if command_exists("getent"):
        result = run_command(["getent", "ahosts", domain], timeout=4)
        duration = elapsed_ms(start)
        if result and result.returncode == 0 and result.stdout.strip():
            return TestResult(True, "OK", duration, "Systemresolver erfolgreich")
        return TestResult(False, "FAILED", duration, "System-Namensauflösung fehlgeschlagen")
    try:
        socket.getaddrinfo(domain, 443)
        return TestResult(True, "OK", elapsed_ms(start), "Python-Systemresolver erfolgreich")
    except socket.gaierror as error:
        return TestResult(False, "FAILED", elapsed_ms(start), "Namensauflösung fehlgeschlagen", type(error).__name__)


def test_dns_server(server: str, domain: str) -> TestResult:
    start = time.monotonic()
    if not command_exists("dig"):
        return TestResult(False, "UNAVAILABLE", 0, "dig nicht installiert")
    result = run_command(
        ["dig", f"@{server}", domain, "+stats", "+time=2", "+tries=1"],
        timeout=5,
    )
    duration = elapsed_ms(start)
    if not result:
        return TestResult(False, "TIMEOUT", duration, "Keine Antwort")
    match = re.search(r"status:\s*([A-Z]+)", result.stdout)
    status = match.group(1) if match else "UNKNOWN"
    query_match = re.search(r"Query time:\s*(\d+)\s*msec", result.stdout)
    query_time = float(query_match.group(1)) if query_match else duration
    if status == "NOERROR":
        return TestResult(True, "OK", query_time, "DNS-Antwort erhalten")
    return TestResult(False, status, query_time, f"DNS status={status}")


def test_dnssec(dns_server: Optional[str] = None) -> dict[str, Any]:
    result_data = {"status": "UNAVAILABLE", "validating": None, "resolver": dns_server}
    if not command_exists("dig"):
        return result_data
    command = ["dig"] + ([f"@{dns_server}"] if dns_server else [])
    try:
        valid = subprocess.run(command + ["sigok.verteiltesysteme.net", "+time=2", "+tries=1"],
                               capture_output=True, text=True, timeout=4)
        invalid = subprocess.run(command + ["sigfail.verteiltesysteme.net", "+time=2", "+tries=1"],
                                 capture_output=True, text=True, timeout=4)
        valid_ok = "status: NOERROR" in valid.stdout
        match = re.search(r"status:\s*([A-Z]+)", invalid.stdout)
        invalid_status = match.group(1) if match else None
        if valid_ok and invalid_status == "SERVFAIL":
            result_data.update({"status": "ACTIVE", "validating": True})
        elif valid_ok and invalid_status == "NOERROR":
            result_data.update({"status": "NOT_VALIDATING", "validating": False})
        else:
            result_data["status"] = "INCONCLUSIVE"
    except Exception:
        result_data["status"] = "ERROR"
    return result_data


def ping_host(host: str, count: int, ipv6: bool = False) -> dict[str, Any]:
    binary = "ping6" if ipv6 else "ping"
    if not command_exists(binary):
        return {"success": False, "status": "UNAVAILABLE", "loss_pct": 100.0,
                "min_ms": None, "avg_ms": None, "max_ms": None, "jitter_ms": None,
                "error": f"{binary} nicht installiert"}
    command = [binary, "-c", str(count), "-W", "2", host]
    start = time.monotonic()
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=(count * 2) + 5)
        output = result.stdout + result.stderr
        loss_match = re.search(r"(\d+(?:\.\d+)?)%\s*(?:packet )?loss", output)
        loss = float(loss_match.group(1)) if loss_match else 100.0
        stats_match = re.search(r"=\s*([\d.]+)/([\d.]+)/([\d.]+)/([\d.]+)", output)
        minimum = average = maximum = mdev = None
        if stats_match:
            minimum, average, maximum, mdev = map(float, stats_match.groups())
        return {
            "success": loss < 100,
            "status": "OK" if loss < 100 else "UNREACHABLE",
            "loss_pct": loss,
            "min_ms": minimum,
            "avg_ms": average,
            "max_ms": maximum,
            "jitter_ms": mdev,
            "elapsed_ms": elapsed_ms(start),
            "error": None,
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "status": "TIMEOUT", "loss_pct": 100.0,
                "min_ms": None, "avg_ms": None, "max_ms": None, "jitter_ms": None,
                "elapsed_ms": elapsed_ms(start), "error": "TIMEOUT"}


def test_tcp(host: str, port: int, timeout: int = 3) -> dict[str, Any]:
    start = time.monotonic()
    try:
        addresses = socket.getaddrinfo(host, port, socket.AF_UNSPEC, socket.SOCK_STREAM)
    except socket.gaierror as error:
        return {"success": False, "status": "DNS_ERROR", "elapsed_ms": elapsed_ms(start), "detail": str(error)}
    last_error = None
    for family, socktype, proto, _, sockaddr in addresses:
        sock = socket.socket(family, socktype, proto)
        sock.settimeout(timeout)
        try:
            sock.connect(sockaddr)
            return {"success": True, "status": "OPEN", "elapsed_ms": elapsed_ms(start), "detail": "TCP-Verbindung erfolgreich"}
        except ConnectionRefusedError:
            return {"success": True, "status": "REFUSED", "elapsed_ms": elapsed_ms(start),
                    "detail": "Host erreichbar; Port lehnt Verbindung ab"}
        except socket.timeout as error:
            last_error = error
        except OSError as error:
            last_error = error
        finally:
            sock.close()
    return {"success": False, "status": "TIMEOUT", "elapsed_ms": elapsed_ms(start),
            "detail": "Keine TCP-Antwort; Firewall nicht bewiesen",
            "error": type(last_error).__name__ if last_error else None}


def test_https(url: str, timeout: int = 5) -> dict[str, Any]:
    start = time.monotonic()
    request = urllib.request.Request(url, method="HEAD", headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return {"success": True, "status": response.status, "elapsed_ms": elapsed_ms(start),
                    "detail": "DNS + TCP + TLS + HTTP erfolgreich"}
    except urllib.error.HTTPError as error:
        return {"success": True, "status": error.code, "elapsed_ms": elapsed_ms(start),
                "detail": f"HTTPS-Stack funktioniert; HTTP {error.code}"}
    except Exception as error:
        return {"success": False, "status": "FAILED", "elapsed_ms": elapsed_ms(start),
                "detail": type(error).__name__}


def test_ntp(host: str = "pool.ntp.org", port: int = 123, timeout: int = 3) -> dict[str, Any]:
    start = time.monotonic()
    packet = b"\x1b" + (47 * b"\0")
    try:
        addresses = socket.getaddrinfo(host, port, socket.AF_INET, socket.SOCK_DGRAM)
        sockaddr = addresses[0][4]
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.settimeout(timeout)
            sock.sendto(packet, sockaddr)
            data, _ = sock.recvfrom(1024)
        return {"success": bool(data), "status": "OPEN", "elapsed_ms": elapsed_ms(start),
                "detail": "NTP-Antwort erhalten"}
    except socket.timeout:
        return {"success": False, "status": "TIMEOUT", "elapsed_ms": elapsed_ms(start),
                "detail": "Keine UDP-Antwort; Firewall nicht bewiesen"}
    except Exception as error:
        return {"success": False, "status": "ERROR", "elapsed_ms": elapsed_ms(start),
                "detail": type(error).__name__}


def run_traceroute(target: str, max_hops: int = 20) -> dict[str, Any]:
    result_data = {"available": False, "target": target, "hops": [], "raw": ""}
    if not command_exists("traceroute"):
        return result_data
    result_data["available"] = True
    result = run_command(["traceroute", "-n", "-w", "1", "-q", "1", "-m", str(max_hops), target], timeout=35)
    if not result:
        return result_data
    result_data["raw"] = (result.stdout + result.stderr).strip()
    for line in result.stdout.splitlines():
        parts = line.split()
        if not parts or not parts[0].isdigit():
            continue
        hop = {"hop": int(parts[0]), "ip": None, "rtt_ms": None, "status": "UNKNOWN"}
        if len(parts) > 1 and parts[1] == "*":
            hop["status"] = "TIMEOUT"
        elif len(parts) > 1:
            hop["ip"] = parts[1]
            hop["status"] = "OK"
        for part in parts[2:]:
            if match := re.match(r"([\d.]+)ms?", part):
                hop["rtt_ms"] = float(match.group(1))
                break
        result_data["hops"].append(hop)
    return result_data


def run_mtr(target: str, count: int) -> dict[str, Any]:
    result_data = {"available": False, "target": target, "raw": ""}
    if not command_exists("mtr"):
        return result_data
    result_data["available"] = True
    result = run_command(["mtr", "--report", "--report-cycles", str(count), "--no-dns", target],
                          timeout=(count * 2) + 10)
    if result:
        result_data["raw"] = (result.stdout + result.stderr).strip()
    return result_data


def get_local_listeners() -> list[dict[str, Any]]:
    if not HAS_PSUTIL:
        return []
    listeners: list[dict[str, Any]] = []
    try:
        connections = psutil.net_connections(kind="inet")
        for connection in connections:
            tcp_listener = connection.type == socket.SOCK_STREAM and connection.status == psutil.CONN_LISTEN
            udp_socket = connection.type == socket.SOCK_DGRAM and bool(connection.laddr)
            if not (tcp_listener or udp_socket):
                continue
            protocol = "TCP" if connection.type == socket.SOCK_STREAM else "UDP"
            ip = connection.laddr.ip
            port = connection.laddr.port
            pid = connection.pid
            process = "unknown"
            if pid:
                try:
                    process = psutil.Process(pid).name()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    process = "access-denied"
            if ip in ("0.0.0.0", "::", ""):
                exposure = "ALL_INTERFACES"
            elif ip.startswith("127.") or ip == "::1":
                exposure = "LOOPBACK"
            elif is_private_address(ip):
                exposure = "LAN"
            else:
                exposure = "OTHER"
            listeners.append({
                "protocol": protocol, "ip": ip, "port": port, "pid": pid or "-",
                "process": process, "exposure": exposure,
            })
    except Exception:
        pass
    listeners.sort(key=lambda item: (item["port"], item["protocol"]))
    return listeners


def is_private_address(address: str) -> bool:
    try:
        return ip_address(address).is_private
    except ValueError:
        return False


def is_cgnat_address(address: str) -> bool:
    try:
        return ip_address(address) in ip_network("100.64.0.0/10")
    except ValueError:
        return False


def detect_cgnat(interfaces: list[dict[str, Any]]) -> list[dict[str, str]]:
    matches = []
    for interface in interfaces:
        if "tailscale" in interface["name"].lower() or interface["name"].lower() == "ts0":
            continue
        for address in interface["ipv4"]:
            if is_cgnat_address(address):
                matches.append({"interface": interface["name"], "address": address})
    return matches


def detect_tailscale(interfaces: list[dict[str, Any]]) -> dict[str, Any]:
    found = [
        interface["name"] for interface in interfaces
        if "tailscale" in interface["name"].lower() or interface["name"].lower() == "ts0"
    ]
    return {"detected": bool(found), "interfaces": found}


def analyze(data: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    local = data["local_network"]
    pings = data["pings"]
    dns = data["dns"]
    https = data["https"]
    wifi = data["wifi"]

    gateway = local.get("gateway")
    gateway_test = pings.get(gateway) if gateway else None

    if gateway_test:
        loss = gateway_test.get("loss_pct", 100)
        average = gateway_test.get("avg_ms")
        jitter = gateway_test.get("jitter_ms")
        if loss >= 20:
            findings.append(Finding("CRITICAL", "LOCAL_NETWORK", "Hoher Paketverlust zum Gateway",
                                    f"Gateway {gateway}: {loss:.1f}% Paketverlust.",
                                    "LAN-Kabel, WLAN-Verbindung, Access Point, Switch und Router prüfen.", "HIGH"))
        elif loss > 0:
            findings.append(Finding("WARNING", "LOCAL_NETWORK", "Paketverlust zum Gateway",
                                    f"Gateway {gateway}: {loss:.1f}% Paketverlust.",
                                    "Lokale Verbindung untersuchen; bei WLAN testweise per LAN vergleichen.", "HIGH"))
        if average is not None and average > 20:
            findings.append(Finding("WARNING", "LOCAL_NETWORK", "Erhöhte Gateway-Latenz",
                                    f"Durchschnittliche Gateway-Latenz: {average:.1f} ms.",
                                    "Bei WLAN Signalqualität/Funkstörungen, bei LAN Switch/Router prüfen.", "MEDIUM"))
        if jitter is not None and jitter > 15:
            findings.append(Finding("WARNING", "LOCAL_NETWORK", "Hohe lokale Laufzeitstreuung",
                                    f"Ping-MDEV zum Gateway: {jitter:.1f} ms.",
                                    "Funkstörungen oder lokale Auslastung untersuchen.", "MEDIUM"))

    if wifi.get("active"):
        signal = wifi.get("signal_dbm")
        if signal is not None:
            if signal <= -80:
                findings.append(Finding("CRITICAL", "WLAN", "Sehr schwaches WLAN-Signal",
                                        f"Signal: {signal:.1f} dBm.",
                                        "Position des Access Points oder Endgeräts verbessern oder LAN verwenden.", "HIGH"))
            elif signal <= -67:
                findings.append(Finding("WARNING", "WLAN", "Schwaches WLAN-Signal",
                                        f"Signal: {signal:.1f} dBm.",
                                        "Abstand, Hindernisse und Funkkanal prüfen.", "HIGH"))

    internet_targets = ["cloudflare.com", "heise.de", "aws.amazon.com"]
    reachable = [target for target in internet_targets if pings.get(target, {}).get("success")]
    https_ok = [target for target, result in https.items() if result.get("success")]

    if not reachable and not https_ok:
        findings.append(Finding("CRITICAL", "INTERNET", "Keine externe Konnektivität nachweisbar",
                                "Keines der getesteten ICMP- oder HTTPS-Ziele war erfolgreich.",
                                "WAN-Verbindung, Router, Provider und Routing untersuchen.", "HIGH"))
    elif not reachable and https_ok:
        findings.append(Finding("INFO", "ICMP", "ICMP eingeschränkt, HTTPS funktioniert",
                                "Externe HTTPS-Ziele sind erreichbar, ICMP-Ziele antworten nicht zuverlässig.",
                                "Keinen Internetausfall aus ICMP allein ableiten; ICMP kann gefiltert werden.", "HIGH"))

    external_loss: list[str] = []
    high_latency: list[str] = []
    high_jitter: list[str] = []
    for target in internet_targets:
        result = pings.get(target)
        if not result:
            continue
        loss = result.get("loss_pct")
        if loss is not None and loss > 0:
            external_loss.append(f"{target}: {loss:.1f}%")
        average = result.get("avg_ms")
        if average is not None and average > 70:
            high_latency.append(f"{target}: {average:.1f} ms")
        jitter = result.get("jitter_ms")
        if jitter is not None and jitter > 20:
            high_jitter.append(f"{target}: {jitter:.1f} ms")
    if external_loss:
        findings.append(Finding("WARNING", "INTERNET_QUALITY", "Externer Paketverlust",
                                ", ".join(external_loss),
                                "Gateway-Verlust mit externem Verlust vergleichen; bei sauberem Gateway liegt die Ursache wahrscheinlich hinter dem LAN.", "MEDIUM"))
    if high_latency:
        findings.append(Finding("WARNING", "LATENCY", "Erhöhte externe Latenz",
                                ", ".join(high_latency),
                                "Leitungsauslastung, Routing und Bufferbloat prüfen.", "MEDIUM"))
    if high_jitter:
        findings.append(Finding("WARNING", "JITTER", "Hohe externe Laufzeitstreuung",
                                ", ".join(high_jitter),
                                "Upload/Download-Auslastung und Queueing untersuchen; SQM/QoS kann bei Bufferbloat helfen.", "MEDIUM"))

    system_dns = dns.get("system")
    public_dns = dns.get("public", {})
    if system_dns and not system_dns.get("success"):
        public_ok = any(result.get("success") for result in public_dns.values())
        findings.append(Finding(
            "CRITICAL" if public_ok else "WARNING",
            "DNS",
            "Systemresolver fehlerhaft" if public_ok else "DNS-Auflösung nicht verfügbar",
            "Öffentliche DNS-Server antworten, der lokale Systemresolver jedoch nicht." if public_ok
            else "Systemresolver und öffentliche DNS-Tests sind fehlgeschlagen.",
            "NetworkManager, systemd-resolved und /etc/resolv.conf prüfen." if public_ok
            else "Netzwerkverbindung und DNS-Konfiguration prüfen.",
            "HIGH" if public_ok else "MEDIUM",
        ))

    dnssec = dns.get("dnssec", {})
    if dnssec.get("validating") is False:
        findings.append(Finding("INFO", "DNSSEC", "DNSSEC-Validierung nicht aktiv",
                                "Der getestete Resolver validiert DNSSEC nicht.",
                                "Falls gewünscht einen DNSSEC-validierenden Resolver einsetzen.", "HIGH"))

    cgnat = data.get("cgnat", [])
    if cgnat:
        addresses = ", ".join(f"{x['interface']}={x['address']}" for x in cgnat)
        findings.append(Finding("WARNING", "NAT", "CGNAT-Adressraum erkannt",
                                addresses,
                                "WAN-Adresse des Routers mit der öffentlichen IPv4 vergleichen; erst dann CGNAT sicher bestätigen.",
                                "MEDIUM"))

    tailscale = data.get("tailscale", {})
    if tailscale.get("detected"):
        findings.append(Finding("INFO", "VPN", "Tailscale erkannt",
                                "Interface(s): " + ", ".join(tailscale["interfaces"]),
                                "Virtuelle Netzwerkpfade bei Routingdiagnosen berücksichtigen.", "HIGH"))

    exposed = [x for x in data.get("listeners", []) if x["exposure"] == "ALL_INTERFACES"]
    important = [x for x in exposed if x["port"] in {22, 80, 443, 3389, 5900}]
    if important:
        details = ", ".join(f"{x['protocol']}/{x['port']} ({x['process']})" for x in important)
        findings.append(Finding("INFO", "LOCAL_SERVICES", "Bekannte Dienste auf allen Interfaces",
                                details,
                                "Bind-Adresse und Firewall-Regeln prüfen, sofern diese Dienste nicht bewusst erreichbar sein sollen.",
                                "HIGH"))
    return findings


def calculate_health(findings: list[Finding]) -> dict[str, Any]:
    score = 100
    for finding in findings:
        score -= {"CRITICAL": 45, "WARNING": 15, "INFO": 0}.get(finding.level, 0)
    score = max(0, min(100, score))
    critical = sum(f.level == "CRITICAL" for f in findings)
    warnings = sum(f.level == "WARNING" for f in findings)
    status = "CRITICAL" if critical else "DEGRADED" if score < 80 or warnings else "HEALTHY"
    return {"score": score, "status": status, "critical_findings": critical, "warning_findings": warnings}


def run_diagnostics(args: argparse.Namespace) -> dict[str, Any]:
    data: dict[str, Any] = {
        "product": {"name": APP_NAME, "version": APP_VERSION, "edition": APP_EDITION},
        "timestamp_utc": now_utc(),
        "system": get_system_information(),
        "capabilities": get_capabilities(),
        "local_network": {}, "wifi": {}, "wifi_environment": {},
        "public_ip": {}, "dns": {}, "pings": {}, "https": {}, "ports": [],
        "traceroute": {}, "mtr": {}, "listeners": [], "tailscale": {}, "cgnat": [],
        "findings": [], "health": {},
    }

    section("LOCAL NETWORK")
    print_message("Ermittle Netzwerkstruktur...")
    gateway, gateway_interface = get_default_gateway()
    ipv6_gateway, ipv6_interface = get_default_ipv6_gateway()
    interfaces = get_local_interfaces()
    data["local_network"] = {
        "gateway": gateway, "gateway_interface": gateway_interface,
        "ipv6_gateway": ipv6_gateway, "ipv6_interface": ipv6_interface,
        "dns_servers": get_system_dns_servers(), "interfaces": interfaces,
        "routes": get_routing_table(),
    }

    section("WIRELESS")
    print_message("Analysiere WLAN...")
    data["wifi"] = get_wifi_info()
    if data["wifi"].get("active") and not args.quick:
        print_message("Analysiere WLAN-Umgebung...")
        data["wifi_environment"] = get_wifi_environment(data["wifi"].get("interface"))

    section("PUBLIC CONNECTIVITY")
    if args.no_geoip:
        print_message("GeoIP/Provider-Abfragen sind deaktiviert (--no-geoip).")
    print_message("Ermittle öffentliche IP...")
    data["public_ip"] = get_public_ip()

    data["tailscale"] = detect_tailscale(interfaces)
    data["cgnat"] = detect_cgnat(interfaces)

    section("DNS")
    print_message("Teste System-DNS...")
    data["dns"]["system"] = asdict(test_system_dns(args.dns_host))
    data["dns"]["public"] = {}
    for server in ("1.1.1.1", "8.8.8.8", "9.9.9.9"):
        print_message(f"Teste DNS {server}...")
        data["dns"]["public"][server] = asdict(test_dns_server(server, args.dns_host))
    print_message("Prüfe DNSSEC...")
    data["dns"]["dnssec"] = test_dnssec()

    section("CONNECTIVITY")
    print_message(f"Teste Konnektivität ({args.ping_count} Pings)...")
    targets = ([gateway] if gateway else []) + ["1.1.1.1", "cloudflare.com", "heise.de", "aws.amazon.com"]
    seen: set[str] = set()
    for target in targets:
        if not target or target in seen:
            continue
        seen.add(target)
        data["pings"][target] = ping_host(target, args.ping_count)

    if ipv6_gateway:
        print_message("Teste IPv6-Konnektivität...")
        data["pings"]["ipv6"] = ping_host("cloudflare.com", max(4, min(args.ping_count, 10)), ipv6=True)

    section("APPLICATION LAYER")
    print_message("Teste HTTPS...")
    for url in ("https://cloudflare.com", "https://www.heise.de", "https://www.google.com"):
        data["https"][url] = test_https(url)

    if not args.quick:
        section("DEEP NETWORK TESTS")
        print_message("Teste ausgewählte TCP-Dienste...")
        tcp_tests = [
            ("1.1.1.1", 53, "DNS-TCP"), ("example.com", 80, "HTTP"),
            ("google.com", 443, "HTTPS"), ("smtp.gmail.com", 465, "SMTPS"),
            ("smtp.gmail.com", 587, "SMTP"), ("imap.gmail.com", 993, "IMAPS"),
        ]
        for host, port, description in tcp_tests:
            data["ports"].append({
                "host": host, "port": port, "protocol": "TCP",
                "description": description, **test_tcp(host, port),
            })
        print_message("Teste UDP/NTP...")
        data["ports"].append({
            "host": "pool.ntp.org", "port": 123, "protocol": "UDP",
            "description": "NTP", **test_ntp(),
        })
        print_message("Analysiere Netzwerkpfad...")
        data["traceroute"] = run_traceroute("1.1.1.1")
        print_message("Führe MTR aus...")
        data["mtr"] = run_mtr("cloudflare.com", min(args.ping_count, 20))

    section("LOCAL SERVICES")
    print_message("Analysiere lokale Listening-Ports...")
    data["listeners"] = get_local_listeners()

    section("ANALYSIS")
    print_message("Führe evidenzbasierte Ursachenanalyse durch...")
    findings = analyze(data)
    data["findings"] = [asdict(f) for f in findings]
    data["health"] = calculate_health(findings)
    return data


def status_markup(status: str) -> str:
    return {
        "HEALTHY": "[bold green]HEALTHY[/bold green]",
        "DEGRADED": "[bold yellow]DEGRADED[/bold yellow]",
        "CRITICAL": "[bold red]CRITICAL[/bold red]",
        "OK": "[green]OK[/green]",
        "OPEN": "[green]OPEN[/green]",
        "REFUSED": "[yellow]REFUSED[/yellow]",
        "TIMEOUT": "[yellow]TIMEOUT[/yellow]",
        "FAILED": "[red]FAILED[/red]",
        "UNREACHABLE": "[red]UNREACHABLE[/red]",
    }.get(status, f"[dim]{status}[/dim]")


def render_rich(data: dict[str, Any]) -> None:
    health = data["health"]
    local = data["local_network"]

    console.print()
    console.print(Panel(
        Align.center(
            Group(
                Text(APP_NAME, style="bold cyan"),
                Text(f"v{APP_VERSION}  •  {APP_EDITION}", style="dim"),
                Text("READ-ONLY DIAGNOSTICS", style="dim"),
            )
        ),
        box=box.DOUBLE,
        border_style="cyan",
        padding=(1, 3),
    ))

    score = health["score"]
    bar_len = 30
    filled = round(bar_len * score / 100)
    bar = "━" * filled + "─" * (bar_len - filled)
    color = {"HEALTHY": "green", "DEGRADED": "yellow", "CRITICAL": "red"}.get(health["status"], "white")

    health_panel = Panel(
        Group(
            Text.from_markup(f"Status     {status_markup(health['status'])}"),
            Text.from_markup(f"Score      [{color}]{score}/100[/{color}]  {bar}"),
            Text(f"Kritisch   {health['critical_findings']}    Warnungen   {health['warning_findings']}"),
        ),
        title="NETWORK HEALTH",
        border_style=color,
        box=box.ROUNDED,
    )

    context = Table(title="NETWORK CONTEXT", box=box.ROUNDED, expand=True)
    context.add_column("Property", style="cyan")
    context.add_column("Value")
    context.add_row("Gateway", str(local.get("gateway") or "—"))
    context.add_row("Interface", str(local.get("gateway_interface") or "—"))
    context.add_row("IPv6 Gateway", str(local.get("ipv6_gateway") or "—"))
    context.add_row("DNS", ", ".join(local.get("dns_servers", [])) or "—")
    context.add_row("Public IPv4", str(data["public_ip"].get("ipv4") or "—"))
    context.add_row("Public IPv6", str(data["public_ip"].get("ipv6") or "—"))

    console.print(health_panel)
    console.print(context)

    table = Table(title="CONNECTIVITY MATRIX", box=box.ROUNDED, expand=True)
    table.add_column("Target", style="cyan")
    table.add_column("Status")
    table.add_column("Loss", justify="right")
    table.add_column("Avg", justify="right")
    table.add_column("MDEV", justify="right")
    for target, result in data["pings"].items():
        table.add_row(
            target,
            status_markup(result.get("status", "UNKNOWN")),
            f"{result.get('loss_pct', 0):.1f}%" if result.get("loss_pct") is not None else "—",
            f"{result['avg_ms']:.1f} ms" if result.get("avg_ms") is not None else "—",
            f"{result['jitter_ms']:.1f} ms" if result.get("jitter_ms") is not None else "—",
        )
    console.print(table)

    wifi = data["wifi"]
    if wifi.get("active"):
        wtable = Table(title="WLAN", box=box.ROUNDED, expand=True)
        wtable.add_column("Interface", style="cyan")
        wtable.add_column("SSID")
        wtable.add_column("Signal")
        wtable.add_column("Channel")
        wtable.add_column("Bitrate")
        wtable.add_row(
            str(wifi.get("interface") or "—"),
            str(wifi.get("ssid") or "<hidden>"),
            f"{wifi['signal_dbm']:.1f} dBm" if wifi.get("signal_dbm") is not None else "—",
            str(wifi.get("channel") or "—"),
            f"{wifi['bitrate_mbps']:.1f} Mbit/s" if wifi.get("bitrate_mbps") is not None else "—",
        )
        console.print(wtable)

    section("DIAGNOSTIC FINDINGS")
    if not data["findings"]:
        console.print(Panel("[bold green]No relevant issues detected.[/bold green]",
                            border_style="green", box=box.ROUNDED))
    else:
        for finding in data["findings"]:
            level = finding["level"]
            style = {"CRITICAL": "red", "WARNING": "yellow", "INFO": "cyan"}.get(level, "white")
            body = Group(
                Text.from_markup(f"[bold]Evidenz[/bold]  {finding['evidence']}"),
                Text.from_markup(f"[bold]Konfidenz[/bold]  {finding['confidence']}"),
                Text.from_markup(f"[bold]Empfehlung[/bold]  {finding['recommendation']}"),
            )
            console.print(Panel(body, title=f"[{style}]{level}[/{style}]  {finding['title']}",
                                border_style=style, box=box.ROUNDED))


def render_plain(data: dict[str, Any]) -> None:
    health = data["health"]
    print(f"\n{'=' * 72}\n{APP_NAME} {APP_VERSION}\n{APP_EDITION}\n{'=' * 72}")
    print(f"STATUS: {health['status']}\nSCORE:  {health['score']}/100")
    print(f"Gateway: {data['local_network'].get('gateway')}")
    print("\nDIAGNOSE:")
    for finding in data["findings"]:
        print(f"[{finding['level']}] {finding['title']}")
        print(f"  Evidenz: {finding['evidence']}")
        print(f"  Empfehlung: {finding['recommendation']}")


def save_json(filename: str, data: dict[str, Any]) -> None:
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False, default=str)


def save_markdown(filename: str, data: dict[str, Any]) -> None:
    health = data["health"]
    with open(filename, "w", encoding="utf-8") as file:
        file.write(f"# {APP_NAME} {APP_VERSION}\n\n")
        file.write(f"**Edition:** {APP_EDITION}\n\n")
        file.write(f"**Diagnosezeitpunkt:** {data['timestamp_utc']}\n\n")
        file.write(f"## Gesamtstatus\n\n**Status:** `{health['status']}`  \n**Health Score:** `{health['score']}/100`\n\n")

        file.write("## System\n\n")
        for key, value in data["system"].items():
            file.write(f"- **{key}:** `{value}`\n")

        local = data["local_network"]
        file.write("\n## Netzwerk\n\n")
        for key in ("gateway", "gateway_interface", "ipv6_gateway", "ipv6_interface"):
            file.write(f"- **{key}:** `{local.get(key)}`\n")
        file.write(f"- **DNS:** {', '.join(local.get('dns_servers', []))}\n")

        file.write("\n## Interfaces\n\n| Interface | Status | IPv4 | IPv6 | MTU | Speed |\n|---|---|---|---|---:|---:|\n")
        for interface in local["interfaces"]:
            file.write(f"| {interface['name']} | {interface['status']} | {', '.join(interface['ipv4'])} | "
                       f"{', '.join(interface['ipv6'])} | {interface['mtu']} | {interface['speed_mbps']} Mbps |\n")

        file.write("\n## WLAN\n\n")
        wifi = data["wifi"]
        if wifi.get("active"):
            for key in ("interface", "ssid", "bssid", "signal_dbm", "frequency_mhz", "channel", "bitrate_mbps"):
                file.write(f"- **{key}:** `{wifi.get(key)}`\n")
        else:
            file.write("Kein aktives WLAN erkannt.\n")

        file.write("\n## Public IP\n\n")
        file.write(f"- IPv4: `{data['public_ip'].get('ipv4')}`\n- IPv6: `{data['public_ip'].get('ipv6')}`\n")

        file.write("\n## DNS\n\n")
        file.write(f"Systemresolver: `{data['dns']['system']}`\n\n")
        file.write(f"DNSSEC: `{data['dns']['dnssec']['status']}`\n\n")

        file.write("## Latenz\n\n| Ziel | Status | Loss | Avg | MDEV |\n|---|---|---:|---:|---:|\n")
        for target, result in data["pings"].items():
            file.write(f"| {target} | {result.get('status')} | {result.get('loss_pct', 0):.1f}% | "
                       f"{result.get('avg_ms') or '-'} | {result.get('jitter_ms') or '-'} |\n")

        file.write("\n## HTTPS\n\n| URL | Status | Zeit |\n|---|---|---:|\n")
        for url, result in data["https"].items():
            file.write(f"| {url} | {result.get('status')} | {result.get('elapsed_ms', 0):.1f} ms |\n")

        file.write("\n## Diagnose\n\n")
        if not data["findings"]:
            file.write("Keine relevanten Auffälligkeiten erkannt.\n")
        for index, finding in enumerate(data["findings"], 1):
            file.write(f"### {index}. {finding['level']} — {finding['title']}\n\n")
            file.write(f"**Kategorie:** {finding['category']}  \n")
            file.write(f"**Evidenz:** {finding['evidence']}  \n")
            file.write(f"**Konfidenz:** `{finding['confidence']}`  \n")
            file.write(f"**Empfehlung:** {finding['recommendation']}\n\n")

        if data["mtr"].get("available"):
            file.write("\n## MTR\n\n```text\n")
            file.write(data["mtr"].get("raw", ""))
            file.write("\n```\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="net-diagnose",
        description=f"{APP_NAME} {APP_VERSION} — {APP_EDITION}",
    )
    profile = parser.add_mutually_exclusive_group()
    profile.add_argument("--quick", action="store_true", help="Schnelle Basisdiagnose")
    profile.add_argument("--standard", action="store_true", help="Standarddiagnose (Default)")
    profile.add_argument("--deep", action="store_true", help="Vollständige Tiefendiagnose")
    parser.add_argument("--ping-count", type=int, default=10, help="Anzahl ICMP-Pings pro Ziel (1–100)")
    parser.add_argument("--dns-host", default="example.com", help="Domain für DNS-Tests")
    parser.add_argument("--save", help="Markdown- oder JSON-Report speichern")
    parser.add_argument("--json", action="store_true", help="Nur JSON auf stdout ausgeben")
    parser.add_argument("--no-geoip", action="store_true", help="Keine externen GeoIP-/Providerinformationen abrufen")
    parser.add_argument("--no-color", action="store_true", help="Rich-Terminalausgabe deaktivieren")
    parser.add_argument("--version", action="version", version=f"{APP_NAME} {APP_VERSION}\n{APP_EDITION}")
    return parser


def calculate_exit_code(health: dict[str, Any]) -> int:
    return {"CRITICAL": EXIT_CRITICAL, "DEGRADED": EXIT_WARNING, "HEALTHY": EXIT_HEALTHY}.get(
        health.get("status"), EXIT_TOOL_ERROR
    )


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if not 1 <= args.ping_count <= 100:
        parser.error("--ping-count muss zwischen 1 und 100 liegen.")

    global HAS_RICH, console
    if args.no_color or args.json or not sys.stdout.isatty():
        HAS_RICH = False
        console = None

    try:
        data = run_diagnostics(args)

        if args.json:
            print(json.dumps(data, indent=2, ensure_ascii=False, default=str))
        elif HAS_RICH:
            render_rich(data)
        else:
            render_plain(data)

        if args.save:
            filename = args.save
            if filename.lower().endswith(".json"):
                save_json(filename, data)
                print_message(f"JSON-Report gespeichert: {filename}", "SUCCESS")
            else:
                if not filename.lower().endswith(".md"):
                    filename += ".md"
                save_markdown(filename, data)
                print_message(f"Markdown-Report gespeichert: {filename}", "SUCCESS")

        if not args.json:
            print_message(
                f"Diagnose abgeschlossen · {data['health']['status']} · "
                f"{data['health']['score']}/100",
                "SUCCESS" if data["health"]["status"] == "HEALTHY" else "WARNING",
            )

        return calculate_exit_code(data["health"])

    except KeyboardInterrupt:
        print("\nDiagnose durch Benutzer abgebrochen.", file=sys.stderr)
        return EXIT_ABORTED
    except Exception as error:
        print(f"\n{APP_NAME}: interner Fehler: {type(error).__name__}: {error}", file=sys.stderr)
        return EXIT_TOOL_ERROR


if __name__ == "__main__":
    sys.exit(main())
