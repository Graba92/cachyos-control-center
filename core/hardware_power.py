#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
 CachyOS Control Center — Hardware & Power Profiles Engine
 Steuerung von CPU-Governors, EPP-Präferenzen, GPU-Powerstates & Thermal-Monitoring
===============================================================================
"""

from __future__ import annotations

import glob
import os
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .polkit import polkit_set_cpu_governor, polkit_set_epp_preference


@dataclass
class CPUGovernorInfo:
    current_governor: str
    available_governors: List[str]
    current_epp: Optional[str] = None
    available_epp: List[str] = field(default_factory=list)
    driver: str = ""
    min_freq_mhz: float = 0.0
    max_freq_mhz: float = 0.0
    current_freqs_mhz: List[float] = field(default_factory=list)


@dataclass
class ThermalZoneInfo:
    zone_id: str
    zone_type: str
    temperature_c: float
    trip_points: List[Tuple[str, float]] = field(default_factory=list)
    is_throttling: bool = False


@dataclass
class PowerProfileStatus:
    cpu: CPUGovernorInfo
    thermals: List[ThermalZoneInfo]
    is_throttled: bool
    throttle_message: str


def get_cpu_governor_info() -> CPUGovernorInfo:
    """Ermittelt den aktuellen CPU-Governor, EPP und Frequenzen aller Kerne."""
    base_cpu = Path("/sys/devices/system/cpu/cpu0/cpufreq")
    curr_gov = "unknown"
    avail_govs: List[str] = []
    curr_epp: Optional[str] = None
    avail_epp: List[str] = []
    driver = "generic"
    min_freq = 0.0
    max_freq = 0.0

    if base_cpu.exists():
        gov_file = base_cpu / "scaling_governor"
        if gov_file.exists():
            curr_gov = gov_file.read_text(encoding="utf-8").strip()

        avail_file = base_cpu / "scaling_available_governors"
        if avail_file.exists():
            avail_govs = avail_file.read_text(encoding="utf-8").strip().split()

        driver_file = base_cpu / "scaling_driver"
        if driver_file.exists():
            driver = driver_file.read_text(encoding="utf-8").strip()

        epp_file = base_cpu / "energy_performance_preference"
        if epp_file.exists():
            curr_epp = epp_file.read_text(encoding="utf-8").strip()

        avail_epp_file = base_cpu / "energy_performance_available_preferences"
        if avail_epp_file.exists():
            avail_epp = avail_epp_file.read_text(encoding="utf-8").strip().split()

        min_file = base_cpu / "scaling_min_freq"
        if min_file.exists():
            try:
                min_freq = round(int(min_file.read_text(encoding="utf-8").strip()) / 1000.0, 1)
            except Exception:
                pass

        max_file = base_cpu / "scaling_max_freq"
        if max_file.exists():
            try:
                max_freq = round(int(max_file.read_text(encoding="utf-8").strip()) / 1000.0, 1)
            except Exception:
                pass

    # Frequenzen aller Cores erfassen
    core_freqs: List[float] = []
    freq_files = sorted(glob.glob("/sys/devices/system/cpu/cpu*/cpufreq/scaling_cur_freq"))
    for ff in freq_files:
        try:
            val = int(Path(ff).read_text(encoding="utf-8").strip())
            core_freqs.append(round(val / 1000.0, 1))
        except Exception:
            pass

    return CPUGovernorInfo(
        current_governor=curr_gov,
        available_governors=avail_govs,
        current_epp=curr_epp,
        available_epp=avail_epp,
        driver=driver,
        min_freq_mhz=min_freq,
        max_freq_mhz=max_freq,
        current_freqs_mhz=core_freqs,
    )


def get_thermal_status() -> Tuple[List[ThermalZoneInfo], bool, str]:
    """Liest alle System Thermal-Zonen und prüft auf aktive Drosselung."""
    zones: List[ThermalZoneInfo] = []
    is_throttled = False
    throttle_msg = "Normalbetrieb (Keine Drosselung)"

    thermal_dirs = sorted(glob.glob("/sys/class/thermal/thermal_zone*"))
    for td in thermal_dirs:
        p = Path(td)
        zone_id = p.name
        type_file = p / "type"
        temp_file = p / "temp"

        z_type = type_file.read_text(encoding="utf-8").strip() if type_file.exists() else "generic"
        temp_c = 0.0
        if temp_file.exists():
            try:
                raw_temp = int(temp_file.read_text(encoding="utf-8").strip())
                temp_c = round(raw_temp / 1000.0, 1)
            except Exception:
                pass

        # Trip-Points ermitteln falls vorhanden
        trips: List[Tuple[str, float]] = []
        for trip_temp_file in glob.glob(str(p / "trip_point_*_temp")):
            try:
                idx = trip_temp_file.split("_")[-2]
                type_f = p / f"trip_point_{idx}_type"
                t_type = type_f.read_text(encoding="utf-8").strip() if type_f.exists() else "trip"
                t_temp = round(int(Path(trip_temp_file).read_text(encoding="utf-8").strip()) / 1000.0, 1)
                trips.append((t_type, t_temp))
                if t_type == "passive" and t_temp > 40.0 and temp_c >= t_temp:
                    is_throttled = True
                    throttle_msg = f"Thermisches Limit bei Zone {zone_id} ({z_type}) erreicht: {temp_c}°C >= {t_temp}°C"
            except Exception:
                pass

        if temp_c > 88.0:
            is_throttled = True
            throttle_msg = f"Kritische CPU/Package-Temperatur: {temp_c}°C!"

        zones.append(
            ThermalZoneInfo(
                zone_id=zone_id,
                zone_type=z_type,
                temperature_c=temp_c,
                trip_points=trips,
                is_throttling=is_throttled,
            )
        )

    # CPU-Thermal Throttle sysfs prüfen
    for th_file in glob.glob("/sys/devices/system/cpu/cpu*/thermal_throttle/*"):
        try:
            val = Path(th_file).read_text(encoding="utf-8").strip()
            if val.isdigit() and int(val) > 0:
                is_throttled = True
                throttle_msg = f"CPU Thermal Throttle Event erkannt: {Path(th_file).name} = {val}"
                break
        except Exception:
            pass

    return zones, is_throttled, throttle_msg


def get_complete_power_profile() -> PowerProfileStatus:
    """Erfasst den gesamten Power- und Hardwarezustand."""
    cpu_info = get_cpu_governor_info()
    zones, is_throttled, msg = get_thermal_status()
    return PowerProfileStatus(
        cpu=cpu_info,
        thermals=zones,
        is_throttled=is_throttled,
        throttle_message=msg,
    )


def apply_governor(governor: str) -> Tuple[bool, str]:
    """Wendet einen neuen CPU Governor an."""
    return polkit_set_cpu_governor(governor)


def apply_epp(preference: str) -> Tuple[bool, str]:
    """Wendet ein neues EPP Profil an."""
    return polkit_set_epp_preference(preference)
