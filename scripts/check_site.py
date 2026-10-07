"""Static checks for dist/, run before every deploy (.github/workflows/pages.yml).

    python scripts/check_site.py

Checks HTML formatting, asset version stamps, internal links and anchors (also in
the header, footer and floating bar that site.js writes, the PDF behind the
download form and the images the stylesheets use; paths must match letter case,
as on GitHub Pages), images, the sitemap and canonical URLs, colour tokens, plan
prices and send counts, answers to the same question on different pages, the phone
number and mail address, which pages load which scripts and forms.css, and that
each script keeps its names to itself and parses (with Node.js when it is
installed; GitHub Actions always checks). Images that nothing uses are listed as
notes without failing. Python 3.10+, no third-party packages. Exit status 1 when
anything fails.
"""
import functools
import html
import os
import re
import shutil
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote

sys.path.insert(0, str(Path(__file__).resolve().parent))
import format_html  # noqa: E402
import stamp_assets  # noqa: E402
from site_files import DIST, html_files, url_of  # noqa: E402

SITE = 'https://bizform.contentsx.jp'
TEL = '03-6261-0764'
EMAIL = 'office@contentsx.jp'
# Plans as in the sales deck (ビズフォーム_営業資料_0926.pdf): monthly send attempts, monthly fee (tax excluded).
PLANS = {'ライト': (30_000, 158_000), 'スタンダード': (50_000, 198_000), 'プレミアム': (80_000, 298_000)}
SETUP_FEE = 198_000
# These stylesheets take every colour from the tokens in site.css.
TOKEN_ONLY_CSS = ['site.css', 'home.css', 'service.css', 'pricing.css', 'examples.css', 'forms.css']
CRM_EMBED = 'https://contentsx-crm.vercel.app/embed/inbound-v1.js'

errors = []
notes = []


def fail(message):
    errors.append(message)


class Page(HTMLParser):
    def __init__(self, path):
        super().__init__(convert_charrefs=True)
        self.path = path
        self.ids, self.links, self.images, self.scripts, self.text = set(), [], [], [], []
        self.canonical = None
        self.forms = set()
        self._skip = 0
        self.feed(path.read_text(encoding='utf-8'))

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if 'id' in a:
            self.ids.add(a['id'])
        # data-download-url: the PDF the download form hands out. An attribute without a
        # value counts as an empty link.
        for attr in ('href', 'src', 'data-download-url'):
            if attr in a and tag != 'script':
                self.links.append((tag, a[attr] or ''))
        if tag == 'img':
            self.images.append(a)
        if tag == 'script':
            self.scripts.append(a.get('src'))
            self._skip += 1
        if tag == 'style':
            self._skip += 1
        if tag == 'link' and a.get('rel') == 'canonical':
            self.canonical = a.get('href')
        for key in ('data-contact-form', 'data-download-form'):
            if key in a:
                self.forms.add(key)

    def handle_endtag(self, tag):
        if tag in ('script', 'style'):
            self._skip -= 1

    def handle_data(self, data):
        if not self._skip:
            self.text.append(data)

    def plain_text(self):
        return re.sub(r'\s+', ' ', html.unescape(' '.join(self.text)))


def load_pages():
    return {url_of(p): Page(p) for p in html_files()}


def check_format(pages):
    for url, page in pages.items():
        text = page.path.read_text(encoding='utf-8')
        try:
            formatted = format_html.format_html(text)
        except ValueError as e:     # unmatched or unclosed tags
            fail(f'{url}: {e}')
            continue
        if formatted != text.replace('\r\n', '\n'):
            fail(f'{url}: not formatted (python scripts/format_html.py)')


def check_stamps():
    stale, problems = stamp_assets.run(check=True)
    for p in problems:
        fail(p)
    for p in stale:
        fail(f'{p}: stale ?v= stamp (python scripts/stamp_assets.py)')


def resolve(url):
    """Map a site URL path to the file that serves it."""
    target = DIST / url.lstrip('/')
    if url.endswith('/'):
        target = target / 'index.html'
    return target


@functools.lru_cache(maxsize=None)
def names_in(folder):
    return frozenset(os.listdir(folder))


def published(path):
    """Whether GitHub Pages serves this file: is_file() with exact letter case, which Windows
    and macOS ignore (a link to /Pricing/ would pass here and break on the site)."""
    try:
        parts = Path(os.path.normpath(path)).relative_to(DIST).parts
    except ValueError:
        return False
    folder = DIST
    for part in parts:
        if not folder.is_dir() or part not in names_in(folder):
            return False
        folder = folder / part
    return folder.is_file()


