[🇩🇪 Zur deutschen Dokumentation wechseln](README_DE.md) | [🇬🇧 Switch to English Documentation](README.md)

# ⚡ CachyOS Control Center & Unified System Administrator

[![GitHub](https://img.shields.io/badge/GitHub-Graba92%2Fcachyos--control--center-blue?logo=github)](https://github.com/Graba92/cachyos-control-center)
[![Platform](https://img.shields.io/badge/Platform-Arch%20Linux%20%7C%20CachyOS-1793d1.svg?style=flat&logo=archlinux)](https://cachyos.org)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg?logo=python)](https://python.org)
[![TUI](https://img.shields.io/badge/UI-Textual%208.2%2B-green.svg)](https://textual.textualize.io)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)
[![Release](https://img.shields.io/badge/Version-v1.1.0-emerald.svg)](CHANGELOG.md)

<p align="center">
  <img src="preview_dashboard.png" alt="CachyOS Control Center Cockpit" width="900">
</p>
<p align="center">
  <img src="preview_kernel.png" alt="CachyOS Kernel & Driver Matrix" width="900">
</p>
<p align="center">
  <img src="preview_power.png" alt="Hardware & Power Profiles" width="900">
</p>
<p align="center">
  <img src="preview_maintenance.png" alt="System Maintenance & Mirrors" width="900">
</p>
<p align="center">
  <img src="preview_interfaces.png" alt="Network & Interfaces" width="900">
</p>

A high-performance, modular Terminal User Interface (TUI) dashboard and headless automation suite built specifically for **CachyOS and Arch Linux**.

---

## 🌟 Core Modules & Functional Scope

### 1. 🐧 Kernel & Driver Management
- **Kernel Matrix:** Inspect running, installed, and available CachyOS repository kernel variants (`BORE`, `Clang LTO`, `PREEMPT_RT`, `BMQ`, `LTS`, `Server`, `RC`).
- **Real-Time Badges:** Instant status indicators (`Active Running`, `Installed`, `Available`).
- **GPU Hardware Matrix:** Detects NVIDIA, AMD, and Intel controllers, displaying active drivers, proprietary vs. open-source status, temperatures, wattage, and power states (`nvidia-smi` / sysfs DPM).
- **Safe Kernel Actions:** Install and remove kernel variants unprivileged with Polkit authentication.

### 2. ⚡ Hardware & Power Profiles
- **CPU Scaling Governors:** Real-time frequency monitoring across all cores, with one-click governor switching (`performance`, `schedutil`, `powersave`, `ondemand`, `conservative`).
- **Energy Performance Preferences (EPP):** Switch between `performance`, `balance_performance`, and `power` profiles.
- **Thermal & Throttling Guard:** Continuous multi-zone monitoring (`/sys/class/thermal/`), detecting passive trip points and hardware throttling events without false positives.

### 3. 🧹 System Maintenance & Repository Hygiene
- **Mirror Speed Benchmarking:** Built-in benchmarking utilizing `cachyos-rate-mirrors` or `rate-mirrors` to rank and optimize download mirrors.
- **Cache Trimming:** Reclaims disk space via `paccache -r -k 2` or `pacman -Sc` with live size previews.
- **Orphan Package Removal:** Identifies unneeded dependencies (`pacman -Qtdq`) and cleans them safely (`pacman -Rns`).
- **Pacnew Auditor:** Scans `/etc` for unmerged `.pacnew` configuration files.
- **SSD TRIM & Journal Vacuum:** One-click `fstrim -av` execution and systemd journal trimming to 50MB.
- **Pacman Lock Safety:** Automatic detection of `/var/lib/pacman/db.lck` to prevent database corruptions.

### 4. ⚙️ Systemd Service Control Center
- **Live Daemon Monitoring:** Monitored daemons include `NetworkManager`, `bluetooth`, `tailscaled`, `sshd`, `ananicy-cpp`, `systemd-resolved`, `ufw`/`firewalld`, `docker`, and `syncthing`.
- **Granular Controls:** Start, stop, restart, enable, or disable services via Polkit.

### 5. 🔍 Deep Diagnostics & Boot Auditing
- **Boot Command Line:** Formatted display of active kernel parameters (`/proc/cmdline`).
- **Systemd-Analyze:** Startup latency breakdown (Firmware, Loader, Kernel, Initrd, Userspace).
- **Kernel Log Feed:** Live tail of kernel messages via `journalctl -k` / `dmesg`.
- **Hardware Snapshot:** CPU architecture, motherboard vendor/model, storage devices, and PCI controllers.
- **Network Health Checks:** Default gateway latency, DNS resolution, and HTTP 204 connectivity.

### 6. 🌐 Localization (i18n) & Privilege Isolation
- **Dual Language Support:** Full native German (`de_DE`) and English (`en_US`). Switch dynamically anytime using the `L` key.
- **Strict Privilege Isolation:** The TUI runs unprivileged as a standard user. Root actions are executed via granular Polkit actions (`org.cachyos.controlcenter.policy`).
- **High-Contrast Typography:** Optimized TCSS tabs with crystal-clear active/focused states preventing cursor washout.
- **XDG Base Directory Compliance:** Strictly follows `~/.config/cachyos-control-center/config.toml` and `/etc/cachyos-control-center/config.toml`.

---

## 🏛️ Architecture & Directory Layout

```text
cachyos-control-center/
├── app.py                             # Universal CLI & TUI entry point
├── cachyos_center.py                  # Textual TUI Master Application (7 Unified Tabs)
├── setup.sh                           # Automated setup script
├── run.sh                             # One-click launcher
├── PKGBUILD                           # Production Arch/CachyOS package build script
├── config.example.toml                # Clean XDG configuration template
├── requirements.txt                   # Python dependencies (textual, rich)
├── CHANGELOG.md                       # Release notes (v1.0.1)
│
├── core/                              # Low-level system & business logic
│   ├── i18n.py                        # Dual-language translation engine (DE / EN)
│   ├── config.py                      # XDG compliant configuration loader
│   ├── polkit.py                      # Privilege isolation & pkexec action dispatcher
│   ├── kernel_driver.py               # CachyOS kernel matrix & GPU driver inspector
│   ├── hardware_power.py              # CPU scaling, EPP profiles & thermal throttling
│   ├── maintenance.py                 # Mirror benchmarking, cache & orphan cleaner
│   ├── system.py                      # Hardware telemetry & systemd unit auditor
│   ├── diagnostics.py                 # Boot parameters, kernel logs & JSON audit engine
│   ├── network.py                     # Wireless interfaces & AP scanner
│   └── tailscale.py                   # Tailscale mesh topology & routing
│
├── ui/                                # Modern Textual interface layer
│   ├── theme.py                       # Catppuccin Mocha / CachyOS Emerald stylesheet
│   └── screens/                       # Modular screen components
│       ├── dashboard_view.py          # Cockpit with live telemetry & quick actions
│       ├── kernel_view.py             # Kernel matrix & GPU driver management
│       ├── power_view.py              # CPU governor, EPP & thermal monitoring
│       ├── maint_view.py              # Mirror ranking, cache cleanup & pacnew auditor
│       ├── services_view.py           # Systemd daemon control panel
│       ├── diag_view.py               # Boot cmdline, logs & systemd-analyze
│       ├── wifi_view.py               # Wireless connection inspector
│       └── tailscale_view.py          # WireGuard mesh status
│
├── data/                              # Desktop & Security Assets
│   ├── org.cachyos.controlcenter.policy  # Polkit policy rules
│   ├── cachyos-control-center.desktop    # XDG desktop application entry
│   └── cachyos-control-center.svg        # Scalable vector application icon
│
└── bin/                               # Standalone helper utilities
    ├── net_diagnose.py                # Standalone CLI network diagnostic tool
    └── agy_migrator.py                # Directory synthesizer
```

---

## 💻 CLI & Automation Subcommands

`cachyos-control-center` provides full headless scripting capabilities:

```bash
# 1. Terminal System Overview (CPU, RAM, Kernel, GPUs, Updates)
./app.py --status

# 2. Automated Headless System Hygiene (Trims cache, removes orphans, runs SSD TRIM)
./app.py --clean

# 3. Full Machine-Readable JSON System Audit
./app.py --json

# 4. Fast Network Diagnostics
./app.py --diag quick

# 5. Switch Default Language
./app.py --lang en   # English
./app.py --lang de   # German
```

---

## 📦 Installation

### Option 1: Direct AUR Installation (Arch Linux / CachyOS)

```bash
# Using yay
yay -S cachyos-control-center

# Using paru
paru -S cachyos-control-center

# Or build manually using makepkg
git clone https://github.com/Graba92/cachyos-control-center.git
cd cachyos-control-center
makepkg -si
```

### Option 2: Quick Local Setup

```bash
git clone https://github.com/Graba92/cachyos-control-center.git
cd cachyos-control-center
chmod +x setup.sh run.sh
./setup.sh
./run.sh
```

---

## ⌨️ Keyboard Shortcuts

| Key | Action |
|:---:|:---|
| `1` | **Cockpit:** Telemetry KPIs & Quick Actions |
| `2` | **Kernel & Drivers:** CachyOS Kernel Matrix & GPU Cards |
| `3` | **Hardware & Power:** CPU Governors, EPP Profiles & Thermals |
| `4` | **Maintenance:** Mirror Benchmarking, Cache Cleaning & Orphans |
| `5` | **Services:** Systemd Service Manager |
| `6` | **Diagnostics:** Boot Parameters, Kernel Logs & Hardware Snapshot |
| `7` | **Network:** Wireless & Tailscale Mesh |
| `L` | **Language Toggle:** Dynamically switch between English and German |
| `R` | **Refresh:** Manually trigger active panel telemetry update |
| `Q` | **Quit:** Exit Control Center |

---

## 📄 License

Distributed under the **MIT License**. See [LICENSE](LICENSE) for details.  
Maintained by **Matthias Haase (@Graba92)**.
