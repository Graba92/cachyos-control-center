"""
CachyOS Control Center — Core Engine Package
Professional low-level system, network, VPN and maintenance modules.
"""

from .system import (
    run_cmd,
    get_system_telemetry,
    get_services_status,
    SystemTelemetry,
    ServiceStatus,
)
from .network import (
    get_network_interfaces,
    scan_wifi_networks,
    set_interface_mode,
    kill_wifi_conflicts,
    restart_network_stack,
    NetworkInterface,
    WifiAccessPoint,
)
from .tailscale import (
    get_tailscale_status,
    toggle_tailscale,
    set_exit_node,
    ping_tailscale_peer,
    TailscaleNode,
    TailscaleMeshStatus,
)
from .diagnostics import (
    run_diagnostic_profile,
    DiagnosticResult,
    DiagnosticItem,
)
from .maintenance import (
    clean_pacman_cache,
    vacuum_journal,
    find_pacnew_files,
    reset_failed_units,
    run_fstrim,
    check_available_updates,
)
from .ricing import (
    inspect_desktop_environment,
    get_fastfetch_output,
    RICE_KNOWLEDGE_BASE,
    DesktopInspectorResult,
)

__all__ = [
    "run_cmd",
    "get_system_telemetry",
    "get_services_status",
    "SystemTelemetry",
    "ServiceStatus",
    "get_network_interfaces",
    "scan_wifi_networks",
    "set_interface_mode",
    "kill_wifi_conflicts",
    "restart_network_stack",
    "NetworkInterface",
    "WifiAccessPoint",
    "get_tailscale_status",
    "toggle_tailscale",
    "set_exit_node",
    "ping_tailscale_peer",
    "TailscaleNode",
    "TailscaleMeshStatus",
    "run_diagnostic_profile",
    "DiagnosticResult",
    "DiagnosticItem",
    "clean_pacman_cache",
    "vacuum_journal",
    "find_pacnew_files",
    "reset_failed_units",
    "run_fstrim",
    "check_available_updates",
    "inspect_desktop_environment",
    "get_fastfetch_output",
    "RICE_KNOWLEDGE_BASE",
    "DesktopInspectorResult",
]
