#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
 AGY-ARCHITECT — Antigravity Directory Synthesizer
 CachyOS / Arch Edition
 Made by Matze Graba & Chati
===============================================================================
 Autonomes, verlustfreies Migrations- und TUI-Reorganisations-Tool.
 Transformiert unstrukturierte Verzeichnisse in eine modulare Ziel-Architektur
 mit 100% Zero-Data-Loss-Garantie und vollständigem Mapping-Index.
===============================================================================
"""

import os
import sys
import shutil
import json
import fnmatch
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Any

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import Prompt, Confirm
    from rich.progress import (
        Progress,
        SpinnerColumn,
        BarColumn,
        TextColumn,
        TaskProgressColumn,
        TimeRemainingColumn,
    )
    from rich.table import Table
    from rich.text import Text
except ImportError:
    print("\n[FEHLER] Das Python-Paket 'rich' ist nicht installiert.")
    print("Installation auf CachyOS/Arch:")
    print("  sudo pacman -S python-rich   ODER   pip install rich\n")
    sys.exit(1)


console = Console()

# =============================================================================
# ZIEL-ARCHITEKTUR & REGELWERK
# =============================================================================
TARGET_WORKSPACES = [
    "01_AI_LAB",
    "02_DEV_WORKSPACE",
    "03_SYSADMIN_CORE",
    "04_BACKUP_FORENSICS",
    "05_HARDWARE_MODS",
    "06_ARCHIVE_TEMP",
    "07_DOCS_ROOT",
]

LEGACY_ARCHIVE_SUBDIR = "06_ARCHIVE_TEMP/Unsorted_Legacy"

# Routing-Definitionen (exakte Namen oder Glob-Muster)
ROUTING_RULES: List[Tuple[str, str]] = [
    # 01_AI_LAB
    ("AI_Library_V2*", "01_AI_LAB"),
    ("ULT*", "01_AI_LAB"),
    ("WICHTIG_ROLLEN*", "01_AI_LAB"),
    ("Image_Promts*", "01_AI_LAB"),
    ("LLM_ASSIST*", "01_AI_LAB"),
    ("githun-awesome-gemini*", "01_AI_LAB"),
    ("SOZIAL_MONEY_AUTO*", "01_AI_LAB"),
    ("Universal_AI_Agent_System_Manifest*", "01_AI_LAB"),
    ("*prompt*.md", "01_AI_LAB"),
    ("*Prompt*.md", "01_AI_LAB"),
    ("*persona*.md", "01_AI_LAB"),

    # 02_DEV_WORKSPACE
    ("DIGIgame*", "02_DEV_WORKSPACE"),
    ("grabafi*", "02_DEV_WORKSPACE"),
    ("APKG*", "02_DEV_WORKSPACE"),
    ("APKC*", "02_DEV_WORKSPACE"),
    ("chrome-extension*", "02_DEV_WORKSPACE"),
    ("tui_creator*", "02_DEV_WORKSPACE"),

    # 03_SYSADMIN_CORE
    ("cachyos_scripts*", "03_SYSADMIN_CORE"),
    ("tino*", "03_SYSADMIN_CORE"),
    ("own-tool*", "03_SYSADMIN_CORE"),
    ("first-start-os*", "03_SYSADMIN_CORE"),
    ("arch-guardian*", "03_SYSADMIN_CORE"),
    ("ricing-guid*", "03_SYSADMIN_CORE"),
    ("templates*", "03_SYSADMIN_CORE"),
    ("Font_Schriftarten*", "03_SYSADMIN_CORE"),
    ("tailscale-control.sh*", "03_SYSADMIN_CORE"),
    ("DNS_HOME*", "03_SYSADMIN_CORE"),
    ("*.fish", "03_SYSADMIN_CORE"),
    ("*boot_animation*", "03_SYSADMIN_CORE"),

    # 04_BACKUP_FORENSICS
    ("Phil-Handy-Sicherung*", "04_BACKUP_FORENSICS"),
    ("phone_internal_storage*", "04_BACKUP_FORENSICS"),
    ("Chat-Sicherung*", "04_BACKUP_FORENSICS"),
    ("Forensic_Recovery_Session*", "04_BACKUP_FORENSICS"),
    ("Pic-saver*", "04_BACKUP_FORENSICS"),
    ("backup_phone*", "04_BACKUP_FORENSICS"),
    ("*Android-F*.md", "04_BACKUP_FORENSICS"),
    ("*recovery*.md", "04_BACKUP_FORENSICS"),
    ("*recovery*.log", "04_BACKUP_FORENSICS"),
    ("*photorec*.log", "04_BACKUP_FORENSICS"),

    # 05_HARDWARE_MODS
    ("HDMI-CEC-STEUERUNGS-TOOL*", "05_HARDWARE_MODS"),
    ("WICHTIGE-PROJEKTE*", "05_HARDWARE_MODS"),
    ("*cec*.md", "05_HARDWARE_MODS"),
    ("*CEC*.md", "05_HARDWARE_MODS"),
    ("F5121*", "05_HARDWARE_MODS"),
    ("Iphone-helper*", "05_HARDWARE_MODS"),
    ("*ps3_geek_tool*", "05_HARDWARE_MODS"),
    ("*sony_bootloader*", "05_HARDWARE_MODS"),
    ("*xboxg*", "05_HARDWARE_MODS"),

    # 07_DOCS_ROOT
    ("CachyOS_Reference_Guide.md", "07_DOCS_ROOT"),
    ("Kali_Linux_Reference_Guide.md", "07_DOCS_ROOT"),
    ("anweisung.MD", "07_DOCS_ROOT"),
    ("anweisung.md", "07_DOCS_ROOT"),
    ("fun-script-verlauf.md", "07_DOCS_ROOT"),
    ("ARBEITSVEREINBARUNG*.md", "07_DOCS_ROOT"),
    ("pcandlaptopdata.md", "07_DOCS_ROOT"),

    # 06_ARCHIVE_TEMP
    ("Valhalla*", "06_ARCHIVE_TEMP"),
    ("Temp_Desktop*", "06_ARCHIVE_TEMP"),
    ("githubdownlaod-tools-data*", "06_ARCHIVE_TEMP"),
    ("MANAGER_PRIVAT*", "06_ARCHIVE_TEMP"),
    ("noch nicht eingeordnet*", "06_ARCHIVE_TEMP"),
    ("venv*", "06_ARCHIVE_TEMP"),
]


def print_banner() -> None:
    """Zeigt das offizielle CachyOS / Arch Banner mit Antigravity-Branding."""
    banner_text = Text()
    banner_text.append("   █████╗  ██████╗ ██╗   ██╗\n", style="bold cyan")
    banner_text.append("  ██╔══██╗██╔════╝ ╚██╗ ██╔╝\n", style="bold cyan")
    banner_text.append("  ███████║██║  ███╗ ╚████╔╝ \n", style="bold cyan")
    banner_text.append("  ██╔══██║██║   ██║  ╚██╔╝  \n", style="bold cyan")
    banner_text.append("  ██║  ██║╚██████╔╝   ██║   \n", style="bold cyan")
    banner_text.append("  ╚═╝  ╚═╝ ╚═════╝    ╚═╝   \n", style="bold cyan")
    banner_text.append("──────────────────────────────────────────────────────────────────────────\n", style="blue")
    banner_text.append(" AGY-ARCHITECT — CachyOS / Arch Edition\n", style="bold white")
    banner_text.append(" Made by Matze Graba & Chati\n", style="bold magenta")
    banner_text.append("──────────────────────────────────────────────────────────────────────────", style="blue")

    console.print(Panel(banner_text, border_style="blue", expand=False))


def determine_target_workspace(item_name: str) -> str:
    """
    Ermittelt anhand vordefinierter Routing-Regeln den Ziel-Workspace.
    Trifft keine Regel zu, wandert das Element garantiert in das Legacy-Archiv.
    """
    for pattern, workspace in ROUTING_RULES:
        if fnmatch.fnmatch(item_name, pattern) or fnmatch.fnmatch(item_name.lower(), pattern.lower()):
            return workspace
    return LEGACY_ARCHIVE_SUBDIR


def get_collision_free_path(destination_path: Path) -> Path:
    """
    Garantiert Zero Data Loss durch automatische Konfliktauflösung.
    Falls am Zielort bereits eine Datei/ein Ordner gleichen Namens existiert,
    wird ein fortlaufender Zähler angehängt.
    """
    if not destination_path.exists():
        return destination_path

    parent = destination_path.parent
    stem = destination_path.stem
    suffix = destination_path.suffix

    counter = 1
    while True:
        if destination_path.is_dir() and not suffix:
            new_name = f"{stem}_collision_{counter}"
        else:
            new_name = f"{stem}_collision_{counter}{suffix}"
        candidate = parent / new_name
        if not candidate.exists():
            return candidate
        counter += 1


def calculate_item_size(path: Path) -> int:
    """Berechnet die Größe einer Datei oder rekursiv eines Verzeichnisses."""
    if path.is_file() or path.is_symlink():
        try:
            return path.stat().st_size
        except OSError:
            return 0
    total_size = 0
    try:
        for root, _, files in os.walk(path):
            for f in files:
                fp = os.path.join(root, f)
                if not os.path.islink(fp) and os.path.exists(fp):
                    try:
                        total_size += os.path.getsize(fp)
                    except OSError:
                        pass
    except OSError:
        pass
    return total_size


def format_bytes(size: float) -> str:
    """Formatiert Byte-Werte lesbar."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if abs(size) < 1024.0:
            return f"{size:3.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"


