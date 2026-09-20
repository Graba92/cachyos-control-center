#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
 CachyOS Control Center — Dashboard (System-Cockpit)
 KPI-Karten, Telemetrieübersicht, aktiver Kernel & administrative Schnellaktionen
===============================================================================
"""

from __future__ import annotations

import shutil
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, DataTable, Label, Static

from core.system import get_system_telemetry, SystemTelemetry
from core.kernel_driver import get_running_kernel
from core.maintenance import clean_pacman_cache, remove_orphan_packages, run_fstrim, reset_failed_units, benchmark_mirrors
from core.polkit import is_pacman_locked
from core.i18n import t


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
                yield Label(t("kpi_cpu_title"), id="kpi_title_cpu", classes="kpi-title")
                yield Static("-- %", id="dash_kpi_cpu_val", classes="kpi-value")
                yield Static("-- Kerne", id="dash_kpi_cpu_sub", classes="kpi-sub")

            with Vertical(classes="kpi-card"):
                yield Label(t("kpi_ram_title"), id="kpi_title_ram", classes="kpi-title")
                yield Static("-- GB", id="dash_kpi_ram_val", classes="kpi-value")
                yield Static("-- % belegt", id="dash_kpi_ram_sub", classes="kpi-sub")

            with Vertical(classes="kpi-card"):
                yield Label(t("kpi_disk_title"), id="kpi_title_disk", classes="kpi-title")
                yield Static("-- GB", id="dash_kpi_disk_val", classes="kpi-value")
                yield Static("-- % belegt", id="dash_kpi_disk_sub", classes="kpi-sub")

            with Vertical(classes="kpi-card"):
                yield Label(t("kpi_kernel_title"), id="kpi_title_kernel", classes="kpi-title")
                yield Static("--", id="dash_kpi_kernel_val", classes="kpi-value")
                yield Static("CachyOS Linux", id="dash_kpi_kernel_sub", classes="kpi-sub")

            with Vertical(classes="kpi-card"):
                yield Label(t("kpi_health_title"), id="kpi_title_health", classes="kpi-title")
                yield Static("HEALTHY", id="dash_kpi_health_val", classes="kpi-value")
                yield Static("0 Failed Units", id="dash_kpi_health_sub", classes="kpi-sub")

        # Hauptbereich: Split Horizontal
        with Horizontal(classes="split-h"):
            # Linke Spalte: Detaillierte Telemetrie & Hostinfo
            with Vertical(classes="col-left panel"):
                yield Label(f"🖥️  {t('telemetry_details')}", classes="panel-title")
                yield Static("", id="dash_telemetry_box", classes="term-box")
                yield Static("", id="dash_pacman_warn", classes="alert-warn")

            # Rechte Spalte: Schnellaktionen
            with Vertical(classes="col-right panel"):
                yield Label(f"⚡  {t('quick_actions')}", classes="panel-title")
                yield Static("Führt administrative Wartungsaufgaben sicher mit Polkit-Isolation aus:", classes="text-muted")
                
                with Vertical(classes="control-box"):
                    yield Button(f"🧹  {t('action_cache_clean')}", id="btn_quick_clean_cache", classes="-primary")
                    yield Button(f"🗑️  {t('action_orphan_remove')}", id="btn_quick_remove_orphans")
                    yield Button(f"🚀  {t('action_rate_mirrors')}", id="btn_quick_rate_mirrors")
                    yield Button(f"💾  {t('action_trim')}", id="btn_quick_trim")
                    yield Button(f"🔄  {t('action_reset_failed')}", id="btn_quick_reset_failed")

                yield Static("", id="dash_action_status", classes="term-box")

    def on_mount(self) -> None:
        self.refresh_telemetry()

    def refresh_telemetry(self) -> None:
        t_data = get_system_telemetry()
        running_kernel = get_running_kernel()

        # Update KPIs
        self.query_one("#dash_kpi_cpu_val", Static).update(f"{t_data.cpu_percent}%")
        self.query_one("#dash_kpi_cpu_sub", Static).update(t("kpi_cores", cores=t_data.cpu_cores))

        self.query_one("#dash_kpi_ram_val", Static).update(f"{t_data.ram_used_gb} / {t_data.ram_total_gb} GB")
        self.query_one("#dash_kpi_ram_sub", Static).update(f"{t_data.ram_percent}% belegt")

        self.query_one("#dash_kpi_disk_val", Static).update(f"{t_data.disk_used_gb} / {t_data.disk_total_gb} GB")
        fs_type = t("kpi_disk_btrfs") if t_data.is_btrfs else t("kpi_disk_standard")
        self.query_one("#dash_kpi_disk_sub", Static).update(f"{t_data.disk_percent}% ({fs_type})")

        self.query_one("#dash_kpi_kernel_val", Static).update(running_kernel.split("-cachyos")[0])
        self.query_one("#dash_kpi_kernel_sub", Static).update(running_kernel)

        total_failed = t_data.failed_system_units + t_data.failed_user_units
        if total_failed > 0:
            self.query_one("#dash_kpi_health_val", Static).update("[red]WARN[/red]")
            self.query_one("#dash_kpi_health_sub", Static).update(t("kpi_failed_units", count=total_failed))
        else:
            self.query_one("#dash_kpi_health_val", Static).update("[green]HEALTHY[/green]")
            self.query_one("#dash_kpi_health_sub", Static).update(t("kpi_all_clean"))

        # Pacman Lock Prüfung
        pac_warn = self.query_one("#dash_pacman_warn", Static)
        if is_pacman_locked():
            pac_warn.update(f"[bold red]⚠️ {t('db_lock_warn')}[/bold red]")
        else:
            pac_warn.update("")

        # Detail-Box formatieren
        detail_lines = [
            f"[bold cyan]{t('hostname')}:[/bold cyan]      {t_data.hostname}",
            f"[bold cyan]{t('os_version')}:[/bold cyan] {t_data.os_name} ({t_data.architecture})",
            f"[bold cyan]{t('uptime')}:[/bold cyan]          {t_data.uptime_str}",
            f"[bold cyan]Root FS:[/bold cyan]          {'BTRFS (Subvolumes aktiv)' if t_data.is_btrfs else 'ext4/Standard'}",
            "",
            f"[bold yellow]CPU:[/bold yellow]              {_render_bar(t_data.cpu_percent)}",
            f"[bold yellow]RAM:[/bold yellow]              {_render_bar(t_data.ram_percent)} ({t_data.ram_used_gb}G / {t_data.ram_total_gb}G)",
            f"[bold yellow]Disk (/):[/bold yellow]         {_render_bar(t_data.disk_percent)} ({t_data.disk_used_gb}G / {t_data.disk_total_gb}G)",
            "",
            f"[bold magenta]Systemd Units:[/bold magenta]    {t_data.failed_system_units} System fehlgeschlagen │ {t_data.failed_user_units} User fehlgeschlagen",
        ]
        if t_data.failed_unit_names:
            detail_lines.append(f"[red]Fehlgeschlagene Dienste: {', '.join(t_data.failed_unit_names[:3])}[/red]")

        self.query_one("#dash_telemetry_box", Static).update("\n".join(detail_lines))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        status_box = self.query_one("#dash_action_status", Static)

        if btn_id == "btn_quick_clean_cache":
            status_box.update(f"[yellow]{t('status_running')} ({t('action_cache_clean')})[/yellow]")
            self.app.action_quick_clean_cache()
        elif btn_id == "btn_quick_remove_orphans":
            status_box.update(f"[yellow]{t('status_running')} ({t('action_orphan_remove')})[/yellow]")
            self.app.action_quick_remove_orphans()
        elif btn_id == "btn_quick_rate_mirrors":
            status_box.update(f"[yellow]{t('status_running')} ({t('action_rate_mirrors')})[/yellow]")
            self.app.action_quick_rate_mirrors()
        elif btn_id == "btn_quick_trim":
            status_box.update(f"[yellow]{t('status_running')} ({t('action_trim')})[/yellow]")
            self.app.action_quick_trim()
        elif btn_id == "btn_quick_reset_failed":
            status_box.update(f"[yellow]{t('status_running')} ({t('action_reset_failed')})[/yellow]")
            self.app.action_quick_reset_failed()
