const base = document.documentElement.dataset.base || '';
const path = window.location.pathname;
const active = (segment) => path.includes(segment) ? ' aria-current="page"' : '';

const header = `
  <a class="skip-link" href="#main">本文へ移動</a>
  <header class="site-header">
    <div class="container header-inner">
      <a class="logo" href="${base}/" aria-label="ビズフォーム トップ">
        <span class="logo-mark" aria-hidden="true">B</span><span>bizform</span>
      </a>
      <nav class="global-nav" id="global-nav" aria-label="メインメニュー">
        <a href="${base}/service/"${active('/service/')}>サービス内容</a>
        <a href="${base}/pricing/"${active('/pricing/')}>料金</a>
        <a href="${base}/examples/"${active('/examples/')}>文面サンプル</a>
        <a href="${base}/use-cases/"${active('/use-cases/')}>活用シーン</a>
        <a href="${base}/faq/"${active('/faq/')}>よくある質問</a>
        <div class="nav-actions">
          <a class="button button-secondary" href="${base}/resources/">資料を見る</a>
          <a class="button button-primary" href="${base}/contact/">無料で相談する</a>
        </div>
      </nav>
      <button class="menu-button" type="button" aria-label="メニューを開く" aria-controls="global-nav" aria-expanded="false"><span></span></button>
      <div class="header-actions">
        <a class="button button-secondary" href="${base}/resources/">資料を見る</a>
        <a class="button button-primary" href="${base}/contact/"><span class="desktop-label">無料で相談する</span><span class="mobile-label">無料相談</span></a>
      </div>
    </div>
  </header>`;

const footer = `
  <footer class="site-footer">
    <div class="container">
      <div class="footer-grid">
        <div class="footer-brand">
          <a class="logo" href="${base}/"><span class="logo-mark" aria-hidden="true">B</span><span>bizform</span></a>
          <p>企業ごとの文面作成から送信運用まで。新規開拓の実務を前に進めるフォーム営業代行です。</p>
        </div>
        <div class="footer-column"><strong>検討する</strong><a href="${base}/service/">サービス内容</a><a href="${base}/pricing/">料金・契約条件</a><a href="${base}/examples/">文面・運用サンプル</a><a href="${base}/use-cases/">活用シーン</a></div>
        <div class="footer-column"><strong>理解する</strong><a href="${base}/faq/">よくある質問</a><a href="${base}/guide/">フォーム営業ガイド</a><a href="${base}/policy/">送信方針</a><a href="${base}/stop/">送信停止・受信窓口</a></div>
        <div class="footer-column"><strong>会社・相談</strong><a href="${base}/resources/">サービス資料</a><a href="${base}/contact/">導入相談</a><a href="${base}/company/">運営会社</a><a href="${base}/policy/#privacy">プライバシーポリシー</a></div>
      </div>
      <div class="footer-bottom"><span>© 2026 Contents X Inc.</span><span>フォーム営業を、判断できる情報から。</span></div>
    </div>
  </footer>`;

document.querySelector('[data-site-header]')?.insertAdjacentHTML('afterbegin', header);
document.querySelector('[data-site-footer]')?.insertAdjacentHTML('afterbegin', footer);

// The header is fixed, so its wrapper has to reserve the matching height.
const headerWrap = document.querySelector('[data-site-header]');
const siteHeader = document.querySelector('.site-header');
const syncHeaderHeight = () => {
  if (!headerWrap || !siteHeader) return;
  const height = siteHeader.offsetHeight;
  if (height) headerWrap.style.setProperty('--header-height', `${height}px`);
};
syncHeaderHeight();
window.addEventListener('load', syncHeaderHeight);
if ('ResizeObserver' in window && siteHeader) {
  new ResizeObserver(syncHeaderHeight).observe(siteHeader);
} else {
  window.addEventListener('resize', syncHeaderHeight);
}

// Floating CTA on every page except the contact form, which already asks for
// the same action. It appears once the hero CTA has scrolled out of reach.
const svgIcon = (paths) => {
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.setAttribute('viewBox', '0 0 24 24');
  svg.setAttribute('aria-hidden', 'true');
  paths.forEach(d => {
    const node = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    node.setAttribute('d', d);
    svg.append(node);
  });
  return svg;
};
const ctaLink = (className, href, icon, labels) => {
  const link = document.createElement('a');
  link.className = className;
  link.href = href;
  link.append(icon);
  labels.forEach(({ text, className: labelClass, hidden }) => {
    const span = document.createElement('span');
    span.textContent = text;
    if (labelClass) span.className = labelClass;
    if (hidden) span.hidden = true;
    link.append(span);
  });
  return link;
};

const isContactPage = /\/contact\/?$/.test(path.replace(/index\.html$/, ''));
if (!isContactPage && !document.querySelector('.floating-cta')) {
  const cta = document.createElement('aside');
  cta.className = 'floating-cta';
  cta.setAttribute('aria-label', 'お問い合わせ');
  cta.append(
    ctaLink('floating-cta-secondary', `${base}/resources/`,
      svgIcon(['M6 3h8l5 5v13a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1Z', 'M14 3v5h5']),
      [{ text: '資料を見る' }]),
    ctaLink('floating-cta-primary', `${base}/contact/`,
      svgIcon(['M3 6h18v12H3z', 'm3 7 9 6 9-6']),
      [
        { text: '無料で相談する', className: 'floating-cta-label-long' },
        { text: '無料相談', className: 'floating-cta-label-short', hidden: true }
      ])
  );
  document.body.append(cta);
  document.body.classList.add('has-floating-cta');

  const shortLabel = cta.querySelector('.floating-cta-label-short');
  const narrow = window.matchMedia('(max-width: 768px)');
  const syncLabel = () => { if (shortLabel) shortLabel.hidden = !narrow.matches; };
  syncLabel();
  narrow.addEventListener('change', syncLabel);

  const revealAfter = () => Math.max(window.innerHeight * 0.6, 420);
  let ctaVisible = false;
  let ctaTicking = false;
  const syncCta = () => {
    ctaTicking = false;
    const shouldShow = window.scrollY > revealAfter();
    if (shouldShow === ctaVisible) return;
    ctaVisible = shouldShow;
    cta.classList.toggle('is-visible', shouldShow);
  };
  const queueCta = () => {
    if (ctaTicking) return;
    ctaTicking = true;
    requestAnimationFrame(syncCta);
  };
  window.addEventListener('scroll', queueCta, { passive: true });
  window.addEventListener('resize', queueCta);
  syncCta();
}

