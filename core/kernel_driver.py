#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
 CachyOS Control Center — Kernel & Driver Management Engine
 Ermittelt installierte und verfügbare CachyOS-Kernelvarianten (BORE, LTO, RT, BMQ),
 GPU-Treiberschnittstellen (NVIDIA, AMD, Intel) & Statusindikatoren
===============================================================================
"""

from __future__ import annotations

import os
import platform
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from .i18n import t
from .polkit import run_polkit_cmd


@dataclass
class KernelInfo:
    package_name: str
    variant_name: str
    version: str
    is_installed: bool
    is_running: bool
    description: str


@dataclass
class GPUDeviceInfo:
    device_name: str
    vendor: str  # NVIDIA, AMD, Intel, Other
    active_driver: str
    driver_version: str
    is_proprietary: bool
    temperature_c: Optional[float] = None
    power_draw_w: Optional[float] = None
    power_state: Optional[str] = None
    vulkan_installed: bool = False


# Bekannte CachyOS Kernel-Profile und Beschreibungen
KNOWN_KERNEL_PROFILES = {
    "linux-cachyos": ("Standard (BORE)", "CachyOS Standardkernel mit BORE CPU-Scheduler & sched-ext"),
    "linux-cachyos-bore": ("BORE Scheduler", "Burst-Oriented Response Enhancer für minimalste Latenzen"),
    "linux-cachyos-lto": ("Clang LTO", "Kompiliert mit LLVM/Clang & Thin-LTO Optimierungen"),
    "linux-cachyos-rt": ("Realtime (RT)", "PREEMPT_RT Kernel für ultra-präzise Audio- & Industrie-Workloads"),
    "linux-cachyos-bmq": ("BMQ Scheduler", "BitMap Queue Scheduler von Alfred Chen"),
    "linux-cachyos-lts": ("Long Term (LTS)", "Langzeitunterstützter CachyOS Kernel mit Stabilitätsfokus"),
    "linux-cachyos-server": ("Server Edition", "Optimiert für hohe Durchsatzraten & Server-Workloads"),
    "linux-cachyos-rc": ("Release Candidate", "Neueste Entwicklungsversionen direkt von Linus Torvalds"),
    "linux-cachyos-hardened": ("Hardened", "Erhöhte Sicherheitsflags und Kernel Self-Protection"),
}


def get_running_kernel() -> str:
    """Gibt das aktuelle Kernel-Release zurück (z.B. 6.18.50-3-cachyos-lts)."""
    return platform.release()


def list_cachyos_kernels() -> Tuple[List[KernelInfo], List[KernelInfo]]:
    """
    Ermittelt alle installierten und verfügbaren CachyOS Kernel.
    Rückgabe: (installierte_kernel, verfuegbare_kernel)
    """
    running = get_running_kernel()

    # 1. Installierte Pakete via pacman -Q
    installed_pkgs: Dict[str, str] = {}
    try:
        res = subprocess.run(["pacman", "-Q"], capture_output=True, text=True, timeout=10)
        if res.returncode == 0:
            for line in res.stdout.splitlines():
                parts = line.split()
                if len(parts) == 2:
                    installed_pkgs[parts[0]] = parts[1]
    except Exception:
        pass

    # 2. Verfügbare Pakete im cachyos Repo via pacman -Sl cachyos
    available_cachyos_pkgs: Dict[str, str] = {}
    try:
        res2 = subprocess.run(["pacman", "-Sl", "cachyos"], capture_output=True, text=True, timeout=10)
        if res2.returncode == 0:
            for line in res2.stdout.splitlines():
                parts = line.split()
                if len(parts) >= 3:
                    pkg = parts[1]
                    ver = parts[2]
                    # Nur Basis-Kernelpakete, keine Header, zfs oder nvidia module
                    if pkg.startswith("linux-cachyos") and not any(
                        pkg.endswith(sfx) for sfx in ["-headers", "-zfs", "-nvidia", "-nvidia-open", "-r8125", "-dbg"]
                    ):
                        available_cachyos_pkgs[pkg] = ver
    except Exception:
        pass

    installed_list: List[KernelInfo] = []
    available_list: List[KernelInfo] = []

    # Basis Kernel aufnehmen (auch Standard Arch linux falls installiert)
    all_kernel_keys = set(list(KNOWN_KERNEL_PROFILES.keys()) + list(available_cachyos_pkgs.keys()))
    if "linux" in installed_pkgs:
        all_kernel_keys.add("linux")
    if "linux-lts" in installed_pkgs:
        all_kernel_keys.add("linux-lts")
    if "linux-zen" in installed_pkgs:
        all_kernel_keys.add("linux-zen")

    for pkg_name in sorted(all_kernel_keys):
        is_inst = pkg_name in installed_pkgs
        version = installed_pkgs.get(pkg_name, available_cachyos_pkgs.get(pkg_name, "N/A"))

        # Prüfen ob dieser Kernel aktuell läuft
        # z.B. running ist 6.18.50-3-cachyos-lts und pkg_name ist linux-cachyos-lts
        is_run = False
        kernel_short = pkg_name.replace("linux-", "")
        if kernel_short in running or (pkg_name == "linux" and "arch" in running):
            is_run = True

        name, desc = KNOWN_KERNEL_PROFILES.get(
            pkg_name,
            (pkg_name.replace("linux-", "").upper(), f"CachyOS Kernelvariante {pkg_name}"),
        )

        k_info = KernelInfo(
            package_name=pkg_name,
            variant_name=name,
            version=version,
            is_installed=is_inst,
            is_running=is_run,
            description=desc,
        )

        if is_inst:
            installed_list.append(k_info)
        elif pkg_name in available_cachyos_pkgs:
            available_list.append(k_info)

    # Sortierung: Laufender Kernel ganz oben bei installierten
    installed_list.sort(key=lambda k: (not k.is_running, k.package_name))
    return installed_list, available_list


def detect_gpu_devices() -> List[GPUDeviceInfo]:
    """Erkennt alle Grafikkarten, aktive Treiber (Open vs. Proprietär) & Live-Metriken."""
    gpus: List[GPUDeviceInfo] = []

    # 1. PCI Controller scannen via lspci
    try:
        res = subprocess.run(["lspci", "-nnk"], capture_output=True, text=True, timeout=10)
        pci_output = res.stdout
    except Exception:
        pci_output = ""

    # Pakete prüfen für Vulkan
    has_vulkan = shutil.which("vulkaninfo") is not None

    current_gpu_lines: List[str] = []
    is_vga = False

    def _parse_block(block: List[str]) -> Optional[GPUDeviceInfo]:
        if not block:
            return None
        header = block[0]
        name = header.split(":", 2)[-1].strip() if ":" in header else header
        vendor = "Other"
        active_driver = "Unbekannt"
        is_prop = False

        if "NVIDIA" in header.upper():
            vendor = "NVIDIA"
        elif "AMD" in header.upper() or "ADVANCED MICRO" in header.upper() or "ATI" in header.upper():
            vendor = "AMD"
        elif "INTEL" in header.upper():
            vendor = "Intel"

        for l in block[1:]:
            l_strip = l.strip()
            if l_strip.startswith("Kernel driver in use:"):
                active_driver = l_strip.split(":", 1)[1].strip()

        if active_driver == "nvidia":
            is_prop = True
        elif active_driver in ["nouveau", "amdgpu", "radeon", "i915", "xe"]:
            is_prop = False

        driver_ver = "N/A"
        temp_c: Optional[float] = None
        power_w: Optional[float] = None
        p_state: Optional[str] = None

        # NVIDIA SMI Telemetrie abfragen falls NVIDIA
        if vendor == "NVIDIA" and shutil.which("nvidia-smi"):
            try:
                smi_res = subprocess.run(
                    ["nvidia-smi", "--query-gpu=driver_version,temperature.gpu,power.draw,pstate", "--format=csv,noheader"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if smi_res.returncode == 0 and smi_res.stdout.strip():
                    parts = [p.strip() for p in smi_res.stdout.strip().split(",")]
                    if len(parts) >= 4:
                        driver_ver = parts[0]
                        try:
                            temp_c = float(parts[1])
                        except Exception:
                            pass
                        try:
                            power_w = float(parts[2].replace("W", "").strip())
                        except Exception:
                            pass
                        p_state = parts[3]
            except Exception:
                pass

        # AMD Telemetrie via sysfs
        if vendor == "AMD":
            try:
                hwmon_paths = list(os.scandir("/sys/class/drm"))
                for entry in hwmon_paths:
                    if entry.name.startswith("card") and not "-" in entry.name:
                        dpm_file = os.path.join(entry.path, "device", "power_dpm_force_performance_level")
                        if os.path.exists(dpm_file):
                            with open(dpm_file) as f:
                                p_state = f.read().strip()
            except Exception:
                pass

        return GPUDeviceInfo(
            device_name=name,
            vendor=vendor,
            active_driver=active_driver,
            driver_version=driver_ver,
            is_proprietary=is_prop,
            temperature_c=temp_c,
            power_draw_w=power_w,
            power_state=p_state,
            vulkan_installed=has_vulkan,
        )

    for line in pci_output.splitlines():
        if re.search(r"(VGA compatible controller|3D controller|Display controller)", line, re.IGNORECASE):
            if current_gpu_lines:
                parsed = _parse_block(current_gpu_lines)
                if parsed:
                    gpus.append(parsed)
                current_gpu_lines = []
            is_vga = True
            current_gpu_lines.append(line)
        elif is_vga:
            if line.startswith("\t") or line.startswith(" "):
                current_gpu_lines.append(line)
            else:
                is_vga = False
                parsed = _parse_block(current_gpu_lines)
                if parsed:
                    gpus.append(parsed)
                current_gpu_lines = []

    if current_gpu_lines:
        parsed = _parse_block(current_gpu_lines)
        if parsed:
            gpus.append(parsed)

    return gpus


def install_kernel(package_name: str) -> Tuple[bool, str]:
    """Installiert einen CachyOS-Kernel via Polkit."""
    clean_pkg = package_name.strip()
    if not clean_pkg.startswith("linux-cachyos") and clean_pkg not in ["linux", "linux-lts", "linux-zen"]:
        return False, f"Ungültiges Kernelpaket: {package_name}"
    cmd = f"pacman -S --noconfirm {clean_pkg} {clean_pkg}-headers"
    ok, msg, _ = run_polkit_cmd(cmd, timeout=180, check_pacman_lock=True)
    return ok, msg


def remove_kernel(package_name: str) -> Tuple[bool, str]:
    """Deinstalliert einen Kernel via Polkit (verhindert das Löschen des laufenden Kernels)."""
    running = get_running_kernel()
    if package_name.replace("linux-", "") in running:
        return False, "Sicherheitsabbruch: Der aktuell laufende Kernel kann nicht deinstalliert werden!"
    clean_pkg = package_name.strip()
    cmd = f"pacman -Rns --noconfirm {clean_pkg}"
    ok, msg, _ = run_polkit_cmd(cmd, timeout=120, check_pacman_lock=True)
    return ok, msg
