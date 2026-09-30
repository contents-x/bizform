"""Layout check in a real browser: every page at many screen widths and two text sizes.

    pip install playwright && python -m playwright install chromium
    python scripts/layout_check.py                 # serves dist/ itself
    python scripts/layout_check.py --base http://127.0.0.1:8765
    python scripts/layout_check.py --pages / /pricing/    # only these pages

Reports sideways page scrolling, header items that wrap, overlap or run off the
row, the menu showing in the wrong mode, floating-bar buttons that overflow or
wrap, buttons whose label is cut off, broken images and script errors. Phones
are emulated as touch devices in portrait and landscape. Exit status 1 when a
problem is found. Fonts differ by OS, so run it on the machine you review on;
the GitHub Actions run (layout-check.yml) is a second opinion.
"""
import argparse
import functools
import http.server
import threading

from playwright.sync_api import sync_playwright

from site_files import DIST, page_urls

WIDTHS = [280, 320, 360, 375, 390, 414, 430, 540, 600, 700, 768, 769, 820, 900, 1024, 1025, 1040, 1041,
          1100, 1180, 1239, 1240, 1280, 1366, 1440, 1920]
DEVICES = [('Galaxy Fold', 280, 653), ('iPhone SE', 375, 667), ('iPhone 14', 390, 844), ('Pixel 7', 412, 915),
           ('iPad mini', 768, 1024), ('iPad Air', 820, 1180), ('iPhone SE 横', 667, 375), ('iPhone 14 横', 844, 390),
           ('iPhone 15 Pro Max 横', 932, 430), ('iPad mini 横', 1024, 768)]

CHECK = r"""() => {
  const r = e => e.getBoundingClientRect(), shown = e => e.getClientRects().length > 0, out = [];
  const lines = el => { const tops = new Set(); const w = document.createTreeWalker(el, NodeFilter.SHOW_TEXT); let n;
    while ((n = w.nextNode())) { if (!n.textContent.trim() || !shown(n.parentElement)) continue;
      const g = document.createRange(); g.selectNodeContents(n); for (const q of g.getClientRects()) if (q.width > .5) tops.add(Math.round(q.top)); }
    return tops.size; };
  const cw = document.documentElement.clientWidth;
  if (document.documentElement.scrollWidth > cw) out.push('page scrolls sideways');
  const row = document.querySelector('.header-inner');
  if (row) {
    const navFixed = getComputedStyle(document.querySelector('.global-nav')).position === 'fixed';
    const items = [...row.querySelectorAll(':scope > .logo, :scope > .menu-button, .header-actions > a' + (navFixed ? '' : ', .global-nav > a'))].filter(shown);
    for (const el of items) {
      const parts = el.matches('.button-tel') ? [...el.querySelectorAll('.button-tel-text small, .button-tel-text span')] : [el];
      for (const p of parts) if (shown(p) && getComputedStyle(p).display !== 'none' && lines(p) > 1) out.push('header label wraps: ' + p.textContent.trim().slice(0, 10));
    }
    const sorted = [...items].sort((a, b) => r(a).left - r(b).left);
    for (let i = 1; i < sorted.length; i++) if (r(sorted[i]).left < r(sorted[i - 1]).right - .5) out.push('header items overlap');
    if (Math.max(...items.map(e => r(e).right)) > r(row).right + .5) out.push('header runs off the row');
    if (shown(document.querySelector('.menu-button')) === !navFixed) out.push('menu button and inline menu disagree');
  }
  const cta = [...document.querySelectorAll('.floating-cta.is-visible:not(.is-minimized) a')];
  if (cta.length) {
    if (Math.max(...cta.map(a => r(a).right)) > cw - 4 || Math.min(...cta.map(a => r(a).left)) < 4) out.push('floating bar runs off screen');
    for (const a of cta) {
      if (a.scrollWidth > a.clientWidth + 1) out.push('floating bar label cut off');
      for (const s of a.querySelectorAll('span')) if (!s.hidden && getComputedStyle(s).display !== 'none' && lines(s) > 1) out.push('floating bar label wraps');
    }
  }
  for (const b of document.querySelectorAll('main :is(.button, .showcase-button), main :is(.button, .showcase-button) *')) if (shown(b) && b.scrollWidth > b.clientWidth + 1 && getComputedStyle(b).overflow !== 'visible') out.push('button label cut off: ' + b.textContent.trim().slice(0, 12));
  for (const img of document.images) if (img.complete && img.naturalWidth === 0 && img.getAttribute('src')) out.push('broken image: ' + img.getAttribute('src'));
  return [...new Set(out)];
}"""


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def serve():
    handler = functools.partial(QuietHandler, directory=str(DIST))
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return f'http://127.0.0.1:{server.server_port}'


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--base', help='serve from this URL instead of starting a local server')
    ap.add_argument('--browser', default='chrome', help='"chrome" (installed Google Chrome) or "chromium" (Playwright\'s)')
    ap.add_argument('--pages', nargs='+', help='check only these paths, e.g. / /pricing/')
    args = ap.parse_args()
    paths = args.pages or page_urls()
    base = args.base.rstrip('/') if args.base else serve()
    problems = {}

    def note(where, issues):
        for i in issues:
            problems.setdefault(i, []).append(where)

    with sync_playwright() as p:
        launch = {'channel': 'chrome'} if args.browser == 'chrome' else {}
        browser = p.chromium.launch(**launch)
        block = lambda route: route.abort()
        # Every page, desktop-style resizing, at the default and an enlarged text size.
        for size in (16, 20):
            page = browser.new_page(viewport={'width': 1440, 'height': 900})
            page.route('https://contentsx-crm.vercel.app/**', block)
            errors = []
            page.on('pageerror', lambda e: errors.append(str(e)))
            for path in paths:
                page.goto(base + path)
                page.add_style_tag(content=f'html {{ font-size: {size}px; }}')
                for w in WIDTHS:
                    page.set_viewport_size({'width': w, 'height': 900})
                    page.wait_for_timeout(40)
                    note(f'{path} {w}px text {size}px', page.evaluate(CHECK))
                page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                page.wait_for_timeout(350)
                note(f'{path} bottom text {size}px', page.evaluate(CHECK))
                page.evaluate('window.scrollTo(0, 0)')
            for e in errors:
                problems.setdefault('script error: ' + e[:120], []).append(f'text {size}px')
            page.close()
        # Phones and tablets as touch devices, portrait and landscape, scrolled to show the floating bar.
        for name, w, h in DEVICES:
            mobile = w < 1000 or h < 800
            ctx = browser.new_context(viewport={'width': w, 'height': h}, is_mobile=mobile, has_touch=mobile, device_scale_factor=2)
            page = ctx.new_page()
            page.route('https://contentsx-crm.vercel.app/**', block)
            for path in paths:
                page.goto(base + path)
                page.wait_for_timeout(150)
                note(f'{path} {name}', page.evaluate(CHECK))
                page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                page.wait_for_timeout(350)
                note(f'{path} {name} bottom', page.evaluate(CHECK))
            ctx.close()
        browser.close()

    for issue, where in sorted(problems.items()):
        print(f'PROBLEM {issue}: {len(where)}x, e.g. ' + '; '.join(where[:4]))
    print(f'{len(paths)} pages, {len(WIDTHS)} widths x 2 text sizes, {len(DEVICES)} devices: '
          + ('no problems' if not problems else f'{len(problems)} kinds of problem'))
    return 1 if problems else 0


if __name__ == '__main__':
    raise SystemExit(main())
