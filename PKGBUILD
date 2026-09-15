# Maintainer: George Apostolidis <your@email>
pkgname=uninews
pkgver=0.2.0
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
source=("$pkgname-$pkgver.tar.gz::$url/archive/refs/tags/v$pkgver.tar.gz")
sha256sums=('SKIP')

build() {
  cd "UniNews-$pkgver"
  python -m build --wheel --no-isolation
}

check() {
  cd "UniNews-$pkgver"
  PYTHONPATH="src" QT_QPA_PLATFORM=offscreen pytest -q
}

package() {
  cd "UniNews-$pkgver"
  python -m installer --destdir="$pkgdir" dist/*.whl

  install -Dm644 packaging/uninews.desktop \
    "$pkgdir/usr/share/applications/uninews.desktop"
  install -Dm644 packaging/uninews.svg \
    "$pkgdir/usr/share/icons/hicolor/scalable/apps/uninews.svg"
  install -Dm644 LICENSE "$pkgdir/usr/share/licenses/$pkgname/LICENSE"
}
