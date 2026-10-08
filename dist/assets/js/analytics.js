// GA4 is enabled only on the published site, so local previews are not counted.
(() => {
  if (window.location.hostname !== 'bizform.contentsx.jp') return;

  window.dataLayer = window.dataLayer || [];
  window.gtag = window.gtag || function () {
    window.dataLayer.push(arguments);
  };
  window.gtag('js', new Date());
  window.gtag('config', 'G-1CXY4Z85C6', {
    cookie_domain: 'bizform.contentsx.jp',
    allow_google_signals: false,
    allow_ad_personalization_signals: false
  });
})();
