#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
 CachyOS Ricing & TUI Framework Toolkit
 Fusion aus ricing-helper.py und tui-helfer-tools.py
 CachyOS / Arch Linux Edition (Stand 2026)
===============================================================================
 Modulares Werkzeug zur Verwaltung von Terminal-UIs (Textual, Rich, Urwid)
 und interaktiver Ricing-Leitfaden für KDE Plasma 6 (Wayland) unter CachyOS.
===============================================================================
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from typing import Dict, Any

# ── Abhängigkeits-Prüfung ────────────────────────────────────────────────────
try:
    from rich.console import Console
    from rich.markdown import Markdown
    from rich.panel import Panel
    from rich.table import Table
    from rich.prompt import Prompt
except ImportError:
    print("[FEHLER] 'rich' Bibliothek fehlt. Bitte via 'sudo pacman -S python-rich' installieren.")
    sys.exit(1)

console = Console()

# ── Ricing-Wissensdatenbank (CachyOS Plasma 6 Wayland) ───────────────────────
RICE_KNOWLEDGE_BASE: Dict[str, Dict[str, str]] = {
    "1": {
        "title": "KDE Plasma 6 (Wayland) KWin Compositing & Effekte",
        "markdown": """
## KDE Plasma 6 (Wayland) — Compositing, KWin & Effekte

Unter CachyOS läuft Plasma 6 standardmäßig auf **Wayland**. KWin übernimmt das komplette Compositing.
*Hinweis: X11-Tools wie `picom` oder `compton` sind unter Wayland wirkungslos.*

### Schlüsselkomponenten:
- **Fensterrahmen & Dekoration:** Nutze **Klassy** (`klassy-bin`) oder native KWin-Dekorationen mit individuellen Button-Abständen.
- **Hintergrundunschärfe (Blur):** Wird nativ in den KDE-Systemeinstellungen unter *Erscheinungsbild -> Fensterdekoration / Effekte* gesteuert.
- **Fensterregeln (Window Rules):** Das mächtigste Feature unter KDE.
  - Tastenkombination `Alt + F3` -> *Weitere Aktionen* -> *Spezielle Einstellungen für dieses Fenster*.
  - Ermöglicht: "Keine Titelleiste", "Immer im Hintergrund", festes Pinning auf allen virtuellen Desktops.
- **Floating Panels:** Plasma 6 unterstützt schwebende Leisten von Haus aus. In Kombination mit `Panel Colorizer` lassen sich transparente Frosted-Glass-Leisten realisieren.

### Empfohlene Pakete:
```bash
sudo pacman -S --needed klassy kvantum qt6ct
```
""",
    },
    "2": {
        "title": "Terminal, Prompt & Oh-My-Posh",
        "markdown": """
## Terminal-Ästhetik: Shell, Prompts & Fastfetch

### 1. Terminal-Emulatoren:
- **Alacritty:** GPU-beschleunigt via OpenGL. Konfiguration unter `~/.config/alacritty/alacritty.toml`.
- **Ghostty:** Moderner Wayland-nativer Terminal-Emulator mit integriertem Blur und Shader-Support.
- **Kitty:** Schneller Emulator mit direkter Bildanzeige (`kitty +kitten icat`).

### 2. Prompt-Styling mit Oh-My-Posh:
- CachyOS nutzt standardmäßig die Fish- oder Zsh-Shell.
- Einbindung in Fish (`~/.config/fish/config.fish`):
  ```fish
  oh-my-posh init fish --config ~/.config/oh-my-posh/theme.omp.json | source
  ```
- Empfohlene Themes: `catppuccin`, `tokyonight_storm`, `powerlevel10k_modern`.

### 3. Fastfetch Info-Tool:
- Liefert Systeminformationen mit Logo. Konfiguration unter `~/.config/fastfetch/config.jsonc`.
""",
    },
    "3": {
        "title": "Wayland Wallpaper-Engines & Live-Backdrops",
        "markdown": """
## Wallpaper-Management unter Wayland

Unter Plasma 6 Wayland stehen moderne Hintergrund-Engines zur Verfügung:
- **Native Plasma Wallpaper:** Rechtsklick auf den Desktop -> *Arbeitsfläche einrichten* -> Bild oder Diashow wählen.
- **SWWW (Sway Wayland Wallpaper):** Extrem schneller Wallpaper-Daemon mit animierten Übergängen:
  ```bash
  swww-daemon &
  swww img /pfad/zum/bild.jpg --transition-type wipe --transition-step 90
  ```
- **MPV-Paper:** Spielt Videos und animierte Loops flüssig als Desktophintergrund ab:
  ```bash
  mpvpaper -o "no-audio --loop-playlist shuffle" '*' /pfad/zu/videos/
  ```
""",
    },
    "4": {
        "title": "Dotfile-Struktur & Farbharmonien",
        "markdown": """
## Standardisierte Verzeichnisstruktur für Ricing

```text
~/.config/
├── alacritty/alacritty.toml   # Terminal Farb- & Font-Einstellungen
├── fastfetch/config.jsonc     # System-Banner
├── kdeglobals                 # KDE Akzentfarben & Farbschemata
├── kwinrc                     # KWin Fenstermanager & Effekte
└── oh-my-posh/                # Shell-Prompt Theme
```

### Empfohlene Farbpaletten:
- **Crimson Abyss:** Primär `#12151d`, Akzent `#dc143c` (Crimson), Text `#f8f9fa`
- **Catppuccin Mocha:** Primär `#1e1e2e`, Akzent `#cba6f7` (Mauve), Text `#cdd6f4`
- **Tokyo Night:** Primär `#1a1b26`, Akzent `#7aa2f7` (Blue), Text `#a9b1d6`
""",
    },
}