const menuButton = document.querySelector('.menu-button');
const globalNav = document.querySelector('.global-nav');
const mobileMenu = window.matchMedia('(max-width: 1040px)');
let menuScrollY = 0;
const setMenuOpen = (open, restoreFocus = false) => {
  if (!menuButton || !globalNav) return;
  const wasOpen = menuButton.getAttribute('aria-expanded') === 'true';
  if (open === wasOpen) return;
  if (open) {
    // Read once, before any class toggle can reflow the page underneath us.
    menuScrollY = Math.round(window.scrollY);
    document.body.style.setProperty('--nav-scroll-top', `-${menuScrollY}px`);
  }
  menuButton.setAttribute('aria-expanded', String(open));
  menuButton.setAttribute('aria-label', open ? 'メニューを閉じる' : 'メニューを開く');
  globalNav.classList.toggle('open', open);
  document.body.classList.toggle('nav-open', open);
  if (!open) {
    document.body.style.removeProperty('--nav-scroll-top');
    window.scrollTo({ top: menuScrollY, behavior: 'instant' });
  }
  if (restoreFocus) menuButton.focus({ preventScroll: true });
};
menuButton?.addEventListener('click', () => {
  setMenuOpen(menuButton.getAttribute('aria-expanded') !== 'true');
});
document.querySelectorAll('.site-header a').forEach(link => link.addEventListener('click', () => {
  setMenuOpen(false);
}));
document.addEventListener('keydown', (event) => {
  if (menuButton?.getAttribute('aria-expanded') !== 'true') return;
  if (event.key === 'Escape') {
    event.preventDefault();
    setMenuOpen(false, true);
  }
  if (event.key === 'Tab') {
    const controls = [...document.querySelectorAll('.site-header a, .site-header button')]
      .filter(el => el.getClientRects().length);
    const first = controls[0];
    const last = controls[controls.length - 1];
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last?.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first?.focus();
    }
  }
});
mobileMenu.addEventListener('change', () => setMenuOpen(false));
window.addEventListener('pagehide', () => setMenuOpen(false));

// Keep wide reference material readable without widening the entire page.
const scrollRegions = [];
const addScrollHint = (region, label) => {
  const hint = document.createElement('p');
  hint.className = 'table-scroll-hint';
  hint.textContent = '左右にスワイプして全体をご覧いただけます。';
  hint.id = `scroll-hint-${scrollRegions.length}`;
  region.before(hint);
  region.setAttribute('role', 'region');
  region.setAttribute('aria-label', label);
  const update = () => {
    const scrollable = region.scrollWidth > region.clientWidth + 1;
    region.tabIndex = scrollable ? 0 : -1;
    hint.hidden = !scrollable;
    if (scrollable) region.setAttribute('aria-describedby', hint.id);
    else region.removeAttribute('aria-describedby');
  };
  scrollRegions.push({ region, update });
  update();
};
document.querySelectorAll('table.comparison').forEach(table => {
  const region = document.createElement('div');
  region.className = 'table-scroll';
  table.before(region);
  region.append(table);
  addScrollHint(region, '比較表');
});
document.querySelectorAll('.pricing-table-wrap').forEach(region => addScrollHint(region, '営業手法の比較表'));
document.querySelectorAll('.examples-reference-frame > img, .examples-dashboard > img').forEach(img => {
  const region = document.createElement('div');
  region.className = 'image-scroll';
  img.before(region);
  region.append(img);
  addScrollHint(region, img.alt);
  img.addEventListener('load', () => scrollRegions.find(item => item.region === region)?.update());
});
if ('ResizeObserver' in window) {
  const resizeObserver = new ResizeObserver(() => scrollRegions.forEach(item => item.update()));
  scrollRegions.forEach(({ region }) => resizeObserver.observe(region));
} else {
  window.addEventListener('resize', () => scrollRegions.forEach(item => item.update()));
}

const observer = 'IntersectionObserver' in window ? new IntersectionObserver((entries) => {
  entries.forEach(entry => { if (entry.isIntersecting) { entry.target.classList.add('visible'); observer.unobserve(entry.target); } });
}, { threshold: .12 }) : null;
document.querySelectorAll('.reveal').forEach(el => observer ? observer.observe(el) : el.classList.add('visible'));

const contactForm = document.querySelector('[data-contact-form]');
contactForm?.addEventListener('submit', (event) => {
  event.preventDefault();
  if (!contactForm.reportValidity()) return;
  const data = new FormData(contactForm);
  const subject = `ビズフォーム導入相談：${data.get('company')}`;
  const body = [
    `会社名：${data.get('company')}`,
    `お名前：${data.get('name')}`,
    `メール：${data.get('email')}`,
    `相談内容：${data.get('topic') || '未選択'}`,
    '',
    `${data.get('message')}`
  ].join('\n');
  document.querySelector('.form-message')?.classList.add('show');
  window.location.href = `mailto:info@content-x.co.jp?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
});
