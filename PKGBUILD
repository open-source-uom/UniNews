# Maintainer: George Apostolidis <your@email.com>
# Builds from the local checkout: run makepkg from the repository root.
pkgname=uninews
pkgver=$(grep -m1 '^version' pyproject.toml | cut -d'"' -f2)
pkgrel=1
pkgdesc="University news from Greek and international universities in one place"
arch=('any')
url="https://github.com/open-source-uom/UniNews"
license=('GPL3')
depends=(
  'python'
  'python-pyqt6'
  'python-requests'
  'python-beautifulsoup4'
  'python-feedparser'
)
makedepends=('python-build' 'python-installer' 'python-wheel' 'python-setuptools')
checkdepends=('python-pytest')
source=()

build() {
  cd "$startdir"
  rm -rf build src/uninews.egg-info
  python -m build --wheel --no-isolation --outdir "$srcdir/dist"
}

check() {
  cd "$startdir"
  PYTHONPATH="src" QT_QPA_PLATFORM=offscreen python -m pytest -q
}

package() {
  cd "$startdir"
  python -m installer --destdir="$pkgdir" "$srcdir"/dist/*.whl

  install -Dm644 packaging/uninews.desktop \
    "$pkgdir/usr/share/applications/uninews.desktop"
  install -Dm644 packaging/uninews.svg \
    "$pkgdir/usr/share/icons/hicolor/scalable/apps/uninews.svg"
  install -Dm644 LICENSE "$pkgdir/usr/share/licenses/$pkgname/LICENSE"
}
