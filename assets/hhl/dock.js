// dock.js — on the home page the banner's logo shrinks into the menu bar's logo as the page scrolls.
// The bar's mark is the same logo in negative (its lattice square, and the wordmark in white); the banner logo's square
// lands on the bar's square. The banner logo swaps to a copy with a transparent ground when it starts to move, so no
// white panel slides onto the black bar, and the two cross-fade over the last part of the move.
// Only transform and opacity. Under reduced motion nothing moves: the bar shows its logo and the banner video stays still.
// Usage: HHDock({ logo, bar, video, moving: 'url of the transparent copy' })
(function () {
  window.HHDock = function ({ logo, bar, video, moving }) {
    const sq = bar.querySelector('.mark .sq');
    const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (reduce) {
      if (video) { video.removeAttribute('autoplay'); video.pause(); }
      bar.style.setProperty('--dock-in', '1');
      return;
    }
    const rest = logo.getAttribute('src');
    const SQUARE = 638 / 1220;                     // the logo's square is this share of the logo's width
    if (moving) new Image().src = moving;          // fetch the transparent copy before it is needed
    let r0, t, s = 1, D = 1, raf = 0;

    function measure() {
      logo.style.transform = logo.style.opacity = logo.style.visibility = '';
      const r = logo.getBoundingClientRect();
      r0 = { x: r.left, y: r.top + scrollY };      // where the logo sits when the page is at the top
      const b = sq.getBoundingClientRect();
      t = { x: b.left, y: b.top };                 // the bar is sticky at the top: its square never moves
      s = b.width / (r.width * SQUARE);
      D = Math.max(200, Math.min(r0.y - t.y, 480));
      update();
    }

    function update() {
      raf = 0;
      const p = Math.min(1, Math.max(0, scrollY / D));
      const q = p * p * (3 - 2 * p);
      const x = (t.x - r0.x) * q;
      const y = r0.y + (t.y - r0.y) * q - (r0.y - scrollY);   // the target, less where scrolling has already taken it
      logo.style.transform = q > 0 ? `translate(${x.toFixed(2)}px, ${y.toFixed(2)}px) scale(${Math.pow(s, q).toFixed(4)})` : '';
      const fade = q > 0.999 ? 1 : Math.min(1, Math.max(0, (q - 0.8) / 0.2));   // (1 - 0.8) / 0.2 is not exactly 1 in floating point
      logo.style.opacity = String(1 - fade);
      logo.style.visibility = fade >= 1 ? 'hidden' : '';     // docked: the bar's own logo has taken over
      bar.style.setProperty('--dock-in', fade.toFixed(3));
      const src = q > 0.02 && moving ? moving : rest;
      if (logo.getAttribute('src') !== src) logo.setAttribute('src', src);
    }

    addEventListener('scroll', () => { if (!raf) raf = requestAnimationFrame(update); }, { passive: true });
    let rt = 0;
    addEventListener('resize', () => { clearTimeout(rt); rt = setTimeout(measure, 120); });
    if (logo.complete) measure(); else logo.addEventListener('load', measure, { once: true });
  };
})();
