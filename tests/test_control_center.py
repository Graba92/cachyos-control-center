#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unit-Tests für CachyOS Control Center
Validiert i18n Lokalisierung, Telemetrie, Systemfunktionen und Konfiguration.
"""

import os
import sys
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from core.i18n import t, set_language, get_language, toggle_language
from core.config import load_config, get_config_file_path
from core.system import get_system_telemetry
from core.kernel_driver import get_running_kernel


class TestCachyOSControlCenter(unittest.TestCase):

    def setUp(self):
        set_language("de")

    def tearDown(self):
        set_language("de")

    def test_i18n_translation(self):
        set_language("de")
        self.assertEqual(get_language(), "de")
        self.assertIn("Cockpit", t("tab_cockpit"))
        self.assertEqual(t("btn_quit"), "Beenden")

        set_language("en")
        self.assertEqual(get_language(), "en")
        self.assertIn("Cockpit", t("tab_cockpit"))
        self.assertEqual(t("btn_quit"), "Quit")

    def test_i18n_toggle(self):
        set_language("de")
        new_lang = toggle_language()
        self.assertEqual(new_lang, "en")
        self.assertEqual(get_language(), "en")
        new_lang = toggle_language()
        self.assertEqual(new_lang, "de")
        self.assertEqual(get_language(), "de")

    def test_i18n_formatting(self):
        set_language("de")
        self.assertEqual(t("kpi_cores", cores=8), "8 Kerne")
        set_language("en")
        self.assertEqual(t("kpi_cores", cores=8), "8 Cores")

    def test_system_telemetry(self):
        telem = get_system_telemetry()
        self.assertIsNotNone(telem.hostname)
        self.assertGreater(telem.cpu_cores, 0)
        self.assertGreater(telem.ram_total_gb, 0)

    def test_running_kernel(self):
        k = get_running_kernel()
        self.assertTrue(len(k) > 0)

    def test_config_loader(self):
        cfg = load_config()
        self.assertIsInstance(cfg, dict)
        self.assertIn("general", cfg)

    def test_maintenance_timers(self):
        from core.maintenance import get_maintenance_timers, MaintenanceTimer
        timers = get_maintenance_timers()
        self.assertIsInstance(timers, list)
        self.assertTrue(len(timers) >= 2)
        timer_names = [t.name for t in timers]
        self.assertIn("fstrim.timer", timer_names)
        self.assertIn("paccache.timer", timer_names)

    def test_safe_run_cmd(self):
        from core.system import run_cmd
        out, err, code = run_cmd(["echo", "safe_token_test"])
        self.assertEqual(code, 0)
        self.assertEqual(out.strip(), "safe_token_test")

    def test_check_available_updates_defensive(self):
        from core.maintenance import check_available_updates
        count, msg = check_available_updates(timeout=5)
        self.assertIsInstance(count, int)
        self.assertIsInstance(msg, str)
        self.assertTrue(len(msg) > 0)


if __name__ == "__main__":
    unittest.main()


