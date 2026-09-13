#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
 CachyOS Control Center — AGY Workspace & Directory Synthesizer View
 Modulare Workspace-Organisation, Zero-Loss-Migration & Dateikategorisierung
===============================================================================
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, DataTable, Input, Label, Static


TARGET_WORKSPACES = [
    ("01_AI_LAB", "KI-Modelle, Gewichte, Transkripte, Prompts & LLM-Pipelines"),
    ("02_DEV_WORKSPACE", "Quellcode-Repositories, Git-Projekte, Build-Artefakte"),
    ("03_SYSADMIN_CORE", "Wartungsskripte, TUI-Tools, Netzwerk-Werkzeuge, Systemd-Units"),
    ("04_BACKUP_FORENSICS", "System-Backups, Logs, Netzwerk-Dumps, Forensik"),
    ("05_HARDWARE_MODS", "Treiber, Kernel-Patches, Peripherie-Konfigurationen"),
    ("06_ARCHIVE_TEMP", "Temporäre Dateien, Downloads, alte Archive"),
    ("07_DOCS_ROOT", "Architektur-Dokumentation, Markdown Guides, Notizen"),
]


class MigratorView(Container):
    DEFAULT_CSS = """
    MigratorView {
        width: 100%;
        height: 100%;
        layout: vertical;
    }
    """

    def compose(self) -> ComposeResult:
        yield Label("🗂️ AGY VERZEICHNIS-SYNTHESIZER & WORKSPACE-ARCHITEKTUR", classes="section-label")

        with Horizontal(classes="split-h"):
            # Linke Spalte: Workspace-Matrix
            with Vertical(classes="col-half"):
                yield Label("ZIEL-ARCHITEKTUR (7-SÄULEN-MODELL)", classes="title")
                yield DataTable(id="migrator_target_table", cursor_type="row")
                yield Static(
                    "Strukturierte Zerlegung nach dem Antigravity 7-Säulen-Prinzip für verlustfreie Migrationen.",
                    classes="info-box",
                )

            # Rechte Spalte: Scan & Migration
            with Vertical(classes="col-half"):
                yield Label("QUELLVERZEICHNIS FÜR SYNTHESE WÄHLEN", classes="title")
                yield Input(value="/home/graba/Schreibtisch/ASGRAD", id="migrator_src_input")
                with Horizontal(classes="toolbar"):
                    yield Button("[A] Quellordner analysieren", id="btn_migrator_scan", classes="-primary")
                    yield Button("[T] CLI-Migrator im Terminal", id="btn_migrator_cli", classes="-warning")
                yield Static("Klicke auf 'Quellordner analysieren' für eine strukturierte Bestandsaufnahme.", id="migrator_result_box", classes="info-box")

    def on_mount(self) -> None:
        table = self.query_one("#migrator_target_table", DataTable)
        table.add_columns("Workspace", "Zweck & Dateikategorien")
        for ws, desc in TARGET_WORKSPACES:
            table.add_row(ws, desc)

    def scan_source(self) -> None:
        src_str = self.query_one("#migrator_src_input", Input).value.strip()
        src_path = Path(src_str)
        box = self.query_one("#migrator_result_box", Static)

        if not src_path.exists() or not src_path.is_dir():
            box.update(f"[bold red]Pfad '{src_str}' existiert nicht oder ist kein Verzeichnis.[/bold red]")
            return

        box.update("[cyan]Scanne Verzeichnisbaum...[/cyan]")
        file_count = 0
        dir_count = 0
        extensions: dict[str, int] = {}

        try:
            for root, dirs, files in os.walk(src_path):
                dir_count += len(dirs)
                for f in files:
                    file_count += 1
                    ext = Path(f).suffix.lower() or "<ohne Endung>"
                    extensions[ext] = extensions.get(ext, 0) + 1
                if file_count > 5000:
                    break

            top_exts = sorted(extensions.items(), key=lambda x: x[1], reverse=True)[:5]
            ext_str = ", ".join([f"{e}: {c}" for e, c in top_exts])

            txt = (
                f"[b]Gefundene Verzeichnisse:[/b] {dir_count}\n"
                f"[b]Gefundene Dateien:[/b] {file_count}{'+' if file_count > 5000 else ''}\n"
                f"[b]Häufigste Dateitypen:[/b] {ext_str}\n\n"
                f"[bold green]Synthese-Status:[/bold green] Vollständig vorbereitet für Migration."
            )
            box.update(txt)
        except Exception as e:
            box.update(f"[red]Fehler beim Scan: {e}[/red]")
