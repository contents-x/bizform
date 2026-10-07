"""Layout check in a real browser: every page at many screen widths and two text sizes.

    pip install playwright==1.63.0
    python scripts/layout_check.py                 # serves dist/ itself; uses the installed Google Chrome
    python scripts/layout_check.py --browser chromium    # Playwright's (python -m playwright install chromium)
    python scripts/layout_check.py --base http://127.0.0.1:8765
    python scripts/layout_check.py --pages / /pricing/    # only these pages (Git Bash: MSYS_NO_PATHCONV=1)

Reports sideways page scrolling, header items that wrap, overlap or run off the
row, the menu showing in the wrong mode, floating-bar buttons that overflow or
wrap, buttons whose label is cut off, broken images, files that fail to load and
script errors. Desktop widths are measured with scrollbars showing, as on Windows
(the test browser hides them by default), scrolled down so the floating bar shows;
they cover common screens and both sides of every width breakpoint in the CSS,
from 319px up. Phones and tablets are emulated as touch devices in portrait and
landscape, also at both text sizes; screens narrower than 319px are folding phones,
which have no desktop scrollbar, and the Galaxy Fold view covers them. Exit status
1 when a problem is found. Fonts differ by OS, so run it on the machine you review
on; the GitHub Actions run (layout-check.yml, same Playwright version) is a second
opinion.
"""
import argparse
import functools
import http.server
import math
import re
import threading

from playwright.sync_api import sync_playwright

from site_files import DIST, page_urls

# Common screens. Both sides of each breakpoint in the CSS are added by widths(). No 280:
# a 280px window with a 15px desktop scrollbar does not exist (the header does not fit
# its 265px); the Galaxy Fold view checks 280px as a phone.
SCREENS = [320, 360, 375, 390, 414, 430, 540, 600, 700, 768, 820, 900, 1024, 1100, 1180, 1280, 1366, 1440, 1920]
DEVICES = [('Galaxy Fold', 280, 653), ('iPhone SE', 375, 667), ('iPhone 14', 390, 844), ('Pixel 7', 412, 915),
           ('iPad mini', 768, 1024), ('iPad Air', 820, 1180), ('iPhone SE 横', 667, 375), ('iPhone 14 横', 844, 390),
           ('iPhone 15 Pro Max 横', 932, 430), ('iPad mini 横', 1024, 768)]
