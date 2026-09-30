"""Static checks for dist/, run before every deploy (.github/workflows/pages.yml).

    python scripts/check_site.py

Checks HTML formatting, asset version stamps, internal links and anchors,
images, the sitemap and canonical URLs, colour tokens, plan prices, the phone
number and mail address, and which pages load which scripts. Python 3.10+, no
third-party packages. Exit status 1 when anything fails.
"""
import html
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import format_html  # noqa: E402
import stamp_assets  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / 'dist'
SITE = 'https://bizform.contentsx.jp'
TEL = '03-6261-0764'
EMAIL = 'office@contentsx.jp'
# Plans as in the sales deck (ビズフォーム_営業資料_0926.pdf): monthly send attempts, monthly fee (tax excluded).
PLANS = {'ライト': (30_000, 158_000), 'スタンダード': (50_000, 198_000), 'プレミアム': (80_000, 298_000)}
SETUP_FEE = 198_000
# These stylesheets take every colour from the tokens in site.css.
TOKEN_ONLY_CSS = ['site.css', 'home.css', 'service.css', 'pricing.css']
CRM_EMBED = 'https://contentsx-crm.vercel.app/embed/inbound-v1.js'

errors = []


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
        for attr in ('href', 'src'):
            if a.get(attr) is not None and tag != 'script':
                self.links.append((tag, a[attr]))
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


def url_of(path):
    rel = path.relative_to(DIST).as_posix()
    return '/' + rel[:-len('index.html')] if rel.endswith('index.html') else '/' + rel


def load_pages():
    return {url_of(p): Page(p) for p in sorted(DIST.rglob('*.html'))}


def check_format(pages):
    for url, page in pages.items():
        text = page.path.read_text(encoding='utf-8')
        if format_html.format_html(text) != text.replace('\r\n', '\n'):
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


def check_links(pages):
    # Header and footer links come from the templates in site.js.
    site_js = (DIST / 'assets/js/site.js').read_text(encoding='utf-8')
    template_links = [('a', h) for h in re.findall(r'href="([^"$]+)"', site_js)]
    for url, page in pages.items():
        for tag, value in page.links + template_links:
            if value.startswith(SITE):
                value = value[len(SITE):] or '/'
            if value.startswith(('http://', 'https://', '//', 'data:')):
                continue
            if value.startswith('mailto:'):
                if value[len('mailto:'):].split('?')[0] != EMAIL:
                    fail(f'{url}: mail link {value} (expected {EMAIL})')
                continue
            if value.startswith('tel:'):
                if value != f'tel:{TEL}':
                    fail(f'{url}: phone link {value} (expected tel:{TEL})')
                continue
            path, _, anchor = value.partition('#')
            path = path.split('?')[0]
            if not path:
                target_url = url
            elif path.startswith('/'):
                target_url = path
            else:
                fail(f'{url}: relative link {value}; use a root-relative path')
                continue
            target = resolve(target_url)
            if not target.is_file():
                fail(f'{url}: <{tag}> {value} does not exist')
                continue
            if anchor and target.suffix == '.html':
                ids = pages[url_of(target)].ids | ({'main'} if anchor == 'main' else set())
                if anchor not in ids:
                    fail(f'{url}: {value} points to a missing id')


def check_images(pages):
    for url, page in pages.items():
        for img in page.images:
            src = img.get('src', '')
            if 'alt' not in img:
                fail(f'{url}: <img src="{src}"> has no alt')
            if not ('width' in img and 'height' in img):
                fail(f'{url}: <img src="{src}"> has no width/height')


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
        css = (DIST / 'assets/css' / name).read_text(encoding='utf-8')
        css = re.sub(r'/\*.*?\*/', '', css, flags=re.S)
        css = re.sub(r':root\s*\{[^}]*\}', '', css)
        for hex_colour in sorted(set(re.findall(r'#[0-9a-fA-F]{3,8}\b', css))):
            fail(f'assets/css/{name}: {hex_colour} is not a token (add it to :root in site.css)')


def check_prices(pages):
    names = '|'.join(PLANS)
    amount = r'(\d{1,3}(?:,\d{3})+)\s*'
    for url, page in pages.items():
        text = page.plain_text()
        for m in re.finditer(names, text):
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
            for y in re.findall(amount + '円', window):
                if int(y.replace(',', '')) not in (price, price + SETUP_FEE // 12):
                    fail(f'{url}: {m.group()} shows {y}円 (expected {price:,}円)')
            for u in re.findall(r'(\d+\.\d+)\s*円', window):
                if u != f'{price / count:.2f}':
                    fail(f'{url}: {m.group()} shows {u}円 per send (expected {price / count:.2f}円)')
        for fee in re.findall(r'初期費用[^0-9。]{0,24}' + amount + '円', text):
            if int(fee.replace(',', '')) != SETUP_FEE:
                fail(f'{url}: setup fee {fee}円 (expected {SETUP_FEE:,}円)')


def check_scripts(pages):
    for url, page in pages.items():
        srcs = [s.split('?')[0] for s in page.scripts if s]
        if srcs.count('/assets/js/site.js') != 1:
            fail(f'{url}: must load /assets/js/site.js once')
        has_form = bool(page.forms)
        if has_form != ('/assets/js/forms.js' in srcs):
            fail(f'{url}: forms.js belongs on exactly the pages with a form')
        if ('/assets/js/forms.js' in srcs and '/assets/js/site.js' in srcs
                and srcs.index('/assets/js/forms.js') < srcs.index('/assets/js/site.js')):
            fail(f'{url}: forms.js must come after site.js')
        if srcs.count(CRM_EMBED) != (1 if has_form else 0):
            fail(f'{url}: the CRM embed script belongs once on each form page and nowhere else')
        if ('faq-accordion' in page.path.read_text(encoding='utf-8')) != ('/assets/js/faq.js' in srcs):
            fail(f'{url}: faq.js belongs on exactly the pages with .faq-accordion')
    # Classic scripts share one global scope: a name declared twice stops the second file.
    seen = {}
    for js in sorted((DIST / 'assets/js').glob('*.js')):
        for name in re.findall(r'^(?:const|let|var|function|class)\s+([A-Za-z_$][\w$]*)', js.read_text(encoding='utf-8'), re.M):
            if name in seen:
                fail(f'assets/js/{js.name}: top-level {name} is also declared in {seen[name]}')
            seen[name] = js.name


def main():
    pages = load_pages()
    check_format(pages)
    check_stamps()
    check_links(pages)
    check_images(pages)
    check_sitemap(pages)
    check_colours()
    check_prices(pages)
    check_scripts(pages)
    for e in errors:
        print('ERROR', e)
    print(f'{len(pages)} pages checked: ' + (f'{len(errors)} problems' if errors else 'all checks passed'))
    return 1 if errors else 0


if __name__ == '__main__':
    raise SystemExit(main())
