#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
 CachyOS Control Center — UI Screens Package
 Exportiert alle modularen Textual-Views und Cockpits
===============================================================================
"""

from .dashboard_view import DashboardView
from .kernel_view import KernelView
from .power_view import PowerView
from .maint_view import MaintView
from .services_view import ServicesView
from .diag_view import DiagView
from .wifi_view import WifiView
from .tailscale_view import TailscaleView
from .rice_view import RiceView
from .migrator_view import MigratorView

__all__ = [
    "DashboardView",
    "KernelView",
    "PowerView",
    "MaintView",
    "ServicesView",
    "DiagView",
    "WifiView",
    "TailscaleView",
    "RiceView",
    "MigratorView",
]
