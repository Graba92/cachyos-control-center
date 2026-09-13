"""
CachyOS Control Center — Screens Package
"""

from .dashboard_view import DashboardView
from .wifi_view import WifiView
from .tailscale_view import TailscaleView
from .diag_view import DiagView
from .maint_view import MaintView
from .rice_view import RiceView
from .migrator_view import MigratorView

__all__ = [
    "DashboardView",
    "WifiView",
    "TailscaleView",
    "DiagView",
    "MaintView",
    "RiceView",
    "MigratorView",
]
