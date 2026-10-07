// Shared by every page: header and footer, the floating inquiry bar, focus
// visibility under the fixed bars, the mobile menu, scroll hints for wide
// tables, and reveal-on-scroll. The two forms are in forms.js,
// which only /contact/ and /resources/ load.
// Wrapped in a function so nothing here becomes a global shared with the other scripts.
(() => {
  // The page's folder, the same with or without index.html: /service/, /contact/. An exact
  // match, so a 404 page served at /contact/foo is not taken for the contact page.
  const page = window.location.pathname.replace(/index\.html$/, '');
  const isPage = (folder) => page === folder;
  const active = (folder) => isPage(folder) ? ' aria-current="page"' : '';

  // Phone consultation uses the same number as BizManga.
  const TEL = '03-6261-0764';

  // Fall back to window resizes where ResizeObserver is unavailable.
  const onResize = (elements, callback) => {
    if ('ResizeObserver' in window) {
      const resizeObserver = new ResizeObserver(() => callback());
      elements.forEach(el => resizeObserver.observe(el));
    } else {
      window.addEventListener('resize', () => callback());
    }
  };

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

  const telIcon = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6.62 10.79a15.05 15.05 0 0 0 6.59 6.59l2.2-2.2a1 1 0 0 1 1.02-.24c1.12.37 2.33.57 3.57.57a1 1 0 0 1 1 1V20a1 1 0 0 1-1 1A17 17 0 0 1 3 4a1 1 0 0 1 1-1h3.5a1 1 0 0 1 1 1c0 1.24.2 2.45.57 3.57a1 1 0 0 1-.25 1.02l-2.2 2.2z"/></svg>';

  const header = `
  <a class="skip-link" href="#main">本文へ移動</a>
  <header class="site-header">
    <div class="container header-inner">
      <a class="logo" href="/" aria-label="ビズフォーム トップ">
        <img src="/assets/images/asset_logo_bizform.webp" width="634" height="128" alt="ビズフォーム">
      </a>
      <nav class="global-nav" id="global-nav" aria-label="メインメニュー">
        <a href="/service/"${active('/service/')}>サービス内容</a>
        <a href="/pricing/"${active('/pricing/')}>料金</a>
        <a href="/examples/"${active('/examples/')}>文面サンプル</a>
        <a href="/use-cases/"${active('/use-cases/')}>活用シーン</a>
        <a href="/faq/"${active('/faq/')}>よくある質問</a>
        <div class="nav-actions">
          <a class="button button-secondary" href="/resources/#download">資料ダウンロード</a>
          <a class="button button-primary" href="/contact/">無料で相談する</a>
          <a class="button button-tel" href="tel:${TEL}">${telIcon}電話で相談（${TEL}）</a>
        </div>
      </nav>
      <button class="menu-button" type="button" aria-label="メニューを開く" aria-controls="global-nav" aria-expanded="false"><span></span></button>
      <div class="header-actions">
        <a class="button button-secondary" href="/resources/#download"><span class="header-dl-long">資料ダウンロード</span><span class="header-dl-short">資料DL</span></a>
        <a class="button button-primary" href="/contact/"><span class="desktop-label">無料で相談する</span><span class="mobile-label">無料相談</span></a>
        <a class="button button-tel" href="tel:${TEL}" aria-label="電話で相談 ${TEL}" title="電話で相談 ${TEL}">${telIcon}<span class="button-tel-text"><small>電話で相談</small><span>${TEL}</span></span></a>
      </div>
    </div>
  </header>`;

  const footer = `
  <footer class="site-footer">
    <div class="container">
      <div class="footer-grid">
        <div class="footer-brand">
          <a class="logo logo-plate" href="/"><img src="/assets/images/asset_logo_bizform.webp" width="634" height="128" alt="ビズフォーム" loading="lazy"></a>
          <p>企業調査・文章作成から問い合わせフォームへの送信・管理まで。初回接点を増やす新規開拓の一括運用サービスです。</p>
        </div>
        <div class="footer-column"><strong>検討する</strong><a href="/service/">サービス内容</a><a href="/pricing/">料金・契約条件</a><a href="/examples/">文面・運用サンプル</a><a href="/use-cases/">活用シーン</a></div>
        <div class="footer-column"><strong>理解する</strong><a href="/faq/">よくある質問</a><a href="/guide/">フォーム営業ガイド</a><a href="/policy/">送信方針</a><a href="/stop/">送信停止・受信窓口</a></div>
        <div class="footer-column"><strong>会社・相談</strong><a href="/resources/#download">資料ダウンロード</a><a href="/contact/">導入相談</a><a href="/company/">運営会社</a><a href="/policy/#privacy">プライバシーポリシー</a></div>
      </div>
      <div class="footer-bottom"><span>© 2026 Contents X Inc.</span><span>フォーム営業を、判断できる情報から。</span></div>
    </div>
  </footer>`;

  function insertHeaderAndFooter() {
    document.querySelector('[data-site-header]')?.insertAdjacentHTML('afterbegin', header);
    document.querySelector('[data-site-footer]')?.insertAdjacentHTML('afterbegin', footer);
  }

  // The header is fixed, so its wrapper has to reserve the matching height.
  function initHeaderFit() {
    const siteHeader = document.querySelector('.site-header');

    // Fonts, scrollbars and text scaling differ by device, so the breakpoints alone
    // cannot promise the header row fits. Measure the row itself: fall back to the
    // short labels, then drop the header phone (the menu and floating bar keep it).
    const headerRow = siteHeader?.querySelector('.header-inner');
    const headerOverflows = () => {
      const limit = headerRow.getBoundingClientRect().right + 0.5;
      // The mobile menu is position: fixed and spans the screen; it is not in the row.
      return [...headerRow.children].some(el => el.getClientRects().length &&
        getComputedStyle(el).position !== 'fixed' && el.getBoundingClientRect().right > limit);
    };
    const fitHeader = () => {
      if (!headerRow) return;
      const root = document.documentElement;
      root.classList.remove('header-compact', 'header-no-tel');
      if (!headerOverflows()) return;
      root.classList.add('header-compact');
      if (headerOverflows()) root.classList.add('header-no-tel');
    };

    const syncHeaderHeight = () => {
      if (!siteHeader) return;
      fitHeader();
      const height = siteHeader.offsetHeight;
      if (height) document.documentElement.style.setProperty('--header-height', `${height}px`);
      keepFocusVisible();
    };
    syncHeaderHeight();
    window.addEventListener('load', syncHeaderHeight);
    if (siteHeader) onResize([siteHeader], syncHeaderHeight);
  }

  // Floating CTA on every page except the contact form, which already asks for
  // the same action. It appears once the hero CTA has scrolled out of reach.
  function initFloatingCta() {
    const ctaLink = (className, href, icon, labels) => {
      const link = document.createElement('a');
      link.className = className;
      link.href = href;
      link.append(icon);
      labels.forEach(({ text, className: labelClass }) => {
        const span = document.createElement('span');
        span.textContent = text;
        span.className = labelClass;
        link.append(span);
      });
      return link;
    };

    if (isPage('/contact/') || document.querySelector('.floating-cta')) return;

    const cta = document.createElement('aside');
    cta.className = 'floating-cta';
    cta.setAttribute('aria-label', 'お問い合わせ');
    cta.append(
      ctaLink('floating-cta-secondary', '/resources/#download',
        svgIcon(['M6 3h8l5 5v13a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1Z', 'M14 3v5h5']),
        [
          { text: '資料ダウンロード', className: 'floating-cta-label-long' },
          { text: '資料DL', className: 'floating-cta-label-short' }
        ]),
      ctaLink('floating-cta-primary', '/contact/',
        svgIcon(['M3 6h18v12H3z', 'm3 7 9 6 9-6']),
        [
          { text: '無料で相談する', className: 'floating-cta-label-long' },
          { text: '無料相談', className: 'floating-cta-label-short' }
        ]),
      ctaLink('floating-cta-tel', `tel:${TEL}`,
        svgIcon(['M22 16.92v3a2 2 0 0 1-2.18 2 19.8 19.8 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.8 19.8 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.13.96.36 1.9.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.91.34 1.85.57 2.81.7A2 2 0 0 1 22 16.92Z']),
        [
          { text: `電話で相談 ${TEL}`, className: 'floating-cta-label-long' },
          { text: '電話', className: 'floating-cta-label-short' }
        ])
    );
    // On /resources/ the download form is already on screen; a second way to it
    // would only compete with the form, as on the contact page.
    if (document.querySelector('[data-download-form]')) cta.querySelector('.floating-cta-secondary')?.remove();
    // The short "電話" label alone would not say what the link is for.
    cta.querySelector('.floating-cta-tel')?.setAttribute('aria-label', `電話で相談 ${TEL}`);

    // Visitors can tuck the bar away; its tab stays at the bottom edge to bring
    // it back. Remembered for the visit so the bar does not return on every page.
    const toggle = document.createElement('button');
    toggle.type = 'button';
    toggle.className = 'floating-cta-toggle';
    const toggleLabel = document.createElement('span');
    toggle.append(toggleLabel, svgIcon(['m6 9 6 6 6-6']));
    cta.append(toggle);
    const minimizedKey = 'bizform-floating-cta-minimized';
    const setMinimized = (minimized) => {
      cta.classList.toggle('is-minimized', minimized);
      toggle.setAttribute('aria-expanded', String(!minimized));
      toggleLabel.textContent = minimized ? 'お問い合わせ' : 'しまう';
    };
    try {
      setMinimized(sessionStorage.getItem(minimizedKey) === '1');
    } catch {
      setMinimized(false);
    }
    toggle.addEventListener('click', () => {
      const minimized = !cta.classList.contains('is-minimized');
      setMinimized(minimized);
      try {
        if (minimized) sessionStorage.setItem(minimizedKey, '1');
        else sessionStorage.removeItem(minimizedKey);
      } catch {
        // Storage blocked (private mode, site data off): the bar still toggles on this page.
      }
    });

    document.body.append(cta);
    document.body.classList.add('has-floating-cta');

    // Kept for one deploy: a page cached before it can pair this file with the old site.css,
    // which does not hide the short labels yet. The CSS does that now; delete this on the
    // next deploy.
    const shortLabels = cta.querySelectorAll('.floating-cta-label-short');
    const narrow = window.matchMedia('(max-width: 768px)');
    const syncLabel = () => shortLabels.forEach(label => { label.hidden = !narrow.matches; });
    syncLabel();
    narrow.addEventListener('change', syncLabel);

    // Reserve the bar's full height, tab included, even while hidden or tucked
    // away: focusing a link can scroll far enough to reveal it before the next frame.
    const syncCtaHeight = () => {
      document.documentElement.style.setProperty('--floating-cta-height', `${cta.offsetHeight + toggle.offsetHeight}px`);
      keepFocusVisible();
    };
    syncCtaHeight();
    onResize([cta, toggle], syncCtaHeight);

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

  // Native focus scrolling uses the root scroll padding where supported.
  // Correct the remaining occlusion without moving focus or horizontal scroll.
  function keepFocusVisible() {
    const target = document.activeElement;
    if (!(target instanceof HTMLElement) || !target.matches(':focus-visible') ||
        target.closest('.site-header, .floating-cta, .skip-link')) return;
    requestAnimationFrame(() => {
      if (document.activeElement !== target || document.body.classList.contains('nav-open')) return;
      const padding = getComputedStyle(document.documentElement);
      const top = parseFloat(padding.scrollPaddingTop) || 0;
      const bottom = window.innerHeight - (parseFloat(padding.scrollPaddingBottom) || 0);
      const rect = target.getBoundingClientRect();
      if (!rect.height || bottom <= top) return;
      // A tall scrollable table cannot fit entirely; keep its start visible.
      const end = rect.top + Math.min(rect.height, bottom - top);
      const delta = rect.top < top ? rect.top - top : end > bottom ? end - bottom : 0;
      if (delta) window.scrollBy({ top: delta, behavior: 'instant' });
    });
  }

  function initFocusVisibility() {
    document.addEventListener('focusin', keepFocusVisible);
    // Let resize observers and the browser's scroll restoration settle first.
    window.addEventListener('resize', () => requestAnimationFrame(keepFocusVisible));
  }

  function initMenu() {
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
  }

  // Keep wide reference material readable without widening the entire page.
  function initScrollHints() {
    const scrollRegions = [];
    const addScrollHint = (region, label) => {
      const hint = document.createElement('p');
      hint.className = 'table-scroll-hint';
      hint.textContent = '左右にスクロールして全体をご覧いただけます。';
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
    onResize(scrollRegions.map(item => item.region), () => scrollRegions.forEach(item => item.update()));
  }

  function initReveal() {
    const observer = 'IntersectionObserver' in window ? new IntersectionObserver((entries) => {
      entries.forEach(entry => { if (entry.isIntersecting) { entry.target.classList.add('visible'); observer.unobserve(entry.target); } });
    }, { threshold: .12 }) : null;
    document.querySelectorAll('.reveal').forEach(el => observer ? observer.observe(el) : el.classList.add('visible'));
  }

  insertHeaderAndFooter();
  initHeaderFit();
  initFloatingCta();
  initFocusVisibility();
  initMenu();
  initScrollHints();
  initReveal();
})();
