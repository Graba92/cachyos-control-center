#!/usr/bin/env bash
# ==============================================================================
# CachyOS Control Center — Production Setup & Dependency Installer
# Bulletproof Bash Engineer Architecture (Arch Linux / CachyOS / Generic Linux)
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="$SCRIPT_DIR/setup.log"

# Dual logging setup
exec > >(tee -a "$LOG_FILE") 2>&1

cleanup() {
    local exit_code=$?
    if [ $exit_code -ne 0 ]; then
        echo -e "\n\033[1;31m[!] Setup wurde mit Fehlercode $exit_code abgebrochen.\033[0m"
        echo -e "Details findest du im Log: $LOG_FILE"
    fi
}
trap cleanup EXIT ERR

# Farben
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m'

echo -e "${CYAN}${BOLD}====================================================================${NC}"
echo -e "${CYAN}${BOLD}   ⚡ CachyOS Control Center & System Architect — Setup             ${NC}"
echo -e "${CYAN}${BOLD}====================================================================${NC}"
echo -e "Startzeit: $(date '+%Y-%m-%d %H:%M:%S')\n"

# 1. Pre-Flight Checks
echo -e "${CYAN}[1/4] Pre-Flight Checks...${NC}"
if ! command -v python3 &>/dev/null; then
    echo -e "${RED}[FEHLER] Python 3 wurde nicht gefunden. Bitte installiere Python 3.${NC}" >&2
    exit 1
fi
PYTHON_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo -e "${GREEN}[✓] Python 3 gefunden (Version $PYTHON_VER)${NC}"

# 2. Abhängigkeiten auflösen (Arch Linux / CachyOS nativ vs. venv)
echo -e "\n${CYAN}[2/4] Abhängigkeiten prüfen & installieren...${NC}"

HAS_TEXTUAL=false
HAS_RICH=false

python3 -c "import textual" &>/dev/null && HAS_TEXTUAL=true || true
python3 -c "import rich" &>/dev/null && HAS_RICH=true || true

if [ "$HAS_TEXTUAL" = true ] && [ "$HAS_RICH" = true ]; then
    echo -e "${GREEN}[✓] Alle erforderlichen Python-Module (textual, rich) sind bereits vorhanden.${NC}"
else
    echo -e "${YELLOW}[i] Fehlende Module erkannt. Suche nach Installationsoptionen...${NC}"
    
    if command -v pacman &>/dev/null; then
        echo -e "${CYAN}[+] Arch Linux / CachyOS erkannt. Installiere Systempakete via pacman...${NC}"
        PKGS_TO_INSTALL=()
        [ "$HAS_TEXTUAL" = false ] && PKGS_TO_INSTALL+=("python-textual")
        [ "$HAS_RICH" = false ] && PKGS_TO_INSTALL+=("python-rich")
        
        echo -e "Führe aus: sudo pacman -S --needed --noconfirm ${PKGS_TO_INSTALL[*]}"
        if sudo pacman -S --needed --noconfirm "${PKGS_TO_INSTALL[@]}"; then
            echo -e "${GREEN}[✓] Systempakete erfolgreich via pacman installiert.${NC}"
        else
            echo -e "${YELLOW}[!] pacman fehlgeschlagen oder keine Root-Rechte. Richte lokales venv ein...${NC}"
            python3 -m venv "$SCRIPT_DIR/.venv"
            "$SCRIPT_DIR/.venv/bin/pip" install --upgrade pip
            "$SCRIPT_DIR/.venv/bin/pip" install -r "$SCRIPT_DIR/requirements.txt"
            echo -e "${GREEN}[✓] Lokales venv unter .venv eingerichtet.${NC}"
        fi
    else
        echo -e "${CYAN}[+] Richte isolierte virtuelle Umgebung (.venv) ein...${NC}"
        python3 -m venv "$SCRIPT_DIR/.venv"
        "$SCRIPT_DIR/.venv/bin/pip" install --upgrade pip
        "$SCRIPT_DIR/.venv/bin/pip" install -r "$SCRIPT_DIR/requirements.txt"
        echo -e "${GREEN}[✓] Virtuelle Umgebung erfolgreich erstellt & Pakete installiert.${NC}"
    fi
fi

# 3. Berechtigungen setzen
echo -e "\n${CYAN}[3/5] Dateiberechtigungen setzen...${NC}"
chmod +x "$SCRIPT_DIR/app.py" "$SCRIPT_DIR/cachyos_center.py"
[ -f "$SCRIPT_DIR/run.sh" ] && chmod +x "$SCRIPT_DIR/run.sh"
[ -d "$SCRIPT_DIR/bin" ] && chmod +x "$SCRIPT_DIR"/bin/*.py 2>/dev/null || true
echo -e "${GREEN}[✓] Alle Skripte sind nun ausführbar.${NC}"

# 4. System- & Desktop-Integration
echo -e "\n${CYAN}[4/5] Desktop- & CLI-Integration einrichten...${NC}"
mkdir -p "$HOME/.local/bin" "$HOME/.local/share/applications" "$HOME/.local/share/icons/hicolor/scalable/apps"

# CLI Symlink
ln -sf "$SCRIPT_DIR/run.sh" "$HOME/.local/bin/cachyos-control-center"
echo -e "${GREEN}[✓] CLI-Befehl 'cachyos-control-center' in ~/.local/bin/ registriert.${NC}"

# Desktop Entry & Icon
if [ -f "$SCRIPT_DIR/data/cachyos-control-center.desktop" ]; then
    cp -f "$SCRIPT_DIR/data/cachyos-control-center.desktop" "$HOME/.local/share/applications/cachyos-control-center.desktop"
    chmod +x "$HOME/.local/share/applications/cachyos-control-center.desktop"
    echo -e "${GREEN}[✓] Desktop-Starter in ~/.local/share/applications/ installiert.${NC}"
fi

if [ -f "$SCRIPT_DIR/data/cachyos-control-center.svg" ]; then
    cp -f "$SCRIPT_DIR/data/cachyos-control-center.svg" "$HOME/.local/share/icons/hicolor/scalable/apps/cachyos-control-center.svg"
    echo -e "${GREEN}[✓] Anwendungs-Icon installiert.${NC}"
fi

if command -v update-desktop-database &>/dev/null; then
    update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
fi

# 5. Verifikation
echo -e "\n${CYAN}[5/5] Funktions-Test (Smoke-Test)...${NC}"
if python3 "$SCRIPT_DIR/app.py" --version &>/dev/null; then
    VERSION_OUTPUT=$(python3 "$SCRIPT_DIR/app.py" --version 2>&1)
    echo -e "${GREEN}[✓] Erfolgreich initialisiert: ${VERSION_OUTPUT}${NC}"
else
    echo -e "${YELLOW}[!] Warnung: Smoke-Test im globalen Python fehlgeschlagen. Prüfe .venv falls genutzt.${NC}"
fi

echo -e "\n${GREEN}${BOLD}====================================================================${NC}"
echo -e "${GREEN}${BOLD}   Setup erfolgreich abgeschlossen! 🚀                              ${NC}"
echo -e "${GREEN}${BOLD}====================================================================${NC}"
echo -e "Starte das Kontrollzentrum bequem über:"
echo -e "  • Terminal:       ${CYAN}cachyos-control-center${NC}  oder  ${CYAN}./run.sh${NC}"
echo -e "  • Startmenü:      ${CYAN}CachyOS Control Center${NC} (KDE / KRunner)"
echo -e "  • Direktaufruf:   ${CYAN}python3 app.py${NC}\n"
sleep 0.1
