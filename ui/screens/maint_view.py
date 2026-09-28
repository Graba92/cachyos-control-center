#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
 CachyOS Control Center — System Maintenance View
 Mirror-Benchmarking, Paket-Cache-Hygiene, Waisenpakete & .pacnew-Audits
===============================================================================
"""

from __future__ import annotations

import shutil
from textual import work
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, DataTable, Label, Static

from core.maintenance import (
    clean_pacman_cache,
    remove_orphan_packages,
    benchmark_mirrors,
    vacuum_journal,
    find_pacnew_files,
    run_fstrim,
    check_available_updates,
    get_orphan_packages,
    get_pacman_cache_size,
    get_maintenance_timers,
)
from core.polkit import is_pacman_locked
from core.i18n import t


class MaintView(Container):
    DEFAULT_CSS = """
    MaintView {
        width: 100%;
        height: 100%;
        layout: vertical;
    }
    """

    def compose(self) -> ComposeResult:
        with Horizontal(classes="split-h"):
            # Linke Spalte: Paket-Cache & Waisenpakete & Hintergrund-Timer
            with Vertical(classes="col-left panel"):
                yield Label(f"📦  {t('pkg_cache_title')}", classes="panel-title")
                yield Static("", id="maint_cache_status", classes="term-box")

                with Horizontal(classes="toolbar"):
                    yield Button(f"🧹  {t('btn_clean_cache')}", id="btn_maint_clean_cache", classes="-primary btn-small")
                    yield Button(f"🗑️  {t('btn_remove_orphans')}", id="btn_maint_remove_orphans", classes="btn-small")

                yield Label("⏱️  Automatisierte Systemd Hintergrund-Timer:", classes="panel-title")
                yield Static("Echte Systempflege läuft im Hintergrund über systemd-timer. Hier den Status überwachen & aktivieren:", classes="text-muted")
                yield DataTable(id="tbl_timers")
                with Horizontal(classes="toolbar"):
                    yield Button("⚡ fstrim.timer aktivieren", id="btn_maint_enable_fstrim_timer", classes="btn-small")
                    yield Button("⚡ paccache.timer aktivieren", id="btn_maint_enable_paccache_timer", classes="btn-small")

                yield Label(f"🚀  {t('mirror_bench_title')}", classes="panel-title")
                yield Static("Misst die Latenz & Bandbreite aller CachyOS/Arch Mirrors und sortiert die Mirrorlist nach Geschwindigkeit:", classes="text-muted")
                with Horizontal(classes="toolbar"):
                    yield Button(f"⚡  {t('btn_run_mirror_bench')}", id="btn_maint_benchmark_mirrors", classes="btn-small")

                yield Label("Manuelle Ad-hoc Bereinigung:", classes="panel-subtitle")
                with Horizontal(classes="toolbar"):
                    yield Button(f"💾  {t('btn_fstrim')}", id="btn_maint_fstrim", classes="btn-small")
                    yield Button(f"📜  {t('btn_journal_vacuum')}", id="btn_maint_vacuum", classes="btn-small")

                yield Static("", id="maint_action_output", classes="term-box")

            # Rechte Spalte: Waisen-Tabelle & Pacnew-Dateien
            with Vertical(classes="col-right panel"):
                yield Label(f"📄  {t('pacnew_audit_title')}", classes="panel-title")
                yield Static("", id="maint_pacnew_info", classes="term-box")
                
                yield Label("Erkannte Waisenpakete (Unbenutzte Bibliotheken):", classes="panel-subtitle")
                yield DataTable(id="tbl_orphans")

    def on_mount(self) -> None:
        self._init_tables()
        self.query_one("#maint_cache_status", Static).update("[dim]Ermittle System- & Paketstatus...[/dim]")
        self.query_one("#maint_pacnew_info", Static).update("[dim]Prüfe Konfigurationsdateien...[/dim]")
        self.refresh_maintenance_info()

    def _init_tables(self) -> None:
        tbl = self.query_one("#tbl_orphans", DataTable)
        tbl.cursor_type = "row"
        tbl.zebra_stripes = True
        tbl.clear(columns=True)
        tbl.add_columns("Paketname", "Aktion")

        tbl_tim = self.query_one("#tbl_timers", DataTable)
        tbl_tim.cursor_type = "row"
        tbl_tim.zebra_stripes = True
        tbl_tim.clear(columns=True)
        tbl_tim.add_columns("Systemd Timer", "Aktiv", "Autostart", "Aufgabe")

    @work(thread=True)
    def refresh_maintenance_info(self) -> None:
        """Sammelt Telemetrie, Waisenpakete und Systemd-Timer im Hintergrundthread."""
        try:
            cache_sz = get_pacman_cache_size()
            orphans = get_orphan_packages()
            pacnews = find_pacnew_files()
            timers = get_maintenance_timers()
            up_count, up_msg = check_available_updates()
            self.app.call_from_thread(self._apply_ui, cache_sz, orphans, pacnews, timers, up_msg)
        except Exception:
            pass

    def _apply_ui(
        self,
        cache_sz: str,
        orphans: list,
        pacnews: list,
        timers: list,
        up_msg: str,
    ) -> None:
        """Aktualisiert die UI-Komponenten auf dem Main-Thread."""
        try:
            # Cache Status
            cache_lines = [
                f"[bold cyan]Pacman Cache Belegung:[/bold cyan] {cache_sz}",
                f"[bold cyan]Waisenpakete (Orphans):[/bold cyan] {len(orphans)} gefunden",
                f"[bold cyan]Anstehende Updates:[/bold cyan]    {up_msg}",
            ]
            if is_pacman_locked():
                cache_lines.append(f"[bold red]⚠️ {t('db_lock_warn')}[/bold red]")

            self.query_one("#maint_cache_status", Static).update("\n".join(cache_lines))

            # Timer-Tabelle
            tbl_tim = self.query_one("#tbl_timers", DataTable)
            tbl_tim.clear()
            for t_obj in timers:
                act_badge = "[bold green]Aktiv[/bold green]" if t_obj.active else "[bold red]Inaktiv[/bold red]"
                en_badge = "[green]Enabled[/green]" if t_obj.enabled else "[yellow]Disabled[/yellow]"
                tbl_tim.add_row(t_obj.name, act_badge, en_badge, t_obj.description, key=t_obj.name)

            # Pacnew Info
            if pacnews:
                pn_lines = [f"[bold yellow]⚠️ {len(pacnews)} ungemergte .pacnew Konfigurationen gefunden:[/bold yellow]"]
                for p in pacnews:
                    pn_lines.append(f"  • [white]{p}[/white]")
                pn_lines.append("\nTipp: Verwenden Sie [bold cyan]pacdiff[/bold cyan] zum Mergen.")
                self.query_one("#maint_pacnew_info", Static).update("\n".join(pn_lines))
            else:
                self.query_one("#maint_pacnew_info", Static).update(f"[bold green]✓ {t('no_pacnews_found')}[/bold green]")

            # Waisen-Tabelle
            tbl = self.query_one("#tbl_orphans", DataTable)
            tbl.clear()
            if not orphans:
                tbl.add_row(f"[dim]{t('no_orphans_found')}[/dim]", "-")
            else:
                for o in orphans:
                    tbl.add_row(o, "[red]Wird entfernt[/red]", key=o)
        except Exception:
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        out_box = self.query_one("#maint_action_output", Static)

        if btn_id == "btn_maint_clean_cache":
            out_box.update(f"[yellow]{t('status_running')} ({t('action_cache_clean')})[/yellow]")
            self.app.action_quick_clean_cache()
        elif btn_id == "btn_maint_remove_orphans":
            out_box.update(f"[yellow]{t('status_running')} ({t('action_orphan_remove')})[/yellow]")
            self.app.action_quick_remove_orphans()
        elif btn_id == "btn_maint_benchmark_mirrors":
            out_box.update(f"[yellow]{t('status_running')} ({t('action_rate_mirrors')})[/yellow]")
            self.app.action_quick_rate_mirrors()
        elif btn_id == "btn_maint_fstrim":
            out_box.update(f"[yellow]{t('status_running')} ({t('action_trim')})[/yellow]")
            self.app.action_quick_trim()
        elif btn_id == "btn_maint_vacuum":
            out_box.update(f"[yellow]{t('status_running')} (Journalctl Vacuum 50M)[/yellow]")
            self.app.action_quick_journal_vacuum()
        elif btn_id == "btn_maint_enable_fstrim_timer":
            out_box.update("[yellow]Aktiviere fstrim.timer...[/yellow]")
            self.app.action_toggle_maintenance_timer("fstrim.timer", True)
        elif btn_id == "btn_maint_enable_paccache_timer":
            out_box.update("[yellow]Aktiviere paccache.timer...[/yellow]")
            self.app.action_toggle_maintenance_timer("paccache.timer", True)

