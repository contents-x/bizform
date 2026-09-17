document.querySelectorAll('.faq-accordion details').forEach((details, index) => {
  const summary = details.querySelector('summary');
  const answer = details.querySelector('.faq-answer');
  if (!summary || !answer) return;

  const answerId = `faq-answer-${index + 1}`;
  answer.id = answerId;
  summary.setAttribute('aria-controls', answerId);
  summary.setAttribute('aria-expanded', String(details.open));

  if (!Element.prototype.animate || window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    details.addEventListener('toggle', () => summary.setAttribute('aria-expanded', String(details.open)));
    return;
  }

  let animation = null;

  const finish = (open) => {
    details.open = open;
    details.style.height = '';
    details.style.overflow = '';
    summary.setAttribute('aria-expanded', String(open));
    animation = null;
  };

  const expand = () => {
    details.open = true;
    summary.setAttribute('aria-expanded', 'true');
    const startHeight = summary.offsetHeight;
    const endHeight = details.offsetHeight;
    details.style.overflow = 'hidden';
    animation = details.animate(
      { height: [`${startHeight}px`, `${endHeight}px`] },
      { duration: 260, easing: 'cubic-bezier(.2,.7,.2,1)' }
    );
    animation.onfinish = () => finish(true);
    animation.oncancel = () => { animation = null; };
  };

  const collapse = () => {
    const startHeight = details.offsetHeight;
    const endHeight = summary.offsetHeight;
    details.style.overflow = 'hidden';
    animation = details.animate(
      { height: [`${startHeight}px`, `${endHeight}px`] },
      { duration: 220, easing: 'cubic-bezier(.4,0,.2,1)' }
    );
    animation.onfinish = () => finish(false);
    animation.oncancel = () => { animation = null; };
  };

  summary.addEventListener('click', (event) => {
    event.preventDefault();
    if (animation) animation.cancel();
    if (details.open) collapse();
    else expand();
  });
});
