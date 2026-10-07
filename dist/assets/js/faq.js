// FAQ page (/faq/): each question opens and closes with a short height animation and
// keeps aria-expanded in step; with reduced motion it uses the native toggle.
// Wrapped in a function so nothing here becomes a global shared with the other scripts.
(() => {
  document.querySelectorAll('.faq-accordion details').forEach((details, index) => {
    const summary = details.querySelector('summary');
    const answer = details.querySelector('.faq-answer');
    if (!summary || !answer) return;

    const answerId = `faq-answer-${index + 1}`;
    answer.id = answerId;
    summary.setAttribute('aria-controls', answerId);
    // Follow every way a question opens or closes, including the browser's find in page.
    const syncExpanded = () => summary.setAttribute('aria-expanded', String(details.open));
    syncExpanded();
    details.addEventListener('toggle', syncExpanded);

    if (!Element.prototype.animate || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

    let animation = null;
    let closing = false;

    const animateHeight = (open, startHeight, endHeight, timing) => {
      closing = !open;
      details.style.overflow = 'hidden';
      const current = details.animate({ height: [`${startHeight}px`, `${endHeight}px`] }, timing);
      animation = current;
      current.onfinish = () => {
        if (animation !== current) return;
        details.open = open;
        details.style.overflow = '';
        animation = null;
        closing = false;
      };
    };

    summary.addEventListener('click', (event) => {
      event.preventDefault();
      // A click during an animation turns it around from the height reached so far.
      const opening = !details.open || closing;
      const reached = animation ? details.offsetHeight : null;
      if (animation) {
        animation.cancel();
        animation = null;
      }
      if (opening) {
        details.open = true;
        animateHeight(true, reached ?? summary.offsetHeight, details.offsetHeight,
          { duration: 260, easing: 'cubic-bezier(.2,.7,.2,1)' });
      } else {
        animateHeight(false, reached ?? details.offsetHeight, summary.offsetHeight,
          { duration: 220, easing: 'cubic-bezier(.4,0,.2,1)' });
      }
    });
  });
})();