def check_link(pages, where, page_url, tag, value):
    """One href, src or data-download-url. where names it in messages; page_url is the page it
    sits on, for links to an id on the same page."""
    if value.startswith(SITE):
        value = value[len(SITE):] or '/'
    if value.startswith(('http://', 'https://', '//', 'data:')):
        return
    if value.startswith('mailto:'):
        if value[len('mailto:'):].split('?')[0] != EMAIL:
            fail(f'{where}: mail link {value} (expected {EMAIL})')
        return
    if value.startswith('tel:'):
        if value != f'tel:{TEL}':
            fail(f'{where}: phone link {value} (expected tel:{TEL})')
        return
    if not value.strip():
        fail(f'{where}: empty <{tag}> link')
        return
    path, _, anchor = value.partition('#')
    path = unquote(path.split('?')[0])
    if not path:
        target_url = page_url
    elif path.startswith('/'):
        target_url = path
    else:
        fail(f'{where}: relative link {value}; use a root-relative path')
        return
    target = resolve(target_url)
    if not published(target):
        fail(f'{where}: <{tag}> {value} does not exist')
        return
    page = pages.get(url_of(target))
    if anchor and page and anchor not in page.ids:
        fail(f'{where}: {value} points to a missing id')


def check_links(pages):
    # The header, footer and floating bar come from site.js: its href/src templates and the
    # ctaLink() targets are checked once, and its skip link (#main) on every page. Its tel:
    # links (header, menu, floating bar) are built from the TEL constant.
    site_js = (DIST / 'assets/js/site.js').read_text(encoding='utf-8')
    template_links = [('a' if attr == 'href' else 'img', value)
                      for attr, value in re.findall(r'(href|src)="([^"$]+)"', site_js)]
    targets = [value for _, value in re.findall(r"ctaLink\(\s*'[^']*',\s*(['`])(.*?)\1", site_js, flags=re.S)]
    if len(targets) != site_js.count('ctaLink('):
        fail('assets/js/site.js: could not read the link of every ctaLink() call')
    template_links += [('a', value) for value in targets if '${' not in value]    # tel:${TEL}: see TEL
    template_links = list(dict.fromkeys(template_links))
    tels = re.findall(r"const TEL = '([^']*)'", site_js)
    if tels != [TEL]:
        fail(f'assets/js/site.js: TEL is {" and ".join(tels) or "missing"} (expected {TEL}, once)')
    for tag, value in template_links:
        if not value.startswith('#'):
            check_link(pages, 'assets/js/site.js', '/', tag, value)
    for url, page in pages.items():
        for tag, value in page.links:
            check_link(pages, url, url, tag, value)
        for tag, value in template_links:
            if value.startswith('#'):
                check_link(pages, url, url, tag, value)


def check_css_urls():
    for css in sorted((DIST / 'assets/css').glob('*.css')):
        text = re.sub(r'/\*.*?\*/', '', css.read_text(encoding='utf-8'), flags=re.S)
        refs = [a or b or c for a, b, c in
                re.findall(r'url\(\s*(?:"([^"]*)"|\'([^\']*)\'|([^)\s]*))\s*\)', text, flags=re.I)]
        refs += [a or b for a, b in re.findall(r'@import\s+(?:"([^"]*)"|\'([^\']*)\')', text, flags=re.I)]
        for ref in refs:
            path = ref[len(SITE):] if ref.startswith(SITE + '/') else ref
            if path.startswith(('data:', 'http://', 'https://', '//', '#')):
                continue
            path = unquote(path.split('?')[0].split('#')[0])
            target = DIST / path.lstrip('/') if path.startswith('/') else css.parent / path
            if not published(target):
                fail(f'assets/css/{css.name}: {ref} does not exist')


def check_images(pages):
    for url, page in pages.items():
        for img in page.images:
            src = img.get('src', '')
            if 'alt' not in img:
                fail(f'{url}: <img src="{src}"> has no alt')
            if not ('width' in img and 'height' in img):
                fail(f'{url}: <img src="{src}"> has no width/height')
    # A note, not a failure: a renamed or dropped image stays for one deploy so pages
    # still in visitors' caches can load it (docs/CONTENT-RULES.md), then goes.
    used = ' '.join(re.sub(r'<!--.*?-->', '', p.read_text(encoding='utf-8'), flags=re.S)
                    for p in DIST.rglob('*') if p.suffix in ('.html', '.css', '.js'))
    for image in sorted(p for p in (DIST / 'assets/images').iterdir() if p.is_file()):
        if image.name not in used:
            notes.append(f'assets/images/{image.name} is not used by any page, stylesheet or script')


