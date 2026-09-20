#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
 CachyOS Control Center — Services View
 Überwachung & Steuerung von Systemd-Diensten mit Polkit-Berechtigungsisolation
===============================================================================
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, DataTable, Label, Static

from core.system import get_services_status, ServiceStatus
from core.polkit import polkit_service_action
from core.i18n import t


class ServicesView(Container):
    DEFAULT_CSS = """
    ServicesView {
        width: 100%;
        height: 100%;
        layout: vertical;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(classes="panel"):
            with Horizontal(classes="toolbar"):
                yield Label(f"⚙️  {t('services_title')}", classes="panel-title")
                yield Button(f"🔄  {t('btn_reload_services')}", id="btn_refresh_services", classes="btn-small")
                yield Button(f"▶️  {t('btn_start_service')}", id="btn_srv_start", classes="-primary btn-small")
                yield Button(f"⏹️  {t('btn_stop_service')}", id="btn_srv_stop", classes="btn-small")
                yield Button(f"🔄  {t('btn_restart_service')}", id="btn_srv_restart", classes="btn-small")
                yield Button(f"✅  {t('btn_enable_service')}", id="btn_srv_enable", classes="btn-small")
                yield Button(f"❌  {t('btn_disable_service')}", id="btn_srv_disable", classes="btn-small")

            yield DataTable(id="tbl_services")
            yield Static("", id="services_action_status", classes="term-box")

    def on_mount(self) -> None:
        self._init_tables()
        self.refresh_services()

    def _init_tables(self) -> None:
        tbl = self.query_one("#tbl_services", DataTable)
        tbl.cursor_type = "row"
        tbl.zebra_stripes = True
        tbl.clear(columns=True)
        tbl.add_columns(
            t("col_service"),
            t("col_state"),
            t("col_substate"),
            t("col_enabled"),
        )

    def refresh_services(self) -> None:
        tbl = self.query_one("#tbl_services", DataTable)
        tbl.clear()

        # Liste der zentralen System- und Performance-Dienste
        monitored = [
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
            "cronie",
            "cups",
        ]

        statuses = get_services_status(monitored)
        for s in statuses:
            if s.active:
                state_str = f"[bold green]● {s.status_text}[/bold green]"
            else:
                state_str = f"[bold red]○ {s.status_text}[/bold red]"

            en_str = "[bold green]Aktiviert[/bold green]" if s.enabled else "[dim]Deaktiviert[/dim]"

            tbl.add_row(
                s.name,
                state_str,
                s.substate,
                en_str,
                key=s.name,
            )

    def _get_selected_service(self) -> str:
        tbl = self.query_one("#tbl_services", DataTable)
        if tbl.row_count > 0:
            try:
                row_key, _ = tbl.coordinate_to_cell_key(tbl.cursor_coordinate)
                return str(row_key.value)
            except Exception:
                pass
        return ""

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        status_box = self.query_one("#services_action_status", Static)

        if btn_id == "btn_refresh_services":
            self.refresh_services()
            status_box.update("[green]Diensteliste aktualisiert.[/green]")
            return

        srv = self._get_selected_service()
        if not srv:
            status_box.update("[yellow]Bitte wählen Sie einen Dienst aus der Tabelle aus.[/yellow]")
            return

        action_map = {
            "btn_srv_start": "start",
            "btn_srv_stop": "stop",
            "btn_srv_restart": "restart",
            "btn_srv_enable": "enable",
            "btn_srv_disable": "disable",
        }

        action = action_map.get(btn_id)
        if action:
            status_box.update(f"[yellow]Führe 'systemctl {action} {srv}' via Polkit aus...[/yellow]")
            self.app.action_execute_service_action(srv, action)
