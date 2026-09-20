#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
 CachyOS Control Center — Kernel & Driver Management View
 Verwaltung von CachyOS-Kernelvarianten (BORE, LTO, RT, BMQ, LTS),
 GPU-Treibern (NVIDIA / AMD / Intel), Hardware-Metriken & Statusindikatoren
===============================================================================
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, DataTable, Label, Static

from core.kernel_driver import (
    list_cachyos_kernels,
    detect_gpu_devices,
    install_kernel,
    remove_kernel,
    KernelInfo,
    GPUDeviceInfo,
)
from core.i18n import t


class KernelView(Container):
    DEFAULT_CSS = """
    KernelView {
        width: 100%;
        height: 100%;
        layout: vertical;
    }
    """

    def compose(self) -> ComposeResult:
        # Oberer Bereich: Kernel Matrix
        with Vertical(classes="panel pane-top"):
            with Horizontal(classes="toolbar"):
                yield Label(f"🐧  {t('kernel_mgmt_title')}", classes="panel-title")
                yield Button(f"🔄  {t('btn_refresh')}", id="btn_refresh_kernels", classes="btn-small")
                yield Button(f"➕  {t('action_install_kernel')}", id="btn_install_kernel", classes="-primary btn-small")
                yield Button(f"➖  {t('action_remove_kernel')}", id="btn_remove_kernel", classes="btn-small")

            yield DataTable(id="tbl_kernels")

        # Unterer Bereich: GPU Adapter & Treiberschnittstellen
        with Vertical(classes="panel pane-bottom"):
            yield Label(f"🎮  {t('gpu_drivers_title')}", classes="panel-title")
            with Horizontal(classes="split-h"):
                yield DataTable(id="tbl_gpus", classes="col-left")
                with Vertical(classes="col-right"):
                    yield Label("Treiber- & Hardware-Details", classes="panel-subtitle")
                    yield Static("", id="gpu_telemetry_box", classes="term-box")

    def on_mount(self) -> None:
        self._init_tables()
        self.refresh_all()

    def _init_tables(self) -> None:
        tbl_k = self.query_one("#tbl_kernels", DataTable)
        tbl_k.cursor_type = "row"
        tbl_k.zebra_stripes = True
        tbl_k.clear(columns=True)
        tbl_k.add_columns(
            t("kernel_variant"),
            "Paketname",
            t("kernel_version"),
            t("kernel_status"),
            t("kernel_desc"),
        )

        tbl_g = self.query_one("#tbl_gpus", DataTable)
        tbl_g.cursor_type = "row"
        tbl_g.zebra_stripes = True
        tbl_g.clear(columns=True)
        tbl_g.add_columns(
            t("col_component"),
            "Hersteller",
            t("col_driver"),
            t("col_type"),
            "Version",
        )

    def refresh_all(self) -> None:
        self.refresh_kernels()
        self.refresh_gpus()

    def refresh_kernels(self) -> None:
        tbl_k = self.query_one("#tbl_kernels", DataTable)
        tbl_k.clear()

        installed, available = list_cachyos_kernels()

        for k in installed:
            if k.is_running:
                status_str = f"[bold green]● {t('active_running')}[/bold green]"
            else:
                status_str = f"[bold cyan]✓ {t('installed')}[/bold cyan]"

            tbl_k.add_row(
                f"[bold]{k.variant_name}[/bold]",
                k.package_name,
                k.version,
                status_str,
                k.description,
                key=k.package_name,
            )

        for k in available:
            status_str = f"[dim]○ {t('available')}[/dim]"
            tbl_k.add_row(
                k.variant_name,
                k.package_name,
                k.version,
                status_str,
                k.description,
                key=k.package_name,
            )

    def refresh_gpus(self) -> None:
        tbl_g = self.query_one("#tbl_gpus", DataTable)
        tbl_g.clear()

        gpus = detect_gpu_devices()
        gpu_box = self.query_one("#gpu_telemetry_box", Static)

        detail_lines = []

        if not gpus:
            tbl_g.add_row("Standard VGA", "Generic", "Vesa/SimpleDRM", "Open Source", "N/A")
            gpu_box.update("[dim]Keine dedizierten PCI-Grafikadapter erkannt.[/dim]")
            return

        for idx, g in enumerate(gpus):
            driver_type = f"[yellow]{t('proprietary')}[/yellow]" if g.is_proprietary else f"[green]{t('open_source')}[/green]"
            tbl_g.add_row(
                g.device_name[:32],
                g.vendor,
                g.active_driver,
                driver_type,
                g.driver_version,
                key=f"gpu_{idx}",
            )

            # Details formatieren
            detail_lines.append(f"[bold cyan]{g.device_name}[/bold cyan]")
            detail_lines.append(f"  Hersteller:         {g.vendor}")
            detail_lines.append(f"  Treiber:            {g.active_driver} ({driver_type})")
            detail_lines.append(f"  Treiber-Version:    {g.driver_version}")
            if g.temperature_c is not None:
                temp_color = "green" if g.temperature_c < 65 else ("yellow" if g.temperature_c < 80 else "red")
                detail_lines.append(f"  {t('gpu_temp')}:         [{temp_color}]{g.temperature_c} °C[/{temp_color}]")
            if g.power_draw_w is not None:
                detail_lines.append(f"  {t('gpu_power_draw')}:   {g.power_draw_w} W")
            if g.power_state:
                detail_lines.append(f"  {t('gpu_power_state')}:   {g.power_state}")
            detail_lines.append(f"  Vulkan Support:     {'[green]Installiert[/green]' if g.vulkan_installed else '[yellow]vulkaninfo fehlt[/yellow]'}")
            detail_lines.append("")

        gpu_box.update("\n".join(detail_lines))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        if btn_id == "btn_refresh_kernels":
            self.refresh_all()
        elif btn_id == "btn_install_kernel":
            tbl = self.query_one("#tbl_kernels", DataTable)
            if tbl.row_count > 0:
                row_key, _ = tbl.coordinate_to_cell_key(tbl.cursor_coordinate)
                pkg = str(row_key.value)
                self.app.action_install_selected_kernel(pkg)
        elif btn_id == "btn_remove_kernel":
            tbl = self.query_one("#tbl_kernels", DataTable)
            if tbl.row_count > 0:
                row_key, _ = tbl.coordinate_to_cell_key(tbl.cursor_coordinate)
                pkg = str(row_key.value)
                self.app.action_remove_selected_kernel(pkg)
