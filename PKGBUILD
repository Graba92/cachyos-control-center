# Maintainer: Matthias Haase (Graba92) <https://github.com/Graba92>
pkgname=cachyos-control-center
pkgver=1.1.0
pkgrel=1
pkgdesc="Unified modular system administration dashboard and control utility for CachyOS and Arch Linux"
arch=('any')
url="https://github.com/Graba92/cachyos-control-center"
license=('MIT')
depends=(
  'python'
  'python-textual>=0.80.0'
  'python-rich>=13.0.0'
  'polkit'
  'pacman-contrib'
)
optdepends=(
  'cachyos-rate-mirrors: Accelerated CachyOS mirror speed ranking'
  'rate-mirrors: Alternative Arch/CachyOS mirror ranking'
  'systemd: Boot analyze, journalctl, and systemctl service manager'
  'pciutils: Hardware and GPU controller detection (lspci)'
  'util-linux: Block device inspection (lsblk) and fstrim'
  'tailscale: Mesh VPN integration and status overview'
  'fastfetch: System ricing summary display'
)
source=("cachyos-control-center-${pkgver}.tar.gz::https://github.com/Graba92/cachyos-control-center/archive/refs/tags/v${pkgver}.tar.gz")
sha256sums=('SKIP')

package() {
  cd "${srcdir}/${pkgname}-${pkgver}" 2>/dev/null || cd "${srcdir}/${pkgname}" 2>/dev/null || cd "${startdir}"

  # Target directories
  install -d "${pkgdir}/usr/lib/${pkgname}"
  install -d "${pkgdir}/usr/bin"
  install -d "${pkgdir}/usr/share/applications"
  install -d "${pkgdir}/usr/share/icons/hicolor/scalable/apps"
  install -d "${pkgdir}/usr/share/polkit-1/actions"
  install -d "${pkgdir}/etc/${pkgname}"
  install -d "${pkgdir}/usr/share/licenses/${pkgname}"

  # Source code copy
  cp -a app.py cachyos_center.py core ui bin "${pkgdir}/usr/lib/${pkgname}/"

  # Executable Launcher
  cat << 'EOF' > "${pkgdir}/usr/bin/${pkgname}"
#!/bin/sh
exec python3 /usr/lib/cachyos-control-center/app.py "$@"
EOF
  chmod 755 "${pkgdir}/usr/bin/${pkgname}"

  # Polkit Policy
  install -m 644 data/org.cachyos.controlcenter.policy "${pkgdir}/usr/share/polkit-1/actions/"

  # Desktop Entry & Icon
  install -m 644 data/cachyos-control-center.desktop "${pkgdir}/usr/share/applications/"
  install -m 644 data/cachyos-control-center.svg "${pkgdir}/usr/share/icons/hicolor/scalable/apps/"

  # Example Config
  install -m 644 config.example.toml "${pkgdir}/etc/${pkgname}/config.example.toml"

  # License
  install -m 644 LICENSE "${pkgdir}/usr/share/licenses/${pkgname}/LICENSE"
}
