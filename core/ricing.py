#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
 CachyOS Control Center — Plasma 6 Wayland Ricing & Desktop Inspector
 Compositor-Audits, Akzentfarben, Fastfetch-Integration & Leitfäden
===============================================================================
"""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from .system import run_cmd


@dataclass
class DesktopInspectorResult:
    session_type: str
    desktop_environment: str
    accent_color_rgb: str
    color_scheme: str
    installed_tools: Dict[str, bool] = field(default_factory=dict)
    kwin_compositor: str = "Wayland"


RICE_KNOWLEDGE_BASE: Dict[str, Dict[str, str]] = {
    "kwin_wayland": {
        "title": "KDE Plasma 6 Wayland & KWin Compositing",
        "content": """# KDE Plasma 6 (Wayland) — Compositing & Effekte

Unter **CachyOS** läuft Plasma 6 standardmäßig mit **Wayland**. KWin übernimmt das vollständige Compositing.
*Hinweis: X11-Tools wie picom oder compton sind unter Wayland funktionslos.*

### Wichtige Architekturpunkte:
- **Fensterrahmen & Titelleisten:** Verwende **Klassy** (`klassy-bin`) für anpassbare Button-Abstände und Blur.
- **Hintergrundunschärfe (Blur):** Nativ in den KDE-Systemeinstellungen (*Erscheinungsbild -> Fensterdekoration / Effekte*).
- **Fensterregeln (Window Rules):** Tastenkürzel `Alt + F3` -> *Weitere Aktionen* -> *Spezielle Einstellungen für dieses Fenster*.
- **Floating Panels:** Plasma 6 unterstützt schwebende Leisten ab Werk.

### Empfohlene Pakete:
```bash
sudo pacman -S --needed klassy kvantum qt6ct
```
""",
    },
    "shell_fastfetch": {
        "title": "Terminal-Ästhetik: Fastfetch & Oh-My-Posh",
        "content": """# Terminal-Ästhetik: Shells & Prompts

### 1. Fastfetch System-Banner
Konfiguriere Fastfetch unter `~/.config/fastfetch/config.jsonc`.
Enthält GPU-, Kernel-, Uptime- und Paketstatistiken mit individuellem ASCII-Logo.

### 2. Prompt-Styling mit Oh-My-Posh:
CachyOS nutzt standardmäßig **Fish** oder **Zsh**.
Einbindung in Fish (`~/.config/fish/config.fish`):
```fish
oh-my-posh init fish --config ~/.config/oh-my-posh/theme.omp.json | source
```
Empfohlene Themes: `catppuccin`, `tokyonight_storm`, `powerlevel10k_modern`.
""",
    },
    "wallpapers": {
        "title": "Wayland Wallpaper-Engines (SWWW & MPV-Paper)",
        "content": """# Wallpaper-Engines unter Plasma 6 Wayland

- **Nativ:** Rechtsklick auf Desktop -> *Arbeitsfläche einrichten* -> Bild/Diashow.
- **SWWW (Sway Wayland Wallpaper):** GPU-beschleunigter Daemon mit weichen Übergängen:
```bash
swww-daemon &
swww img /pfad/zum/wallpaper.jpg --transition-type wipe --transition-step 90
```
- **MPV-Paper:** Spielt Loops und Videos nahtlos als Desktop-Backdrop ab:
```bash
mpvpaper -o "no-audio --loop-playlist shuffle" '*' /pfad/zu/videos/
```
""",
    },
    "color_schemes": {
        "title": "Standardisierte Farbpaletten & Dotfiles",
        "content": """# Standardisierte Farbpaletten

### Empfohlene Farbschemata:
- **Catppuccin Mocha:** Basis `#1e1e2e`, Akzent `#cba6f7` (Mauve), Text `#cdd6f4`
- **Crimson Abyss:** Basis `#12151d`, Akzent `#dc143c` (Crimson), Text `#f8f9fa`
- **Tokyo Night:** Basis `#1a1b26`, Akzent `#7aa2f7` (Blue), Text `#a9b1d6`

### Konfigurationspfade:
- Terminal: `~/.config/alacritty/alacritty.toml`
- System-Banner: `~/.config/fastfetch/config.jsonc`
- KDE Globals: `~/.config/kdeglobals`
- KWin Regeln: `~/.config/kwinrc`
""",
    },
}


def inspect_desktop_environment() -> DesktopInspectorResult:
    """Liest Live-Informationen über Desktop, Wayland und KDE Globals aus."""
    session = os.environ.get("XDG_SESSION_TYPE", "Unbekannt").upper()
    desktop = os.environ.get("XDG_CURRENT_DESKTOP", "Unbekannt")

    accent = "Standard"
    scheme = "BreezeDark"

    if shutil.which("kreadconfig6"):
        acc_out, _, _ = run_cmd("kreadconfig6 --file kdeglobals --group General --key AccentColor")
        sch_out, _, _ = run_cmd("kreadconfig6 --file kdeglobals --group General --key colorScheme")
        if acc_out:
            accent = acc_out
        if sch_out:
            scheme = sch_out

    tools = ["klassy-settings", "kvantummanager", "oh-my-posh", "fastfetch", "alacritty", "ghostty", "kitty"]
    installed: Dict[str, bool] = {t: bool(shutil.which(t)) for t in tools}

    return DesktopInspectorResult(
        session_type=session,
        desktop_environment=desktop,
        accent_color_rgb=accent,
        color_scheme=scheme,
        installed_tools=installed,
        kwin_compositor="Wayland Compositor (KWin)" if "wayland" in session.lower() else "X11",
    )


def get_fastfetch_output() -> str:
    """Holt die formatierte Konsolenausgabe von Fastfetch ab."""
    if shutil.which("fastfetch"):
        out, err, code = run_cmd("fastfetch --pipe false", timeout=6)
        if code == 0 and out:
            return out
    return "Fastfetch ist nicht installiert oder lieferte keine Ausgabe."