# ── TUI Framework Management ────────────────────────────────────────────────
def check_tui_libraries() -> Table:
    """Prüft installierte Python TUI-Bibliotheken."""
    table = Table(title="Python TUI Framework Status", border_style="cyan")
    table.add_column("Bibliothek", style="bold white")
    table.add_column("Status", style="bold")
    table.add_column("Version", style="yellow")
    table.add_column("Beschreibung", style="dim")

    frameworks = {
        "textual": "Modernes Asynchrones Terminal UI Framework",
        "rich": "Reiche Formatierung, Tabellen, Markdown & Konsolen-Ausgabe",
        "urwid": "Klassisches konsolenbasiertes Widget-Toolkit",
        "curses": "Standard Curses Interface (Python Built-in)",
    }

    for name, desc in frameworks.items():
        try:
            mod = __import__(name)
            ver = getattr(mod, "__version__", "Vorhanden")
            table.add_row(name, "[green]✔ Installiert[/green]", str(ver), desc)
        except ImportError:
            table.add_row(name, "[red]✘ Fehlt[/red]", "-", desc)

    return table


def inspect_live_desktop_environment() -> Table:
    """Inspiziert die aktive Desktop-Umgebung und Ricing-Komponenten."""
    table = Table(title="CachyOS Desktop- & Ricing-Inspektor", border_style="magenta")
    table.add_column("Komponente", style="bold white")
    table.add_column("Erkannter Wert / Status", style="cyan")

    # Wayland Check
    session_type = os.environ.get("XDG_SESSION_TYPE", "Unbekannt")
    table.add_row("Session Typ", f"[bold green]{session_type}[/bold green]" if session_type == "wayland" else session_type)

    # Desktop
    current_desktop = os.environ.get("XDG_CURRENT_DESKTOP", "Unbekannt")
    table.add_row("Desktop Environment", current_desktop)

    # Accent Color via kreadconfig6
    accent = "-"
    if shutil.which("kreadconfig6"):
        res = subprocess.run(["kreadconfig6", "--file", "kdeglobals", "--group", "General", "--key", "AccentColor"], capture_output=True, text=True)
        accent = res.stdout.strip() or "Standard / Breeze"
    table.add_row("KDE Akzentfarbe (RGB)", accent)

    # Color Scheme
    scheme = "-"
    if shutil.which("kreadconfig6"):
        res = subprocess.run(["kreadconfig6", "--file", "kdeglobals", "--group", "General", "--key", "colorScheme"], capture_output=True, text=True)
        scheme = res.stdout.strip() or "BreezeDark"
    table.add_row("KDE Farbschema", scheme)

    # Tools vorhanden?
    for tool in ["klassy-settings", "kvantummanager", "oh-my-posh", "fastfetch", "alacritty"]:
        status = "[green]✔ Gefunden[/green]" if shutil.which(tool) else "[yellow]○ Nicht im PATH[/yellow]"
        table.add_row(f"Tool: {tool}", status)

    return table


def run_framework_demo(framework: str) -> None:
    """Startet Demonstrations-Tools der jeweiligen Bibliothek."""
    console.print(f"[bold cyan]Starte Demo für '{framework}'...[/bold cyan]")
    if framework == "textual":
        subprocess.run([sys.executable, "-m", "textual", "colors"])
    elif framework == "rich":
        subprocess.run([sys.executable, "-m", "rich.markdown", "--help"])
    elif framework == "urwid":
        demo_code = (
            "import urwid\n"
            "def handle_input(key):\n"
            "    if key in ('q', 'Q'): raise urwid.ExitMainLoop()\n"
            "txt = urwid.Text(('bold', 'Urwid 2026 Demo laeuft! Druecke Q zum Schliessen.'), align='center')\n"
            "fill = urwid.Filler(txt, valign='middle')\n"
            "loop = urwid.MainLoop(fill, unhandled_input=handle_input)\n"
            "loop.run()\n"
        )
        subprocess.run([sys.executable, "-c", demo_code])
    else:
        console.print(f"[red]Keine Demo für '{framework}' verfügbar.[/red]")


