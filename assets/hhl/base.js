// base.js — two small jobs shared by the pages: the scroll entrances and the pause button for looping media.

// 1. Entrances. An element marked data-enter="title" rises out of a mask and one marked data-enter="picture" opens
// downwards, once, when it scrolls into view (the styles are in base.css; running text never moves). The hidden
// states only exist under html.enter; the <head> drops that class when this script did not load, so nothing stays hidden.
window.HHEnter = true;
(() => {
  const targets = document.querySelectorAll('[data-enter]');
  if (!targets.length) return;
  const show = (el) => el.classList.add('is-in');
  if (!('IntersectionObserver' in window)) { targets.forEach(show); return; }
  const io = new IntersectionObserver((entries) => {
    for (const entry of entries) {
      if (!entry.isIntersecting) continue;
      show(entry.target);
      io.unobserve(entry.target);
    }
  }, { rootMargin: '0px 0px 140px 0px' });   // a title waits one line below its place, so it starts as its place reaches the screen
  targets.forEach((el) => io.observe(el));
  // safety net: anything on screen that the observer missed is shown a moment after the page has loaded
  addEventListener('load', () => setTimeout(() => {
    targets.forEach((el) => { const r = el.getBoundingClientRect(); if (r.top < innerHeight && r.bottom > 0) show(el); });
  }, 2500));
})();

// 2. The pause button for media that loops by itself.
// Any block marked data-motion="the figures" (the words finish the button's label) that holds autoplaying videos or
// animated images gets one button that stops and restarts all of them. An animated image is written as
//   <picture><source media="(prefers-reduced-motion: reduce)" srcset="still.jpg"><img src="moving.webp" data-still="still.jpg"></picture>
// so it already stands still for a visitor who asked for less motion, even before this script runs. With that setting
// on, videos start stopped too and the button reads "Play". The button goes into the block's [data-motion-slot] if it
// has one, otherwise at the end of the block.
(() => {
  const blocks = document.querySelectorAll('[data-motion]');
  if (!blocks.length) return;
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  blocks.forEach((block) => {
    const videos = [...block.querySelectorAll('video')];
    const images = [...block.querySelectorAll('img[data-still]')];
    if (!videos.length && !images.length) return;
    const what = block.dataset.motion || 'the animation';
    // from here on the script picks the picture, so the reduced-motion <source> steps aside
    images.forEach((im) => {
      im.dataset.moving = im.getAttribute('src');
      im.closest('picture')?.querySelectorAll('source').forEach((s) => s.remove());
    });
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'motion';
    let playing = true;
    function set(play) {
      playing = play;
      videos.forEach((v) => { if (play) v.play().catch(() => {}); else v.pause(); });
      images.forEach((im) => { im.src = play ? im.dataset.moving : im.dataset.still; });
      button.textContent = (play ? 'Pause ' : 'Play ') + what;
    }
    button.addEventListener('click', () => set(!playing));
    (block.querySelector('[data-motion-slot]') || block).appendChild(button);
    set(!reduce);
  });
})();
