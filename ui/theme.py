#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
 CachyOS Control Center — Professional TCSS Theme (Edition 10/10)
 Scharfe Kanten, optimale Kontraste, btop/Nordic/Catppuccin-Ästhetik
===============================================================================
"""

APP_TCSS = """
/* ── Grundlayout & Basisfarben (Catppuccin Mocha Dark) ────────────────────── */
Screen {
    background: #11111b;
    color: #cdd6f4;
    layout: vertical;
}

Header {
    background: #181825;
    color: #89b4fa;
    text-style: bold;
    border-bottom: solid #313244;
}

Footer {
    background: #181825;
    color: #a6adc8;
    border-top: solid #313244;
}

/* ── System-Status-Ribbon (Oben) ─────────────────────────────────────────── */
#sys_ribbon {
    height: 3;
    background: #181825;
    border-bottom: solid #313244;
    padding: 0 1;
    layout: horizontal;
    align-vertical: middle;
}

.ribbon-item {
    margin-right: 2;
    color: #cdd6f4;
    text-style: bold;
}

.ribbon-sep {
    color: #45475a;
    margin-right: 2;
}

/* ── Tabbed Navigation (Volle Breite) ─────────────────────────────────────── */
TabbedContent {
    height: 1fr;
    background: #11111b;
}

Tabs {
    background: #181825;
    border-bottom: solid #313244;
    height: 3;
}

Tab {
    background: #181825;
    color: #a6adc8;
    padding: 0 2;
    text-style: bold;
}

Tab:hover {
    color: #cdd6f4;
    background: #1e1e2e;
}

Tab.-active {
    background: #1e1e2e;
    color: #89b4fa;
    text-style: bold;
    border-bottom: wide #89b4fa;
}

TabPane {
    padding: 1;
    height: 1fr;
    background: #11111b;
    overflow-y: auto;
}

/* ── Struktur-Panels & Karten (Deutliche visuelle Abhebung) ───────────────── */
.panel {
    border: round #45475a;
    background: #181825;
    padding: 1;
    margin-bottom: 1;
}

.panel:focus-within {
    border: round #89b4fa;
}

.cards-row {
    height: 5;
    margin-bottom: 1;
    layout: horizontal;
}

.kpi-card {
    width: 1fr;
    height: 100%;
    border: round #45475a;
    background: #181825;
    padding: 0 1;
    margin-right: 1;
}

.kpi-card:last-child {
    margin-right: 0;
}

.kpi-card:focus-within {
    border: round #89b4fa;
}

.kpi-title {
    color: #89b4fa;
    text-style: bold;
    text-align: center;
}

.kpi-value {
    color: #cdd6f4;
    text-style: bold;
    text-align: center;
    margin-top: 1;
}

.kpi-sub {
    color: #6c7086;
    text-align: center;
}

/* ── Split Layouts ────────────────────────────────────────────────────────── */
.split-h {
    height: 1fr;
    layout: horizontal;
}

.split-v {
    height: 1fr;
    layout: vertical;
}

.col-left {
    width: 50%;
    height: 100%;
    padding-right: 1;
    overflow-y: auto;
}

.col-right {
    width: 50%;
    height: 100%;
    padding-left: 1;
    overflow-y: auto;
}

.col-half {
    width: 50%;
    height: 100%;
    padding: 0 1;
    overflow-y: auto;
}

.pane-top {
    height: 55%;
    width: 100%;
    margin-bottom: 1;
}

.pane-bottom {
    height: 45%;
    width: 100%;
}

/* ── DataTables mit runder Umrandung & abgesetzten Bereichen ─────────────── */
DataTable {
    height: 1fr;
    background: #11111b;
    border: round #45475a;
}

DataTable:focus {
    border: round #89b4fa;
}

DataTable > .datatable--header {
    background: #181825;
    color: #89b4fa;
    text-style: bold;
    border-bottom: solid #45475a;
}

DataTable > .datatable--cursor {
    background: #313244;
    color: #ffffff;
    text-style: bold;
}

/* ── Toolbar & Buttons ───────────────────────────────────────────────────── */
.toolbar {
    height: 3;
    layout: horizontal;
    margin: 0;
    align-vertical: middle;
}

Button {
    height: 3;
    min-width: 15;
    padding: 0 1;
    margin-right: 1;
    border: round #45475a;
    background: #181825;
    color: #cdd6f4;
    text-style: bold;
}

Button:hover {
    background: #313244;
    color: #89b4fa;
    border: round #89b4fa;
}

Button:focus {
    border: round #89b4fa;
    text-style: bold;
}

Button.-primary {
    background: #1e3a5f;
    color: #89b4fa;
    border: round #89b4fa;
}

Button.-primary:hover {
    background: #2b5282;
    color: #ffffff;
    border: round #b4befe;
}

Button.-success {
    background: #1e4a38;
    color: #a6e3a1;
    border: round #a6e3a1;
}

Button.-success:hover {
    background: #2d6b52;
    color: #ffffff;
    border: round #a6e3a1;
}

Button.-warning {
    background: #4a3e1e;
    color: #f9e2af;
    border: round #f9e2af;
}

Button.-warning:hover {
    background: #6e5c2d;
    color: #ffffff;
    border: round #f9e2af;
}

Button.-error {
    background: #4a1e28;
    color: #f38ba8;
    border: round #f38ba8;
}

Button.-error:hover {
    background: #6e2d3c;
    color: #ffffff;
    border: round #f38ba8;
}

Button.-default {
    background: #181825;
    color: #cdd6f4;
    border: round #45475a;
}

Button.-default:hover {
    background: #313244;
    color: #89b4fa;
    border: round #89b4fa;
}

Input {
    height: 3;
    border: round #45475a;
    background: #181825;
    color: #cdd6f4;
    padding: 0 1;
}

Input:focus {
    border: round #89b4fa;
}

/* ── Info-Boxen & Markdown (Schön abgehobene Container) ───────────────────── */
.info-box {
    border: round #45475a;
    background: #181825;
    padding: 0 1;
    height: auto;
    margin-bottom: 1;
}

.info-box:focus-within {
    border: round #89b4fa;
}

MarkdownViewer {
    height: 1fr;
    border: round #45475a;
    background: #11111b;
    padding: 1;
}

MarkdownViewer:focus {
    border: round #89b4fa;
}

/* ── Text-Hierarchie & Bezeichnungen ─────────────────────────────────────── */
.title {
    color: #89b4fa;
    text-style: bold;
    margin-bottom: 1;
}

.section-label {
    color: #f9e2af;
    text-style: bold;
    margin-bottom: 1;
}
"""
