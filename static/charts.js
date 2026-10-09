// 輕量圖表：細線條、單一基準線、hover 提示；顏色只承載資料身分，文字一律用中性色
// 讀目前主題的 CSS 變數（SVG 屬性不吃 var()，畫圖時先解析成實際色碼）
const cssVar = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();

const Charts = (() => {
  const NS = 'http://www.w3.org/2000/svg';
  const esc = (s) => String(s ?? '').replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const fmt = (v, d = 1, fixed = false) => (v == null || Number.isNaN(v) ? '—' : Number(v).toLocaleString('zh-TW', { maximumFractionDigits: d, minimumFractionDigits: fixed ? d : 0 }));

  function niceTicks(min, max, n = 4) {
    if (min === max) { max = min + 1; }
    const span = max - min;
    const step0 = span / n;
    const mag = 10 ** Math.floor(Math.log10(step0));
    const step = [1, 2, 2.5, 5, 10].map((m) => m * mag).find((s) => span / s <= n) || 10 * mag;
    const lo = Math.floor(min / step) * step;
    const hi = Math.ceil(max / step) * step;
    const ticks = [];
    for (let v = lo; v <= hi + step / 2; v += step) ticks.push(+v.toFixed(6));
    return ticks;
  }

  // 橫條：items [{label, value, highlight, bad, note, dim}]；signed 時以 0 為中線
  function hbars(items, opt = {}) {
    if (!items.length) return '<div class="empty">沒有資料</div>';
    const vals = items.map((i) => i.value ?? 0);
    const lo = opt.signed ? Math.min(0, ...vals) : 0;
    const hi = Math.max(opt.max ?? 0, ...vals, opt.ref?.value ?? 0, lo + 1e-6);
    const span = hi - lo;
    const pos = (v) => ((v - lo) / span) * 100;
    const zero = pos(0);
    const unit = opt.unit ?? '';
    return `<div class="hbars" style="--lw:${opt.labelWidth || 128}px">${items.map((it) => {
      const v = it.value ?? 0;
      const a = Math.min(zero, pos(v));
      const w = Math.max(Math.abs(pos(v) - zero), v === 0 ? 0 : 0.6);
      const cls = `${v < 0 ? 'neg' : 'pos'} ${it.bad ? 'bad' : it.highlight ? 'hl' : ''}`;
      const tip = `<b>${esc(it.label)}</b><br>${opt.signed && v > 0 ? '+' : ''}${fmt(v)}${esc(unit)}${it.note ? `<br><span class=tk>${esc(it.note)}</span>` : ''}`;
      return `<div class="hbar ${it.dim ? 'dim' : ''}" data-tip="${esc(tip)}">
        <div class="l" title="${esc(it.label)}">${esc(it.label)}</div>
        <div class="trk">${opt.signed ? `<span class="zero" style="left:${zero}%"></span>` : ''}
          <b class="${cls}" style="left:${a}%;width:${w}%"></b>
          ${opt.ref ? `<span class="ref" style="left:calc(${pos(opt.ref.value)}% - 1px)" data-tip="${esc(`${opt.ref.label}：${fmt(opt.ref.value)}${unit}`)}"></span>` : ''}
        </div>
        <div class="v">${opt.signed && v > 0 ? '+' : ''}${fmt(v, opt.digits ?? 1, opt.fixed)}${esc(opt.valueUnit ?? unit)}${it.note && opt.showNote ? `<small>${esc(it.note)}</small>` : ''}</div>
      </div>`;
    }).join('')}</div>`;
  }

  function el(tag, attrs = {}, parent) {
    const e = document.createElementNS(NS, tag);
    for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v);
    if (parent) parent.appendChild(e);
    return e;
  }

  function frame(host, height) {
    host.innerHTML = '';
    host.classList.add('chart');
    const W = Math.max(240, host.clientWidth || 480);
    const svg = el('svg', { width: W, height, viewBox: `0 0 ${W} ${height}` }, host);
    return { svg, W };
  }

  // 折線：spec {x: [...], series: [{name, color, values}], unit, height, digits}
  function line(host, spec) {
    const surface = cssVar('--surface');
    const H = spec.height || 200;
    const { svg, W } = frame(host, H);
    const m = { l: 36, r: spec.endLabels ? 64 : 14, t: 12, b: 26 };
    const all = spec.series.flatMap((s) => s.values).filter((v) => v != null);
    const lo0 = spec.yMin ?? Math.min(...all);
    const hi0 = Math.max(...all);
    const pad = (hi0 - lo0) * 0.12 || 1;
    const ticks = niceTicks(spec.yMin ?? lo0 - pad, hi0 + pad, 4);
    const lo = ticks[0]; const hi = ticks[ticks.length - 1];
    const n = spec.x.length;
    const X = (i) => m.l + (n === 1 ? (W - m.l - m.r) / 2 : (i * (W - m.l - m.r)) / (n - 1));
    const Y = (v) => m.t + (1 - (v - lo) / (hi - lo)) * (H - m.t - m.b);
    ticks.forEach((tv) => {
      el('line', { x1: m.l, x2: W - m.r, y1: Y(tv), y2: Y(tv), class: tv === lo ? 'axis-line' : 'grid-line' }, svg);
      const t = el('text', { x: m.l - 8, y: Y(tv) + 4, 'text-anchor': 'end', class: 'axis-text' }, svg);
      t.textContent = fmt(tv, 1);
    });
    spec.x.forEach((xv, i) => {
      const t = el('text', { x: X(i), y: H - 6, 'text-anchor': 'middle', class: 'axis-text' }, svg);
      t.textContent = xv;
    });
    spec.series.forEach((s) => {
      const pts = s.values.map((v, i) => (v == null ? null : [X(i), Y(v)]));
      let d = ''; let pen = false;
      pts.forEach((p) => { if (!p) { pen = false; return; } d += `${pen ? 'L' : 'M'}${p[0].toFixed(1)},${p[1].toFixed(1)}`; pen = true; });
      el('path', { d, fill: 'none', stroke: s.color, 'stroke-width': 2, 'stroke-linejoin': 'round', 'stroke-linecap': 'round' }, svg);
      const last = [...pts].reverse().find(Boolean);
      if (last) {
        el('circle', { cx: last[0], cy: last[1], r: 4, fill: s.color, stroke: surface, 'stroke-width': 2 }, svg);
        if (spec.endLabels) {
          const v = [...s.values].reverse().find((x) => x != null);
          const t = el('text', { x: last[0] + 9, y: last[1] + 4, class: 'lbl-text' }, svg);
          t.textContent = `${s.short ?? s.name}${s.short === '' ? '' : ' '}${fmt(v, spec.digits ?? 1)}${spec.endUnit || ''}`;
        }
      }
    });
    // hover：垂直準線 + 各系列數值
    const cross = el('line', { y1: m.t, y2: H - m.b, stroke: cssVar('--ink'), 'stroke-width': 1, opacity: 0 }, svg);
    const dots = spec.series.map((s) => el('circle', { r: 4, fill: s.color, stroke: surface, 'stroke-width': 2, opacity: 0 }, svg));
    const hit = el('rect', { x: m.l, y: 0, width: W - m.l - m.r, height: H, fill: 'transparent' }, svg);
    hit.addEventListener('mousemove', (e) => {
      const r = svg.getBoundingClientRect();
      const px = e.clientX - r.left;
      let i = Math.round(((px - m.l) / (W - m.l - m.r)) * (n - 1));
      i = Math.max(0, Math.min(n - 1, i));
      cross.setAttribute('x1', X(i)); cross.setAttribute('x2', X(i)); cross.setAttribute('opacity', 0.25);
      spec.series.forEach((s, k) => {
        const v = s.values[i];
        dots[k].setAttribute('opacity', v == null ? 0 : 1);
        if (v != null) { dots[k].setAttribute('cx', X(i)); dots[k].setAttribute('cy', Y(v)); }
      });
      const rows = spec.series.map((s) => `<span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:${s.color};margin-right:6px"></span>${esc(s.name)}　<b>${fmt(s.values[i], spec.digits ?? 1)}</b>${esc(spec.unit || '')}`).join('<br>');
      Tip.show(`<b>${esc(spec.x[i])}</b><br>${rows}`, e.clientX, e.clientY);
    });
    hit.addEventListener('mouseleave', () => { cross.setAttribute('opacity', 0); dots.forEach((d) => d.setAttribute('opacity', 0)); Tip.hide(); });
  }

  // 直條（例如 24 小時分布）：spec {x, values, unit, height, highlight: [index], color}
  function columns(host, spec) {
    const H = spec.height || 170;
    const { svg, W } = frame(host, H);
    const m = { l: 30, r: 6, t: 10, b: 24 };
    const n = spec.values.length;
    const ticks = niceTicks(0, Math.max(1, ...spec.values), 3);
    const hi = ticks[ticks.length - 1];
    const Y = (v) => m.t + (1 - v / hi) * (H - m.t - m.b);
    ticks.forEach((tv) => {
      el('line', { x1: m.l, x2: W - m.r, y1: Y(tv), y2: Y(tv), class: tv === 0 ? 'axis-line' : 'grid-line' }, svg);
      const t = el('text', { x: m.l - 7, y: Y(tv) + 4, 'text-anchor': 'end', class: 'axis-text' }, svg);
      t.textContent = fmt(tv, 0);
    });
    const band = (W - m.l - m.r) / n;
    const bw = Math.min(22, band - 2);
    const hl = new Set(spec.highlight || []);
    const brand = cssVar('--ok'); const neutral = cssVar('--neutral-bar');
    spec.values.forEach((v, i) => {
      const x = m.l + i * band + (band - bw) / 2;
      const y = Y(v); const h = Y(0) - y;
      const color = hl.size ? (hl.has(i) ? (spec.color || brand) : neutral) : (spec.color || brand);
      if (h > 0) {
        const r = Math.min(4, h, bw / 2);
        el('path', { d: `M${x},${Y(0)}V${y + r}Q${x},${y} ${x + r},${y}H${x + bw - r}Q${x + bw},${y} ${x + bw},${y + r}V${Y(0)}Z`, fill: color }, svg);
      }
      if (spec.xEvery == null || i % spec.xEvery === 0) {
        const t = el('text', { x: x + bw / 2, y: H - 6, 'text-anchor': 'middle', class: 'axis-text' }, svg);
        t.textContent = spec.x[i];
      }
      const hit = el('rect', { x: m.l + i * band, y: m.t, width: band, height: H - m.t - m.b, fill: 'transparent' }, svg);
      hit.addEventListener('mousemove', (e) => Tip.show(`<b>${esc(spec.tipX ? spec.tipX(i) : spec.x[i])}</b><br>${fmt(v, 1)} ${esc(spec.unit || '')}`, e.clientX, e.clientY));
      hit.addEventListener('mouseleave', () => Tip.hide());
    });
  }

  function sparkline(values, w = 72, h = 22, color = cssVar('--ok')) {
    const vs = values.filter((v) => v != null);
    if (vs.length < 2) return '';
    const lo = Math.min(...vs); const hi = Math.max(...vs);
    const X = (i) => 2 + (i * (w - 4)) / (values.length - 1);
    const Y = (v) => 2 + (1 - (v - lo) / (hi - lo || 1)) * (h - 4);
    let d = ''; let pen = false;
    values.forEach((v, i) => { if (v == null) { pen = false; return; } d += `${pen ? 'L' : 'M'}${X(i).toFixed(1)},${Y(v).toFixed(1)}`; pen = true; });
    const li = values.length - 1 - [...values].reverse().findIndex((v) => v != null);
    return `<svg width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" style="display:block;overflow:visible"><path d="${d}" fill="none" stroke="${cssVar('--faint')}" stroke-width="1.6" stroke-linejoin="round" stroke-linecap="round"/><circle cx="${X(li)}" cy="${Y(values[li])}" r="2.8" fill="${color}"/></svg>`;
  }

  return { hbars, line, columns, sparkline, fmt, esc };
})();

// 共用 hover 提示
const Tip = (() => {
  let node;
  const get = () => (node ||= document.getElementById('tip'));
  return {
    show(html, x, y) {
      const n = get();
      n.innerHTML = html;
      n.classList.add('on');
      const r = n.getBoundingClientRect();
      let left = x + 14; let top = y + 14;
      if (left + r.width > window.innerWidth - 8) left = x - r.width - 14;
      if (top + r.height > window.innerHeight - 8) top = y - r.height - 14;
      n.style.left = `${left}px`; n.style.top = `${top}px`;
    },
    hide() { get().classList.remove('on'); },
  };
})();

document.addEventListener('mouseover', (e) => {
  const t = e.target.closest('[data-tip]');
  if (!t) return;
  const move = (ev) => Tip.show(t.dataset.tip, ev.clientX, ev.clientY);
  move(e);
  t.addEventListener('mousemove', move);
  t.addEventListener('mouseleave', () => { Tip.hide(); t.removeEventListener('mousemove', move); }, { once: true });
});
