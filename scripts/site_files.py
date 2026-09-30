"""Where the published site lives and which pages it has. Shared by the scripts in this folder."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / 'dist'


def html_files():
    """Every published HTML file, in a stable order."""
    return sorted(DIST.rglob('*.html'))


def url_of(path):
    """The URL path a file is served at: dist/faq/index.html -> /faq/, dist/404.html -> /404.html."""
    rel = path.relative_to(DIST).as_posix()
    return '/' + rel[:-len('index.html')] if rel.endswith('index.html') else '/' + rel


def page_urls():
    return [url_of(p) for p in html_files()]
