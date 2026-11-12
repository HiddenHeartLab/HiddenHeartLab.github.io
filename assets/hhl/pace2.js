// pace2.js — pace a patch of atrial tissue, drawn as a figure at screen resolution.
// The eikonal equation is solved on a grid (Dijkstra, 16 neighbours, anisotropic: faster along the fibres);
// every screen pixel then reads the activation time by bilinear interpolation, so the bands, the isochrones
// and the outline of the tissue stay sharp at any size. Colours follow the activation maps in the lab's papers.
// Usage: HHPace2(canvas, { onPace, onDone }) → { fibres(on) }
(function () {
  const hex = (h) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16));
  const MAGMA = ['#fcfdbf', '#fec488', '#fc8961', '#e85362', '#b73779', '#7b2382', '#3b0f70', '#0d0829', '#000004'].map(hex);
  const lut = new Uint8ClampedArray(256 * 3);
  for (let i = 0; i < 256; i++) {
    const x = (i / 255) * (MAGMA.length - 1), k = Math.min(MAGMA.length - 2, Math.floor(x)), f = x - k;
    for (let c = 0; c < 3; c++) lut[i * 3 + c] = MAGMA[k][c] + (MAGMA[k + 1][c] - MAGMA[k][c]) * f;
  }
  const STEN = [];
  for (let dy = -2; dy <= 2; dy++) for (let dx = -2; dx <= 2; dx++) {
    const a = Math.abs(dx), b = Math.abs(dy);
    if ((!a && !b) || (a === 2 && b === 2) || (a === 2 && b === 0) || (a === 0 && b === 2)) continue;
    STEN.push([dx, dy, Math.hypot(dx, dy)]);
  }

  window.HHPace2 = function (canvas, opt = {}) {
    const o = Object.assign({ cell: 3, sizeCm: 7, vf: 0.65, vn: 0.22, iso: 10, rest: [233, 233, 233], auto: [0.62, 0.42] }, opt);
    const ctx = canvas.getContext('2d');
    const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
    let W, H, dpr, PW, PH, NX, NY, h, mask, theta, T, Tmax = 0, img, pix, aIn, showFibres = false, raf = 0, src = null, marker = null;

    // the patch: a rounded wall with two vein openings; s > 0 inside, in units of the short side
    function shape(px, py, a) {
      const ex = 0.8 * Math.max(1, a), ey = 0.74;
      const phi = Math.atan2(py / ey, px / ex);
      const edge = 1 + 0.07 * Math.sin(3 * phi + 0.6) + 0.045 * Math.sin(5 * phi + 1.9);
      const r = Math.hypot(px / ex, py / ey) / edge;
      let s = (1 - r) * Math.min(ex, ey);
      s = Math.min(s, Math.hypot(px - ex * 0.42, py + ey * 0.18) - 0.13 * ey);
      s = Math.min(s, Math.hypot(px + ex * 0.36, py - ey * 0.26) - 0.1 * ey);
      return s;
    }
    const fibre = (u, v) => 0.95 * Math.sin(2.3 * u + 0.5) + 0.7 * Math.cos(2.1 * v + 1.1 * u) + 0.55 * Math.sin(3.1 * u * v + 0.2);

    function build() {
      const b = canvas.getBoundingClientRect();
      W = Math.max(60, b.width); H = Math.max(60, b.height); dpr = Math.min(2, devicePixelRatio || 1);
      PW = Math.round(W * dpr); PH = Math.round(H * dpr); canvas.width = PW; canvas.height = PH;
      NX = Math.round(W / o.cell); NY = Math.round(H / o.cell); h = (o.sizeCm / 100) / Math.max(NX, NY);
      const a = W / H;
      mask = new Uint8Array(NX * NY); theta = new Float32Array(NX * NY);
      for (let y = 0; y < NY; y++) for (let x = 0; x < NX; x++) {
        const u = (x + 0.5) / NX, v = (y + 0.5) / NY, k = y * NX + x;
        mask[k] = shape((u - 0.5) * 2 * a, (v - 0.5) * 2, a) > -0.012 ? 1 : 0;
        theta[k] = fibre(u, v);
      }
      // per-pixel coverage of the tissue, anti-aliased over one pixel
      aIn = new Float32Array(PW * PH);
      const px1 = 2 / PH;
      for (let y = 0; y < PH; y++) for (let x = 0; x < PW; x++) {
        const s = shape(((x + 0.5) / PW - 0.5) * 2 * a, ((y + 0.5) / PH - 0.5) * 2, a);
        aIn[y * PW + x] = Math.max(0, Math.min(1, s / px1 + 0.5));
      }
      img = ctx.createImageData(PW, PH); pix = img.data;
      T = new Float32Array(NX * NY).fill(Infinity); Tmax = 0;
    }

    function solve(sx, sy) {
      T.fill(Infinity);
      const N = NX * NY, cap = N * 6, heap = new Int32Array(cap), key = new Float32Array(cap);
      let n = 0;
      const push = (i, t) => { let c = n++; heap[c] = i; key[c] = t; while (c > 0) { const p = (c - 1) >> 1; if (key[p] <= key[c]) break; const hi = heap[p]; heap[p] = heap[c]; heap[c] = hi; const hk = key[p]; key[p] = key[c]; key[c] = hk; c = p; } };
      const s0 = sy * NX + sx; T[s0] = 0; push(s0, 0);
      const ivf2 = 1 / (o.vf * o.vf), ivn2 = 1 / (o.vn * o.vn);
      while (n > 0 && n < cap - 20) {
        const i = heap[0], t = key[0]; n--; heap[0] = heap[n]; key[0] = key[n];
        let c = 0; for (;;) { const l = 2 * c + 1, r = l + 1; let m = c; if (l < n && key[l] < key[m]) m = l; if (r < n && key[r] < key[m]) m = r; if (m === c) break; const hi = heap[m]; heap[m] = heap[c]; heap[c] = hi; const hk = key[m]; key[m] = key[c]; key[c] = hk; c = m; }
        if (t > T[i]) continue;
        const x = i % NX, y = (i / NX) | 0, cs = Math.cos(theta[i]), sn = Math.sin(theta[i]);
        for (let q = 0; q < STEN.length; q++) {
          const [dx, dy, len] = STEN[q], X = x + dx, Y = y + dy;
          if (X < 0 || Y < 0 || X >= NX || Y >= NY) continue;
          const j = Y * NX + X; if (!mask[j]) continue;
          const ux = dx / len, uy = dy / len, al = ux * cs + uy * sn, ac = -ux * sn + uy * cs;
          const nt = t + len * h * Math.sqrt(al * al * ivf2 + ac * ac * ivn2) * 1000;
          if (nt < T[j]) { T[j] = nt; push(j, nt); }
        }
      }
      Tmax = 0;
      for (let i = 0; i < N; i++) if (T[i] < Infinity && T[i] > Tmax) Tmax = T[i];
      for (let i = 0; i < N; i++) if (T[i] === Infinity) T[i] = Tmax * 1.02; // cells just outside the wall, for smooth edges
    }

    function paint(tNow) {
      const gx = NX / PW, gy = NY / PH, iso = o.iso, rest = o.rest;
      for (let y = 0; y < PH; y++) {
        let fy = (y + 0.5) * gy - 0.5; if (fy < 0) fy = 0; if (fy > NY - 1.001) fy = NY - 1.001;
        const y0 = fy | 0, wy = fy - y0, r0 = y0 * NX, r1 = r0 + NX;
        for (let x = 0; x < PW; x++) {
          const p = y * PW + x, a = aIn[p], q = p * 4;
          if (a <= 0) { pix[q + 3] = 0; continue; }
          let fx = (x + 0.5) * gx - 0.5; if (fx < 0) fx = 0; if (fx > NX - 1.001) fx = NX - 1.001;
          const x0 = fx | 0, wx = fx - x0;
          const t = (T[r0 + x0] * (1 - wx) + T[r0 + x0 + 1] * wx) * (1 - wy) + (T[r1 + x0] * (1 - wx) + T[r1 + x0 + 1] * wx) * wy;
          let R = rest[0], G = rest[1], B = rest[2];
          if (src && t <= tNow) {
            const li = Math.min(255, Math.max(0, Math.round((t / Math.max(1, Tmax)) * 255))) * 3;
            R = lut[li]; G = lut[li + 1]; B = lut[li + 2];
            const m = t % iso, d = Math.min(m, iso - m);
            if (d < 0.32 && t > 1) { R *= 0.72; G *= 0.72; B *= 0.72; }           // isochrones every 10 ms
            if (tNow < Tmax + 1 && tNow - t < 2.2) { R = 255; G = 255; B = 255; }  // the wavefront
          }
          pix[q] = R; pix[q + 1] = G; pix[q + 2] = B; pix[q + 3] = 255 * a;
        }
      }
      ctx.setTransform(1, 0, 0, 1, 0, 0);
      ctx.putImageData(img, 0, 0);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      if (showFibres) drawFibres();
      if (src) legend(Math.min(tNow, Tmax));
      if (marker && document.activeElement === canvas) {
        ctx.strokeStyle = '#121212'; ctx.lineWidth = 2;
        ctx.beginPath(); ctx.arc((marker[0] + 0.5) * W / NX, (marker[1] + 0.5) * H / NY, 10, 0, Math.PI * 2); ctx.stroke();
      }
    }

    function drawFibres() {
      const step = 18, L = 7, a = W / H;
      ctx.lineCap = 'round'; ctx.beginPath();
      for (let y = step / 2; y < H; y += step) for (let x = step / 2; x < W; x += step) {
        if (shape((x / W - 0.5) * 2 * a, (y / H - 0.5) * 2, a) < 0.02) continue;
        const th = fibre(x / W, y / H), c = Math.cos(th) * L, s = Math.sin(th) * L;
        ctx.moveTo(x - c, y - s); ctx.lineTo(x + c, y + s);
      }
      ctx.strokeStyle = 'rgba(18,18,18,0.85)'; ctx.lineWidth = 3.6; ctx.stroke();
      ctx.strokeStyle = '#ffffff'; ctx.lineWidth = 1.5; ctx.stroke();
    }

    function legend(tShown) {
      const bw = Math.min(200, W * 0.32), bh = 10, x0 = 20, y0 = H - 40;
      for (let i = 0; i < bw; i++) { const li = Math.round((i / (bw - 1)) * 255) * 3; ctx.fillStyle = `rgb(${lut[li]},${lut[li + 1]},${lut[li + 2]})`; ctx.fillRect(x0 + i, y0, 1.2, bh); }
      ctx.fillStyle = '#121212'; ctx.font = '500 13px "Red Hat Text", Arial, sans-serif'; ctx.textBaseline = 'top';
      ctx.textAlign = 'left'; ctx.fillText('0 ms', x0, y0 + bh + 6);
      ctx.textAlign = 'right'; ctx.fillText(Math.round(Tmax) + ' ms', x0 + bw, y0 + bh + 6);
      ctx.textAlign = 'left'; ctx.fillText('Activation time', x0, y0 - 19);
    }

    function nearest(x, y) {
      x = Math.max(0, Math.min(NX - 1, x)); y = Math.max(0, Math.min(NY - 1, y));
      for (let r = 0; r < Math.max(NX, NY); r++) for (let dy = -r; dy <= r; dy++) for (let dx = -r; dx <= r; dx++) {
        const X = x + dx, Y = y + dy;
        if (X >= 0 && Y >= 0 && X < NX && Y < NY && mask[Y * NX + X]) return [X, Y];
      }
      return null;
    }
    function pace(x, y, instant) {
      const p = nearest(x, y); if (!p) return;
      src = p; marker = p.slice(); solve(p[0], p[1]);
      if (opt.onPace) opt.onPace(Tmax);
      cancelAnimationFrame(raf);
      if (instant || reduce) { paint(Tmax + 5); if (opt.onDone) opt.onDone(Tmax); return; }
      const dur = Math.max(1100, Math.min(2200, Tmax * 11)), t0 = performance.now();
      const step = (now) => { const k = Math.min(1, (now - t0) / dur); paint(k * (Tmax + 3)); if (k < 1) raf = requestAnimationFrame(step); else if (opt.onDone) opt.onDone(Tmax); };
      raf = requestAnimationFrame(step);
    }

    canvas.addEventListener('pointerdown', (e) => {
      const b = canvas.getBoundingClientRect();
      pace(Math.floor(((e.clientX - b.left) / W) * NX), Math.floor(((e.clientY - b.top) / H) * NY));
    });
    canvas.addEventListener('keydown', (e) => {
      if (!marker) marker = nearest(Math.round(NX * o.auto[0]), Math.round(NY * o.auto[1]));
      const st = Math.round(24 / o.cell), mv = { ArrowLeft: [-st, 0], ArrowRight: [st, 0], ArrowUp: [0, -st], ArrowDown: [0, st] }[e.key];
      if (mv) { e.preventDefault(); const p = nearest(marker[0] + mv[0], marker[1] + mv[1]); if (p) marker = p; paint(Tmax + 5); return; }
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); pace(marker[0], marker[1]); }
    });
    canvas.addEventListener('focus', () => paint(Tmax + 5));
    canvas.addEventListener('blur', () => paint(Tmax + 5));

    build(); paint(-1);
    let started = false;
    new IntersectionObserver((es) => { if (!started && es[0].isIntersecting) { started = true; pace(Math.round(NX * o.auto[0]), Math.round(NY * o.auto[1])); } }, { threshold: 0.25 }).observe(canvas);
    let rt = 0, lastW = W;
    new ResizeObserver(() => { clearTimeout(rt); rt = setTimeout(() => {
      const b = canvas.getBoundingClientRect(); if (Math.abs(b.width - lastW) < 2) return; lastW = b.width;
      const rel = src ? [src[0] / NX, src[1] / NY] : null; build();
      if (rel) pace(Math.round(rel[0] * NX), Math.round(rel[1] * NY), true); else paint(-1);
    }, 150); }).observe(canvas);
    return { fibres(on) { showFibres = on; paint(Tmax + 5); } };
  };
})();
