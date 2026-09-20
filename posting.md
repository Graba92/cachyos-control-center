# 🚀 CachyOS Control Center — The Ultimate Linux System Administrator & Hardware Cockpit

**CachyOS Control Center** ist das fortschrittlichste, native All-in-One Administrations- und Tuning-Cockpit für CachyOS und Arch Linux. Es verbindet ein reaktionsschnelles Terminal-Cockpit (Textual TUI) mit einer blitzschnellen Headless-CLI, tiefgreifender Hardware-Telemetrie und Kernel-/Treiberverwaltung.

---

### 🌟 Highlights & Features
- **🌐 Dual-Language Support (DE & EN):** Nahtloses Umschalten der Benutzeroberfläche zur Laufzeit (Taste `L` oder `--lang de|en`).
- **⚡ Echtzeit-Telemetrie:** CPU-, GPU-, RAM- und NVMe/BTRFS-Metriken im Sekundentakt ohne spürbaren Overhead.
- **🐧 Kernel- & Treibermatrix:** Erkennung und Verwaltung von CachyOS-Kerneln (BORE, LTO, RT, BMQ) und NVIDIA-/AMD-Grafiktreibern.
- **🔋 Power & Governor Management:** Live-Umschaltung von CPU-Governors (Performance, Schedutil, Powersave) und EPP-Profilen.
- **🧹 1-Klick Systemhygiene:** Sichere Bereinigung von Pacman-Caches, Entfernung verwaister Pakete und Ausführung von SSD-TRIM.
- **🩺 Tiefendiagnose:** Boot-Performance-Analyse via `systemd-analyze`, dmesg-Feed und D-Bus-Dienstesteuerung.

---

### 🚀 Schnellstart

```bash
# Repository klonen & starten
git clone https://github.com/Graba92/cachyos-control-center.git
cd cachyos-control-center
./setup.sh
./run.sh

# Headless CLI-Übersicht (Deutsch oder Englisch)
cachyos-control-center --status
cachyos-control-center --lang en --status

# Headless Systemhygiene ausführen
cachyos-control-center --clean
```

---
*Entwickelt von Matthias Haase (xxgrabaxx) für die CachyOS & Arch Linux Community.*