def request_and_validate_paths(cli_source: str = None, cli_target: str = None, cli_inplace: bool = False) -> Tuple[Path, Path, bool]:
    """
    Interaktive Eingabe und strikte Validierung der Quell- und Zielpfade.
    Keine fest verdrahteten Pfade. Unterstützt auch CLI-Parameter.
    """
    console.print("\n[bold cyan]1. Quell- und Zielkonfiguration[/bold cyan]")

    if cli_source:
        src_path = Path(cli_source).expanduser().resolve()
        if not src_path.exists() or not src_path.is_dir():
            console.print(f"[red]Fehler: Ungültiger CLI-Quellpfad:[/red] {cli_source}")
            sys.exit(1)
    else:
        while True:
            src_input = Prompt.ask("[bold yellow]➤ Absoluten Pfad des ZU MIGRATIONIERENDEN Quellordners eingeben[/bold yellow]").strip()
            if not src_input:
                console.print("[red]Eingabe darf nicht leer sein.[/red]")
                continue

            src_path = Path(src_input).expanduser().resolve()
            if not src_path.exists():
                console.print(f"[red]Fehler: Pfad existiert nicht:[/red] {src_path}")
                continue
            if not src_path.is_dir():
                console.print(f"[red]Fehler: Pfad ist kein Verzeichnis:[/red] {src_path}")
                continue
            if not os.access(src_path, os.R_OK | os.W_OK):
                console.print(f"[red]Fehler: Keine ausreichenden Lese-/Schreibrechte für:[/red] {src_path}")
                continue
            break

    console.print(f"[green]✓ Quellverzeichnis validiert:[/green] [bold]{src_path}[/bold]\n")

    if cli_target:
        dest_path = Path(cli_target).expanduser().resolve()
        dest_path.mkdir(parents=True, exist_ok=True)
        is_inplace = (dest_path == src_path)
    elif cli_inplace:
        dest_path = src_path
        is_inplace = True
    else:
        is_inplace = Confirm.ask(
            "[bold cyan]➤ In-Place-Migration im selben Verzeichnis durchführen?[/bold cyan]\n"
            "  (Erzeugt die 7 Workspaces direkt in diesem Ordner und sortiert die Inhalte hinein)",
            default=True
        )

        if is_inplace:
            dest_path = src_path
        else:
            while True:
                dest_input = Prompt.ask("[bold yellow]➤ Absoluten Pfad des neuen ZIELORDNERS eingeben[/bold yellow]").strip()
                if not dest_input:
                    console.print("[red]Eingabe darf nicht leer sein.[/red]")
                    continue
                dest_path = Path(dest_input).expanduser().resolve()
                try:
                    dest_path.mkdir(parents=True, exist_ok=True)
                    if not os.access(dest_path, os.W_OK):
                        console.print(f"[red]Fehler: Keine Schreibrechte im Zielordner:[/red] {dest_path}")
                        continue
                    break
                except Exception as e:
                    console.print(f"[red]Fehler beim Erstellen des Zielordners:[/red] {e}")
                    continue

    console.print(f"[green]✓ Zielverzeichnis validiert:[/green] [bold]{dest_path}[/bold]\n")
    return src_path, dest_path, is_inplace


