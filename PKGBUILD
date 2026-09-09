pkgname=uninews
_pkgname=UniNews 
pkgver=0.1.0
pkgrel=1
pkgdesc="A small desktop application that brings together news and announcements from universities into a single place."
arch=('any')
url="https://github.com/open-source-uom/UniNews.git"
license=('GPL-3.0-or-later')
depends=(
	'python'
	'python-beautifulsoup4'
	'python-certifi'
	'python-charset-normalizer'
	'python-decorator'
	'python-feedparser'
	'python-idna'
	'python-markdown'
	'python-pyqt6'
	'python-requests'
	'python-sgmllib3k'
	'python-soupsieve'
	'python-typing_extensions'
	'python-urllib3'
) 
makedepends=('python-setuptools'
             'git'
             'python-pip'
)
source=("git+https://github.com/open-source-uom/UniNews.git")
sha256sums=('SKIP')

prepare() {
  cd "$srcdir/" 
}

pkgver() {
  cd "$srcdir/$_pkgname" || return 1
  local version=$(git describe --long --tags 2>/dev/null | sed 's/^v//;s/\([^-]*-g\)/r\1/;s/-/./g')
  if [ -z "$version" ]; then
    echo "0.1.0"
  else
    echo "$version"
  fi
}

build() {
  cd "$srcdir/$_pkgname"
  python setup.py build
}

package() {
  cd "$srcdir/$_pkgname"

  python setup.py install --root="$pkgdir" --optimize=1
  
  pip install --root="$pkgdir" --no-deps plyer
  
  install -Dm644 LICENSE "$pkgdir/usr/share/licenses/$_pkgname/LICENSE" 2>/dev/null || true
  install -Dm644 README.md "$pkgdir/usr/share/doc/$_pkgname/README.md" 2>/dev/null || true
  install -d "$pkgdir/usr/share/applications"
  install -d "$pkgdir/usr/share/pixmaps"
  install -d "$pkgdir/usr/share/icons/hicolor/128x128/apps"

  if [ -f "$srcdir/$_pkgname/resources/uninews-logo.png" ]; then
    install -Dm644 "$srcdir/$_pkgname/resources/uninews-logo.png" "$pkgdir/usr/share/pixmaps/uninews.png"
    install -Dm644 "$srcdir/$_pkgname/resources/uninews-logo.png" "$pkgdir/usr/share/icons/hicolor/128x128/apps/uninews.png"
    ICON="uninews"
  else
    ICON="system-help"
  fi

  cat << EOF > "$pkgdir/usr/share/applications/uninews.desktop"

[Desktop Entry]
Type=Application
Name=UniNews
GenericName=University News Reader
Exec=uninews
Icon=$ICON
Terminal=false
StartupNotify=true
StartupWMClass=UniNews
Categories=News;Network;Qt;
EOF
}

