#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
 CACHYOS ULTIMATE CONTROL CENTER & SYSTEM ARCHITECT (TUI)
 Professionelles Administrations-, Telemetrie- und Wartungszentrum
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

from core.system import (
    get_system_telemetry,
    get_services_status,
    run_cmd,
)
from core.network import (
    scan_wifi_networks,
    set_interface_mode,
    kill_wifi_conflicts,
    restart_network_stack,
)
from core.tailscale import (
    get_tailscale_status,
    toggle_tailscale,
    set_exit_node,
    disable_exit_node,
    ping_tailscale_peer,
)
from core.diagnostics import run_diagnostic_profile
from core.maintenance import (
    clean_pacman_cache,
    vacuum_journal,
    reset_failed_units,
    run_fstrim,
    check_available_updates,
)
from core.ricing import get_fastfetch_output
from ui.theme import APP_TCSS
from ui.screens.dashboard_view import DashboardView
from ui.screens.wifi_view import WifiView
from ui.screens.tailscale_view import TailscaleView
from ui.screens.diag_view import DiagView
from ui.screens.maint_view import MaintView
from ui.screens.rice_view import RiceView
from ui.screens.migrator_view import MigratorView


class CachyOSCenterApp(App):
    TITLE = "CACHYOS CONTROL CENTER & SYSTEM ARCHITECT"
    SUB_TITLE = "Professional Edition 2026 │ CachyOS Linux x86_64"
    CSS = APP_TCSS
    ENABLE_COMMAND_PALETTE = False

    BINDINGS = [
        Binding("1", "switch_tab('tab_dash')", "1. Cockpit"),
        Binding("2", "switch_tab('tab_wifi')", "2. Funk"),
        Binding("3", "switch_tab('tab_ts')", "3. Tailscale"),
        Binding("4", "switch_tab('tab_diag')", "4. Diagnose"),
        Binding("5", "switch_tab('tab_maint')", "5. Wartung"),
        Binding("6", "switch_tab('tab_rice')", "6. Ricing"),
        Binding("7", "switch_tab('tab_migr')", "7. Architekt"),
        Binding("f1", "switch_tab('tab_dash')", "F1 Cockpit", show=False),
        Binding("f2", "switch_tab('tab_wifi')", "F2 Funk", show=False),
        Binding("f3", "switch_tab('tab_ts')", "F3 Tailscale", show=False),
        Binding("f4", "switch_tab('tab_diag')", "F4 Diagnose", show=False),
        Binding("f5", "switch_tab('tab_maint')", "F5 Wartung", show=False),
        Binding("f6", "switch_tab('tab_rice')", "F6 Ricing", show=False),
        Binding("f7", "switch_tab('tab_migr')", "F7 Architekt", show=False),
        Binding("r", "refresh_data", "Aktualisieren [r]"),
        Binding("q", "quit", "Beenden [q]"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        # System-Status-Band direkt unter dem Header
        with Horizontal(id="sys_ribbon"):
            yield Static("HOST: --", id="ribbon_host", classes="ribbon-item")
            yield Static("│", classes="ribbon-sep")
            yield Static("KERNEL: --", id="ribbon_kernel", classes="ribbon-item")
            yield Static("│", classes="ribbon-sep")
            yield Static("UPTIME: --", id="ribbon_uptime", classes="ribbon-item")
            yield Static("│", classes="ribbon-sep")
            yield Static("CPU: --%", id="ribbon_cpu", classes="ribbon-item")
            yield Static("│", classes="ribbon-sep")
            yield Static("RAM: --", id="ribbon_ram", classes="ribbon-item")
            yield Static("│", classes="ribbon-sep")
            yield Static("DISK: --", id="ribbon_disk", classes="ribbon-item")
            yield Static("│", classes="ribbon-sep")
            yield Static("TAILSCALE: --", id="ribbon_ts", classes="ribbon-item")
            yield Static("│", classes="ribbon-sep")
            yield Static("UNITS: 0", id="ribbon_units", classes="ribbon-item")
            yield Static("│", classes="ribbon-sep")
            yield Static("STATUS: [bold green]● Bereit[/bold green]", id="ribbon_status", classes="ribbon-item")

        # Tabbed Navigation über die volle Terminalbreite
        with TabbedContent(initial="tab_dash", id="main_tabs"):
            with TabPane("📊 1. COCKPIT", id="tab_dash"):
                yield DashboardView(id="view_dashboard")
            with TabPane("🛰️ 2. FUNK & INTERFACES", id="tab_wifi"):
                yield WifiView(id="view_wifi")
            with TabPane("🧅 3. TAILSCALE MESH", id="tab_ts"):
                yield TailscaleView(id="view_tailscale")
            with TabPane("🔍 4. TIEFENDIAGNOSE", id="tab_diag"):
                yield DiagView(id="view_diag")
            with TabPane("🔒 5. SYSTEMWARTUNG", id="tab_maint"):
                yield MaintView(id="view_maint")
            with TabPane("🎨 6. PLASMA 6 RICING", id="tab_rice"):
                yield RiceView(id="view_rice")
            with TabPane("🗂️ 7. WORKSPACE-ARCHITEKT", id="tab_migr"):
                yield MigratorView(id="view_migrator")

        yield Footer()

    def on_mount(self) -> None:
        self.update_ribbon()
        self.set_interval(3.0, self.update_ribbon)

    def set_activity(self, text: str = "") -> None:
        try:
            widget = self.query_one("#ribbon_status", Static)
            if text:
                widget.update(f"STATUS: [bold yellow]⏳ {text}[/bold yellow]")
            else:
                widget.update("STATUS: [bold green]● Bereit[/bold green]")
        except Exception:
            pass

    def update_ribbon(self) -> None:
        try:
            t = get_system_telemetry()
            self.query_one("#ribbon_host", Static).update(f"[bold cyan]{t.hostname}[/bold cyan]")
            self.query_one("#ribbon_kernel", Static).update(f"Linux {t.kernel}")
            self.query_one("#ribbon_uptime", Static).update(f"Up: {t.uptime_str}")

            cpu_col = "green" if t.cpu_percent < 70 else "yellow"
            self.query_one("#ribbon_cpu", Static).update(f"CPU: [{cpu_col}]{t.cpu_percent}%[/{cpu_col}]")

            ram_col = "green" if t.ram_percent < 70 else "yellow"
            self.query_one("#ribbon_ram", Static).update(f"RAM: [{ram_col}]{t.ram_used_gb}/{t.ram_total_gb}G ({t.ram_percent}%)[/{ram_col}]")

            disk_fs = "BTRFS" if t.is_btrfs else "EXT4"
            self.query_one("#ribbon_disk", Static).update(f"Disk: {t.disk_percent}% ({disk_fs})")

            # Tailscale
            ts_status = get_tailscale_status()
            ts_text = "[bold green]Online[/bold green]" if ts_status.running else "[dim]Offline[/dim]"
            self.query_one("#ribbon_ts", Static).update(f"Tailscale: {ts_text}")

            # Units
            failed_total = t.failed_system_units + t.failed_user_units
            units_text = f"[bold red]⚠ {failed_total} Failed[/bold red]" if failed_total > 0 else "[green]0 Failed[/green]"
            self.query_one("#ribbon_units", Static).update(f"Units: {units_text}")
        except Exception:
            pass

    def action_switch_tab(self, tab_id: str) -> None:
        self.query_one("#main_tabs", TabbedContent).active = tab_id

    def action_refresh_data(self) -> None:
        self.update_ribbon()
        active = self.query_one("#main_tabs", TabbedContent).active
        if active == "tab_dash":
            self.query_one(DashboardView).refresh_dashboard()
        elif active == "tab_wifi":
            self.query_one(WifiView).refresh_interfaces()
        elif active == "tab_ts":
            self.query_one(TailscaleView).refresh_tailscale_view()
        elif active == "tab_maint":
            self.query_one(MaintView).refresh_pacnew_list()
        elif active == "tab_rice":
            self.query_one(RiceView).refresh_inspector()
        self.notify("Telemetrie & Daten aktualisiert.", title="Aktualisierung", severity="information")

    # ── Asynchrone Worker für unterbrechungsfreie TUI ────────────────────────
    @work(thread=True)
    def worker_quick_diag(self) -> None:
        self.call_from_thread(self.set_activity, "Schnelldiagnose...")
        self.call_from_thread(self.notify, "Schnelldiagnose gestartet...", title="Diagnose", severity="information")
        self.call_from_thread(self.action_switch_tab, "tab_diag")
        try:
            diag_view = self.query_one(DiagView)
            res = run_diagnostic_profile("quick")
            self.call_from_thread(diag_view.populate_results, res)
            self.call_from_thread(self.notify, f"Diagnose fertig: {res.overall_health}", title="Ergebnis", severity="information")
        finally:
            self.call_from_thread(self.set_activity, "")

    @work(thread=True)
    def worker_standard_diag(self) -> None:
        self.call_from_thread(self.set_activity, "Standard-Audit...")
        self.call_from_thread(self.notify, "Standard-Diagnose gestartet...", title="Diagnose", severity="information")
        try:
            diag_view = self.query_one(DiagView)
            res = run_diagnostic_profile("standard")
            self.call_from_thread(diag_view.populate_results, res)
            self.call_from_thread(self.notify, f"Standard-Diagnose fertig: {res.overall_health}", title="Ergebnis", severity="information")
        finally:
            self.call_from_thread(self.set_activity, "")

    @work(thread=True)
    def worker_deep_diag(self) -> None:
        self.call_from_thread(self.set_activity, "Tiefen-Audit...")
        self.call_from_thread(self.notify, "Tiefen-Audit gestartet (kann einige Sekunden dauern)...", title="Diagnose", severity="information")
        try:
            diag_view = self.query_one(DiagView)
            res = run_diagnostic_profile("deep")
            self.call_from_thread(diag_view.populate_results, res)
            self.call_from_thread(self.notify, f"Tiefen-Audit abgeschlossen: {res.overall_health}", title="Ergebnis", severity="information")
        finally:
            self.call_from_thread(self.set_activity, "")

    @work(thread=True)
    def worker_pacman_cache(self) -> None:
        self.call_from_thread(self.set_activity, "Cache leeren...")
        self.call_from_thread(self.notify, "Pacman Cache-Bereinigung läuft...", title="Wartung", severity="information")
        try:
            ok, msg = clean_pacman_cache()
            sev = "information" if ok else "error"
            self.call_from_thread(self.notify, msg.splitlines()[0] if msg else "Fertig", title="Cache", severity=sev)
            self.call_from_thread(self.query_one(DashboardView).refresh_dashboard)
        finally:
            self.call_from_thread(self.set_activity, "")

    @work(thread=True)
    def worker_vacuum_journal(self) -> None:
        self.call_from_thread(self.set_activity, "Journal trimmen...")
        self.call_from_thread(self.notify, "Trimme Journald Logs auf 50M...", title="Wartung", severity="information")
        try:
            ok, msg = vacuum_journal("50M")
            sev = "information" if ok else "error"
            self.call_from_thread(self.notify, msg.splitlines()[0] if msg else "Fertig", title="Journal", severity=sev)
            self.call_from_thread(self.query_one(DashboardView).refresh_dashboard)
        finally:
            self.call_from_thread(self.set_activity, "")

    @work(thread=True)
    def worker_restart_nm(self) -> None:
        self.call_from_thread(self.set_activity, "NetworkManager Neustart...")
        self.call_from_thread(self.notify, "Starte NetworkManager neu...", title="Netzwerk", severity="information")
        try:
            ok, msg = restart_network_stack()
            sev = "information" if ok else "error"
            self.call_from_thread(self.notify, msg, title="NetworkManager", severity=sev)
            self.call_from_thread(self.query_one(DashboardView).refresh_dashboard)
            self.call_from_thread(self.query_one(WifiView).refresh_interfaces)
        finally:
            self.call_from_thread(self.set_activity, "")

    @work(thread=True)
    def worker_fstrim(self) -> None:
        self.call_from_thread(self.set_activity, "SSD TRIM...")
        self.call_from_thread(self.notify, "Führe SSD TRIM (fstrim) aus...", title="Speicher", severity="information")
        try:
            ok, msg = run_fstrim()
            sev = "information" if ok else "error"
            self.call_from_thread(self.notify, msg.splitlines()[0] if msg else "Fertig", title="FSTRIM", severity=sev)
        finally:
            self.call_from_thread(self.set_activity, "")

    @work(thread=True)
    def worker_reset_units(self) -> None:
        self.call_from_thread(self.set_activity, "Reset Units...")
        self.call_from_thread(self.notify, "Setze fehlgeschlagene Units zurück...", title="Systemd", severity="information")
        try:
            ok, msg = reset_failed_units()
            self.call_from_thread(self.notify, "Fehlgeschlagene Units zurückgesetzt.", title="Systemd", severity="information")
            self.call_from_thread(self.query_one(DashboardView).refresh_dashboard)
            self.call_from_thread(self.update_ribbon)
        finally:
            self.call_from_thread(self.set_activity, "")

    @work(thread=True)
    def worker_wifi_scan(self) -> None:
        self.call_from_thread(self.set_activity, "WLAN Scan...")
        self.call_from_thread(self.notify, "WLAN-Umgebungsscan läuft...", title="WLAN", severity="information")
        try:
            wifi_view = self.query_one(WifiView)
            iface = wifi_view.get_selected_interface()
            aps = scan_wifi_networks(iface)
            self.call_from_thread(wifi_view.populate_scan_results, aps)
            self.call_from_thread(self.notify, f"{len(aps)} Funknetzwerke gefunden.", title="WLAN Scan", severity="information")
        finally:
            self.call_from_thread(self.set_activity, "")

    @work(thread=True)
    def worker_wifi_mode(self, mode: str) -> None:
        self.call_from_thread(self.set_activity, f"WLAN {mode}...")
        try:
            wifi_view = self.query_one(WifiView)
            iface = wifi_view.get_selected_interface()
            if not iface:
                self.call_from_thread(self.notify, "Kein Interface ausgewählt!", title="WLAN", severity="warning")
                return
            self.call_from_thread(self.notify, f"Schalte {iface} in Modus {mode}...", title="WLAN", severity="information")
            ok, msg = set_interface_mode(iface, mode)
            sev = "information" if ok else "error"
            self.call_from_thread(self.notify, msg.splitlines()[0] if msg else "Abgeschlossen", title="WLAN", severity=sev)
            self.call_from_thread(wifi_view.refresh_interfaces)
        finally:
            self.call_from_thread(self.set_activity, "")

    @work(thread=True)
    def worker_wifi_kill(self) -> None:
        self.call_from_thread(self.set_activity, "Kill Prozesse...")
        self.call_from_thread(self.notify, "Beende interferierende Prozesse...", title="WLAN", severity="information")
        try:
            ok, msg = kill_wifi_conflicts()
            sev = "information" if ok else "error"
            self.call_from_thread(self.notify, msg.splitlines()[0] if msg else "Abgeschlossen", title="WLAN", severity=sev)
        finally:
            self.call_from_thread(self.set_activity, "")

    @work(thread=True)
    def worker_ts_toggle(self, up: bool) -> None:
        action = "Verbinde mit" if up else "Trenne"
        self.call_from_thread(self.set_activity, "Tailscale...")
        self.call_from_thread(self.notify, f"{action} Tailscale Mesh...", title="Tailscale", severity="information")
        try:
            ok, msg = toggle_tailscale(up)
            sev = "information" if ok else "error"
            self.call_from_thread(self.notify, msg, title="Tailscale", severity=sev)
            self.call_from_thread(self.query_one(TailscaleView).refresh_tailscale_view)
            self.call_from_thread(self.update_ribbon)
        finally:
            self.call_from_thread(self.set_activity, "")

    @work(thread=True)
    def worker_ts_exit_node(self, target: str) -> None:
        self.call_from_thread(self.set_activity, "Exit-Node...")
        try:
            if not target:
                self.call_from_thread(self.notify, "Deaktiviere Exit-Node Routing...", title="Tailscale", severity="information")
                ok, msg = disable_exit_node()
            else:
                self.call_from_thread(self.notify, f"Setze Exit-Node auf: {target}...", title="Tailscale", severity="information")
                ok, msg = set_exit_node(target)
            sev = "information" if ok else "error"
            self.call_from_thread(self.notify, msg, title="Exit-Node", severity=sev)
            self.call_from_thread(self.query_one(TailscaleView).refresh_tailscale_view)
        finally:
            self.call_from_thread(self.set_activity, "")

    @work(thread=True)
    def worker_ts_ping(self, target: str) -> None:
        self.call_from_thread(self.set_activity, f"Ping {target}...")
        self.call_from_thread(self.notify, f"Pinge {target}...", title="Tailscale", severity="information")
        try:
            ok, out = ping_tailscale_peer(target)
            ts_view = self.query_one(TailscaleView)
            self.call_from_thread(ts_view.query_one("#ts_ping_result_box", Static).update, out)
            self.call_from_thread(self.notify, f"Ping {target} beendet", title="Tailscale", severity="information" if ok else "warning")
        finally:
            self.call_from_thread(self.set_activity, "")

    @work(thread=True)
    def worker_check_updates(self) -> None:
        self.call_from_thread(self.set_activity, "Prüfe Updates...")
        self.call_from_thread(self.notify, "Prüfe auf offene Paket-Updates...", title="Paketverwaltung", severity="information")
        try:
            count, msg = check_available_updates()
            sev = "information" if count == 0 else "warning"
            self.call_from_thread(self.notify, msg, title="Updates", severity=sev)
        finally:
            self.call_from_thread(self.set_activity, "")

    # ── Event Dispatching ───────────────────────────────────────────────────
    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id

        # Cockpit (Dashboard)
        if bid == "btn_dash_refresh":
            self.action_refresh_data()
        elif bid == "btn_quick_diag":
            self.worker_quick_diag()
        elif bid == "btn_quick_cache":
            self.worker_pacman_cache()
        elif bid == "btn_quick_journal":
            self.worker_vacuum_journal()
        elif bid == "btn_quick_reset_units":
            self.worker_reset_units()

        # WLAN
        elif bid == "btn_wifi_mon":
            self.worker_wifi_mode("monitor")
        elif bid == "btn_wifi_man":
            self.worker_wifi_mode("managed")
        elif bid == "btn_wifi_kill":
            self.worker_wifi_kill()
        elif bid == "btn_wifi_restart_nm":
            self.worker_restart_nm()
        elif bid == "btn_wifi_scan":
            self.worker_wifi_scan()

        # Tailscale
        elif bid == "btn_ts_start":
            self.worker_ts_toggle(up=True)
        elif bid == "btn_ts_stop":
            self.worker_ts_toggle(up=False)
        elif bid == "btn_ts_no_exit":
            self.worker_ts_exit_node("")
        elif bid == "btn_ts_set_exit":
            ts_view = self.query_one(TailscaleView)
            target = ts_view.query_one("#ts_custom_exit_input", Input).value.strip() or ts_view.get_selected_peer_ip_or_host()
            if target:
                self.worker_ts_exit_node(target)
            else:
                self.notify("Bitte eine IP oder Hostnamen für den Exit-Node angeben!", title="Fehler", severity="warning")
        elif bid == "btn_ts_ping_node":
            ts_view = self.query_one(TailscaleView)
            target = ts_view.get_selected_peer_ip_or_host()
            if target:
                self.worker_ts_ping(target)
            else:
                self.notify("Kein Peer in der Tabelle ausgewählt!", title="Fehler", severity="warning")

        # Diagnose
        elif bid == "btn_diag_run_quick":
            self.worker_quick_diag()
        elif bid == "btn_diag_run_standard":
            self.worker_standard_diag()
        elif bid == "btn_diag_run_deep":
            self.worker_deep_diag()
        elif bid == "btn_diag_run_full":
            diag_bin = SCRIPT_DIR / "bin" / "net_diagnose.py"
            if diag_bin.exists():
                for term in ["alacritty", "konsole", "ghostty", "kitty", "xterm"]:
                    if shutil.which(term):
                        subprocess.Popen([term, "-e", sys.executable, str(diag_bin)])
                        self.notify("net_diagnose.py im Terminal gestartet.", title="Terminal", severity="information")
                        return
                self.notify("Kein Terminal-Emulator gefunden!", title="Fehler", severity="error")

        # Wartung
        elif bid == "btn_maint_cache":
            self.worker_pacman_cache()
        elif bid == "btn_maint_journal":
            self.worker_vacuum_journal()
        elif bid == "btn_maint_reset_units":
            self.worker_reset_units()
        elif bid == "btn_maint_fstrim":
            self.worker_fstrim()
        elif bid == "btn_maint_check_updates":
            self.worker_check_updates()
        elif bid == "btn_maint_refresh_pacnew":
            self.query_one(MaintView).refresh_pacnew_list()
            self.notify("Pacnew-Scan aktualisiert.", title="Wartung", severity="information")
        elif bid == "btn_maint_launch_wartung":
            ok = self.query_one(MaintView).launch_terminal_script("wartung-os.sh")
            if ok:
                self.notify("wartung-os.sh im Terminal gestartet.", title="Terminal", severity="information")
            else:
                self.notify("wartung-os.sh konnte nicht gestartet werden.", title="Fehler", severity="error")
        elif bid == "btn_maint_launch_manager":
            ok = self.query_one(MaintView).launch_terminal_script("cachyos_ultimate_manager.sh")
            if ok:
                self.notify("cachyos_ultimate_manager.sh im Terminal gestartet.", title="Terminal", severity="information")
            else:
                self.notify("cachyos_ultimate_manager.sh konnte nicht gestartet werden.", title="Fehler", severity="error")

        # Ricing
        elif bid == "btn_rice_show_fastfetch":
            out = get_fastfetch_output()
            self.query_one("#rice_demo_output", Static).update(Text.from_ansi(out))
            self.notify("Fastfetch-Daten geladen.", title="Ricing", severity="information")
        elif bid == "btn_rice_textual_demo":
            subprocess.Popen([sys.executable, "-m", "textual", "colors"])
            self.notify("Textual Colors Demo gestartet.", title="Demo", severity="information")
        elif bid == "btn_rice_rich_demo":
            subprocess.Popen([sys.executable, "-m", "rich.markdown", "--help"])
            self.notify("Rich Markdown Demo gestartet.", title="Demo", severity="information")
        elif bid == "btn_guide_kwin":
            self.query_one(RiceView).load_guide("kwin_wayland")
        elif bid == "btn_guide_shell":
            self.query_one(RiceView).load_guide("shell_fastfetch")
        elif bid == "btn_guide_wall":
            self.query_one(RiceView).load_guide("wallpapers")
        elif bid == "btn_guide_colors":
            self.query_one(RiceView).load_guide("color_schemes")

        # Migrator
        elif bid == "btn_migrator_scan":
            self.query_one(MigratorView).scan_source()
            self.notify("Verzeichnis-Scan abgeschlossen.", title="Synthese", severity="information")
        elif bid == "btn_migrator_cli":
            migr_bin = SCRIPT_DIR / "bin" / "agy_migrator.py"
            if migr_bin.exists():
                for term in ["alacritty", "konsole", "ghostty", "kitty", "xterm"]:
                    if shutil.which(term):
                        subprocess.Popen([term, "-e", sys.executable, str(migr_bin)])
                        self.notify("agy_migrator.py im Terminal gestartet.", title="Terminal", severity="information")
                        return

    def on_key(self, event) -> None:
        """Globale und tab-spezifische Hotkeys für professionelle Tastaturbedienung."""
        key = event.key.lower()
        if self.focused and isinstance(self.focused, Input):
            return

        active_tab = self.query_one("#main_tabs", TabbedContent).active
        if active_tab == "tab_wifi":
            if key == "m":
                self.worker_wifi_mode("monitor")
            elif key == "s":
                self.worker_wifi_mode("managed")
            elif key == "k":
                self.worker_wifi_kill()
            elif key == "a":
                self.worker_wifi_scan()
        elif active_tab == "tab_ts":
            if key == "u":
                self.worker_ts_toggle(up=True)
            elif key == "d":
                self.worker_ts_toggle(up=False)
            elif key == "x":
                self.worker_ts_exit_node("")
            elif key == "p":
                target = self.query_one(TailscaleView).get_selected_peer_ip_or_host()
                if target:
                    self.worker_ts_ping(target)
        elif active_tab == "tab_diag":
            if key == "q":
                self.worker_quick_diag()
            elif key == "s":
                self.worker_standard_diag()
            elif key == "d":
                self.worker_deep_diag()
            elif key == "c":
                diag_bin = SCRIPT_DIR / "bin" / "net_diagnose.py"
                if diag_bin.exists():
                    for term in ["alacritty", "konsole", "ghostty", "kitty", "xterm"]:
                        if shutil.which(term):
                            subprocess.Popen([term, "-e", sys.executable, str(diag_bin)])
                            self.notify("net_diagnose.py im Terminal gestartet.", title="Terminal", severity="information")
                            break
        elif active_tab == "tab_maint":
            if key == "c":
                self.worker_pacman_cache()
            elif key == "j":
                self.worker_vacuum_journal()
            elif key == "r":
                self.worker_reset_units()
            elif key == "t":
                self.worker_fstrim()
            elif key == "u":
                self.worker_check_updates()
            elif key == "s":
                self.query_one(MaintView).refresh_pacnew_list()
            elif key == "w":
                self.query_one(MaintView).launch_terminal_script("wartung-os.sh")
            elif key == "m":
                self.query_one(MaintView).launch_terminal_script("cachyos_ultimate_manager.sh")
        elif active_tab == "tab_rice":
            if key == "f":
                out = get_fastfetch_output()
                self.query_one("#rice_demo_output", Static).update(Text.from_ansi(out))
                self.notify("Fastfetch-Daten geladen.", title="Ricing", severity="information")
            elif key == "t":
                subprocess.Popen([sys.executable, "-m", "textual", "colors"])
            elif key == "k":
                self.query_one(RiceView).load_guide("kwin_wayland")
            elif key == "h":
                self.query_one(RiceView).load_guide("shell_fastfetch")
            elif key == "w":
                self.query_one(RiceView).load_guide("wallpapers")
            elif key == "c":
                self.query_one(RiceView).load_guide("color_schemes")
        elif active_tab == "tab_migr":
            if key == "a":
                self.query_one(MigratorView).scan_source()
            elif key == "t":
                migr_bin = SCRIPT_DIR / "bin" / "agy_migrator.py"
                if migr_bin.exists():
                    for term in ["alacritty", "konsole", "ghostty", "kitty", "xterm"]:
                        if shutil.which(term):
                            subprocess.Popen([term, "-e", sys.executable, str(migr_bin)])
                            self.notify("agy_migrator.py im Terminal gestartet.", title="Terminal", severity="information")
                            break


def main() -> None:
    app = CachyOSCenterApp()
    app.run()


if __name__ == "__main__":
    main()
