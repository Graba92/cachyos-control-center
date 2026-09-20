# 📜 Changelog — CachyOS Control Center

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-09-20 (Unified Architecture & Modularization)

### 🌟 Added
- **Unified Modular Dashboard (TUI):** Complete refactor into high-performance Python `textual` architecture with Catppuccin Mocha / CachyOS Emerald design.
- **Kernel & Driver Management:**
  - Real-time detection of installed and repository CachyOS kernel variants (BORE, LTO, RT, BMQ, LTS, Server, RC).
  - Dynamic status badges: `[Active Running]`, `[Installed]`, `[Available]`.
  - Comprehensive GPU hardware matrix (NVIDIA, AMD, Intel) with driver type detection (Proprietary vs. Open Source), live wattage, thermals, and clock states.
- **Hardware & Power Profiles:**
  - Dynamic CPU scaling governor controls (`performance`, `schedutil`, `powersave`, `ondemand`, `conservative`).
  - Energy Performance Preference (EPP) switcher (`performance`, `balance_performance`, `power`).
  - Thermal monitoring engine across all `/sys/class/thermal/` zones with passive trip point validation and throttle alerts.
- **System Maintenance & Package Hygiene:**
  - One-click mirror benchmarking integration supporting `cachyos-rate-mirrors` and `rate-mirrors`.
  - Package cache trimmer (`paccache` / `pacman -Sc`) with disk usage calculations.
  - Orphan package cleaner (`pacman -Qtdq` -> `pacman -Rns`).
  - Configuration audit detecting unmerged `.pacnew` files in `/etc`.
  - SSD TRIM (`fstrim -av`) and systemd journal vacuuming.
  - Pacman lock detection (`/var/lib/pacman/db.lck`) preventing race conditions.
- **Systemd Service Manager:**
  - Dedicated service control panel with real-time status, substate, and enable/disable state.
  - Granular start, stop, restart, enable, and disable actions.
- **Deep Diagnostics & Boot Auditing:**
  - Active kernel boot parameter inspection (`/proc/cmdline`).
  - Boot performance breakdown via `systemd-analyze time` (Firmware, Loader, Kernel, Initrd, Userspace).
  - Kernel log feed via `journalctl -k` / `dmesg`.
  - Complete hardware specification snapshot.
- **Privilege Isolation & Security:**
  - Control center runs completely unprivileged as standard user.
  - Root elevation isolated via modular Polkit policy (`org.cachyos.controlcenter.policy`).
  - Clean error interception for Polkit cancellation (exit code 126).
- **Localization (i18n):**
  - Full dual-language engine (German `de_DE` and English `en_US`).
  - Dynamic runtime language toggle (shortcut `L`).
- **CLI Subcommands & Headless Automation:**
  - `--status`: System telemetry and hardware snapshot in terminal.
  - `--clean`: Headless cache trimming and orphan removal.
  - `--json`: Machine-readable full system audit report.
  - `--diag`: Network and latency diagnostics.
  - `--lang`: Set persistent default language.
- **Packaging & Desktop Assets:**
  - Production-ready `PKGBUILD` for Arch Linux & CachyOS.
  - FreeDesktop `cachyos-control-center.desktop` entry.
  - Scalable vector icon (`data/cachyos-control-center.svg`).
  - Configuration template (`config.example.toml`).
