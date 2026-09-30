"""Stamp every CSS and JS reference with a hash of the file's content.

GitHub Pages lets browsers cache HTML, CSS and JS for 10 minutes each, so a page
and a stylesheet changed together could meet as new page + old stylesheet. The
?v= hash gives every version of a file its own URL, so a page always loads the
files it was written for.

    python scripts/stamp_assets.py          update ?v= in dist/**/*.html
    python scripts/stamp_assets.py --check  exit 1 if any reference is missing or stale

Run it after changing anything in dist/assets/css or dist/assets/js. Python 3.10+,
no third-party packages.
"""
import argparse
import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / 'dist'
# Local stylesheets and scripts live in these two folders and nowhere else.
REF = re.compile(r'(?P<attr>href|src)="(?P<path>/assets/(?:css|js)/[\w.-]+\.(?:css|js))(?:\?v=[0-9a-f]*)?"')
LOCAL_ASSET = re.compile(r'(?:href|src)="(/[^"?]+\.(?:css|js))(?:\?[^"]*)?"')
ASSET_PATH = re.compile(r'/assets/(?:css|js)/[\w.-]+\.(?:css|js)')


def digest(path):
    # Hash the committed form: a Windows checkout may carry CRLF, the published file has LF.
    return hashlib.sha256(path.read_bytes().replace(b'\r\n', b'\n')).hexdigest()[:10]


def stamp(text, problems, page):
    for m in LOCAL_ASSET.finditer(text):
        if not ASSET_PATH.fullmatch(m[1]):
            problems.append(f'{page}: {m[1]} is outside /assets/css/ and /assets/js/')

    def fix(m):
        target = DIST / m['path'].lstrip('/')
        if not target.is_file():
            problems.append(f'{page}: {m["path"]} does not exist')
            return m[0]
        return f'{m["attr"]}="{m["path"]}?v={digest(target)}"'
    return REF.sub(fix, text)


def run(check):
    """Return (pages whose stamps are stale, other problems); write fixes unless check."""
    stale, problems = [], []
    for page in sorted(DIST.rglob('*.html')):
        rel = page.relative_to(ROOT).as_posix()
        text = page.read_text(encoding='utf-8')
        stamped = stamp(text, problems, rel)
        if stamped != text:
            stale.append(rel)
            if not check:
                page.write_text(stamped, encoding='utf-8', newline='\n')
    return stale, problems


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--check', action='store_true', help='report stale stamps without writing')
    args = parser.parse_args()
    stale, problems = run(args.check)
    for p in problems:
        print('ERROR', p)
    for p in stale:
        print(('stale ' if args.check else 'stamped ') + p)
    if args.check and stale:
        print('Run: python scripts/stamp_assets.py')
    return 1 if problems or (args.check and stale) else 0


if __name__ == '__main__':
    raise SystemExit(main())
