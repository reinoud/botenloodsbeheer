// Sluit het hoofdmenu bij een klik erbuiten of Escape (BV-100, D1). Zonder dit script werkt het menu als disclosure.
const kop = () => document.querySelector('.dj-menu__kop[open]');
if (matchMedia('(min-width: 56.25rem)').matches) kop()?.removeAttribute('open');
document.addEventListener('click', e => document.querySelectorAll('.dj-menu__kop[open], .dj-menu[open]').forEach(d => d.contains(e.target) || d.removeAttribute('open')));
document.addEventListener('keydown', e => {
  const d = e.key === 'Escape' && (kop() || document.querySelector('.dj-menu[open]'));
  if (d) { d.removeAttribute('open'); d.querySelector('summary').focus(); }
});
