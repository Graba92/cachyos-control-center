#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
 CachyOS Control Center — Wi-Fi & Interface Hub View
 Schnittstellen-Audit, Monitor-Mode Injection & Funkumgebungs-Scanner
===============================================================================
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, DataTable, Label, Static

from core.network import (
    get_network_interfaces,
    scan_wifi_networks,
    set_interface_mode,
    kill_wifi_conflicts,
    restart_network_stack,
    NetworkInterface,
    WifiAccessPoint,
)


class WifiView(Container):
    DEFAULT_CSS = """
    WifiView {
        width: 100%;
        height: 100%;
        layout: vertical;
    }
    """

    def compose(self) -> ComposeResult:
        # Obere Hälfte: Schnittstellen
        with Vertical(classes="pane-top"):
            yield Label("🛰️ NETZWERK-SCHNITTSTELLEN (INTERFACES)", classes="section-label")
            yield DataTable(id="wifi_iface_table", cursor_type="row")
            with Horizontal(classes="toolbar"):
                yield Button("[M] Monitor-Mode", id="btn_wifi_mon", classes="-warning")
                yield Button("[S] Managed-Mode", id="btn_wifi_man", classes="-success")
                yield Button("[K] Störprozesse killen", id="btn_wifi_kill", classes="-error")
                yield Button("[R] Network Restart", id="btn_wifi_restart_nm", classes="-default")

        # Untere Hälfte: AP Scan
        with Vertical(classes="pane-bottom"):
            yield Label("📡 FUNKNETZWERK-UMGEBUNG (ACCESS POINTS)", classes="section-label")
            yield DataTable(id="wifi_ap_table", cursor_type="row")
            with Horizontal(classes="toolbar"):
                yield Button("[A] AP-Scan starten", id="btn_wifi_scan", classes="-primary")
                yield Static("Wähle ein Interface oben und klicke auf '[A] AP-Scan starten'.", id="wifi_scan_hint")

    def on_mount(self) -> None:
        if_table = self.query_one("#wifi_iface_table", DataTable)
        if_table.add_columns("Interface", "Typ", "Betriebsmodus", "MAC-Adresse", "Treiber", "Link-Status", "IPv4")

        ap_table = self.query_one("#wifi_ap_table", DataTable)
        ap_table.add_columns("SSID (Netzwerk)", "BSSID", "Kanal", "Signalstärke", "Verschlüsselung")

        self.refresh_interfaces()

    def refresh_interfaces(self) -> None:
        table = self.query_one("#wifi_iface_table", DataTable)
        table.clear()
        ifaces = get_network_interfaces()
        for i in ifaces:
            typ_badge = "[cyan]Wireless 📶[/cyan]" if i.is_wireless else "[blue]Ethernet 🖧[/blue]"
            mode_badge = f"[bold yellow]{i.mode}[/bold yellow]" if i.mode.lower() == "monitor" else f"[green]{i.mode}[/green]"
            link_badge = "[bold green]UP[/bold green]" if i.state == "UP" else f"[dim]{i.state}[/dim]"
            table.add_row(i.name, typ_badge, mode_badge, i.mac, i.driver, link_badge, i.ip4)

    def get_selected_interface(self) -> str | None:
        table = self.query_one("#wifi_iface_table", DataTable)
        try:
            row_idx = table.cursor_row
            return str(table.get_row_at(row_idx)[0])
        except Exception:
            ifaces = get_network_interfaces()
            wls = [i.name for i in ifaces if i.is_wireless]
            return wls[0] if wls else (ifaces[0].name if ifaces else None)

    def populate_scan_results(self, aps: list[WifiAccessPoint]) -> None:
        table = self.query_one("#wifi_ap_table", DataTable)
        table.clear()
        for ap in aps:
            sig_color = "green" if ap.signal >= 60 else ("yellow" if ap.signal >= 35 else "red")
            sig_badge = f"[{sig_color}]{ap.signal}% {ap.bars}[/{sig_color}]"
            table.add_row(ap.ssid, ap.bssid, ap.channel, sig_badge, ap.security)

        hint = self.query_one("#wifi_scan_hint", Static)
        hint.update(f"[green]Scan abgeschlossen: {len(aps)} Funknetzwerke gefunden.[/green]")

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        if event.data_table.id == "wifi_iface_table":
            vals = event.data_table.get_row_at(event.cursor_row)
            iface = str(vals[0])
            mode = str(vals[2])
            hint = self.query_one("#wifi_scan_hint", Static)
            hint.update(f"Ausgewählte Schnittstelle: [bold cyan]{iface}[/bold cyan] │ Modus: {mode}")