def show_knowledge_base() -> None:
    """Interaktives Handbuch für Ricing-Techniken."""
    while True:
        console.clear()
        console.print(Panel.fit("[bold magenta]CachyOS Plasma 6 Wayland Ricing-Enzyklopädie[/bold magenta]\n[dim]Best Practices, KWin Compositing & Konfigurationen[/dim]"))
        for key, item in RICE_KNOWLEDGE_BASE.items():
            console.print(f"  [bold yellow]{key})[/bold yellow] {item['title']}")
        console.print("  [bold yellow]q)[/bold yellow] Zurück zum Hauptmenü")

        choice = Prompt.ask("\nWähle ein Kapitel", default="1")
        if choice.lower() in ["q", "quit", "exit"]:
            break

        if choice in RICE_KNOWLEDGE_BASE:
            console.clear()
            doc = RICE_KNOWLEDGE_BASE[choice]
            console.print(Panel(doc["title"], style="bold cyan"))
            console.print(Markdown(doc["markdown"]))
            Prompt.ask("\n[dim]Drücke Enter zum Fortfahren...[/dim]")


def main_interactive_menu() -> None:
    """Hauptmenü der Anwendung."""
    while True:
        console.clear()
        console.print(Panel.fit(
            "[bold cyan]CachyOS Ricing & TUI Framework Master Toolkit[/bold cyan]\n"
            "[dim]KDE Plasma 6 Wayland Styling, Framework-Status & Interaktive Demos[/dim]",
            border_style="cyan"
        ))

        console.print("  [bold green]1)[/bold green] 📊 Python TUI Frameworks Status prüfen (Textual, Rich, Urwid)")
        console.print("  [bold green]2)[/bold green] 🖥️ CachyOS Desktop & Wayland Ricing-Inspektor ausführen")
        console.print("  [bold green]3)[/bold green] 📖 Plasma 6 Wayland Ricing Enzyklopädie öffnen")
        console.print("  [bold green]4)[/bold green] ▶️ Textual Color Demo starten")
        console.print("  [bold green]5)[/bold green] ▶️ Rich Markdown Demo starten")
        console.print("  [bold green]6)[/bold green] ▶️ Urwid Interactive Demo starten")
        console.print("  [bold green]7)[/bold green] 🔄 TUI Frameworks via Pip / Pacman aktualisieren")
        console.print("  [bold red]q)[/bold red] Beenden")

        choice = Prompt.ask("\nAuswahl", default="1")

        if choice == "1":
            console.clear()
            console.print(check_tui_libraries())
            Prompt.ask("\n[dim]Drücke Enter...[/dim]")
        elif choice == "2":
            console.clear()
            console.print(inspect_live_desktop_environment())
            Prompt.ask("\n[dim]Drücke Enter...[/dim]")
        elif choice == "3":
            show_knowledge_base()
        elif choice == "4":
            run_framework_demo("textual")
        elif choice == "5":
            run_framework_demo("rich")
        elif choice == "6":
            run_framework_demo("urwid")
        elif choice == "7":
            console.print("[bold yellow]Aktualisiere Textual, Rich und Urwid...[/bold yellow]")
            subprocess.run([sys.executable, "-m", "pip", "install", "--break-system-packages", "--upgrade", "textual", "rich", "urwid"])
            Prompt.ask("\n[dim]Drücke Enter...[/dim]")
        elif choice.lower() in ["q", "quit", "exit"]:
            console.print("[bold cyan]Auf Wiedersehen![/bold cyan]")
            break


def main() -> None:
    parser = argparse.ArgumentParser(description="CachyOS Ricing & TUI Framework Master Toolkit")
    parser.add_argument("--status", action="store_true", help="Gibt Bibliotheks- und Ricing-Status aus")
    parser.add_argument("--guide", action="store_true", help="Öffnet das Ricing-Handbuch")
    parser.add_argument("--demo-textual", action="store_true", help="Startet Textual Demo")
    parser.add_argument("--demo-rich", action="store_true", help="Startet Rich Demo")
    parser.add_argument("--demo-urwid", action="store_true", help="Startet Urwid Demo")

    args = parser.parse_args()

    if args.status:
        console.print(check_tui_libraries())
        console.print("")
        console.print(inspect_live_desktop_environment())
    elif args.guide:
        show_knowledge_base()
    elif args.demo_textual:
        run_framework_demo("textual")
    elif args.demo_rich:
        run_framework_demo("rich")
    elif args.demo_urwid:
        run_framework_demo("urwid")
    else:
        main_interactive_menu()


if __name__ == "__main__":
    main()