# Wait two animation frames: resize observers run before a frame is drawn, and site.js
# fits the header in one. A fixed wait can measure first while the browser is busy.
SETTLE = '() => new Promise(done => requestAnimationFrame(() => requestAnimationFrame(done)))'

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
      for (const s of a.querySelectorAll('span')) if (getComputedStyle(s).display !== 'none' && lines(s) > 1) out.push('floating bar label wraps');
    }
  }
  for (const b of document.querySelectorAll('main :is(.button, .showcase-button), main :is(.button, .showcase-button) *')) if (shown(b) && b.scrollWidth > b.clientWidth + 1 && getComputedStyle(b).overflow !== 'visible') out.push('button label cut off: ' + b.textContent.trim().slice(0, 12));
  for (const img of document.images) if (img.complete && img.naturalWidth === 0 && img.getAttribute('src')) out.push('broken image: ' + img.getAttribute('src'));
  return [...new Set(out)];
}"""


def widths():
    """SCREENS plus the last width on each side of every max-width/min-width breakpoint, from
    319px up (narrower screens are phones without desktop scrollbars: see DEVICES)."""
    found = set(SCREENS)
    for css in (DIST / 'assets/css').glob('*.css'):
        for query in re.findall(r'@media([^{]+)\{', css.read_text(encoding='utf-8')):
            for kind, value in re.findall(r'(max|min)-width\s*:\s*([\d.]+)px', query, flags=re.I):
                last = math.floor(float(value)) if kind.lower() == 'max' else math.ceil(float(value)) - 1
                found |= {last, last + 1}
    return sorted(w for w in found if w >= min(SCREENS) - 1)


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    # Keep connections open: every page load fetches a dozen files.
    protocol_version = 'HTTP/1.1'

    def log_message(self, *args):
        pass


class Server(http.server.ThreadingHTTPServer):
    # Windows refuses connections beyond the listen queue (5 by default) while the machine is
    # busy, which would show up as files that failed to load.
    request_queue_size = 128


def serve():
    handler = functools.partial(QuietHandler, directory=str(DIST))
    server = Server(('127.0.0.1', 0), handler)
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
    screen_widths = widths()
    problems = {}
    where = {'now': ''}     # what is on screen, for problems reported by events

    def note(label, issues):
        for i in issues:
            problems.setdefault(i, []).append(label)

    def watch(page):
        """Script errors and site files that fail to load."""
        page.on('pageerror', lambda e: note(where['now'], ['script error: ' + str(e)[:120]]))
        page.on('response', lambda res: res.status >= 400 and res.url.startswith(base)
                and note(where['now'], [f'{res.status}: {res.url[len(base):]}']))
        # Requests cut off by moving on to the next page are not failures.
        page.on('requestfailed', lambda req: req.url.startswith(base) and req.failure != 'net::ERR_ABORTED'
                and note(where['now'], [f'failed to load: {req.url[len(base):]} ({req.failure})']))

    with sync_playwright() as p:
        launch = {'channel': 'chrome'} if args.browser == 'chrome' else {}
        # Show scrollbars: Windows gives them 15-17px of the window, which the CSS has to fit around.
        # The CRM script on the form pages is not ours: the browser cannot resolve its host (blocking
        # it with page.route would also turn off the HTTP cache and refetch every file on every page).
        browser = p.chromium.launch(**launch, ignore_default_args=['--hide-scrollbars'],
                                    args=['--host-resolver-rules=MAP contentsx-crm.vercel.app ~NOTFOUND'])
        # Every page, desktop-style resizing, at the default and an enlarged text size.
        scrollbar = None
        for size in (16, 20):
            page = browser.new_page(viewport={'width': 1440, 'height': 900})
            watch(page)
            for path in paths:
                where['now'] = f'{path} text {size}px'
                page.goto(base + path)
                page.add_style_tag(content=f'html {{ font-size: {size}px; }}')
                if scrollbar is None and page.evaluate('document.documentElement.scrollHeight > innerHeight'):
                    scrollbar = page.evaluate('innerWidth - document.documentElement.clientWidth')
                # Scrolled down, so the floating bar shows and is measured at every width; the
                # header and the buttons are measured the same anywhere on the page.
                page.evaluate("window.scrollTo({ top: document.body.scrollHeight, behavior: 'instant' })")
                for w in screen_widths:
                    page.set_viewport_size({'width': w, 'height': 900})
                    page.evaluate(SETTLE)
                    note(f'{path} {w}px text {size}px', page.evaluate(CHECK))
            page.close()
        # Phones and tablets as touch devices, portrait and landscape, at both text sizes,
        # scrolled to show the floating bar.
        for name, w, h in DEVICES:
            mobile = w < 1000 or h < 800
            ctx = browser.new_context(viewport={'width': w, 'height': h}, is_mobile=mobile, has_touch=mobile, device_scale_factor=2)
            page = ctx.new_page()
            watch(page)
            for size in (16, 20):
                for path in paths:
                    label = f'{path} {name}' + ('' if size == 16 else f' text {size}px')
                    where['now'] = label
                    page.goto(base + path)
                    page.add_style_tag(content=f'html {{ font-size: {size}px; }}')
                    page.wait_for_timeout(150)
                    note(label, page.evaluate(CHECK))
                    page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                    page.wait_for_timeout(350)
                    note(f'{label} bottom', page.evaluate(CHECK))
            ctx.close()
        browser.close()

    if scrollbar == 0:
        print('NOTE no scrollbar showed (overlay scrollbars?): desktop widths were measured without one')
    for issue, found_at in sorted(problems.items()):
        print(f'PROBLEM {issue}: {len(found_at)}x, e.g. ' + '; '.join(found_at[:4]))
    print(f'{len(paths)} pages, {len(screen_widths)} widths and {len(DEVICES)} device views, each at 2 text sizes: '
          + ('no problems' if not problems else f'{len(problems)} kinds of problem'))
    return 1 if problems else 0


if __name__ == '__main__':
    raise SystemExit(main())
