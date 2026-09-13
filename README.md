# ⚡ CachyOS Control Center & System Architect (Masterpiece Edition)

[![Platform](https://img.shields.io/badge/Platform-Arch%20Linux%20%7C%20CachyOS-1793d1.svg?style=flat&logo=archlinux)](https://cachyos.org)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python)](https://python.org)
[![TUI](https://img.shields.io/badge/UI-Textual-green.svg)](https://textual.textualize.io)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

[🇩🇪 Zur deutschen Dokumentation wechseln](README_DE.md)

A high-performance, modular Terminal User Interface (TUI) and administration suite built specifically for **CachyOS / Arch Linux (KDE Plasma 6 Wayland)**.

Engineered under strict architectural tenets:
- **The Architect (Node 01)**: Evidence-based causality checks, low-level kernel and hardware monitoring.
- **Omni-Feature Architect**: Full, uncompromising implementation without placeholders or redundant components.
- **Universal OS Janitor**: Defensive system hygiene, graceful error handling, and absolute system integrity preservation.

---

## 🏛️ Architecture & Module Structure

```text
cachyos-control-center/
├── app.py                      # Universal CLI & TUI entry point
├── cachyos_center.py           # Textual TUI Master Application (Full-Width Tabs & Ribbon)
├── setup.sh                    # Indestructible installation & setup script
├── run.sh                      # Universal launcher
├── requirements.txt            # Python dependencies
├── README.md                   # English documentation (this file)
├── README_DE.md                # German documentation
├── .gitignore                  # Git ignore rules
│
├── core/                       # Low-level system & business logic
│   ├── system.py               # Hardware telemetry (CPU, RAM, Btrfs, systemd units)
│   ├── network.py              # Interface management, monitor mode, AP scanner
│   ├── tailscale.py            # Tailscale mesh topology, exit nodes, peer pings
│   ├── diagnostics.py          # Evidence-based network diagnostics (DNSSEC, ports, MTU)
│   ├── maintenance.py          # Pacman cache, pacnew audit, journal trimming, SSD-TRIM
│   └── ricing.py               # Wayland KWin inspector, Fastfetch, ricing handbook
│
├── ui/                         # Modern Textual interface layer
│   ├── theme.py                # Nordic Dark high-contrast TCSS stylesheet
│   └── screens/                # Multi-pane ergonomic screen components
│       ├── dashboard_view.py   # Cockpit: live gauges, service matrix & telemetry
│       ├── wifi_view.py        # Wireless & interfaces: control & AP scanning
│       ├── tailscale_view.py   # Tailscale Mesh: peer table, node inspector & routing
│       ├── diag_view.py        # Deep diagnostics: quick, standard & deep audits
│       ├── maint_view.py       # System hygiene: cache, journal, SSD & .pacnew auditor
│       ├── rice_view.py        # Plasma 6 Ricing: KWin compositor & markdown manual
│       └── migrator_view.py    # Workspace architect: 7-pillar synthesis & scanner
│
└── bin/                        # Autonomous standalone utilities
    ├── net_diagnose.py         # Standalone network diagnostic suite
    ├── agy_migrator.py         # Autonomous directory synthesizer
    └── cachyos_rice_toolkit.py # Interactive ricing and TUI toolkit
```

---

## 🚀 Installation & Setup

### 1. Automated Quick Setup (Recommended)

The included `setup.sh` script automatically detects Arch Linux / CachyOS and either installs native packages via `pacman` or provisions an isolated Python virtual environment:

```bash
git clone https://github.com/Graba92/cachyos-control-center.git
cd cachyos-control-center
chmod +x setup.sh run.sh
./setup.sh
```

### 2. Manual Installation via Pacman (Arch Linux / CachyOS)

```bash
sudo pacman -S --needed python-textual python-rich
```

### 3. Manual Installation via pip / Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## 🖥️ Usage

### 1. Interactive TUI Control Center
```bash
./run.sh
# or
python3 app.py
```

### 2. Standalone CLI Commands (Headless / Non-TUI)
```bash
# Print hardware telemetry and system telemetry:
python3 app.py --status

# Quick network & DNS diagnostic:
python3 app.py --diag quick

# Standard or deep diagnostics:
python3 app.py --diag standard
python3 app.py --diag deep

# Run system hygiene & .pacnew audit:
python3 app.py --maint

# Display version:
python3 app.py --version
```

---

## ⌨️ Keybindings

| Key | Section | Description |
| :---: | :--- | :--- |
| `1` | **Cockpit** | System telemetry, CPU/RAM/Disk gauges, systemd units & routing |
| `2` | **Wireless & Interfaces** | Physical interfaces, monitor mode toggles & AP scanner |
| `3` | **Tailscale Mesh** | Mesh peers, exit node routing & latency pings |
| `4` | **Diagnostics** | Evidence-based network tests, DNSSEC, ports, MTU & tips |
| `5` | **Maintenance** | Pacman cache cleanup, journal vacuum, SSD TRIM, .pacnew audit |
| `6` | **Plasma 6 Ricing** | Wayland KWin compositor inspection & ricing guide |
| `7` | **Workspace Architect** | 7-pillar synthesis & workspace restructuring |
| `r` | **Refresh** | Re-read telemetry ribbon and active views |
| `q` | **Quit** | Cleanly exit the control center |

---

## 🛡️ Security & Integrity Guarantees

- **Non-Destructive Operations**: Maintenance routines use standard Arch Linux utilities (`paccache`, `journalctl --vacuum-time`, `fstrim`).
- **Privilege Separation**: Privileged operations invoke `pkexec` with standard polkit authentication dialogues without arbitrary background root escalation.
- **Fail-Safe Checks**: Interfaces and network tools execute defensive pre-flight process checks before modifying device modes.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
