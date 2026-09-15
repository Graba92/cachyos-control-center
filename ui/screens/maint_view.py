#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
 CachyOS Control Center — Maintenance & System Hygiene View
 Pacman Cache, Journal Vacuum, Pacnew Auditor, Failed Unit Resets & CLI Suites
===============================================================================
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, DataTable, Label, Static

from core.maintenance import find_pacnew_files


class MaintView(Container):
    DEFAULT_CSS = """
    MaintView {
        width: 100%;
        height: 100%;
        layout: vertical;
    }
    """

    def compose(self) -> ComposeResult:
        yield Label("🔒 CACHYOS SYSTEMHYGIENE & WARTUNGSZENTRUM", classes="section-label")

        with Horizontal(classes="split-h"):
            # Linke Spalte: Wartungs-Aktionen
            with Vertical(classes="col-half"):
                yield Label("⚡ HYGIENE- & SPEICHEROPERATIONEN", classes="title")
                with Vertical(classes="panel"):
                    yield Button("[C] Pacman Cache leeren (paccache)", id="btn_maint_cache", classes="-warning")
                    yield Button("[J] Journal trimmen (50M)", id="btn_maint_journal", classes="-warning")
                    yield Button("[R] Fehlgeschlagene Units resetten", id="btn_maint_reset_units", classes="-error")
                    yield Button("[T] SSD TRIM (fstrim)", id="btn_maint_fstrim", classes="-default")
                    yield Button("[U] Paketupdates prüfen", id="btn_maint_check_updates", classes="-primary")

                yield Label("EXTERNE WARTUNGSSUITEN (IM TERMINAL)", classes="title")
                with Horizontal(classes="toolbar"):
                    yield Button("[W] wartung-os.sh", id="btn_maint_launch_wartung", classes="-primary")
                    yield Button("[M] Ultimate Manager", id="btn_maint_launch_manager", classes="-default")

            # Rechte Spalte: Pacnew Auditor
            with Vertical(classes="col-half"):
                yield Label("📄 UNGEMERGTE .PACNEW DATEIEN IN /ETC", classes="title")
                yield DataTable(id="maint_pacnew_table", cursor_type="row")
                with Horizontal(classes="toolbar"):
                    yield Button("[S] Pacnew Scan aktualisieren", id="btn_maint_refresh_pacnew", classes="-default")
                yield Static(
                    "Tipp: .pacnew Dateien entstehen bei Updates, wenn geänderte Konfigurationen kollidieren. "
                    "Nutze 'pacdiff' oder meld im Terminal für den Drei-Wege-Merge.",
                    id="maint_pacnew_info",
                    classes="info-box",
                )

    def on_mount(self) -> None:
        table = self.query_one("#maint_pacnew_table", DataTable)
        table.add_columns("Dateipfad in /etc", "Status")
        self.refresh_pacnew_list()

    def refresh_pacnew_list(self) -> None:
        table = self.query_one("#maint_pacnew_table", DataTable)
        table.clear()
        pacnews = find_pacnew_files()
        for p in pacnews:
            table.add_row(p, "[bold yellow]Ungemergt[/bold yellow]")

        info = self.query_one("#maint_pacnew_info", Static)
        if pacnews:
            info.update(
                f"[bold yellow]Gefunden: {len(pacnews)} ungemergte .pacnew Dateien.[/bold yellow]\n"
                f"Ausstehende Dateien gefährden langfristig die Systemstabilität. Abgleich mit pacdiff empfohlen."
            )
        else:
            info.update("[bold green]Perfekt: Keine ungemergten .pacnew Dateien gefunden.[/bold green]")

    def launch_terminal_script(self, script_name: str) -> bool:
        """Startet ein externes Wartungsskript in einem separaten Terminal."""
        local_bin = Path(__file__).resolve().parent.parent.parent / "bin"
        user_scripts = Path.home() / ".local" / "bin"
        
        target = local_bin / script_name
        if not target.exists():
            target = user_scripts / script_name
        if not target.exists():
            return False

        term_cmd = None
        for term in ["alacritty", "konsole", "ghostty", "kitty", "xterm"]:
            if shutil.which(term):
                term_cmd = [term, "-e", "bash", str(target)]
                break

        if term_cmd:
            subprocess.Popen(term_cmd)
            return True
        return False
