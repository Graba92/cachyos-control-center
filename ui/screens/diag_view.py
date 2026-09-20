#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
 CachyOS Control Center — Diagnostics & Kernel Logs View
 Hardware-Snapshot, Boot-Parameter (/proc/cmdline), Boot-Analyse,
 Live Kernel-Logs (journalctl -k) & Netzwerkprüfungen
===============================================================================
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, DataTable, Label, Static

from core.diagnostics import (
    get_boot_cmdline,
    get_boot_time_analysis,
    get_kernel_logs,
    get_hardware_snapshot,
    run_diagnostic_profile,
    DiagnosticResult,
)
from core.i18n import t


class DiagView(Container):
    DEFAULT_CSS = """
    DiagView {
        width: 100%;
        height: 100%;
        layout: vertical;
    }
    """

    def compose(self) -> ComposeResult:
        with Horizontal(classes="split-h"):
            # Linke Spalte: Boot-Parameter & Systemstart-Analyse
            with Vertical(classes="col-left panel"):
                yield Label(f"🚀  {t('boot_cmdline_title')}", classes="panel-title")
                yield Static("", id="diag_boot_cmdline", classes="term-box")

                yield Label(f"⏱️  {t('boot_analyze_title')}", classes="panel-title")
                yield Static("", id="diag_boot_time", classes="term-box")

                yield Label(f"🔍  {t('hardware_specs_title')}", classes="panel-title")
                yield Static("", id="diag_hardware_box", classes="term-box")

                with Horizontal(classes="toolbar"):
                    yield Button("🌐  Netzwerk-Diagnose", id="btn_run_net_diag", classes="-primary btn-small")
                    yield Button("🔄  Logs neu laden", id="btn_refresh_diag", classes="btn-small")

            # Rechte Spalte: Kernel Logs Feed & Netzwerkübersicht
            with Vertical(classes="col-right panel"):
                yield Label(f"📜  {t('kernel_logs_title')}", classes="panel-title")
                yield Static("", id="diag_kernel_logs", classes="term-box")
                yield DataTable(id="tbl_net_diag")

    def on_mount(self) -> None:
        self._init_tables()
        self.refresh_diagnostics()

    def _init_tables(self) -> None:
        tbl = self.query_one("#tbl_net_diag", DataTable)
        tbl.cursor_type = "row"
        tbl.zebra_stripes = True
        tbl.clear(columns=True)
        tbl.add_columns("Kategorie", "Test", "Status", "Messwert")

    def refresh_diagnostics(self) -> None:
        # Boot Cmdline
        cmdline = get_boot_cmdline()
        # Zeilenumbruch bei Parametern für Lesbarkeit
        fmt_cmdline = " ".join([f"[cyan]{p}[/cyan]" for p in cmdline.split()])
        self.query_one("#diag_boot_cmdline", Static).update(fmt_cmdline)

        # Boot Time
        b_time = get_boot_time_analysis()
        self.query_one("#diag_boot_time", Static).update(f"[bold green]{b_time.get('summary', 'N/A')}[/bold green]")

        # Hardware Snapshot
        hw = get_hardware_snapshot()
        hw_lines = [
            f"[bold cyan]CPU Modell:[/bold cyan]    {hw.get('cpu_model', 'N/A')}",
            f"[bold cyan]Kerne:[/bold cyan]         {hw.get('cpu_cores', 1)} Threads",
            f"[bold cyan]Mainboard:[/bold cyan]     {hw.get('motherboard', 'N/A')}",
            f"[bold cyan]Laufwerke:[/bold cyan]     {', '.join(hw.get('disks', [])) or 'Keine'}",
        ]
        if hw.get("pci_controllers"):
            hw_lines.append("[bold cyan]PCI-Controller:[/bold cyan]")
            for pci in hw.get("pci_controllers", [])[:4]:
                hw_lines.append(f"  • {pci}")

        self.query_one("#diag_hardware_box", Static).update("\n".join(hw_lines))

        # Kernel Logs
        logs = get_kernel_logs(max_lines=25)
        log_lines = []
        for l in logs:
            if "error" in l.lower() or "fail" in l.lower():
                log_lines.append(f"[red]{l}[/red]")
            elif "warn" in l.lower():
                log_lines.append(f"[yellow]{l}[/yellow]")
            else:
                log_lines.append(f"[white]{l}[/white]")
        self.query_one("#diag_kernel_logs", Static).update("\n".join(log_lines))

    def run_network_audit(self) -> None:
        tbl = self.query_one("#tbl_net_diag", DataTable)
        tbl.clear()

        res: DiagnosticResult = run_diagnostic_profile("quick")
        for it in res.items:
            s_col = "green" if it.status == "PASS" else ("yellow" if it.status == "WARN" else "red")
            tbl.add_row(
                it.category,
                it.test_name,
                f"[{s_col}]{it.status}[/{s_col}]",
                it.metric_value,
            )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_run_net_diag":
            self.run_network_audit()
        elif event.button.id == "btn_refresh_diag":
            self.refresh_diagnostics()
