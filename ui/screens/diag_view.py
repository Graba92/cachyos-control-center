#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
 CachyOS Control Center — Network Deep Diagnostics View
 Multi-Profile-Diagnostik, DNSSEC-Validierung, MTU-Audits & Remediation
===============================================================================
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, DataTable, Label, Static

from core.diagnostics import (
    run_diagnostic_profile,
    DiagnosticResult,
    DiagnosticItem,
)


class DiagView(Container):
    DEFAULT_CSS = """
    DiagView {
        width: 100%;
        height: 100%;
        layout: vertical;
    }
    """

    def compose(self) -> ComposeResult:
        yield Label("🔍 EVIDENZBASIERTE NETZWERK- & URSACHENANALYSE", classes="section-label")

        with Horizontal(classes="toolbar"):
            yield Button("[Q] Schnelldiagnose", id="btn_diag_run_quick", classes="-primary")
            yield Button("[S] Standard-Audit", id="btn_diag_run_standard", classes="-success")
            yield Button("[D] Tiefen-Audit", id="btn_diag_run_deep", classes="-warning")
            yield Button("[C] CLI net_diagnose", id="btn_diag_run_full", classes="-default")

        yield DataTable(id="diag_results_table", cursor_type="row")

        yield Label("ANALYSE & HANDLUNGSEMPFEHLUNG DES AUSGEWÄHLTEN PRÜFPUNKTS:", classes="section-label")
        yield Static("Wähle ein Diagnoseprofil oben, um die Tests auszuführen.", id="diag_remediation_box", classes="info-box")

    def on_mount(self) -> None:
        table = self.query_one("#diag_results_table", DataTable)
        table.add_columns("Kategorie", "Prüfpunkt", "Status", "Messwert", "Details")
        self._last_items: list[DiagnosticItem] = []

    def populate_results(self, res: DiagnosticResult) -> None:
        table = self.query_one("#diag_results_table", DataTable)
        table.clear()
        self._last_items = res.items

        for item in res.items:
            if item.status == "PASS":
                st_badge = "[bold green]✔ PASS[/bold green]"
            elif item.status == "WARN":
                st_badge = "[bold yellow]⚠ WARN[/bold yellow]"
            else:
                st_badge = "[bold red]✘ FAIL[/bold red]"
            table.add_row(item.category, item.test_name, st_badge, item.metric_value, item.details)

        health_color = "green" if res.overall_health == "HEALTHY" else ("yellow" if res.overall_health == "DEGRADED" else "red")
        box = self.query_one("#diag_remediation_box", Static)
        box.update(
            f"Gesamtzustand: [{health_color}][b]{res.overall_health}[/b][/{health_color}]  │  "
            f"Dauer: {res.duration_seconds}s  │  "
            f"Klicke auf eine Zeile für Detail-Empfehlungen."
        )

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        idx = event.cursor_row
        if 0 <= idx < len(self._last_items):
            item = self._last_items[idx]
            rem = item.recommendation or "Keine Auffälligkeiten — Konfiguration ist optimal."
            text = (
                f"[b]Kategorie:[/b] {item.category}  │  [b]Prüfpunkt:[/b] [cyan]{item.test_name}[/cyan]\n"
                f"[b]Status:[/b] {item.status}  │  [b]Messwert:[/b] {item.metric_value}\n"
                f"[b]Details:[/b] {item.details}\n"
                f"[b]Handlungsempfehlung:[/b] [yellow]{rem}[/yellow]"
            )
            self.query_one("#diag_remediation_box", Static).update(text)
