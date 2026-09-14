# ⚡ CachyOS Control Center & System Architect (Masterpiece Edition)

[![Platform](https://img.shields.io/badge/Platform-Arch%20Linux%20%7C%20CachyOS-1793d1.svg?style=flat&logo=archlinux)](https://cachyos.org)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python)](https://python.org)
[![TUI](https://img.shields.io/badge/UI-Textual-green.svg)](https://textual.textualize.io)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

[🇬🇧 Switch to English Documentation](README.md)

<p align="center">
  <img src="preview_dashboard.png" alt="CachyOS Control Center Cockpit" width="900">
</p>
<p align="center">
  <img src="preview_interfaces.png" alt="CachyOS Control Center Netzwerk & Schnittstellen" width="900">
</p>

Das hochperformante, modulare Terminal-Kontrollzentrum (TUI) und Systemadministrations-Toolkit für **CachyOS / Arch Linux (KDE Plasma 6 Wayland)**.

Entwickelt nach strikten Architekturprinzipien:
- **The Architect (Node 01)**: Evidenzbasierte Kausalitätsprüfung, Low-Level-Kernel- & Hardware-Monitoring.
- **Omni-Feature Architect**: Vollständige, kompromisslose Implementierung ohne Platzhalter und ohne Funktionsduplikate.
- **Universal OS Janitor**: Sichere Systemhygiene, defensive Fehlerbehandlung und absoluter Schutz der Systemintegrität.

---

## 🏛️ Architektur & Modulübersicht

```text
cachyos-control-center/
├── app.py                      # Universeller Einstiegspunkt (TUI- & CLI-Modus)
├── cachyos_center.py           # Textual TUI Master Application (Full-Width Tabs & Ribbon)
├── setup.sh                    # Indestructible Installations-Skript (pacman / venv)
├── run.sh                      # Universal-Starter
├── requirements.txt            # Python-Abhängigkeiten
├── README.md                   # Englische Dokumentation
├── README_DE.md                # Deutsche Dokumentation (dieses Dokument)
├── .gitignore                  # Git-Ausschlussregeln
│
├── core/                       # Low-Level & Business-Logik
│   ├── system.py               # Hardware-Telemetrie (CPU, RAM, Btrfs, Systemd-Units)
│   ├── network.py              # Interface-Management, Monitor-Mode, AP-Scanner
│   ├── tailscale.py            # Tailscale Mesh-Topologie, Exit-Nodes, Pings
│   ├── diagnostics.py          # Evidenzbasierte Netzwerkprüfungen (DNSSEC, Ports, MTU)
│   ├── maintenance.py          # Pacman-Cache, Pacnew-Audit, Journal-Trimming, SSD-TRIM
│   └── ricing.py               # Wayland KWin Inspector, Fastfetch, Ricing-Guide
│
├── ui/                         # Modernes Benutzeroberflächen-Framework
│   ├── theme.py                # TCSS-Stylesheet (High-Contrast Nordic Dark)
│   └── screens/                # Ergonomische Multi-Pane Screens ohne Duplikate
│       ├── dashboard_view.py   # Cockpit: 4 Gauges, Service-Matrix & Integritäts-Audit
│       ├── wifi_view.py        # Funk & Interfaces: Interface-Steuerung & AP-Scanner
│       ├── tailscale_view.py   # Tailscale Mesh: Peer-Tabelle, Knoten-Inspektor & Routing
│       ├── diag_view.py        # Tiefendiagnose: Schnell-, Standard- & Deep-Audit + Befund
│       ├── maint_view.py       # Systemwartung: Cache, Journal, SSD, Units & .pacnew Auditor
│       ├── rice_view.py        # Plasma 6 Ricing: KWin Compositor & Markdown-Handbuch
│       └── migrator_view.py    # Workspace-Architekt: 7-Säulen-Synthese & Verzeichnis-Scan
│
└── bin/                        # Autarke Standalone-Werkzeuge
    ├── net_diagnose.py         # Vollständige Standalone-Diagnosesuite
    ├── agy_migrator.py         # Autonomer Verzeichnis-Synthesizer
    └── cachyos_rice_toolkit.py # Interaktiver Ricing- & TUI-Leitfaden
```

---

## 🚀 Installation & Voraussetzungen

### 1. Schnelleinrichtung (Empfohlen)

Das Skript `setup.sh` erkennt CachyOS / Arch Linux automatisch und installiert fehlende Abhängigkeiten nativ via `pacman` oder richtet ein lokales `.venv` ein:

```bash
git clone https://github.com/Graba92/cachyos-control-center.git
cd cachyos-control-center
chmod +x setup.sh run.sh
./setup.sh
```

### 2. Manuelle Installation via Pacman (Arch Linux / CachyOS)

```bash
sudo pacman -S --needed python-textual python-rich
```

### 3. Manuelle Installation via pip / Virtualenv

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## 🖥️ Bedienung

### 1. Interaktives TUI Control Center
```bash
./run.sh
# oder
python3 app.py
```

### 2. Schnelle CLI-Befehle (ohne grafische TUI)
```bash
# Systemstatus & Hardwaremetriken ausgeben:
python3 app.py --status

# Schnelle Netzwerk- und DNS-Diagnose:
python3 app.py --diag quick

# Standard- oder Tiefenprüfung:
python3 app.py --diag standard
python3 app.py --diag deep

# Systemwartung & .pacnew-Prüfung:
python3 app.py --maint

# Versionsausgabe:
python3 app.py --version
```

---

## ⌨️ Tastaturkürzel (Keybindings)

| Taste | Bereich | Funktion |
| :---: | :--- | :--- |
| `1` | **Cockpit** | Systemstatus, CPU/RAM/Disk Gauges, Systemd-Dienste & Netzwerk-Routing |
| `2` | **Funk & Interfaces** | Physische Schnittstellen, Monitor-Mode, Störprozesse killen & AP-Scan |
| `3` | **Tailscale Mesh** | Mesh-Peers, Exit-Node-Routing & Latenz-Pings |
| `4` | **Tiefendiagnose** | Evidenzbasierte Netzwerkprüfungen, DNSSEC, Ports, MTU & Empfehlungen |
| `5` | **Systemwartung** | Pacman-Cache, Journal-Vakuum, SSD TRIM, Unit-Resets & .pacnew-Auditor |
| `6` | **Plasma 6 Ricing** | Wayland KWin Inspector, Fastfetch-Ausgabe & Ricing-Handbuch |
| `7` | **Workspace-Architekt** | 7-Säulen-Synthese & Verzeichnis-Kategorisierung |
| `r` | **Aktualisieren** | Telemetrieband und alle aktiven Ansichten neu einlesen |
| `q` | **Beenden** | Control Center sauber schließen |

---

## 🛡️ Sicherheits- & Integritätsgarantien

- **Keine Zerstörung**: Wartungsfunktionen (wie das Leeren von Caches oder das Bereinigen des Systemd-Journals) nutzen systemkonforme Kommandos (`paccache`, `journalctl --vacuum-time`, `fstrim`).
- **Berechtigungs-Management**: Befehle, die Root-Rechte erfordern, nutzen `pkexec` mit grafischem Polkit-Dialog oder führen Fallbacks durch, falls keine Rechte vorliegen.
- **Defensive Netzwerk-Steuerung**: Schnittstellen-Umschaltungen (z. B. Monitor-Mode) führen vorab Prozessprüfungen durch, um Paketkonflikte zu verhindern.

---

## 📄 Lizenz

Dieses Projekt steht unter der [MIT-Lizenz](LICENSE).