def check_sitemap(pages):
    sitemap = (DIST / 'sitemap.xml').read_text(encoding='utf-8')
    listed = {loc[len(SITE):] for loc in re.findall(r'<loc>([^<]+)</loc>', sitemap)}
    for url in listed:
        if url not in pages:
            fail(f'sitemap.xml: {url} has no page')
    for url, page in pages.items():
        if url == '/404.html':
            continue
        if url not in listed:
            fail(f'sitemap.xml: {url} is missing')
        if page.canonical != SITE + url:
            fail(f'{url}: canonical is {page.canonical}, expected {SITE + url}')


def check_colours():
    for name in TOKEN_ONLY_CSS:
        if not (DIST / 'assets/css' / name).is_file():
            fail(f'assets/css/{name} is missing (listed in TOKEN_ONLY_CSS)')
            continue
        css = (DIST / 'assets/css' / name).read_text(encoding='utf-8')
        css = re.sub(r'/\*.*?\*/', '', css, flags=re.S)
        css = re.sub(r':root\s*\{[^}]*\}', '', css)
        for hex_colour in sorted(set(re.findall(r'#[0-9a-fA-F]{3,8}\b', css))):
            fail(f'assets/css/{name}: {hex_colour} is not a token (add it to :root in site.css)')


def check_prices(pages):
    names = '|'.join(PLANS)
    amount = r'(\d{1,3}(?:,\d{3})+)\s*'
    counts = [count for count, _ in PLANS.values()]
    for url, page in pages.items():
        text = page.plain_text()
        # A plan name, not the end of a longer katakana word (ハイライト).
        for m in re.finditer(rf'(?<![ァ-ヶー])(?:{names})', text):
            around = text[max(0, m.start() - 1):m.start()] + text[m.end():m.end() + 1]
            if (re.search(r'社\s*$', text[max(0, m.start() - 3):m.start()]) or set(around) & set('〜・')
                    or text.startswith('を', m.end())):
                continue    # another company's plan, a list or range of plans, or a button (ライトを相談する)
            window = text[m.end():m.end() + 120]
            window = re.split(rf'{names}|[A-Z]社|。', window)[0]
            window = re.sub(r'初期費用[^0-9。]{0,24}' + amount + '円', '', window)
            count, price = PLANS[m.group()]
            for c in re.findall(amount + '件', window):
                if int(c.replace(',', '')) != count:
                    fail(f'{url}: {m.group()} shows {c}件 (expected {count:,}件)')
            for c in re.findall(r'(\d+)万件', window):
                if int(c) * 10_000 != count:
                    fail(f'{url}: {m.group()} shows {c}万件 (expected {count:,}件)')
            for y in re.findall(amount + '円', window):
                if int(y.replace(',', '')) not in (price, price + SETUP_FEE // 12):
                    fail(f'{url}: {m.group()} shows {y}円 (expected {price:,}円)')
            for u in re.findall(r'(\d+\.\d+)\s*円', window):
                if u != f'{price / count:.2f}':
                    fail(f'{url}: {m.group()} shows {u}円 per send (expected {price / count:.2f}円)')
        for fee in re.findall(r'初期費用[^0-9。]{0,24}' + amount + '円', text):
            if int(fee.replace(',', '')) != SETUP_FEE:
                fail(f'{url}: setup fee {fee}円 (expected {SETUP_FEE:,}円)')
        # Counts in 万 on the service's own pages (the guides also quote other services): both
        # ends of a range (月3万〜8万件) and every size in a list (3万件・5万件・8万件) are plan
        # sizes. Spaces and markup between the parts are ignored, but not between two digits;
        # a sentence that names another company (A社, 他社, 各社) is skipped.
        if not url.startswith('/guide/'):
            compact = re.sub(r'(?<!\d)\s+|\s+(?!\d)', '', text)
            for m in re.finditer(r'\d+(?:万件?)?[〜～~]\d+万件|(?:\d+万件?[・、])+\d+万件', compact):
                sentence = compact[compact.rfind('。', 0, m.start()) + 1:m.start()]
                if re.search(r'[A-ZＡ-Ｚ]社|他社|各社', sentence):
                    continue
                if not {int(n) * 10_000 for n in re.findall(r'\d+', m[0])} <= set(counts):
                    fail(f'{url}: {m[0]} (the plans are {"・".join(f"{c // 10_000}万件" for c in counts)})')


def check_scripts(pages):
    for url, page in pages.items():
        srcs = [s.split('?')[0] for s in page.scripts if s]
        if srcs.count('/assets/js/site.js') != 1:
            fail(f'{url}: must load /assets/js/site.js once')
        has_form = bool(page.forms)
        if has_form != ('/assets/js/forms.js' in srcs):
            fail(f'{url}: forms.js belongs on exactly the pages with a form')
        styles = [value.split('?')[0] for tag, value in page.links if tag == 'link']
        if has_form != ('/assets/css/forms.css' in styles):
            fail(f'{url}: forms.css belongs on exactly the pages with a form')
        if ('/assets/js/forms.js' in srcs and '/assets/js/site.js' in srcs
                and srcs.index('/assets/js/forms.js') < srcs.index('/assets/js/site.js')):
            fail(f'{url}: forms.js must come after site.js')
        if srcs.count(CRM_EMBED) != (1 if has_form else 0):
            fail(f'{url}: the CRM embed script belongs once on each form page and nowhere else')
        if ('faq-accordion' in page.path.read_text(encoding='utf-8')) != ('/assets/js/faq.js' in srcs):
            fail(f'{url}: faq.js belongs on exactly the pages with .faq-accordion')
    # Classic scripts share one global scope, so each file keeps its names inside one
    # function. A top-level const, let or class declared in two files stops the second
    # file; a function or var silently replaces the first one.
    for js in sorted((DIST / 'assets/js').glob('*.js')):
        code = [line for line in js.read_text(encoding='utf-8').splitlines() if line.strip() and not line.startswith('//')]
        if not code or code[0] != '(() => {' or code[-1] != '})();':
            fail(f'assets/js/{js.name}: wrap the whole file in (() => {{ ... }})();')
        for line in code:
            if re.match(r'(?:const|let|var|function|class)\s', line):
                fail(f'assets/js/{js.name}: top-level declaration outside the wrapper: {line.strip()[:60]}')
    # A syntax error stops the whole file in the browser. vm.Script parses each file as a
    # classic script, as the browser does; node --check would also accept module syntax.
    node = shutil.which('node')
    if not node:
        if os.environ.get('CI', '').lower() == 'true':
            fail('node not found: JavaScript syntax was not checked')
        else:
            notes.append('node not found: JavaScript syntax not checked here (GitHub Actions checks it)')
        return
    parse = ("const fs = require('fs'), vm = require('vm'), path = require('path');"
             "for (const f of process.argv.slice(1)) {"
             " try { new vm.Script(fs.readFileSync(f, 'utf8'), { filename: path.basename(f) }); }"
             " catch (e) { console.log(`${e.stack.split('\\n')[0]} ${e.message}`); } }")
    files = [str(js) for js in sorted((DIST / 'assets/js').glob('*.js'))]
    result = subprocess.run([node, '-e', parse, *files], capture_output=True, encoding='utf-8', errors='replace')
    for line in result.stdout.splitlines():
        fail(f'assets/js/{line[:160]}')
    if result.returncode:
        fail(f'node could not check the scripts: {result.stderr.strip()[:160]}')


def faq_entries(page):
    """(question, answer) for each <details> on a page, without the 問/答 badges or any spacing."""
    source = page.path.read_text(encoding='utf-8')
    badge = r'<span[^>]*>\s*(?:問|答)?\s*</span>'

    def text(fragment):
        return re.sub(r'\s+', '', html.unescape(re.sub(r'<[^>]+>', '', re.sub(badge, '', fragment))))
    for m in re.finditer(r'<details[^>]*>(.*?)</details>', source, re.S):
        question, _, answer = m.group(1).partition('</summary>')
        yield text(question), text(answer)


def check_faq(pages):
    # A question worded the same on two pages (FAQ, pricing, examples, top) must get the same answer.
    # Reworded questions are not matched. /faq/ goes first, so the other pages are held to its answers.
    seen = {}
    for url, page in sorted(pages.items(), key=lambda item: item[0] != '/faq/'):
        for question, answer in faq_entries(page):
            if question in seen and seen[question][1] != answer:
                fail(f'{url}: the answer to 「{question}」 differs from {seen[question][0]}')
            seen.setdefault(question, (url, answer))


def main():
    names_in.cache_clear()
    pages = load_pages()
    checks = [(check_format, pages), (check_stamps,), (check_links, pages), (check_css_urls,), (check_images, pages),
              (check_sitemap, pages), (check_colours,), (check_prices, pages), (check_faq, pages), (check_scripts, pages)]
    for check, *args in checks:
        # A check that breaks is a failure too, reported with everything found so far.
        try:
            check(*args)
        except Exception as e:
            fail(f'{check.__name__} stopped: {e!r}')
    for n in notes:
        print('NOTE', n)
    for e in errors:
        print('ERROR', e)
    print(f'{len(pages)} pages checked: ' + (f'{len(errors)} problems' if errors else 'all checks passed'))
    return 1 if errors else 0


if __name__ == '__main__':
    raise SystemExit(main())
