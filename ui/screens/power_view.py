#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
 CachyOS Control Center — Hardware & Power Profiles View
 CPU Frequenz-Scaling, Governor-Umschaltung, EPP-Profile & Thermal-Monitoring
===============================================================================
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, DataTable, Label, Static

from core.hardware_power import (
    get_complete_power_profile,
    apply_governor,
    apply_epp,
    PowerProfileStatus,
)
from core.i18n import t


class PowerView(Container):
    DEFAULT_CSS = """
    PowerView {
        width: 100%;
        height: 100%;
        layout: vertical;
    }
    """

    def compose(self) -> ComposeResult:
        with Horizontal(classes="split-h"):
            # Linke Spalte: CPU Governors & EPP Profile
            with Vertical(classes="col-left panel"):
                yield Label(f"⚡  {t('cpu_scaling_title')}", classes="panel-title")
                yield Static("", id="power_cpu_summary", classes="term-box")

                yield Label("CPU Governor umschalten (Polkit):", classes="panel-subtitle")
                with Horizontal(classes="toolbar"):
                    yield Button(t("btn_set_gov_perf"), id="btn_gov_performance", classes="-primary btn-small")
                    yield Button(t("btn_set_gov_sched"), id="btn_gov_schedutil", classes="btn-small")
                    yield Button(t("btn_set_gov_powersave"), id="btn_gov_powersave", classes="btn-small")

                yield Label("Energy Performance Preference (EPP):", classes="panel-subtitle")
                with Horizontal(classes="toolbar"):
                    yield Button(t("btn_set_epp_perf"), id="btn_epp_performance", classes="btn-small")
                    yield Button(t("btn_set_epp_balance"), id="btn_epp_balance_perf", classes="btn-small")
                    yield Button(t("btn_set_epp_power"), id="btn_epp_power", classes="btn-small")

                yield Static("", id="power_action_result", classes="term-box")

            # Rechte Spalte: Thermal Monitoring & Throttling
            with Vertical(classes="col-right panel"):
                yield Label(f"🌡️  {t('thermal_title')}", classes="panel-title")
                yield Static("", id="power_throttle_banner", classes="alert-warn")
                yield DataTable(id="tbl_thermals")

    def on_mount(self) -> None:
        self._init_tables()
        self.refresh_power_data()

    def _init_tables(self) -> None:
        tbl = self.query_one("#tbl_thermals", DataTable)
        tbl.cursor_type = "row"
        tbl.zebra_stripes = True
        tbl.clear(columns=True)
        tbl.add_columns(
            t("thermal_zone"),
            "Sensor / Typ",
            t("thermal_temp"),
            "Status",
        )

    def refresh_power_data(self) -> None:
        prof: PowerProfileStatus = get_complete_power_profile()

        # CPU Status formatieren
        gov_color = "green" if prof.cpu.current_governor in ["performance", "schedutil"] else "yellow"
        epp_str = prof.cpu.current_epp or "N/A (Nicht von CPU-Treiber unterstützt)"
        
        freq_str = ""
        if prof.cpu.current_freqs_mhz:
            freq_str = f"{min(prof.cpu.current_freqs_mhz):.0f} MHz - {max(prof.cpu.current_freqs_mhz):.0f} MHz"

        summary_lines = [
            f"[bold cyan]Treiber:[/bold cyan]                 {prof.cpu.driver}",
            f"[bold cyan]{t('current_governor')}:[/bold cyan]      [{gov_color} bold]{prof.cpu.current_governor}[/{gov_color} bold]",
            f"[bold cyan]{t('available_governors')}:[/bold cyan]    {', '.join(prof.cpu.available_governors)}",
            "",
            f"[bold cyan]{t('current_epp')}:[/bold cyan]           {epp_str}",
            f"[bold cyan]{t('available_epp')}:[/bold cyan]         {', '.join(prof.cpu.available_epp) if prof.cpu.available_epp else 'Keine'}",
            "",
            f"[bold cyan]Frequenzspanne:[/bold cyan]          {prof.cpu.min_freq_mhz} - {prof.cpu.max_freq_mhz} MHz",
            f"[bold cyan]Aktuelle Taktung:[/bold cyan]         {freq_str}",
        ]
        self.query_one("#power_cpu_summary", Static).update("\n".join(summary_lines))

        # Throttling Banner
        banner = self.query_one("#power_throttle_banner", Static)
        if prof.is_throttled:
            banner.update(f"[bold red]⚠️  {t('throttle_warning')}[/bold red]\n[dim]{prof.throttle_message}[/dim]")
        else:
            banner.update(f"[bold green]✓  {t('throttle_ok')}[/bold green]")

        # Thermal Tabelle
        tbl = self.query_one("#tbl_thermals", DataTable)
        tbl.clear()
        for z in prof.thermals:
            temp_c = z.temperature_c
            t_col = "green" if temp_c < 60 else ("yellow" if temp_c < 80 else "red")
            status_text = "[red]THROTTLING[/red]" if z.is_throttling else "[green]OK[/green]"
            tbl.add_row(
                z.zone_id,
                z.zone_type,
                f"[{t_col}]{temp_c:.1f} °C[/{t_col}]",
                status_text,
                key=z.zone_id,
            )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        res_box = self.query_one("#power_action_result", Static)

        if btn_id == "btn_gov_performance":
            self.app.action_apply_cpu_governor("performance")
        elif btn_id == "btn_gov_schedutil":
            self.app.action_apply_cpu_governor("schedutil")
        elif btn_id == "btn_gov_powersave":
            self.app.action_apply_cpu_governor("powersave")
        elif btn_id == "btn_epp_performance":
            self.app.action_apply_epp_profile("performance")
        elif btn_id == "btn_epp_balance_perf":
            self.app.action_apply_epp_profile("balance_performance")
        elif btn_id == "btn_epp_power":
            self.app.action_apply_epp_profile("power")
