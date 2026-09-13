#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
 CachyOS Control Center — Dashboard (System-Cockpit)
 Reine Status-, Hardware- und Telemetrieübersicht ohne Funktionsduplikate
===============================================================================
"""

from __future__ import annotations

import shutil
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, DataTable, Label, Static

from core.system import (
    get_system_telemetry,
    get_services_status,
    SystemTelemetry,
    ServiceStatus,
    run_cmd,
)
from core.maintenance import find_pacnew_files
from core.tailscale import get_tailscale_status


def _render_bar(percent: float, width: int = 14) -> str:
    """Erzeugt einen scharfkantigen ASCII-Auslastungsbalken."""
    filled = int(round((percent / 100.0) * width))
    filled = max(0, min(width, filled))
    bar = "█" * filled + "░" * (width - filled)
    color = "green" if percent < 70 else ("yellow" if percent < 85 else "red")
    return f"[{color}]{bar}[/{color}] {percent:.1f}%"


class DashboardView(Container):
    DEFAULT_CSS = """
    DashboardView {
        width: 100%;
        height: 100%;
        layout: vertical;
    }
    """

    def compose(self) -> ComposeResult:
        # Top KPI-Karten
        with Horizontal(classes="cards-row"):
            with Vertical(classes="kpi-card"):
                yield Label("PROZESSOR (CPU)", classes="kpi-title")
                yield Static("-- %", id="dash_kpi_cpu_val", classes="kpi-value")
                yield Static("-- Kerne", id="dash_kpi_cpu_sub", classes="kpi-sub")

            with Vertical(classes="kpi-card"):
                yield Label("ARBEITSSPEICHER (RAM)", classes="kpi-title")
                yield Static("-- GB", id="dash_kpi_ram_val", classes="kpi-value")
                yield Static("-- % belegt", id="dash_kpi_ram_sub", classes="kpi-sub")

            with Vertical(classes="kpi-card"):
                yield Label("ROOT-DATEISYSTEM (/)", classes="kpi-title")
                yield Static("-- GB", id="dash_kpi_disk_val", classes="kpi-value")
                yield Static("BTRFS", id="dash_kpi_disk_sub", classes="kpi-sub")

            with Vertical(classes="kpi-card"):
                yield Label("SYSTEM-IDENTITÄT", classes="kpi-title")
                yield Static("CachyOS Linux", id="dash_kpi_os_val", classes="kpi-value")
                yield Static("Uptime: --", id="dash_kpi_os_sub", classes="kpi-sub")

        # Hauptbereich: Split Layout
        with Horizontal(classes="split-h"):
            # Linke Spalte: Services-Matrix
            with Vertical(classes="col-left"):
                yield Label("🔒 STATUS DER SYSTEMD-KERN-DIENSTE", classes="section-label")
                yield DataTable(id="dash_services_table", cursor_type="row")

            # Rechte Spalte: Systemintegrität & Aktionen
            with Vertical(classes="col-right"):
                yield Label("🛡️ SYSTEM-INTEGRITÄT & NETZWERK-AUDIT", classes="section-label")
                yield Static("Ermittle Systemzustand...", id="dash_combined_status_box", classes="info-box")

                yield Label("⚡ COCKPIT-SOFORTAKTIONEN", classes="section-label")
                with Vertical(classes="panel"):
                    yield Button("[D] Schnelldiagnose ausführen", id="btn_quick_diag", classes="-primary")
                    yield Button("[C] Pacman Cache leeren (paccache)", id="btn_quick_cache", classes="-warning")
                    yield Button("[J] Journal-Logs trimmen (50M)", id="btn_quick_journal", classes="-warning")
                    yield Button("[R] Fehlgeschlagene Units resetten", id="btn_quick_reset_units", classes="-error")
                    yield Button("[A] Telemetrie aktualisieren", id="btn_dash_refresh", classes="-default")

    def on_mount(self) -> None:
        table = self.query_one("#dash_services_table", DataTable)
        table.add_columns("Dienst", "Status", "Substate", "Starttyp")
        self.refresh_dashboard()

    def refresh_dashboard(self) -> None:
        t = get_system_telemetry()

        # 1. Update KPI-Gauges
        self.query_one("#dash_kpi_cpu_val", Static).update(_render_bar(t.cpu_percent))
        self.query_one("#dash_kpi_cpu_sub", Static).update(f"{t.cpu_cores} Kerne aktiv │ Last stabil")

        self.query_one("#dash_kpi_ram_val", Static).update(_render_bar(t.ram_percent))
        self.query_one("#dash_kpi_ram_sub", Static).update(f"{t.ram_used_gb} GB von {t.ram_total_gb} GB")

        self.query_one("#dash_kpi_disk_val", Static).update(_render_bar(t.disk_percent))
        fs_str = "Btrfs (CoW & Snapshots)" if t.is_btrfs else "Standard-Dateisystem"
        self.query_one("#dash_kpi_disk_sub", Static).update(f"{t.disk_used_gb} / {t.disk_total_gb} GB ({fs_str})")

        self.query_one("#dash_kpi_os_val", Static).update(f"[bold cyan]{t.os_name}[/bold cyan]")
        self.query_one("#dash_kpi_os_sub", Static).update(f"Up: {t.uptime_str} │ Kernel: {t.kernel}")

        # 2. Update Services-Matrix
        table = self.query_one("#dash_services_table", DataTable)
        table.clear()
        services = get_services_status(["NetworkManager", "tailscaled", "sshd", "syncthing", "docker", "bluetooth"])
        for s in services:
            st_badge = "[bold green]● AKTIV[/bold green]" if s.active else "[dim]○ INAKTIV[/dim]"
            en_badge = "[green]Autostart[/green]" if s.enabled else "[dim]Manuell[/dim]"
            table.add_row(s.name, st_badge, s.substate, en_badge)

        # 3. Update Integritäts- und Netzwerkdaten
        pacnews = find_pacnew_files()
        pacnew_msg = (
            f"[bold yellow]⚠ {len(pacnews)} ungemergte .pacnew Konfigurationen in /etc[/bold yellow] (Tab 5 'Wartung')"
            if pacnews
            else "[green]✔ Keine .pacnew Konflikte vorhanden[/green]"
        )

        units_total = t.failed_system_units + t.failed_user_units
        units_msg = (
            f"[bold red]⚠ {units_total} fehlgeschlagene Einheiten ({t.failed_system_units} System, {t.failed_user_units} User)![/bold red] (Tab 5 'Wartung')"
            if units_total > 0
            else "[green]✔ Alle Systemd-Einheiten laufen fehlerfrei[/green]"
        )

        gw_out, _, _ = run_cmd("ip route | awk '/default/ {print $3 \" via \" $5}' | head -n 1")
        ip_out, _, _ = run_cmd("ip -4 -o addr show scope global | awk '{print $2 \": \" $4}' | head -n 2")
        dns_out, _, _ = run_cmd("grep 'nameserver' /etc/resolv.conf 2>/dev/null | awk '{print $2}' | head -n 2")

        ts = get_tailscale_status()
        ts_ip = ts.self_node.ip if (ts.running and ts.self_node) else "Nicht verbunden"

        combined_text = (
            f"[b]INTEGRITÄTS-AUDIT:[/b]\n"
            f"• Rechner: [cyan]{t.hostname}[/cyan] ({t.architecture}) │ Kernel: {t.kernel}\n"
            f"• Konfiguration: {pacnew_msg}\n"
            f"• Systemd-Units: {units_msg}\n\n"
            f"[b]NETZWERK & MESH-ROUTING:[/b]\n"
            f"• Lokale IPv4: {ip_out.replace(chr(10), ' │ ') or 'Keine aktive Verbindung'}\n"
            f"• Standard-Gateway: {gw_out or 'Keine Standard-Route'}\n"
            f"• DNS-Resolver: {dns_out.replace(chr(10), ', ') or 'systemd-resolved'}\n"
            f"• Tailscale Mesh-IP: [cyan]{ts_ip}[/cyan]"
        )
        self.query_one("#dash_combined_status_box", Static).update(combined_text)
