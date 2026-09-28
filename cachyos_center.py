#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
 CACHYOS CONTROL CENTER & SYSTEM ARCHITECT (TUI)
 Unified Modular System Administration Dashboard & Control Utility
 Tailored for CachyOS and Arch Linux
 Edition 2026 — Made by Matze Graba & Chati
===============================================================================
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from rich.text import Text

# Dependency Check
try:
    from textual import work
    from textual.app import App, ComposeResult
    from textual.binding import Binding
    from textual.containers import Container, Horizontal, Vertical
    from textual.widgets import (
        Button,
        DataTable,
        Footer,
        Header,
        Input,
        Label,
        Static,
        TabbedContent,
        TabPane,
    )
except ImportError:
    print("[FEHLER] 'textual' Bibliothek nicht gefunden.")
    print("Installation: sudo pacman -S python-textual  ODER  pip install textual")
    sys.exit(1)

# Lokale Pfade registrieren
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from core.i18n import t, set_language, get_language, toggle_language
from core.config import load_config, save_user_config
from core.system import get_system_telemetry, get_services_status, run_cmd
from core.kernel_driver import (
    get_running_kernel,
    list_cachyos_kernels,
    detect_gpu_devices,
    install_kernel,
    remove_kernel,
)
from core.hardware_power import (
    get_complete_power_profile,
    apply_governor,
    apply_epp,
)
from core.maintenance import (
    clean_pacman_cache,
    remove_orphan_packages,
    benchmark_mirrors,
    vacuum_journal,
    find_pacnew_files,
    reset_failed_units,
    run_fstrim,
    check_available_updates,
    get_maintenance_timers,
    toggle_maintenance_timer,
)
from core.polkit import polkit_service_action, is_pacman_locked
from core.diagnostics import run_diagnostic_profile
from ui.theme import APP_TCSS
from ui.screens.dashboard_view import DashboardView
from ui.screens.kernel_view import KernelView
from ui.screens.power_view import PowerView
from ui.screens.maint_view import MaintView
from ui.screens.services_view import ServicesView
from ui.screens.diag_view import DiagView
from ui.screens.wifi_view import WifiView
from ui.screens.tailscale_view import TailscaleView


