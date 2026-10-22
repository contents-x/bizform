// The two forms: 導入相談 (/contact/) and 資料ダウンロード (/resources/#download).
// Loaded after site.js on those two pages only, next to the CRM embed script.
// Wrapped in a function so nothing here becomes a global shared with the other scripts.
(() => {
  // The shared Contents X HubSpot form (also used by BizManga and ContentsX).
  const HUBSPOT_ENDPOINT = 'https://api.hsforms.com/submissions/v3/integration/submit/48367061/b6da14d0-d60d-4357-89fc-0015ed32b704';
  const formField = (data, name) => String(data.get(name) || '').trim();
  // The shared HubSpot form makes 部署 (busyo) required and refuses a blank value
  // (REQUIRED_FIELD, confirmed 2026-09-29), while both forms here leave it
  // optional. Send a placeholder instead of losing the submission.
  const hubspotDepartment = (data) => formField(data, 'busyo') || '未入力';
  // HubSpot names the failing field in its error body (field names only, no
  // visitor input); keep it in the console so a refusal can be diagnosed.
  const hubspotErrors = (res) => res.json()
    .then((body) => (body.errors || []).map((e) => e.message))
    .catch(() => []);

  // The tail HubSpot shows staff: which form, where the visitor came from, which page.
  const hubspotTrackingNote = (label) => {
    const params = new URLSearchParams(window.location.search);
    const lines = [label];
    [['utm_source', '流入元'], ['utm_medium', '媒体'], ['utm_campaign', 'キャンペーン']].forEach(([key, name]) => {
      const value = params.get(key);
      if (value) lines.push(`${name}: ${value}`);
    });
    lines.push(`ページ: ${window.location.href}`);
    return `---\n${lines.join('\n')}`;
  };

  // Both forms send the same fields to the shared HubSpot form; only the message and
  // the page name differ. The forms have one name field; the other Contents X sites
  // fill both HubSpot name properties with it, so do the same here.
  const hubspotPayload = (data, message, pageName) => {
    const name = formField(data, 'name');
    return {
      fields: [
        { name: 'company', value: formField(data, 'company') },
        { name: 'busyo', value: hubspotDepartment(data) },
        { name: 'lastname', value: name },
        { name: 'firstname', value: name },
        { name: 'email', value: formField(data, 'email') },
        { name: 'message', value: message }
      ],
      context: {
        pageUri: window.location.href,
        pageName
      }
    };
  };
  const postToHubSpot = (payload, signal) => fetch(HUBSPOT_ENDPOINT, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    signal
  });

  // Hand a form to the CRM embed script, which loads async (data-auto="false").
  // A visitor on a slow connection can submit before it arrives, so wait for it
  // rather than dropping the copy; the form keeps its values after it is hidden.
  // The script is external and unversioned: if it ever throws, the HubSpot send and
  // the download that follow must still run, so its call is guarded.
  const sendFormToCrm = (form) => {
    try {
      window.BizcarteInbound?.sendForm(form);
    } catch (err) {
      console.warn('CRM copy failed (ignored):', err);
    }
  };
  // One wait per form: a resend while the script is still loading must not queue a
  // second copy (each would send the form's latest values, so the CRM got two).
  const waitingForCrm = new Set();
  const copyToCrm = (form) => {
    if (window.BizcarteInbound) {
      sendFormToCrm(form);
      return;
    }
    if (waitingForCrm.has(form)) return;
    const script = document.querySelector('script[src*="/embed/inbound-v1.js"]');
    if (!script) return;
    waitingForCrm.add(form);
    script.addEventListener('load', () => {
      waitingForCrm.delete(form);
      sendFormToCrm(form);
    }, { once: true });
  };

  function initContactForm() {
    const contactForm = document.querySelector('[data-contact-form]');
    const contactSubmit = contactForm?.querySelector('[data-contact-submit]');
    if (!contactForm || !contactSubmit) return;

    // HubSpot is the system of record: its answer alone decides what the visitor
    // sees. The Contents X CRM inbox gets a copy through the CRM's embed script
    // (loaded on the contact page with data-auto="false"), whose call is guarded,
    // never waits for a reply and cannot block the HubSpot submission. Same
    // arrangement as BizManga, ContentsX and イチオシ採用 (README: 外部連携).
    const HUBSPOT_TIMEOUT_MS = 20000;

    // The TOP campaign links open the form with ?topic=campaign; start on that
    // topic so staff can tell the inquiry asks for the campaign discount.
    const presetTopic = new URLSearchParams(window.location.search).get('topic');
    contactForm.querySelectorAll('#topic option[data-topic]').forEach((option) => {
      if (option.dataset.topic === presetTopic) option.selected = true;
    });

    const complete = document.querySelector('[data-contact-complete]');
    const failures = {
      rejected: contactForm.querySelector('[data-contact-error="rejected"]'),
      unknown: contactForm.querySelector('[data-contact-error="unknown"]')
    };
    const submitLabel = contactSubmit.textContent;
    let submitting = false;
    // A refused or unconfirmed HubSpot send re-enables the button, and each
    // resend used to add the same inquiry to the CRM inbox again (two identical
    // rows on 2026-09-29). Copy each distinct set of answers only once; a
    // corrected resend still goes through as a new copy.
    let copiedToCrm = '';

    // An async function: a fetch wrapped by an extension or in-app browser can throw
    // before it returns a promise, and that must end as a failure the form reports,
    // not leave the button stuck on 送信中…. The timeout uses AbortController rather than
    // AbortSignal.timeout, which Safari only has from 16 (AbortController is in every
    // browser that can run this file).
    const sendToHubSpot = async (payload) => {
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), HUBSPOT_TIMEOUT_MS);
      try {
        const res = await postToHubSpot(payload, controller.signal);
        if (res.ok) return;
        const error = new Error(`HubSpot responded ${res.status}`);
        // A 4xx is a definite refusal (HubSpot validates before storing), so
        // nothing arrived and resending is safe. Anything else may have landed.
        error.rejected = res.status >= 400 && res.status < 500;
        error.details = await hubspotErrors(res);
        throw error;
      } finally {
        clearTimeout(timer);
      }
    };

    const showComplete = () => {
      contactForm.hidden = true;
      if (!complete) return;
      complete.hidden = false;
      complete.focus();
    };

    contactForm.addEventListener('submit', (event) => {
      event.preventDefault();
      // Enter in a field and requestSubmit() skip the disabled button, so the
      // form itself carries the in-flight flag.
      if (submitting) return;
      if (!contactForm.reportValidity()) return;
      submitting = true;
      contactSubmit.disabled = true;
      contactSubmit.textContent = '送信中…';
      Object.values(failures).forEach((el) => { if (el) el.hidden = true; });

      const data = new FormData(contactForm);
      const message = `【相談内容】${formField(data, 'topic') || '未選択'}\n\n${formField(data, 'message')}`;
      // Only bots fill the off-screen field. Pretend it worked and keep them out
      // of HubSpot; the embed script sends it as hp and the CRM drops that copy.
      const sending = formField(data, 'website') ? Promise.resolve() : sendToHubSpot(hubspotPayload(data,
        `${message}\n\n${hubspotTrackingNote('[ビズアプローチ経由のお問い合わせ]')}`,
        'ビズアプローチ - お問い合わせ'
      ));

      // CRM の受信箱へも送る（HubSpot の送信を始めてから。失敗しても受付・完了表示には影響しない）
      const answers = JSON.stringify([...data.entries()]);
      if (answers !== copiedToCrm) {
        copiedToCrm = answers;
        copyToCrm(contactForm);
      }

      sending.then(showComplete).catch((err) => {
        console.error('HubSpot submission error:', err, err?.details || []);
        submitting = false;
        contactSubmit.disabled = false;
        contactSubmit.textContent = submitLabel;
        // A lost response or a 5xx is not a lost submission. Asking for a retry
        // there would duplicate inquiries that did arrive, so that message points
        // to email; only a definite refusal asks the visitor to check and resend.
        const failure = err && err.rejected ? failures.rejected : failures.unknown;
        if (failure) {
          failure.hidden = false;
          failure.focus();
        }
      });
    });

    // Enable only after the handler is installed. method="dialog" keeps the
    // fields from being posted over HTTP when JavaScript fails to load.
    contactSubmit.disabled = false;
  }

  // Resource download (/resources/#download). The download starts as soon as the
  // form is valid; HubSpot and the CRM each get a copy, but neither reply is
  // awaited, so an outage on either side can never hold back the PDF.
  function initDownloadForm() {
    const downloadForm = document.querySelector('[data-download-form]');
    const downloadSubmit = downloadForm?.querySelector('[data-download-submit]');
    if (!downloadForm || !downloadSubmit) return;

    const fileUrl = downloadForm.dataset.downloadUrl;
    const documentName = downloadForm.dataset.crmDocument;
    const complete = document.querySelector('[data-download-complete]');
    const retryLink = complete?.querySelector('[data-download-link]');
    let sent = false;

    const startDownload = () => {
      const link = document.createElement('a');
      link.href = fileUrl;
      link.download = '';
      // Browsers that ignore download (some in-app browsers) open a new tab
      // instead of replacing this one, so the completion panel stays visible.
      link.target = '_blank';
      link.rel = 'noopener';
      document.body.append(link);
      link.click();
      link.remove();
    };

    // HubSpot is being retired, so this copy is fire-and-forget: a refusal only
    // leaves a console warning. The form has no message field, so the message
    // property carries what was downloaded (and the phone number, which is not
    // a field on the shared HubSpot form).
    // An async function, so a fetch wrapped by an extension or in-app browser that throws
    // at once still ends in the catch below and the PDF downloads.
    const copyToHubSpot = async (data) => {
      const lines = [`【資料ダウンロード】${documentName}`];
      const tel = formField(data, 'tel');
      if (tel) lines.push(`電話番号: ${tel}`);
      const res = await postToHubSpot(hubspotPayload(data,
        `${lines.join('\n')}\n\n${hubspotTrackingNote('[ビズアプローチ経由の資料ダウンロード]')}`,
        'ビズアプローチ - 資料ダウンロード'
      ));
      if (!res.ok) console.warn('HubSpot download copy refused (ignored):', res.status, await hubspotErrors(res));
    };

    downloadForm.addEventListener('submit', (event) => {
      event.preventDefault();
      // Enter in a field and requestSubmit() skip the disabled button.
      if (sent) return;
      if (!downloadForm.reportValidity()) return;
      sent = true;
      downloadSubmit.disabled = true;

      const data = new FormData(downloadForm);
      // Only bots fill the off-screen field; keep them out of HubSpot. The embed
      // script sends it as hp and the CRM drops that copy.
      if (!formField(data, 'website')) {
        copyToHubSpot(data).catch((err) => console.warn('HubSpot download copy failed (ignored):', err));
      }
      startDownload();
      // CRM の受信箱（資料DL）へも送る。ダウンロードを始めてから呼ぶので、失敗しても止めない
      copyToCrm(downloadForm);
      if (retryLink) retryLink.href = fileUrl;
      downloadForm.hidden = true;
      if (complete) {
        complete.hidden = false;
        complete.focus();
      }
    });

    // Enable only after the handler is installed. method="dialog" keeps the
    // fields from being posted over HTTP when JavaScript fails to load.
    downloadSubmit.disabled = false;
  }

  initContactForm();
  initDownloadForm();
})();
