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
      </nav>
      <button class="menu-button" type="button" aria-label="メニューを開く" aria-controls="global-nav" aria-expanded="false"><span></span></button>
      <div class="header-actions">
        <a class="button button-secondary" href="${base}/resources/">資料を見る</a>
        <a class="button button-primary" href="${base}/contact/">無料で相談する</a>
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

const menuButton = document.querySelector('.menu-button');
const globalNav = document.querySelector('.global-nav');
menuButton?.addEventListener('click', () => {
  const open = menuButton.getAttribute('aria-expanded') !== 'true';
  menuButton.setAttribute('aria-expanded', String(open));
  menuButton.setAttribute('aria-label', open ? 'メニューを閉じる' : 'メニューを開く');
  globalNav?.classList.toggle('open', open);
  document.body.classList.toggle('nav-open', open);
});
globalNav?.querySelectorAll('a').forEach(link => link.addEventListener('click', () => {
  menuButton?.setAttribute('aria-expanded', 'false');
  globalNav.classList.remove('open');
  document.body.classList.remove('nav-open');
}));

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