class CachyOSCenterApp(App):
    TITLE = "CACHYOS CONTROL CENTER & SYSTEM ARCHITECT"
    SUB_TITLE = "Professional Edition │ CachyOS Linux x86_64"
    CSS = APP_TCSS
    ENABLE_COMMAND_PALETTE = False

    BINDINGS = [
        Binding("1", "switch_tab('tab_dash')", "1. Cockpit"),
        Binding("2", "switch_tab('tab_kernel')", "2. Kernel & Treiber"),
        Binding("3", "switch_tab('tab_power')", "3. Hardware & Power"),
        Binding("4", "switch_tab('tab_maint')", "4. Wartung"),
        Binding("5", "switch_tab('tab_services')", "5. Dienste"),
        Binding("6", "switch_tab('tab_diag')", "6. Diagnose"),
        Binding("7", "switch_tab('tab_network')", "7. Netzwerk"),
        Binding("r", "refresh_active()", "Aktualisieren"),
        Binding("l", "toggle_lang()", "Sprache (DE/EN)"),
        Binding("q", "quit", "Beenden"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.config_data = load_config()
        # Initiale Sprache aus Konfiguration laden
        lang = self.config_data.get("general", {}).get("language", "de")
        set_language(lang)

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        # Ribbon Statusleiste oben
        with Horizontal(id="sys_ribbon"):
            yield Static("🖥️  [bold cyan]CachyOS[/bold cyan]", classes="ribbon-item")
            yield Static("│", classes="ribbon-sep")
            yield Static("🐧  Kernel: [bold green]--[/bold green]", id="ribbon_kernel", classes="ribbon-item")
            yield Static("│", classes="ribbon-sep")
            yield Static("🧠  RAM: --", id="ribbon_ram", classes="ribbon-item")
            yield Static("│", classes="ribbon-sep")
            yield Static("⚡  CPU: --", id="ribbon_cpu", classes="ribbon-item")
            yield Static("│", classes="ribbon-sep")
            yield Static("🌐  [bold yellow]DE[/bold yellow]", id="ribbon_lang", classes="ribbon-item")

        # Tabbed Navigation
        with TabbedContent(initial="tab_dash", id="main_tabs"):
            with TabPane(t("tab_cockpit"), id="tab_dash"):
                yield DashboardView(id="view_dash")

            with TabPane(t("tab_kernel"), id="tab_kernel"):
                yield KernelView(id="view_kernel")

            with TabPane(t("tab_power"), id="tab_power"):
                yield PowerView(id="view_power")

            with TabPane(t("tab_maint"), id="tab_maint"):
                yield MaintView(id="view_maint")

            with TabPane(t("tab_services"), id="tab_services"):
                yield ServicesView(id="view_services")

            with TabPane(t("tab_diag"), id="tab_diag"):
                yield DiagView(id="view_diag")

            with TabPane(t("tab_network"), id="tab_network"):
                yield WifiView(id="view_wifi")

        yield Footer()

    def on_mount(self) -> None:
        self.update_ribbon()
        refresh_sec = self.config_data.get("general", {}).get("refresh_interval_seconds", 3)
        self.set_interval(refresh_sec, self.update_ribbon)

    def update_ribbon(self) -> None:
        """Aktualisiert die kompakte obere Statuszeile."""
        try:
            t_data = get_system_telemetry()
            self.query_one("#ribbon_kernel", Static).update(
                f"🐧  Kernel: [bold green]{t_data.kernel.split('-cachyos')[0]}[/bold green]"
            )
            self.query_one("#ribbon_ram", Static).update(
                f"🧠  RAM: [bold]{t_data.ram_percent}%[/bold] ({t_data.ram_used_gb}G)"
            )
            self.query_one("#ribbon_cpu", Static).update(
                f"⚡  CPU: [bold]{t_data.cpu_percent}%[/bold]"
            )
            lang_code = get_language().upper()
            self.query_one("#ribbon_lang", Static).update(
                f"🌐  [bold yellow]{lang_code}[/bold yellow]"
            )
        except Exception:
            pass

    def action_switch_tab(self, tab_id: str) -> None:
        """Wechselt direkt zum gewünschten Tab."""
        tabs = self.query_one("#main_tabs", TabbedContent)
        tabs.active = tab_id

    def action_refresh_active(self) -> None:
        """Aktualisiert den aktuell angezeigten Screen."""
        self.update_ribbon()
        tabs = self.query_one("#main_tabs", TabbedContent)
        act = tabs.active

        if act == "tab_dash":
            self.query_one("#view_dash", DashboardView).refresh_telemetry()
        elif act == "tab_kernel":
            self.query_one("#view_kernel", KernelView).refresh_all()
        elif act == "tab_power":
            self.query_one("#view_power", PowerView).refresh_power_data()
        elif act == "tab_maint":
            self.query_one("#view_maint", MaintView).refresh_maintenance_info()
        elif act == "tab_services":
            self.query_one("#view_services", ServicesView).refresh_services()
        elif act == "tab_diag":
            self.query_one("#view_diag", DiagView).refresh_diagnostics()

        self.notify("Ansicht aktualisiert", severity="information", timeout=2)

    def action_toggle_lang(self) -> None:
        """Wechselt zwischen Deutsch und Englisch und aktualisiert die UI."""
        new_lang = toggle_language()
        self.config_data.setdefault("general", {})["language"] = new_lang
        save_user_config(self.config_data)

        # Tab-Titel dynamisch aktualisieren
        tabs = self.query_one("#main_tabs", TabbedContent)
        # Update Ribbon
        self.update_ribbon()
        lang_name = "Deutsch" if new_lang == "de" else "English"
        self.notify(f"Sprache gewechselt: {lang_name}", severity="information", timeout=3)

    # ── Asynchrone Aktionen via Worker (Verhindert GUI-Freezes bei Polkit) ──

    @work(thread=True)
    def action_quick_clean_cache(self) -> None:
        self.notify("Bereinige Pacman Cache via Polkit...", severity="information")
        ok, msg = clean_pacman_cache(keep_versions=2)
        if ok:
            self.notify("Pacman Cache erfolgreich bereinigt!", severity="information")
        else:
            self.notify(f"Cache-Bereinigung: {msg}", severity="warning" if "abgebrochen" in msg.lower() else "error")
        self.call_from_thread(self._post_action_refresh)

    @work(thread=True)
    def action_quick_remove_orphans(self) -> None:
        self.notify("Entferne verwaiste Pakete via Polkit...", severity="information")
        ok, msg = remove_orphan_packages()
        if ok:
            self.notify("Waisenpakete erfolgreich entfernt!", severity="information")
        else:
            self.notify(f"Waisenpakete: {msg}", severity="warning" if "abgebrochen" in msg.lower() else "error")
        self.call_from_thread(self._post_action_refresh)

    @work(thread=True)
    def action_quick_rate_mirrors(self) -> None:
        self.notify("Starte Mirror Benchmarking (kann bis zu 60s dauern)...", severity="information")
        ok, msg = benchmark_mirrors()
        if ok:
            self.notify("Mirrors erfolgreich optimiert & gespeichert!", severity="information")
        else:
            self.notify(f"Mirror Benchmarking: {msg}", severity="error")
        self.call_from_thread(self._post_action_refresh)

    @work(thread=True)
    def action_quick_trim(self) -> None:
        self.notify("Führe SSD TRIM (fstrim -av) aus...", severity="information")
        ok, msg = run_fstrim()
        if ok:
            self.notify("SSD TRIM erfolgreich abgeschlossen!", severity="information")
        else:
            self.notify(f"TRIM Fehler: {msg}", severity="error")

    @work(thread=True)
    def action_quick_reset_failed(self) -> None:
        ok, msg = reset_failed_units()
        self.notify(msg, severity="information")
        self.call_from_thread(self._post_action_refresh)

    @work(thread=True)
    def action_quick_journal_vacuum(self) -> None:
        self.notify("Trimme Systemd Journal auf 50M...", severity="information")
        ok, msg = vacuum_journal("50M")
        if ok:
            self.notify("Journal erfolgreich getrimmt!", severity="information")
        else:
            self.notify(f"Journal: {msg}", severity="error")

    @work(thread=True)
    def action_toggle_maintenance_timer(self, timer_name: str, enable: bool) -> None:
        self.notify(f"Passe Hintergrund-Timer {timer_name} an...", severity="information")
        ok, msg = toggle_maintenance_timer(timer_name, enable)
        if ok:
            self.notify(msg, severity="information")
        else:
            self.notify(f"Timer Fehler: {msg}", severity="error")
        self.call_from_thread(self._post_action_refresh)

    @work(thread=True)
    def action_install_selected_kernel(self, package_name: str) -> None:
        self.notify(f"Installiere {package_name} via Polkit...", severity="information")
        ok, msg = install_kernel(package_name)
        if ok:
            self.notify(f"{package_name} erfolgreich installiert!", severity="information")
        else:
            self.notify(f"Fehler: {msg}", severity="error")
        self.call_from_thread(self._post_action_refresh)

    @work(thread=True)
    def action_remove_selected_kernel(self, package_name: str) -> None:
        self.notify(f"Deinstalliere {package_name} via Polkit...", severity="information")
        ok, msg = remove_kernel(package_name)
        if ok:
            self.notify(f"{package_name} deinstalliert!", severity="information")
        else:
            self.notify(f"Fehler: {msg}", severity="error")
        self.call_from_thread(self._post_action_refresh)

    @work(thread=True)
    def action_apply_cpu_governor(self, governor: str) -> None:
        self.notify(f"Setze CPU Governor '{governor}'...", severity="information")
        ok, msg = apply_governor(governor)
        if ok:
            self.notify(f"Governor '{governor}' aktiv!", severity="information")
        else:
            self.notify(f"Fehler: {msg}", severity="error")
        self.call_from_thread(self._post_action_refresh)

    @work(thread=True)
    def action_apply_epp_profile(self, preference: str) -> None:
        self.notify(f"Setze EPP '{preference}'...", severity="information")
        ok, msg = apply_epp(preference)
        if ok:
            self.notify(f"EPP '{preference}' aktiv!", severity="information")
        else:
            self.notify(f"Fehler: {msg}", severity="error")
        self.call_from_thread(self._post_action_refresh)

    @work(thread=True)
    def action_execute_service_action(self, service: str, action: str) -> None:
        ok, msg = polkit_service_action(service, action)
        if ok:
            self.notify(f"Dienst {service}: {action.upper()} erfolgreich!", severity="information")
        else:
            self.notify(f"Fehler: {msg}", severity="error")
        self.call_from_thread(self._post_action_refresh)

    def _post_action_refresh(self) -> None:
        """Wird auf dem Main Thread nach Beendigung von Hintergrundaktionen aufgerufen."""
        try:
            self.query_one("#view_dash", DashboardView).refresh_telemetry()
            self.query_one("#view_kernel", KernelView).refresh_all()
            self.query_one("#view_power", PowerView).refresh_power_data()
            self.query_one("#view_maint", MaintView).refresh_maintenance_info()
            self.query_one("#view_services", ServicesView).refresh_services()
        except Exception:
            pass


if __name__ == "__main__":
    if not sys.stdin.isatty():
        for term in ["konsole", "alacritty", "kitty", "ptyxis", "xfce4-terminal", "gnome-terminal", "xterm"]:
            if shutil.which(term):
                launcher = SCRIPT_DIR / "run.sh"
                if launcher.exists():
                    os.execvp(term, [term, "-e", str(launcher)])
    app = CachyOSCenterApp()
    app.run()
