#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
 CachyOS Control Center — Plasma 6 Wayland Ricing & Aesthetics View
 KWin Compositing, Fastfetch Banner, KDE Accent-Colors & Ricing Guide
===============================================================================
"""

from __future__ import annotations

import subprocess
import sys
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Label, MarkdownViewer, Static

from rich.text import Text

from core.ricing import (
    inspect_desktop_environment,
    get_fastfetch_output,
    RICE_KNOWLEDGE_BASE,
    DesktopInspectorResult,
)


class RiceView(Container):
    DEFAULT_CSS = """
    RiceView {
        width: 100%;
        height: 100%;
        layout: vertical;
    }
    """

    def compose(self) -> ComposeResult:
        yield Label("🎨 KDE PLASMA 6 (WAYLAND) RICING & TERMINAL ÄSTHETIK", classes="section-label")

        with Horizontal(classes="split-h"):
            # Linke Spalte: Live Desktop Inspektor
            with Vertical(classes="col-left"):
                yield Label("🖥️ DESKTOP- & COMPOSITOR-INSPEKTOR", classes="title")
                yield Static("Lade Desktop-Informationen...", id="rice_info_box", classes="info-box")

                yield Label("FASTFETCH & TUI-DEMOS", classes="title")
                with Horizontal(classes="toolbar"):
                    yield Button("[F] Fastfetch", id="btn_rice_show_fastfetch", classes="-primary")
                    yield Button("[T] Textual Demo", id="btn_rice_textual_demo", classes="-default")
                    yield Button("[R] Rich Demo", id="btn_rice_rich_demo", classes="-default")

                yield Static("Lade Fastfetch...", id="rice_demo_output", classes="info-box")

            # Rechte Spalte: Ricing Handbuch
            with Vertical(classes="col-right"):
                yield Label("📖 PLASMA 6 RICING-ENZYKLOPÄDIE", classes="title")
                with Horizontal(classes="toolbar"):
                    yield Button("[K] KWin & Blur", id="btn_guide_kwin", classes="-default")
                    yield Button("[H] Shell & Fonts", id="btn_guide_shell", classes="-default")
                    yield Button("[W] Wallpapers", id="btn_guide_wall", classes="-default")
                    yield Button("[C] Farben & Akzente", id="btn_guide_colors", classes="-default")
                yield MarkdownViewer(RICE_KNOWLEDGE_BASE["kwin_wayland"]["content"], id="rice_guide_viewer")

    def on_mount(self) -> None:
        self.refresh_inspector()
        try:
            ff = get_fastfetch_output()
            self.query_one("#rice_demo_output", Static).update(Text.from_ansi(ff))
        except Exception:
            pass

    def refresh_inspector(self) -> None:
        info = inspect_desktop_environment()

        tools_str = "  ".join(
            [f"[green]✔ {t}[/green]" if ok else f"[dim]○ {t}[/dim]" for t, ok in info.installed_tools.items()]
        )

        txt = (
            f"[b]Session Typ:[/b] [cyan]{info.session_type}[/cyan]  │  "
            f"[b]Desktop:[/b] [magenta]{info.desktop_environment}[/magenta]\n"
            f"[b]Compositor:[/b] [green]{info.kwin_compositor}[/green]\n"
            f"[b]KDE Farbschema:[/b] [yellow]{info.color_scheme}[/yellow]\n"
            f"[b]Akzentfarbe (RGB):[/b] [green]{info.accent_color_rgb}[/green]\n\n"
            f"[b]Installierte Tools:[/b]\n{tools_str}"
        )
        self.query_one("#rice_info_box", Static).update(txt)

    def load_guide(self, section_key: str) -> None:
        if section_key in RICE_KNOWLEDGE_BASE:
            viewer = self.query_one("#rice_guide_viewer", MarkdownViewer)
            viewer.document.update(RICE_KNOWLEDGE_BASE[section_key]["content"])
