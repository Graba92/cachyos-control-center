#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
 CachyOS Control Center — Tailscale Mesh View
 Topologie, Peer-Inspektion, Exit-Node-Routing & Latenztests
===============================================================================
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, DataTable, Input, Label, Static

from core.tailscale import (
    get_tailscale_status,
    TailscaleNode,
    TailscaleMeshStatus,
)


class TailscaleView(Container):
    DEFAULT_CSS = """
    TailscaleView {
        width: 100%;
        height: 100%;
        layout: vertical;
    }
    """

    def compose(self) -> ComposeResult:
        # Obere Hälfte: Peer Tabelle
        with Vertical(classes="pane-top"):
            yield Label("🧅 TAILSCALE MESH PEERS & TOPOLOGIE", classes="section-label")
            yield DataTable(id="ts_peer_table", cursor_type="row")
            with Horizontal(classes="toolbar"):
                yield Button("[U] Verbinden (Up)", id="btn_ts_start", classes="-primary")
                yield Button("[D] Trennen (Down)", id="btn_ts_stop", classes="-error")
                yield Button("[X] Exit-Node aus", id="btn_ts_no_exit", classes="-default")

        # Untere Hälfte: Split-Details
        with Horizontal(classes="pane-bottom"):
            with Vertical(classes="col-half"):
                yield Label("🔍 AUSGEWÄHLTER KNOTEN", classes="section-label")
                yield Static("Wähle einen Knoten in der Tabelle oben aus.", id="ts_node_detail_box", classes="info-box")
                with Horizontal(classes="toolbar"):
                    yield Button("[E] Als Exit-Node setzen", id="btn_ts_set_exit", classes="-warning")
                    yield Button("[P] Mesh Ping testen", id="btn_ts_ping_node", classes="-default")

            with Vertical(classes="col-half"):
                yield Label("⚡ KNOTEN-TELEMETRIE & PING", classes="section-label")
                yield Static("Klicke auf 'Mesh Ping testen' für Live-Latenz.", id="ts_ping_result_box", classes="info-box")
                yield Input(placeholder="Manueller Exit-Node Hostname / IP...", id="ts_custom_exit_input")

    def on_mount(self) -> None:
        table = self.query_one("#ts_peer_table", DataTable)
        table.add_columns("IP-Adresse", "Hostname", "Betriebssystem", "Status", "Exit-Node")
        self.refresh_tailscale_view()

    def refresh_tailscale_view(self) -> None:
        table = self.query_one("#ts_peer_table", DataTable)
        table.clear()

        status = get_tailscale_status()
        if not status.available:
            self.query_one("#ts_node_detail_box", Static).update("[red]Tailscale ist auf diesem System nicht installiert.[/red]")
            return

        if not status.running:
            self.query_one("#ts_node_detail_box", Static).update(
                f"[yellow]Tailscale Daemon inaktiv ({status.backend_state}). Klicke auf 'Verbinden (Up)'.[/yellow]"
            )
            return

        # Eigenes System
        if status.self_node:
            s = status.self_node
            table.add_row(s.ip, f"{s.hostname} (Dieses Gerät)", s.os_name, "[bold green]Online[/bold green]", "-")

        # Peers
        for p in status.peers:
            st_str = "[bold green]Online[/bold green]" if p.online else "[dim]Offline[/dim]"
            exit_str = "[bold yellow]AKTIVER EXIT-NODE[/bold yellow]" if p.is_exit_node else ("Kandidat" if p.exit_node_option else "-")
            table.add_row(p.ip, p.hostname, p.os_name, st_str, exit_str)

        info = (
            f"[b]Backend-Status:[/b] [green]{status.backend_state}[/green]\n"
            f"[b]Aktiver Exit-Node:[/b] [cyan]{status.active_exit_node or 'Keiner (Direktes Routing)'}[/cyan]\n"
            f"[b]Gesamt-Knoten:[/b] {len(status.peers) + 1} Geräte im Mesh"
        )
        self.query_one("#ts_node_detail_box", Static).update(info)

    def get_selected_peer_ip_or_host(self) -> str | None:
        table = self.query_one("#ts_peer_table", DataTable)
        try:
            row_idx = table.cursor_row
            return str(table.get_row_at(row_idx)[0])
        except Exception:
            return None

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        row_vals = event.data_table.get_row_at(event.cursor_row)
        ip = str(row_vals[0])
        host = str(row_vals[1])
        os_name = str(row_vals[2])
        status = str(row_vals[3])
        exit_val = str(row_vals[4])

        self.query_one("#ts_custom_exit_input", Input).value = ip
        info = (
            f"[b]Gerät:[/b] [cyan]{host}[/cyan]\n"
            f"[b]IP:[/b] {ip}  │  [b]OS:[/b] {os_name}\n"
            f"[b]Status:[/b] {status}  │  [b]Exit-Node Rolle:[/b] {exit_val}"
        )
        self.query_one("#ts_node_detail_box", Static).update(info)