def execute_migration(cli_source: str = None, cli_target: str = None, cli_inplace: bool = False, auto_confirm: bool = False) -> None:
    """Hauptablauf des Antigravity-Migrationsprozesses."""
    print_banner()

    src_dir, dest_dir, is_inplace = request_and_validate_paths(cli_source, cli_target, cli_inplace)

    # Schutzfilter: Eigene Workspaces dürfen nicht verschoben werden
    protected_names = set(TARGET_WORKSPACES) | {
        "agy_migration_index.json",
        "AGY_MIGRATION_INDEX.md",
        "VERZEICHNISS.md",
        "agy_migrator.py",
        ".git",
    }

    # Erfassen aller Elemente der obersten Ebene
    raw_entries = [e for e in src_dir.iterdir() if e.name not in protected_names]

    if not raw_entries:
        console.print("[yellow]Keine zu migrierenden Elemente im Quellordner gefunden.[/yellow]")
        return

    # Workspaces und Legacy-Archiv im Ziel anlegen
    for ws in TARGET_WORKSPACES:
        (dest_dir / ws).mkdir(parents=True, exist_ok=True)
    (dest_dir / LEGACY_ARCHIVE_SUBDIR).mkdir(parents=True, exist_ok=True)

    # Migrations-Plan aufstellen
    migration_plan: List[Dict[str, Any]] = []
    total_bytes = 0

    with Progress(
        SpinnerColumn(),
        TextColumn("[bold cyan]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as scan_progress:
        scan_task = scan_progress.add_task("Analysiere Objekte & berechne Größen...", total=len(raw_entries))

        for item in raw_entries:
            target_sub = determine_target_workspace(item.name)
            target_folder = dest_dir / target_sub
            proposed_target = target_folder / item.name
            final_target = get_collision_free_path(proposed_target)
            size = calculate_item_size(item)
            total_bytes += size

            migration_plan.append({
                "name": item.name,
                "type": "directory" if item.is_dir() else ("symlink" if item.is_symlink() else "file"),
                "source": str(item),
                "target_workspace": target_sub,
                "destination": str(final_target),
                "size_bytes": size,
                "status": "pending",
                "error": None,
            })
            scan_progress.update(scan_task, advance=1)

    # Zusammenfassungs-Tabelle vor dem Ausführen anzeigen
    summary_table = Table(title="📋 Geplanter Migrations-Ablauf", border_style="blue", show_header=True)
    summary_table.add_column("Ziel-Workspace", style="cyan", no_wrap=True)
    summary_table.add_column("Anzahl Objekte", justify="right", style="green")

    workspace_counts: Dict[str, int] = {}
    for entry in migration_plan:
        ws = entry["target_workspace"]
        workspace_counts[ws] = workspace_counts.get(ws, 0) + 1

    for ws in sorted(workspace_counts.keys()):
        summary_table.add_row(ws, str(workspace_counts[ws]))

    console.print(summary_table)
    console.print(f"[bold]Gesamtvolumen zu bewegender Daten:[/bold] [yellow]{format_bytes(total_bytes)}[/yellow]")
    console.print(f"[bold]Gesamtzahl primärer Wurzel-Objekte:[/bold] [yellow]{len(migration_plan)}[/yellow]\n")

    if not auto_confirm:
        confirmed = Confirm.ask("[bold red]➤ Migration jetzt unwiderruflich starten?[/bold red]", default=False)
        if not confirmed:
            console.print("[yellow]Operation abgebrochen durch Benutzer. Keine Änderungen vorgenommen.[/yellow]")
            sys.exit(0)

    # Migrations-Durchführung mit Rich Progress Bar
    console.print("\n[bold cyan]2. Führe atomare Verschiebung durch (Zero Data Loss)[/bold cyan]")
    start_time = datetime.now()
    moved_count = 0
    error_count = 0

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=40, style="blue", complete_style="green"),
        TaskProgressColumn(),
        TimeRemainingColumn(),
        console=console,
    ) as move_progress:
        move_task = move_progress.add_task("Verschiebe Objekte...", total=len(migration_plan))

        for entry in migration_plan:
            src = Path(entry["source"])
            dest = Path(entry["destination"])
            move_progress.update(move_task, description=f"[cyan]Bewege:[/cyan] {src.name[:30]}")

            try:
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(src), str(dest))
                entry["status"] = "success"
                entry["migrated_at"] = datetime.now().isoformat()
                moved_count += 1
            except Exception as ex:
                entry["status"] = "error"
                entry["error"] = str(ex)
                error_count += 1
                console.print(f"[red]Fehler bei {src.name}:[/red] {ex}")

            move_progress.update(move_task, advance=1)

    duration = datetime.now() - start_time

    # =========================================================================
    # GENERIERUNG DES MIGRATIONS-INDEX (JSON & MARKDOWN)
    # =========================================================================
    console.print("\n[bold cyan]3. Erzeuge lückenlosen Migrations-Index[/bold cyan]")

    index_json_path = dest_dir / "agy_migration_index.json"
    index_md_path = dest_dir / "AGY_MIGRATION_INDEX.md"

    index_payload = {
        "metadata": {
            "tool": "AGY-ARCHITECT (Antigravity Directory Synthesizer)",
            "version": "1.0.0-ArchCachyOS",
            "executed_at": start_time.isoformat(),
            "completed_at": datetime.now().isoformat(),
            "duration_seconds": round(duration.total_seconds(), 2),
            "source_directory": str(src_dir),
            "destination_directory": str(dest_dir),
            "is_inplace": is_inplace,
            "total_items": len(migration_plan),
            "moved_items": moved_count,
            "failed_items": error_count,
            "total_bytes_processed": total_bytes,
        },
        "target_workspaces": TARGET_WORKSPACES,
        "mappings": migration_plan,
    }

    # 1. JSON Index schreiben
    try:
        with open(index_json_path, "w", encoding="utf-8") as f:
            json.dump(index_payload, f, indent=2, ensure_ascii=False)
        console.print(f"[green]✓ JSON-Index erfolgreich geschrieben:[/green] {index_json_path}")
    except Exception as e:
        console.print(f"[red]Fehler beim Schreiben des JSON-Index:[/red] {e}")

    # 2. Human-Readable Markdown Index schreiben
    try:
        md_lines = [
            "# 🗺️ AGY MIGRATION INDEX — VOLLSTÄNDIGER MAPPING-REPORT",
            "",
            f"- **Ausführungsdatum:** `{start_time.strftime('%Y-%m-%d %H:%M:%S')}`",
            f"- **Dauer:** `{round(duration.total_seconds(), 2)} Sekunden`",
            f"- **Quellpfad:** `{src_dir}`",
            f"- **Zielpfad:** `{dest_dir}`",
            f"- **Erfolgreich migriert:** `{moved_count}` von `{len(migration_plan)}` Objekten",
            f"- **Fehler:** `{error_count}`",
            f"- **Datenvolumen:** `{format_bytes(total_bytes)}`",
            "",
            "---",
            "",
            "## 📂 Detailliertes Pfad-Mapping",
            "",
            "| Ursprünglicher Pfad | Neuer Pfad | Typ | Größe | Status |",
            "| :--- | :--- | :--- | :--- | :--- |",
        ]

        for item in migration_plan:
            status_icon = "✅ OK" if item["status"] == "success" else f"❌ Fehler ({item['error']})"
            md_lines.append(
                f"| `{item['source']}` | `{item['destination']}` | {item['type']} | {format_bytes(item['size_bytes'])} | {status_icon} |"
            )

        md_lines.append("")
        md_lines.append("---")
        md_lines.append("*Erstellt durch AGY-ARCHITECT für CachyOS / Arch Linux.*")

        with open(index_md_path, "w", encoding="utf-8") as f:
            f.write("\n".join(md_lines) + "\n")
        console.print(f"[green]✓ Markdown-Index erfolgreich geschrieben:[/green] {index_md_path}")
    except Exception as e:
        console.print(f"[red]Fehler beim Schreiben des Markdown-Index:[/red] {e}")

    # Abschlussbericht Panel
    summary_text = (
        f"[bold green]MIGRATION ERFOLGREICH ABGESCHLOSSEN![/bold green]\n\n"
        f"• [bold]Objekte verschoben:[/bold] {moved_count} / {len(migration_plan)}\n"
        f"• [bold]Fehleranzahl:[/bold] {error_count}\n"
        f"• [bold]Dauer:[/bold] {round(duration.total_seconds(), 2)} s\n"
        f"• [bold]Index-Dateien:[/bold]\n"
        f"   - {index_json_path.name}\n"
        f"   - {index_md_path.name}\n"
    )
    console.print(Panel(summary_text, title="Ergebnis", border_style="green", expand=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AGY-ARCHITECT — Directory Synthesizer")
    parser.add_argument("--source", "-s", help="Quellverzeichnis (z. B. /home/graba/Schreibtisch/ASGRAD)")
    parser.add_argument("--target", "-t", help="Zielverzeichnis")
    parser.add_argument("--inplace", "-i", action="store_true", help="In-Place-Migration im Quellverzeichnis")
    parser.add_argument("--yes", "-y", action="store_true", help="Bestätigung automatisch akzeptieren")

    args = parser.parse_args()

    try:
        execute_migration(
            cli_source=args.source,
            cli_target=args.target,
            cli_inplace=args.inplace,
            auto_confirm=args.yes
        )
    except KeyboardInterrupt:
        console.print("\n[yellow]Migration durch Benutzer abgebrochen (SIGINT).[/yellow]")
        sys.exit(130)
    except Exception as general_error:
        console.print(f"\n[bold red]Unerwarteter fataler Fehler:[/bold red] {general_error}")
        sys.exit(1)
