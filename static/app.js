// HINO Pilot 車隊經營 AI 儀表板（原生 JS，無框架）
const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];
const { esc, fmt } = Charts;

// ---------------- 圖示（Lucide 風格） ----------------
const ICONS = {
  dashboard: '<rect x="3" y="3" width="7" height="9" rx="1.5"/><rect x="14" y="3" width="7" height="5" rx="1.5"/><rect x="14" y="12" width="7" height="9" rx="1.5"/><rect x="3" y="16" width="7" height="5" rx="1.5"/>',
  route: '<circle cx="6" cy="19" r="3"/><path d="M9 19h8.5a3.5 3.5 0 0 0 0-7h-11a3.5 3.5 0 0 1 0-7H15"/><circle cx="18" cy="5" r="3"/>',
  users: '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
  truck: '<path d="M14 18V6a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v11a1 1 0 0 0 1 1h2"/><path d="M15 18H9"/><path d="M19 18h2a1 1 0 0 0 1-1v-3.65a1 1 0 0 0-.22-.62l-3.48-4.35A1 1 0 0 0 17.52 8H14"/><circle cx="17" cy="18" r="2"/><circle cx="7" cy="18" r="2"/>',
  shield: '<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/><path d="m9 12 2 2 4-4"/>',
  sparkles: '<path d="M9.94 15.5A2 2 0 0 0 8.5 14.06l-6.14-1.58a.5.5 0 0 1 0-.96L8.5 9.94A2 2 0 0 0 9.94 8.5l1.58-6.14a.5.5 0 0 1 .96 0l1.58 6.14a2 2 0 0 0 1.44 1.44l6.14 1.58a.5.5 0 0 1 0 .96l-6.14 1.58a2 2 0 0 0-1.44 1.44l-1.58 6.14a.5.5 0 0 1-.96 0z"/>',
  bell: '<path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/>',
  play: '<polygon points="7 4 20 12 7 20 7 4"/>',
  pause: '<rect x="6" y="4" width="4" height="16" rx="1"/><rect x="14" y="4" width="4" height="16" rx="1"/>',
  send: '<path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/>',
  x: '<path d="M18 6 6 18"/><path d="m6 6 12 12"/>',
  chevron: '<path d="m9 18 6-6-6-6"/>',
  alert: '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"/><path d="M12 9v4"/><path d="M12 17h.01"/>',
  clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  fuel: '<path d="M3 22h12"/><path d="M4 9h10"/><path d="M14 22V4a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v18"/><path d="M14 13h2a2 2 0 0 1 2 2v2a2 2 0 0 0 4 0V9.83a2 2 0 0 0-.59-1.42L18 5"/>',
  message: '<path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z"/>',
  wrench: '<path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>',
  check: '<path d="M20 6 9 17l-5-5"/>',
  rotate: '<path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/>',
  moon: '<path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/>',
  sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="m6.34 17.66-1.41 1.41"/><path d="m19.07 4.93-1.41 1.41"/>',
  rain: '<path d="M4 14.9A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.24"/><path d="M16 14v6"/><path d="M8 14v6"/><path d="M12 16v6"/>',
  eye: '<path d="M2.06 12.35a1 1 0 0 1 0-.7 10.75 10.75 0 0 1 19.88 0 1 1 0 0 1 0 .7 10.75 10.75 0 0 1-19.88 0"/><circle cx="12" cy="12" r="3"/>',
  file: '<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M16 13H8"/><path d="M16 17H8"/><path d="M10 9H8"/>',
  sliders: '<path d="M4 21v-7"/><path d="M4 10V3"/><path d="M12 21v-9"/><path d="M12 8V3"/><path d="M20 21v-5"/><path d="M20 12V3"/><path d="M2 14h4"/><path d="M10 8h4"/><path d="M18 16h4"/>',
  phone: '<rect x="5" y="2" width="14" height="20" rx="2"/><path d="M12 18h.01"/>',
  arrow: '<path d="M5 12h14"/><path d="m12 5 7 7-7 7"/>',
  database: '<ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5v14a9 3 0 0 0 18 0V5"/><path d="M3 12a9 3 0 0 0 18 0"/>',
  info: '<circle cx="12" cy="12" r="9"/><path d="M12 16v-4"/><path d="M12 8h.01"/>',
};
const icon = (n, cls = '') => `<svg class="ic ${cls}" viewBox="0 0 24 24">${ICONS[n] || ''}</svg>`;
const TRUCK_SVG = '<svg viewBox="0 0 24 24"><path d="M3 16V7a1 1 0 0 1 1-1h9v10"/><path d="M13 9h4l3 3.5V16h-2"/><circle cx="7.5" cy="16.5" r="1.8"/><circle cx="16.5" cy="16.5" r="1.8"/></svg>';
function hydrateIcons(root = document) { $$('i[data-icon]', root).forEach((i) => { i.innerHTML = icon(i.dataset.icon); }); }

// ---------------- 狀態 ----------------
const S = {
  boot: null, t: 14 * 3600, page: 'home', playing: false, timer: null,
  live: null, overview: null, brief: null, seenAlerts: null,
  drivers: { period: null, rows: null, sel: null, weights: null },
  fleet: { period: 'all', series: 'all', rows: null, sel: null },
  safety: { tab: 'hours', period: null, data: null, sel: null },
  delivery: { filter: 'all', task: null, plate: null },
  feedFilter: 'all',
  ask: { history: [], busy: false },
};
const PAGES = {
  home: ['首頁總覽', '一個畫面看懂車隊、司機與配送現況；AI 主動指出問題、說明原因、建議下一步'],
  delivery: ['即時配送', '每台車的任務進度與預計到達時間；延誤風險高的任務標紅，一鍵通知客戶'],
  drivers: ['司機績效', '同車型、每百公里標準化的綜合分數：安全 40%｜節能 30%｜準時 20%｜合規 10%'],
  fleet: ['車隊績效', '每車油耗、怠速、成本與保養；油耗偏高時拆出多耗的油花在哪裡'],
  safety: ['安全與合規', '2026 工時新規即時檢查、疲勞與分心事件、客訴追蹤'],
};
// 車型識別色；跟著主題換（app.css 的 --s300/--s500/--s700）
const SERIES_COLOR = {};
const syncSeriesColor = () => ['300', '500', '700'].forEach((s) => { SERIES_COLOR[s] = cssVar(`--s${s}`); });
syncSeriesColor();
const SUB_LABEL = { safety: '安全', eco: '節能', ontime: '準時', compliance: '合規' };
const WEEK = '日一二三四五六';

// ---------------- 共用 ----------------
async function api(path, body) {
  const init = body !== undefined ? { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) } : {};
  const r = await fetch(path, init);
  if (!r.ok) throw new Error(`${r.status} ${path}`);
  return r.json();
}
const hhmm = (sec) => `${String(Math.floor(sec / 3600)).padStart(2, '0')}:${String(Math.floor((sec % 3600) / 60)).padStart(2, '0')}`;
const pct = (v, d = 0) => (v == null ? '—' : `${(v * 100).toFixed(d)}%`);
const ntd = (v) => (v == null ? '—' : `NT$${Math.round(v).toLocaleString('zh-TW')}`);
const md = (d) => d.slice(5).replace('-', '/');
const tier = (v) => (v < 60 ? 'low' : v < 75 ? 'mid' : '');
const avatarCls = (id) => `c${(parseInt(String(id).replace(/\D/g, ''), 10) % 6) + 1}`;
const surname = (name) => name?.[0] || '';
const mockTag = (txt = '模擬') => `<span class="tag mock" data-tip="${esc('競賽資料未提供，依 FAQ 規範以模擬資料補足，與原始資料分開存放')}">${txt}</span>`;
const realTag = (txt = 'iTRAQ 實際資料') => `<span class="src-dot" data-tip="${esc(`資料來源：${txt}`)}">${icon('database')}</span>`;
// 說明文字收進 ⓘ 提示，畫面只留重點
const infoTip = (text) => `<span class="info-tip" data-tip="${esc(text)}">${icon('info')}</span>`;
// 長段落收合：預設只看結論，需要時再展開
const more = (label, html) => `<details class="more"><summary>${esc(label)}${icon('chevron')}</summary><div class="more-bd">${html}</div></details>`;
// 「違反 2026 工時新規，每次罰鍰…」→「違反 2026 工時新規」
const short = (s) => String(s || '').split(/[，；（(]/)[0];
const aiTag = (mode) => {
  const live = mode === 'live';
  const label = live ? (S.boot?.ai.llm === 'gpt-6-luna' ? 'GPT-6 Luna' : S.boot?.ai.llm) : '規則模擬';
  return `<span class="tag ai" data-tip="${esc(live ? '由 LLM 依分析引擎算出的數字撰寫' : '未連線 LLM，使用規則模板')}">${icon('sparkles')}${esc(label)}</span>`;
};
function toast(msg) {
  const t = $('#toast');
  t.innerHTML = `${icon('check')}${esc(msg)}`;
  t.classList.add('on');
  clearTimeout(toast._t);
  toast._t = setTimeout(() => t.classList.remove('on'), 2600);
}
function skeleton(lines = 3) {
  return `<div style="display:flex;flex-direction:column;gap:10px">${Array.from({ length: lines }, (_, i) => `<div class="skel" style="width:${[92, 78, 85, 64, 70][i % 5]}%"></div>`).join('')}</div>`;
}
function mdLite(text) {
  const lines = esc(text || '').replace(/\*\*(.+?)\*\*/g, '<b>$1</b>').split('\n');
  let html = ''; let list = null;
  for (const raw of lines) {
    const ln = raw.trim();
    const ul = ln.match(/^[-•・]\s*(.+)/); const ol = ln.match(/^\d+[.、)]\s*(.+)/);
    if (ul || ol) {
      const tag = ul ? 'ul' : 'ol';
      if (list !== tag) { if (list) html += `</${list}>`; html += `<${tag}>`; list = tag; }
      html += `<li>${(ul || ol)[1]}</li>`;
    } else {
      if (list) { html += `</${list}>`; list = null; }
      if (ln) html += `<p>${ln}</p>`;
    }
  }
  if (list) html += `</${list}>`;
  return html;
}

// ---------------- 夜間模式 ----------------
function renderThemeBtn() {
  const dark = document.documentElement.dataset.theme === 'dark';
  const b = $('#btn-theme');
  b.innerHTML = icon(dark ? 'sun' : 'moon');
  b.title = dark ? '切換成日間模式' : '切換成夜間模式';
}
function toggleTheme() {
  const dark = document.documentElement.dataset.theme !== 'dark';
  if (dark) document.documentElement.dataset.theme = 'dark'; else delete document.documentElement.dataset.theme;
  try { localStorage.setItem('theme', dark ? 'dark' : 'light'); } catch { /* 私密視窗等情況存不了，只影響下次開啟 */ }
  syncSeriesColor();
  renderThemeBtn();
  drawSelection._key = null;   // 路線顏色寫在圖層上，要強制重畫
  renderPage(true);
}

// ---------------- 瀏覽器外框（Demo 展示用） ----------------
function renderFrameSwitch() {
  $('#frame-switch').setAttribute('aria-checked', String(document.documentElement.classList.contains('framed')));
}
function toggleFrame() {
  const on = document.documentElement.classList.toggle('framed');
  try { localStorage.setItem('frame', on ? 'on' : 'off'); } catch { /* 存不了只影響下次開啟 */ }
  renderFrameSwitch();
  window.dispatchEvent(new Event('resize'));   // 讓地圖與圖表依新尺寸重畫
}

// ---------------- AI 開關 ----------------
function renderAiStatus() {
  const ai = S.boot.ai;
  const name = ai.llm === 'gpt-6-luna' ? 'GPT-6 Luna' : ai.llm;
  $('#ai-dot').className = `dot ${ai.live ? 'ok' : 'warn'}`;
  $('#ai-label').textContent = ai.live ? `AI 已連線 · ${name}` : ai.configured ? 'AI 已關閉（規則模擬）' : 'AI 模擬模式（未設定 API key）';
  $('#ask-sub').textContent = `${ai.live ? name : '規則模擬'} · 查 iTRAQ 數據後回答`;
  const sw = $('#ai-switch');
  sw.setAttribute('aria-checked', String(ai.live));
  sw.disabled = !ai.configured;
  sw.dataset.tip = ai.configured ? (ai.live ? '關閉後改用規則模擬，不再呼叫 LLM、不消耗 token' : '開啟後由 LLM 產生內容（會消耗 token）') : '未設定 OPENAI_API_KEY，只能使用規則模擬';
}
async function toggleAi() {
  const sw = $('#ai-switch');
  sw.disabled = true;
  try {
    S.boot.ai = await api('/api/ai', { enabled: !S.boot.ai.live });
    toast(S.boot.ai.live ? 'AI 已開啟，新產生的內容會由 LLM 撰寫' : 'AI 已關閉，改用規則模擬，不會消耗 token');
  } finally {
    renderAiStatus();
  }
}

// ---------------- 啟動 ----------------
async function boot() {
  hydrateIcons();
  S.boot = await api('/api/bootstrap');
  S.drivers.period = S.boot.months[S.boot.months.length - 1];
  S.safety.period = S.drivers.period;
  $('#company-name').textContent = S.boot.company;
  $('#company-ava').textContent = S.boot.company[0];
  renderAiStatus();
  bindChrome();
  bindAsk();
  $('#ai-switch').addEventListener('click', toggleAi);
  renderThemeBtn();
  $('#btn-theme').addEventListener('click', toggleTheme);
  renderFrameSwitch();
  $('#frame-switch').addEventListener('click', toggleFrame);
  window.addEventListener('hashchange', route);
  await setT(S.t, { silent: true });
  route();
  api('/api/briefing').then((b) => {
    S.brief = b;
    if (S.page === 'home') { renderBrief(); if (S.overview) renderHomeKpi(); }
  }).catch(() => {});
}

function bindChrome() {
  $('#demo-range').addEventListener('input', (e) => { stopPlay(); setT(+e.target.value * 60); });
  $$('#demo-scenes button').forEach((b) => b.addEventListener('click', async () => {
    stopPlay();
    if (b.dataset.monthly) { location.hash = '#drivers'; openMonthly(); return; }
    await setT(+b.dataset.t * 60);
    if (b.dataset.go) location.hash = `#${b.dataset.go}`;
    if (b.dataset.go === 'home' && S.brief) setTimeout(() => openLinePreview('brief'), 350);
  }));
  $('#btn-play').addEventListener('click', () => (S.playing ? stopPlay() : startPlay()));
  $('#btn-reset').addEventListener('click', async () => {
    stopPlay();
    await api('/api/reset', {});
    S.delivery = { filter: 'all', task: null, plate: null };
    S.safety.sel = null; S.seenAlerts = null;
    S.ask.history = []; renderAskEmpty();
    await setT(14 * 3600);
    location.hash = '#home';
    toast('Demo 已重置');
  });
  $('#btn-ask').addEventListener('click', openAsk);
  $('#btn-bell').addEventListener('click', () => { location.hash = '#home'; setTimeout(() => $('#feed-card')?.scrollIntoView({ behavior: 'smooth', block: 'center' }), 80); });
  $('#scrim').addEventListener('click', closeAsk);
  $('#modal-wrap').addEventListener('click', (e) => { if (e.target.id === 'modal-wrap') closeModal(); });
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') { closeModal(); closeAsk(); } });
  window.addEventListener('resize', () => { clearTimeout(bindChrome._r); bindChrome._r = setTimeout(() => renderPage(true), 150); });
}

function route() {
  const page = (location.hash || '#home').slice(1).split('/')[0];
  S.page = PAGES[page] ? page : 'home';
  $$('#nav-list a').forEach((a) => a.classList.toggle('on', a.dataset.page === S.page));
  $$('.page').forEach((p) => p.classList.toggle('on', p.dataset.page === S.page));
  $('#page-title').textContent = PAGES[S.page][0];
  $('#page-title').title = PAGES[S.page][1];
  $('#bf-tab-page').textContent = $('#bf-url-page').textContent = PAGES[S.page][0];
  $('#main').scrollTop = 0;
  renderPage();
}
function goTo(page, ref) {
  if (page === 'drivers' && ref) S.drivers.sel = ref;
  if (page === 'fleet' && ref) S.fleet.sel = ref;
  if (page === 'delivery' && ref) { S.delivery.task = ref; S.delivery.filter = 'all'; }
  if (page === 'safety' && ref) {
    if (/^C\d+/.test(ref)) { S.safety.tab = 'complaints'; S.safety.sel = ref; } else { S.safety.tab = 'hours'; S.safety.hl = ref; }
  }
  if (location.hash === `#${page}`) route(); else location.hash = `#${page}`;
}
function renderPage(resize = false) {
  ({ home: renderHome, delivery: renderDelivery, drivers: renderDrivers, fleet: renderFleet, safety: renderSafety })[S.page]?.(resize);
}

// ---------------- 時間軸 ----------------
async function setT(sec, { silent = false } = {}) {
  S.t = Math.round(sec);
  const m = Math.round(S.t / 60);
  $('#demo-range').value = m;
  $('#demo-time').textContent = hhmm(S.t);
  const d = new Date(`${S.boot.today}T00:00:00`);
  $('#demo-date').textContent = `${S.boot.today.replaceAll('-', '/')}（${WEEK[d.getDay()]}）`;
  $('#top-clock').textContent = `${md(S.boot.today)}（${WEEK[d.getDay()]}）${hhmm(S.t)}`;
  $$('#demo-scenes button[data-t]').forEach((b) => b.classList.toggle('on', +b.dataset.t === m));
  const req = (setT._n = (setT._n || 0) + 1);
  const live = await api(`/api/live?t=${S.t}`);
  if (req !== setT._n) return;
  S.live = live;
  updateBadges();
  if (!silent) renderPage(false, true);
}
function startPlay() {
  S.playing = true;
  $('#btn-play').classList.add('on');
  $('#btn-play').innerHTML = icon('pause');
  S.timer = setInterval(() => {
    if (S.t >= 22 * 3600) { stopPlay(); return; }
    setT(S.t + 120);
  }, 700);
}
function stopPlay() {
  S.playing = false;
  clearInterval(S.timer);
  $('#btn-play').classList.remove('on');
  $('#btn-play').innerHTML = icon('play');
}
function updateBadges() {
  const k = S.live.kpi;
  const b = $('#nav-badge-delivery');
  b.hidden = !k.risk_high; b.textContent = k.risk_high;
  const hours = S.live.alerts.filter((a) => a.kind === 'hours' && a.level === 'high').length;
  const sb = $('#nav-badge-safety');
  sb.hidden = !hours; sb.textContent = hours;
  const recent = S.live.alerts.filter((a) => S.t - a.at <= 3600).length;
  $('#bell-count').hidden = !recent; $('#bell-count').textContent = recent;
  // 播放時有新提醒就跳通知
  const keys = new Set(S.live.alerts.map((a) => `${a.kind}|${a.plate}|${a.title}`));
  if (S.seenAlerts && S.playing) {
    const fresh = S.live.alerts.find((a) => !S.seenAlerts.has(`${a.kind}|${a.plate}|${a.title}`) && a.level === 'high');
    if (fresh) toast(`${fresh.time} ${fresh.title}`);
  }
  S.seenAlerts = keys;
}

// =====================================================================
// 首頁總覽
// =====================================================================
async function renderHome() {
  const el = $('#page-home');
  if (!el.dataset.built) {
    el.innerHTML = `
      <div class="card kpi-strip" id="home-kpi"></div>
      <div class="grid g-main mt">
        <div class="card brief" id="brief-card"></div>
        <div class="card" id="feed-card"></div>
      </div>
      <div class="grid g-3 mt">
        <div class="card"><div class="card-hd"><h3>各車型油耗趨勢</h3><span class="sub">L/100km</span>${infoTip('排除里程或油耗資料異常的車輛；資料為每月抽樣日')}<div class="right">${realTag()}</div></div>
          <div class="card-bd"><div class="legend" id="trend-legend"></div><div id="trend-fuel" class="mt" style="margin-top:10px"></div></div></div>
        <div class="card"><div class="card-hd"><h3>全隊怠速占比</h3>${infoTip('占引擎運轉時數；怠速每小時約耗油 1.2–2.3 公升（依車型）')}<div class="right">${realTag()}</div></div>
          <div class="card-bd"><div id="trend-idle"></div></div></div>
        <div class="card"><div class="card-hd"><h3>需要關心的司機</h3><span class="sub" id="att-sub"></span></div>
          <div class="card-bd" id="attention" style="padding-top:6px"></div></div>
      </div>`;
    el.dataset.built = '1';
  }
  renderBrief();
  const ov = await api(`/api/overview?t=${S.t}`);
  S.overview = ov;
  renderHomeKpi();
  renderFeed();
  renderHomeCharts();
  renderAttention();
}

function renderHomeKpi() {
  const k = S.live.kpi; const ov = S.overview;
  const p = ov.prev_day;
  const otPrev = S.brief?.prev_day?.on_time_rate;
  const done = k.tasks_total ? (k.tasks_done / k.tasks_total) * 100 : 0;
  $('#home-kpi').innerHTML = `
    <div class="kpi" data-tip="${esc(`車隊 ${k.vehicles_total} 台，${k.vehicles_total - k.vehicles_planned} 台今日未排班`)}"><div class="kpi-label">${icon('truck')}今日出車</div>
      <div class="kpi-value">${k.vehicles_out}<small>/ ${k.vehicles_planned} 台</small></div></div>
    <div class="kpi ${k.risk_high ? 'alert' : ''}" data-tip="${esc(`今日已行駛 ${fmt(k.km, 0)} km`)}"><div class="kpi-label">${icon('route')}配送進度 ${mockTag()}</div>
      <div class="kpi-value">${k.tasks_done}<small>/ ${k.tasks_total} 站</small>${k.risk_high ? `<span class="kpi-flag">${k.risk_high} 筆延誤</span>` : ''}</div>
      <div class="progress"><b style="width:${done}%"></b></div></div>
    <div class="kpi"><div class="kpi-label">${icon('clock')}今日準點率 ${mockTag()}</div>
      <div class="kpi-value">${k.on_time_rate == null ? '—' : pct(k.on_time_rate, 1)}${k.on_time_rate != null && otPrev != null ? deltaHtml((k.on_time_rate - otPrev) * 100, '%', true, 1) : ''}</div></div>
    <div class="kpi" data-tip="${esc(`${md(p.date)}：${fmt(p.fuel, 0)} 公升 · ${fmt(p.km, 0)} km · ${p.vehicles} 台出車`)}"><div class="kpi-label">${icon('fuel')}昨日油錢</div>
      <div class="kpi-value">${ntd(p.fuel_cost)}</div></div>`;
}
function deltaHtml(v, unit = '', upGood = true, d = 0) {
  if (v == null || Number.isNaN(v)) return '';
  const r = +v.toFixed(d);
  if (r === 0) return '<span class="delta flat">持平</span>';
  const good = (r > 0) === upGood;
  return `<span class="delta ${good ? 'good' : 'bad'}">${r > 0 ? '▲' : '▼'} ${Math.abs(r)}${unit}</span>`;
}

function renderBrief() {
  const el = $('#brief-card');
  if (!el) return;
  const b = S.brief;
  const hd = `<div class="card-hd"><span class="tag ai">${icon('sparkles')}AI 晨報</span>
      ${b ? '' : '<span class="sub">整理中</span>'}${b ? infoTip(`${b.summary.join('')}\n${b.data_note}`) : ''}
      <div class="right"><button class="btn sm" id="btn-brief-line" ${b ? '' : 'disabled'}>${icon('message')}LINE 預覽</button></div></div>`;
  if (!b) {
    el.innerHTML = `${hd}<div class="card-bd"><div class="thinking" style="margin-bottom:14px"><span class="spinner"></span>AI 正在整理今天的重點…</div>${skeleton(4)}</div>`;
    return;
  }
  const kindIcon = { hours: 'clock', delay: 'route', fuel: 'fuel', safety: 'shield', complaint: 'message', maintenance: 'wrench' };
  const kindTag = { hours: 'critical', delay: 'warning', fuel: 'brand', safety: 'warning', complaint: 'info', maintenance: '' };
  el.innerHTML = `${hd}<div class="card-bd">
    <div class="brief-sec first">今天先處理這 ${b.top.length} 件事</div>
    <div>${b.top.map((x, i) => `
      <div class="todo" data-tip="${esc(`${x.why}${x.action_text ? `\n→ ${x.action_text}` : ''}`)}">
        <div class="todo-n">${i + 1}</div>
        <div class="grow">
          <div class="todo-title">${esc(x.title)}</div>
          <span class="tag ${kindTag[x.kind]}">${icon(kindIcon[x.kind] || 'info')}${esc(short(x.impact))}</span>
        </div>
        <button class="btn sm ${i === 0 ? 'primary' : ''}" data-go="${x.action.page}" data-ref="${esc(x.action.ref || '')}">${esc(x.action.label)}${icon('chevron')}</button>
      </div>`).join('')}</div>
    ${b.others.length ? `<div class="brief-sec">其他提醒</div><div class="others">${b.others.map((x) => `
      <button class="other" data-go="${x.action.page}" data-ref="${esc(x.action.ref || '')}" data-tip="${esc(x.why)}">${icon(kindIcon[x.kind] || 'info')}<span class="grow ellipsis">${esc(x.title)}</span>${icon('chevron')}</button>`).join('')}</div>` : ''}
  </div>`;
  $$('[data-go]', el).forEach((btn) => btn.addEventListener('click', () => goTo(btn.dataset.go, btn.dataset.ref)));
  $('#btn-brief-line').addEventListener('click', () => openLinePreview('brief'));
}

const FEED_KINDS = { all: '全部', delay: '延誤', hours: '工時', dms: '疲勞分心', dtc: '故障碼' };
function renderFeed() {
  const el = $('#feed-card');
  if (!el) return;
  const alerts = S.live.alerts;
  const counts = Object.fromEntries(Object.keys(FEED_KINDS).map((k) => [k, k === 'all' ? alerts.length : alerts.filter((a) => a.kind === k).length]));
  const list = alerts.filter((a) => S.feedFilter === 'all' || a.kind === S.feedFilter);
  const ic = { delay: 'route', hours: 'clock', dms: 'eye', dtc: 'wrench' };
  const prevKeys = renderFeed._keys || new Set();
  el.innerHTML = `<div class="card-hd"><h3>即時提醒</h3><div class="right">${realTag('iTRAQ 事件')}</div></div>
    <div class="card-bd" style="padding-bottom:6px">
      <div class="chips" style="margin-bottom:6px">${Object.entries(FEED_KINDS).map(([k, v]) => `<button class="chip ${S.feedFilter === k ? 'on' : ''}" data-k="${k}">${v}<b>${counts[k]}</b></button>`).join('')}</div>
      <div class="feed">${list.length ? list.map((a) => {
        const key = `${a.kind}|${a.plate}|${a.title}`;
        return `<div class="feed-item ${prevKeys.size && !prevKeys.has(key) ? 'new' : ''}" data-kind="${a.kind}" data-plate="${esc(a.plate)}" data-task="${esc(a.task_id || '')}" data-tip="${esc(a.body)}">
          <div class="feed-ic ${a.level}">${icon(ic[a.kind] || 'alert')}</div>
          <div class="feed-title"><span class="ellipsis">${esc(a.title)}</span><span class="t">${a.time}</span></div>
        </div>`;
      }).join('') : '<div class="empty">目前沒有提醒</div>'}</div>
    </div>`;
  renderFeed._keys = new Set(alerts.map((a) => `${a.kind}|${a.plate}|${a.title}`));
  $$('.chip', el).forEach((c) => c.addEventListener('click', () => { S.feedFilter = c.dataset.k; renderFeed(); }));
  $$('.feed-item', el).forEach((it) => it.addEventListener('click', () => {
    const k = it.dataset.kind;
    if (k === 'delay') goTo('delivery', it.dataset.task);
    else if (k === 'dtc') goTo('fleet', it.dataset.plate);
    else goTo('safety', it.dataset.plate);
  }));
}

function renderHomeCharts() {
  const tr = S.overview.fleet_trend;
  const x = tr.map((r) => `${+r.month.slice(5)} 月`);
  const series = ['300', '500', '700'].map((s) => ({ name: `HINO ${s}`, short: s, color: SERIES_COLOR[s], values: tr.map((r) => r[s]) }));
  $('#trend-legend').innerHTML = series.map((s) => `<span><i style="background:${s.color}"></i>${s.name}</span>`).join('');
  Charts.line($('#trend-fuel'), { x, series, unit: ' L/100km', height: 190, endLabels: true });
  Charts.line($('#trend-idle'), { x, series: [{ name: '怠速占比', short: '', color: cssVar('--ok'), values: tr.map((r) => +(r.idle_share * 100).toFixed(1)) }], unit: '%', endUnit: '%', height: 218, endLabels: true });
}

function renderAttention() {
  const el = $('#attention');
  const ov = S.overview;
  $('#att-sub').textContent = `${ov.month_label.split('（')[0]} 分數下降最多`;
  el.innerHTML = ov.attention.map((a) => {
    return `<div class="person" data-id="${a.driver_id}">
      <div class="avatar ${avatarCls(a.driver_id)}">${esc(surname(a.name))}</div>
      <div class="grow"><div class="person-name">${esc(a.name)}</div>
        <div class="person-sub">${esc(a.plate)}</div></div>
      <div class="score-chg"><b>${a.score}</b>${deltaHtml(a.score - a.prev, ' 分', true)}</div>
    </div>`;
  }).join('') + `<button class="btn sm ghost" style="margin-top:8px" id="btn-all-drivers">查看全部司機績效${icon('chevron')}</button>`;
  $$('.person', el).forEach((p) => p.addEventListener('click', () => goTo('drivers', p.dataset.id)));
  $('#btn-all-drivers').addEventListener('click', () => goTo('drivers'));
}

// =====================================================================
// 即時配送
// =====================================================================
const MAP = { map: null, markers: {}, stops: null, routeDone: null, routeAhead: null, fitted: false };
const STATE_CLS = { 行駛中: 's-move', 卸貨中: 's-unload', 怠速: 's-idle', 停車中: 's-stop', 待出車: 's-wait', 已收車: 's-off' };

function renderDelivery() {
  const el = $('#page-delivery');
  if (!el.dataset.built) {
    el.innerHTML = `<div class="delivery">
      <div class="card map-card"><div id="map"></div>
        <div class="map-overlay" id="map-stats"></div>
        <div class="map-weather" id="map-weather"></div>
        <div class="map-legend">${Object.entries({ 行駛中: 's-move', 卸貨中: 's-unload', 怠速: 's-idle', 停車中: 's-stop', 待出車: 's-wait' }).map(([k, c]) => `<span><span class="vm ${c}" style="width:12px;height:12px;border-width:1.5px;box-shadow:none"></span>${k}</span>`).join('')}
          <span><span class="vm s-move risk" style="width:12px;height:12px;border-width:1.5px"></span>有延誤風險</span></div>
      </div>
      <div class="card panel" id="d-panel"></div>
    </div>`;
    el.dataset.built = '1';
  }
  initMap();
  updateMap();
  renderDeliveryPanel();
}

// 底圖：內政部國土測繪中心「臺灣通用電子地圖」淺色版（中文地名、免金鑰）
function baseLayer() {
  return L.tileLayer('https://wmts.nlsc.gov.tw/wmts/EMAP2/default/GoogleMapsCompatible/{z}/{y}/{x}', {
    attribution: '&copy; 內政部國土測繪中心', maxZoom: 18, minZoom: 6,
    updateWhenZooming: false, keepBuffer: 4,
  });
}

function initMap() {
  if (MAP.map || typeof L === 'undefined') return;
  MAP.map = L.map('map', { zoomControl: false, attributionControl: true, preferCanvas: true }).setView([23.9, 120.9], 8);
  // 時間軸推進時讓車輛滑動過去；縮放期間關掉，避免跟 Leaflet 的縮放動畫打架
  const box = MAP.map.getContainer();
  MAP.map.on('zoomstart', () => { MAP.zooming = true; box.classList.remove('glide'); });
  MAP.map.on('zoomend', () => { MAP.zooming = false; });
  L.control.zoom({ position: 'bottomright' }).addTo(MAP.map);
  baseLayer().addTo(MAP.map);
  MAP.stops = L.layerGroup().addTo(MAP.map);
  MAP.map.on('click', () => { if (S.delivery.plate || S.delivery.task) { S.delivery.plate = null; S.delivery.task = null; renderDelivery(); } });
}

function updateMap() {
  const live = S.live;
  const k = live.kpi;
  $('#map-stats').innerHTML = `
    <div class="map-stat"><div class="n">${k.vehicles_out}<span class="faint" style="font-size:13px;font-weight:500"> / ${k.vehicles_planned}</span></div><div class="l">出車中</div></div>
    <div class="map-stat"><div class="n">${k.tasks_done}<span class="faint" style="font-size:13px;font-weight:500"> / ${k.tasks_total}</span></div><div class="l">已送達 ${mockTag()}</div></div>
    <div class="map-stat ${k.risk_high ? 'bad' : ''}"><div class="n">${k.risk_high}</div><div class="l">延誤風險</div></div>`;
  const rain = S.boot && (S.t >= 14 * 3600 && S.t <= 17.5 * 3600);
  $('#map-weather').innerHTML = rain ? `${icon('rain')}台中 午後雷陣雨 14:00–17:30 ${mockTag('模擬天氣')}` : `${icon('rain')}各區天氣穩定 ${mockTag('模擬天氣')}`;
  if (!MAP.map) return;
  const riskPlates = new Set(live.tasks.filter((x) => x.risk === 'high').map((x) => x.plate));
  const bounds = [];
  if (MAP.fitted && !MAP.zooming) MAP.map.getContainer().classList.add('glide');
  live.vehicles.forEach((v) => {
    if (v.lat == null) return;
    bounds.push([v.lat, v.lon]);
    const cls = `vm ${STATE_CLS[v.state] || 's-stop'} ${riskPlates.has(v.plate) ? 'risk' : ''} ${S.delivery.plate === v.plate ? 'sel' : ''}`;
    const html = `<div class="${cls}">${TRUCK_SVG}</div>${S.delivery.plate === v.plate ? `<div class="vm-label">${esc(v.plate)}</div>` : ''}`;
    const tip = `<b>${esc(v.plate)}</b>｜${esc(v.driver)}<br>${esc(v.state)}${v.state === '行駛中' ? ` · ${v.speed} km/h` : ''}<br>今日駕駛 ${v.drive_h} h · 連續 ${v.cont_h} h<br>任務 ${v.tasks_done}/${v.tasks_total}`;
    const z = S.delivery.plate === v.plate ? 1000 : riskPlates.has(v.plate) ? 500 : 0;
    let m = MAP.markers[v.plate];
    if (!m) {
      m = L.marker([v.lat, v.lon], { icon: L.divIcon({ className: 'vm-wrap', html, iconSize: [30, 30], iconAnchor: [15, 15] }), zIndexOffset: z }).addTo(MAP.map);
      m.on('click', (e) => { L.DomEvent.stopPropagation(e); selectPlate(v.plate); });
      m.bindTooltip(tip, { className: 'vt', direction: 'top', offset: [0, -14] });
      Object.assign(m, { _html: html, _tip: tip, _z: z, _ll: `${v.lat},${v.lon}` });
      MAP.markers[v.plate] = m;
      return;
    }
    // 只動有變的部分；不再每次 setIcon 重建 DOM
    const ll = `${v.lat},${v.lon}`;
    if (m._ll !== ll) { m._ll = ll; m.setLatLng([v.lat, v.lon]); }
    if (m._html !== html) { m._html = html; m.getElement().innerHTML = html; }
    if (m._tip !== tip) { m._tip = tip; m.setTooltipContent(tip); }
    if (m._z !== z) { m._z = z; m.setZIndexOffset(z); }
  });
  if (!MAP.fitted && bounds.length) {
    MAP.map.invalidateSize();
    MAP.map.fitBounds(bounds, { padding: [70, 70] });
    MAP.fitted = true;
  }
  drawSelection();
}

async function drawSelection() {
  const plate = S.delivery.plate || (S.delivery.task && S.live.tasks.find((x) => x.id === S.delivery.task)?.plate);
  const req = (drawSelection._n = (drawSelection._n || 0) + 1);
  if (!plate) { MAP.stops.clearLayers(); drawSelection._key = null; return; }
  const r = await api(`/api/route/${plate}?t=${S.t}`);
  if (req !== drawSelection._n) return;
  // 路線與站點沒變就不重畫
  const tasks = S.live.tasks.filter((x) => x.plate === plate);
  const key = JSON.stringify([plate, S.delivery.task, r.done.length, r.ahead.length, r.done.at(-1), tasks.map((x) => [x.status, x.risk, x.eta, x.delay_min])]);
  if (key === drawSelection._key) return;
  drawSelection._key = key;
  MAP.stops.clearLayers();
  if (r.done.length > 1) L.polyline(r.done, { color: cssVar('--ok'), weight: 4, opacity: 0.9, lineJoin: 'round' }).addTo(MAP.stops);
  if (r.ahead.length > 1) L.polyline(r.ahead, { color: cssVar('--route-ahead'), weight: 3, opacity: 0.6, dashArray: '2 7', lineCap: 'round' }).addTo(MAP.stops);
  tasks.forEach((x) => {
    const cls = x.status === '已送達' ? 'done' : x.risk === 'high' ? 'risk' : '';
    const sel = S.delivery.task === x.id;
    const pin = L.marker([x.lat, x.lon], {
      icon: L.divIcon({ className: 'vm-wrap', html: `<div class="sm-pin ${cls}" style="${sel ? 'transform:scale(1.3);box-shadow:0 0 0 3px var(--pin-sel)' : ''}">${x.seq}</div>`, iconSize: [22, 22], iconAnchor: [11, 11] }),
      zIndexOffset: sel ? 900 : 100,
    }).addTo(MAP.stops);
    pin.bindTooltip(`<b>${x.seq}. ${esc(x.customer)}</b><br>預約 ${x.window_start}–${x.window_end}<br>${x.status === '已送達' ? `到達 ${x.arrived}` : `預計 ${x.eta}`}${x.delay_min > 0 && x.status !== '已送達' ? `（晚 ${x.delay_min} 分）` : ''}`, { className: 'vt', direction: 'top', offset: [0, -10] });
    pin.on('click', (e) => { L.DomEvent.stopPropagation(e); selectTask(x.id); });
  });
}

function selectPlate(plate) {
  S.delivery.plate = S.delivery.plate === plate && !S.delivery.task ? null : plate;
  S.delivery.task = null;
  const v = S.live.vehicles.find((x) => x.plate === plate);
  if (S.delivery.plate && v?.lat) MAP.map.flyTo([v.lat, v.lon], Math.max(MAP.map.getZoom(), 11), { duration: 0.6 });
  updateMap();
  renderDeliveryPanel();
  setTimeout(() => $(`#d-panel [data-group="${plate}"]`)?.scrollIntoView({ block: 'start', behavior: 'smooth' }), 50);
}
function selectTask(id) {
  S.delivery.task = id;
  const x = S.live.tasks.find((k) => k.id === id);
  if (x) S.delivery.plate = x.plate;
  if (x && MAP.map) MAP.map.flyTo([x.lat, x.lon], Math.max(MAP.map.getZoom(), 12), { duration: 0.6 });
  updateMap();
  renderDeliveryPanel();
}

function renderDeliveryPanel() {
  const el = $('#d-panel');
  if (S.delivery.task) { renderTaskDetail(el); return; }
  const tasks = S.live.tasks;
  const f = S.delivery.filter;
  const filt = (x) => f === 'all' || (f === 'risk' && ['high', 'medium'].includes(x.risk)) || (f === 'active' && ['配送中', '卸貨中', '待配送'].includes(x.status)) || (f === 'done' && x.status === '已送達');
  const counts = { all: tasks.length, risk: tasks.filter((x) => ['high', 'medium'].includes(x.risk)).length, active: tasks.filter((x) => x.status !== '已送達').length, done: tasks.filter((x) => x.status === '已送達').length };
  const groups = S.live.vehicles.filter((v) => v.tasks_total).map((v) => ({ v, items: tasks.filter((x) => x.plate === v.plate && filt(x)) })).filter((g) => g.items.length);
  groups.sort((a, b) => (S.delivery.plate === b.v.plate) - (S.delivery.plate === a.v.plate) || b.items.some((x) => x.risk === 'high') - a.items.some((x) => x.risk === 'high'));
  el.innerHTML = `<div class="panel-hd">
      <div class="row between"><div><b style="font-size:15px">今日配送任務</b> <span class="muted small">${md(S.boot.today)} · ${hhmm(S.t)}</span></div>${mockTag('任務與客戶為模擬')}</div>
      <div class="seg" id="d-filter">${Object.entries({ all: '全部', risk: '延誤風險', active: '未完成', done: '已送達' }).map(([k, v]) => `<button class="${f === k ? 'on' : ''}" data-f="${k}">${v} <span class="faint">${counts[k]}</span></button>`).join('')}</div>
    </div>
    <div class="panel-bd">${groups.length ? groups.map(({ v, items }) => `
      <div class="group-hd" data-group="${v.plate}"><span class="s-dot s-${v.type}"></span><b>${esc(v.plate)}</b>${esc(v.driver)}<span class="tag" style="height:19px;font-size:11px">${esc(v.state)}</span><span class="right">${v.tasks_done}/${v.tasks_total} 站</span></div>
      ${items.map((x) => taskRow(x)).join('')}`).join('') : '<div class="empty">沒有符合的任務</div>'}</div>`;
  $$('#d-filter button', el).forEach((b) => b.addEventListener('click', () => { S.delivery.filter = b.dataset.f; renderDeliveryPanel(); }));
  $$('.task', el).forEach((r) => r.addEventListener('click', () => selectTask(r.dataset.id)));
  $$('.group-hd', el).forEach((g) => g.addEventListener('click', () => selectPlate(g.dataset.group)));
}
function taskRow(x) {
  const done = x.status === '已送達';
  const late = x.delay_min > 0;
  const pinCls = done ? 'done' : x.risk === 'high' ? 'risk' : '';
  return `<div class="task" data-id="${x.id}">
    <div class="task-seq"><div class="sm-pin ${pinCls}" style="box-shadow:none">${x.seq}</div></div>
    <div><div class="task-name">${esc(x.customer)}</div>
      <div class="task-sub">${esc(x.district)} · 預約 ${x.window_start}–${x.window_end}${x.notified ? ` · <span style="color:var(--ok-700)">已通知 ${x.notified}</span>` : ''}</div></div>
    <div class="task-eta">${done ? `<b class="${late ? 'late' : ''}">${x.arrived}</b><small>${late ? `遲到 ${x.delay_min} 分` : '準時送達'}</small>`
      : `<b class="${x.risk === 'high' ? 'late' : ''}">${x.eta}</b><small>${x.status === '卸貨中' ? '卸貨中' : x.risk === 'high' ? `預計晚 ${x.delay_min} 分` : x.risk === 'medium' ? `可能晚 ${x.delay_min} 分` : '預計準時'}</small>`}</div>
  </div>`;
}

async function renderTaskDetail(el) {
  const x = S.live.tasks.find((k) => k.id === S.delivery.task);
  if (!x) { S.delivery.task = null; renderDeliveryPanel(); return; }
  const done = x.status === '已送達';
  const p = x.pred;
  const risky = !done && x.risk === 'high';
  const v = S.live.vehicles.find((k) => k.plate === x.plate);
  const featTxt = p ? {
    remaining_km: `${p.features.remaining_km} km`, hist_speed: `${p.features.hist_speed} km/h`, hour: `${p.features.hour} 點出發`,
    rain: p.rain ? p.rain : '無', urban: p.features.urban ? '是' : '否', vehicle_type: `HINO ${p.features.vehicle_type}`, weekday: '星期五',
  } : {};
  const maxAbs = p ? Math.max(...p.factors.filter((f) => f.key !== 'remaining_km').map((f) => Math.abs(f.minutes)), 1) : 1;
  el.innerHTML = `<div class="panel-hd"><div class="row between"><button class="back" id="t-back">${icon('chevron')}全部任務</button>${mockTag('任務與客戶為模擬')}</div></div>
  <div class="panel-bd">
    <div class="detail-sec">
      <div class="row" style="gap:10px;align-items:flex-start">
        <div class="sm-pin ${done ? 'done' : risky ? 'risk' : ''}" style="margin-top:2px">${x.seq}</div>
        <div class="grow"><div style="font-size:16px;font-weight:600">${esc(x.customer)}</div>
          <div class="muted small" data-tip="${esc(`${x.cargo} · 聯絡人 ${x.contact}`)}">${esc(x.city)}${esc(x.district)}</div></div>
        <span class="tag ${done ? '' : risky ? 'critical' : 'brand'}">${esc(x.status)}</span>
      </div>
      <div class="eta-hero" style="margin-top:16px">
        <div><div class="muted small">${done ? '實際到達' : '預計到達（ETA）'}</div><div class="n ${x.delay_min > 0 ? 'late' : ''}">${done ? x.arrived : x.eta}</div></div>
        <div style="padding-bottom:4px"><div class="muted small">預約時段</div><div style="font-weight:600;font-size:15px" class="num">${x.window_start}–${x.window_end}</div></div>
        <div style="padding-bottom:4px;margin-left:auto">${x.delay_min > 0 ? `<span class="tag critical">${done ? '遲到' : '預計晚'} ${x.delay_min} 分</span>` : `<span class="tag brand">${done ? '準時' : '預計準時'}</span>`}</div>
      </div>
      <div class="kv-list" style="margin-top:14px">
        <span>車輛／司機</span><b>${esc(x.plate)}｜${esc(x.driver)}</b>
        <span>目前狀態</span><b>${esc(v?.state || '—')}${v?.state === '行駛中' ? ` · ${v.speed} km/h` : ''}</b>
      </div>
    </div>
    ${p ? `<div class="detail-sec">
      <div class="sec-title">${icon('sparkles')}為什麼會晚${infoTip(`LightGBM 預測、SHAP 貢獻值：距離以外的因素讓時間增加或減少多少。模型以模擬的歷史配送紀錄訓練（${S.boot.eta_model.n_train.toLocaleString()} 筆），時段車速參考 iTRAQ 真實資料`)}<span class="right muted small">剩 ${p.leg_km} km · 約 ${p.leg_minutes} 分</span></div>
      <div class="factors">${p.factors.filter((f) => f.key !== 'remaining_km' && Math.abs(f.minutes) >= 1).map((f) => {
        const w = (Math.abs(f.minutes) / maxAbs) * 50;
        const up = f.minutes > 0;
        return `<div class="factor"><div class="l">${esc(f.name)}<small>${esc(featTxt[f.key] || '')}</small></div>
          <div class="trk"><b class="${up ? 'up' : 'down'}" style="width:${w}%"></b></div>
          <div class="v ${up ? 'up' : 'down'}">${up ? '+' : '−'}${Math.abs(f.minutes).toFixed(1)} 分</div></div>`;
      }).join('')}</div>
    </div>` : ''}
    ${!done ? `<div class="detail-sec">
      ${risky ? `<div class="callout critical" style="margin-bottom:12px">${icon('alert')}<div>預計晚 <b>${x.delay_min} 分</b>，建議現在通知客戶</div></div>` : ''}
      ${x.notified ? `<button class="btn done" style="width:100%">${icon('check')}已於 ${x.notified} 通知客戶</button>`
        : `<button class="btn ${risky ? 'primary' : ''}" style="width:100%" id="t-notify">${icon('sparkles')}AI 擬客戶通知</button>`}
    </div>` : ''}
  </div>`;
  $('#t-back').addEventListener('click', () => { S.delivery.task = null; drawSelection(); renderDeliveryPanel(); });
  $('#t-notify')?.addEventListener('click', () => openNotice(x.id));
}

async function openNotice(taskId) {
  openModal(`<div class="modal-hd"><div class="grow"><h3>客戶延誤通知</h3><div class="sub">AI 依預測到達時間擬稿，可直接修改</div></div><button class="icon-btn ghost" data-close>${icon('x')}</button></div>
    <div class="modal-bd" id="notice-bd"><div class="thinking"><span class="spinner"></span>AI 正在擬稿…</div></div>
    <div class="modal-ft"><span class="left">LINE 推播為模擬，不會真的送出</span><button class="btn ghost" data-close>取消</button><button class="btn line" id="notice-send" disabled>${icon('send')}以 LINE 發送</button></div>`);
  const r = await api('/api/notice', { task_id: taskId, t: S.t });
  $('#notice-bd').innerHTML = `<div class="line-phone">
      <div class="line-top"><span class="line-badge">LINE</span>${esc(S.boot.company)} → ${esc(r.task.customer)}</div>
      <div class="line-chat"><div class="line-time">今天 ${hhmm(S.t)}</div>
        <div class="line-msg"><div class="line-ava">${TRUCK_SVG}</div><div class="grow"><div class="line-name">${esc(S.boot.company)}</div>
          <div class="line-bubble"><textarea class="line-edit" id="notice-text" rows="6">${esc(r.message)}</textarea></div></div></div>
      </div></div>
    <div class="row" style="margin-top:12px;justify-content:space-between">${aiTag(r.mode)}<span class="muted small">預計 ${r.task.eta} 到達 · 原約 ${r.task.window_end} 前</span></div>`;
  const ta = $('#notice-text');
  ta.style.height = `${ta.scrollHeight}px`;
  $('#notice-send').disabled = false;
  $('#notice-send').addEventListener('click', async () => {
    await api('/api/notice/send', { task_id: taskId, t: S.t });
    closeModal();
    toast(`已透過 LINE 通知 ${r.task.customer}`);
    await setT(S.t);
  });
}

// =====================================================================
// 司機績效
// =====================================================================
function periodSeg(id, current, withAll = true) {
  return `<div class="seg" id="${id}">${S.boot.periods.filter((p) => withAll || p.id !== 'all').map((p) => `<button class="${p.id === current ? 'on' : ''}" data-p="${p.id}" data-tip="${esc(p.full)}">${p.label}</button>`).join('')}</div>`;
}
function weightsQuery() {
  const w = S.drivers.weights;
  return w ? `&w=${[w.safety, w.eco, w.ontime, w.compliance].join(',')}` : '';
}

async function renderDrivers() {
  const el = $('#page-drivers');
  const P = S.drivers.period;
  const pl = S.boot.periods.find((p) => p.id === P);
  el.innerHTML = `<div class="toolbar">${periodSeg('dr-period', P)}<span class="toolbar-label">${esc(pl.full)}</span><span class="spacer"></span>
      <div style="position:relative"><button class="btn" id="btn-weights">${icon('sliders')}調整權重</button></div>
      <button class="btn dark" id="btn-monthly">${icon('file')}AI 月報與獎金建議</button></div>
    <div class="grid g-side"><div class="card" id="dr-table"><div class="card-bd">${skeleton(8)}</div></div><div class="card detail" id="dr-detail"></div></div>`;
  $$('#dr-period button').forEach((b) => b.addEventListener('click', () => { S.drivers.period = b.dataset.p; renderDrivers(); }));
  $('#btn-monthly').addEventListener('click', () => openMonthly());
  $('#btn-weights').addEventListener('click', toggleWeights);
  const d = await api(`/api/drivers?period=${P}${weightsQuery()}`);
  S.drivers.rows = d.rows;
  if (!S.drivers.sel || !d.rows.find((r) => r.driver_id === S.drivers.sel)) S.drivers.sel = d.rows.reduce((a, r) => (r.prev && (!a || (r.score - r.prev.score) < (a.score - a.prev.score)) ? r : a), null)?.driver_id || d.rows[0]?.driver_id;
  renderDriverTable();
  renderDriverDetail();
}

function renderDriverTable() {
  const rows = S.drivers.rows;
  const w = S.drivers.weights || S.boot.weights;
  const prevLabel = rows.find((r) => r.prev)?.prev?.period;
  $('#dr-table').innerHTML = `<div class="card-hd"><h3>司機綜合排名</h3><span class="sub">${rows.length} 位</span>${infoTip('一車一位主要駕駛。安全與節能以同車型中位數、每百公里（DMS 為每駕駛小時）標準化，安全分數另對照該車自身歷史。* 未裝 DMS（HINO 300），安全分數不含疲勞分心')}<div class="right">${mockTag('駕駛姓名與準時率為模擬')}</div></div>
  <div class="card-bd" style="padding:12px 8px 8px"><div class="table-wrap"><table class="t dense">
    <thead><tr><th class="c">#</th><th>司機</th><th>綜合分數</th><th class="c">安全<small>${w.safety}%</small></th><th class="c">節能<small>${w.eco}%</small></th><th class="c">準時<small>${w.ontime}%</small></th><th class="c">合規<small>${w.compliance}%</small></th><th class="r">${prevLabel ? `較 ${+prevLabel.slice(5)} 月` : '較上期'}</th></tr></thead>
    <tbody>${rows.map((r) => `<tr data-id="${r.driver_id}" class="${S.drivers.sel === r.driver_id ? 'sel' : ''}">
      <td class="c"><span class="rank ${r.rank <= 3 ? 'top' : ''}">${r.rank}</span></td>
      <td><div class="row" style="gap:10px"><div class="avatar sm ${avatarCls(r.driver_id)}">${esc(surname(r.name))}</div><div><div class="cell-main">${esc(r.name)}</div><div class="cell-sub"><span class="s-dot s-${r.type}"></span> ${esc(r.plate)} · ${r.type}</div></div></div></td>
      <td><div class="score-cell"><span class="score-num">${r.score}</span><div class="score-bar"><b class="${tier(r.score)}" style="width:${r.score}%"></b></div></div></td>
      ${['safety', 'eco', 'ontime', 'compliance'].map((k) => `<td class="c"><span class="sub-score ${tier(r.sub[k])}" ${k === 'safety' && !r.has_dms ? 'data-tip="此車未裝 DMS，安全分數只看急加減速、超速與 ADAS"' : ''}>${r.sub[k]}${k === 'safety' && !r.has_dms ? '<sup class="faint">*</sup>' : ''}</span></td>`).join('')}
      <td class="r">${r.prev ? deltaHtml(r.score - r.prev.score, '', true) : '<span class="faint">—</span>'}</td>
    </tr>`).join('')}</tbody></table></div>
    </div>`;
  $$('#dr-table tbody tr').forEach((tr) => tr.addEventListener('click', () => { S.drivers.sel = tr.dataset.id; $$('#dr-table tbody tr').forEach((x) => x.classList.toggle('sel', x === tr)); renderDriverDetail(); }));
}

async function renderDriverDetail() {
  const el = $('#dr-detail');
  const id = S.drivers.sel;
  if (!id) { el.innerHTML = ''; return; }
  el.innerHTML = `<div class="detail-sec">${skeleton(6)}</div>`;
  const d = await api(`/api/drivers/${id}?period=${S.drivers.period}${weightsQuery()}`);
  if (S.drivers.sel !== id) return;
  const r = d.row; const dv = d.driver;
  if (!r) { el.innerHTML = `<div class="detail-hd"><div class="avatar lg ${avatarCls(id)}">${esc(surname(dv.name))}</div><div><h3>${esc(dv.name)}</h3><div class="muted small">${esc(dv.plate)}</div></div></div><div class="empty">此期間沒有行駛資料</div>`; return; }
  const m = r.metrics;
  const cmp = (v, base, upBad = true, unit = '', d1 = 1) => {
    if (v == null) return '<b class="faint">—</b>';
    const bad = base != null && (upBad ? v > base * 1.1 : v < base * 0.9);
    return `<b class="${bad ? 'bad' : ''}">${fmt(v, d1)}${unit}${base != null ? ` <span class="faint" style="font-weight:400">／同型 ${fmt(base, d1)}</span>` : ''}</b>`;
  };
  const dmsSum = d.dms_hours.reduce((a, b) => a + b, 0);
  const peak = dmsSum ? d.dms_hours.indexOf(Math.max(...d.dms_hours)) : null;
  el.innerHTML = `<div class="detail-hd">
      <div class="avatar lg ${avatarCls(id)}">${esc(surname(dv.name))}</div>
      <div class="grow"><h3>${esc(dv.name)} <span class="muted" style="font-size:13px;font-weight:400">${esc(dv.nick)}</span></h3>
        <div class="muted small">${esc(dv.plate)} · ${esc(r.series)} · 年資 ${dv.years} 年 ${mockTag()}</div></div>
      <button class="btn sm line" id="btn-line-fb">${icon('message')}LINE 回饋</button>
    </div>
    <div class="detail-sec">
      <div class="row between" style="align-items:flex-end">
        <div class="big-score"><div class="n">${r.score}</div><div class="of">/ 100　第 ${r.rank} 名</div></div>
        <div style="text-align:right">${r.prev ? `${deltaHtml(r.score - r.prev.score, ' 分', true)}<div class="muted small">${+r.prev.period.slice(5)} 月 ${r.prev.score} 分</div>` : ''}</div>
      </div>
      <div class="subbars" style="margin-top:16px">${['safety', 'eco', 'ontime', 'compliance'].map((k) => `
        <div class="subbar" data-tip="${esc(`${SUB_LABEL[k]} ${r.sub[k]} 分${r.prev ? `（上期 ${r.prev.sub[k]}）` : ''}`)}"><span class="lbl">${SUB_LABEL[k]}${k === 'ontime' ? '<small>模擬</small>' : ''}</span>
          <div class="trk"><b class="${tier(r.sub[k])}" style="width:${r.sub[k]}%"></b>${r.prev ? `<u style="left:calc(${r.prev.sub[k]}% - 1px)"></u>` : ''}</div>
          <span class="v">${r.sub[k]}</span></div>`).join('')}</div>
    </div>
    <div class="detail-sec" id="dr-ai"><div class="ai-box"><div class="ai-box-hd">${icon('sparkles')}AI 教練分析</div>${skeleton(4)}</div></div>
    <div class="detail-sec">
      <div class="sec-title">關鍵指標<span class="right muted small">${esc(d.period_label.split('（')[0])}</span></div>
      <div class="kv-list">
        <span>行駛</span><b>${fmt(m.km, 0)} km · ${fmt(m.drive_h, 1)} h · ${m.n_days} 天</b>
        <span>油耗 L/100km</span>${r.quality ? '<b class="faint">資料異常</b>' : cmp(m.l100, m.median_l100)}
        <span>怠速占比</span><b>${pct(m.idle_share, 1)}</b>
        <span>急加減速／百公里</span><b>${fmt(m.harsh_100, 1)}</b>
        <span>超速／百公里</span><b>${fmt(m.speeding_100, 1)}</b>
        ${r.has_dms ? `<span>分心／駕駛小時</span><b>${fmt(m.distract_per_h, 2)}</b><span>疲勞／駕駛小時</span><b>${fmt(m.fatigue_per_h, 2)}</b><span>使用手機／駕駛小時</span><b>${fmt(m.phone_per_h, 2)}</b>` : ''}
        <span>工時違規</span><b class="${m.over10 + m.over4 ? 'bad' : ''}">${m.over10 + m.over4 ? `${m.over10} 天超過 10h、${m.over4} 段連續超過 4h` : '無'}</b>
        <span>準時率 ${mockTag()}</span><b>${pct(m.ontime_rate, 1)}（${m.tasks} 趟）</b>
      </div>
    </div>
    ${dmsSum ? `<div class="detail-sec"><div class="sec-title">疲勞／分心／手機事件時段<span class="right muted small">高峰 ${peak}–${peak + 1} 點</span></div><div id="dr-hours"></div></div>` : ''}
    ${d.trend.length > 1 ? `<div class="detail-sec"><div class="sec-title">各月綜合分數</div><div id="dr-trend"></div></div>` : ''}`;
  if (dmsSum) {
    const top2 = [...d.dms_hours.keys()].sort((a, b) => d.dms_hours[b] - d.dms_hours[a]).slice(0, 2);
    Charts.columns($('#dr-hours'), { x: d.dms_hours.map((_, h) => `${h}`), values: d.dms_hours, unit: '次', height: 140, highlight: top2, xEvery: 3, tipX: (h) => `${h}:00–${h + 1}:00` });
  }
  if (d.trend.length > 1) Charts.line($('#dr-trend'), { x: d.trend.map((t) => `${+t.month.slice(5)} 月`), series: [{ name: '綜合分數', color: cssVar('--ok'), values: d.trend.map((t) => t.score) }], unit: ' 分', height: 150, digits: 0 });
  $('#btn-line-fb').addEventListener('click', () => openLinePreview('driver', id));
  const adv = await api(`/api/drivers/${id}/advice?period=${S.drivers.period}`);
  if (S.drivers.sel !== id) return;
  S.drivers.advice = adv;
  $('#dr-ai').innerHTML = `<div class="ai-box"><div class="ai-box-hd">${icon('sparkles')}AI 教練分析<span class="right">${aiTag(adv.mode)}</span></div>
    <div class="ai-headline">${esc(adv.headline)}</div>
    <div class="ai-actions">${(adv.actions || []).map((a) => `<div class="ai-action">${icon('arrow')}<span>${esc(a)}</span></div>`).join('')}</div>
    ${(adv.findings || []).length ? more('分析依據', `<ul class="ai-list">${adv.findings.map((f) => `<li>${esc(f)}</li>`).join('')}</ul>`) : ''}</div>`;
}

function toggleWeights() {
  const host = $('#btn-weights').parentElement;
  const old = $('.pop', host);
  if (old) { old.remove(); return; }
  const w = { ...(S.drivers.weights || S.boot.weights) };
  const pop = document.createElement('div');
  pop.className = 'pop';
  pop.style.right = '0'; pop.style.top = '42px';
  const draw = () => {
    const sum = Object.values(w).reduce((a, b) => a + b, 0);
    pop.innerHTML = `<div class="row between" style="margin-bottom:8px"><b>綜合分數權重</b><span class="muted small">合計 ${sum}%</span></div>
      ${Object.keys(SUB_LABEL).map((k) => `<div class="w-row"><span>${SUB_LABEL[k]}</span><input type="range" min="0" max="60" step="5" value="${w[k]}" data-k="${k}"><b>${w[k]}%</b></div>`).join('')}
      <div class="row" style="margin-top:10px;justify-content:flex-end"><button class="btn sm ghost" id="w-reset">恢復預設</button><button class="btn sm primary" id="w-apply">套用</button></div>`;
    $$('input', pop).forEach((i) => i.addEventListener('input', () => { w[i.dataset.k] = +i.value; draw(); }));
    $('#w-reset', pop).addEventListener('click', () => { Object.assign(w, S.boot.weights); draw(); });
    $('#w-apply', pop).addEventListener('click', () => { S.drivers.weights = { ...w }; pop.remove(); renderDrivers(); toast('已套用新的權重'); });
  };
  draw();
  host.appendChild(pop);
}

async function openMonthly() {
  const P = S.boot.months[S.boot.months.length - 1];
  openModal(`<div class="modal-hd"><span class="tag ai">${icon('sparkles')}AI 績效月報</span><div class="grow"><h3>${+P.slice(5)} 月司機績效與獎金建議</h3><div class="sub" id="mr-sub">整理中…</div></div><button class="icon-btn ghost" data-close>${icon('x')}</button></div>
    <div class="modal-bd" id="mr-bd"><div class="thinking" style="margin-bottom:14px"><span class="spinner"></span>AI 正在彙整本月績效…</div>${skeleton(6)}</div>
    <div class="modal-ft"><span class="left" id="mr-total"></span><button class="btn ghost" data-close>關閉</button><button class="btn line" id="mr-send" disabled>${icon('send')}推播月報到 LINE</button></div>`, true);
  const r = await api(`/api/monthly?period=${P}`);
  $('#mr-sub').textContent = `${r.period_label}${r.compare ? `，對照 ${r.compare.split('（')[0]}` : ''}`;
  $('#mr-bd').innerHTML = `<div class="mr-summary">
      <div class="mr-box"><h4>本月重點 ${aiTag(r.mode)}</h4><div class="brief-summary" style="font-size:14px">${r.summary.map((s) => `<p>${esc(s)}</p>`).join('')}</div></div>
      <div class="mr-box"><h4>下月改善重點</h4><div class="ai-actions">${r.next_focus.map((a) => `<div class="ai-action">${icon('arrow')}<span>${esc(a)}</span></div>`).join('')}</div></div>
    </div>
    <div class="table-wrap" style="margin-top:16px"><table class="t">
      <thead><tr><th class="c">#</th><th>司機</th><th class="c">綜合</th><th class="c">安全</th><th class="c">節能</th><th class="c">準時</th><th class="c">合規</th><th class="r">建議獎金</th><th>AI 備註</th></tr></thead>
      <tbody>${r.drivers.map((x, i) => `<tr style="cursor:default"><td class="c"><span class="rank ${i < 3 ? 'top' : ''}">${i + 1}</span></td>
        <td><div class="cell-main">${esc(x.name)}</div><div class="cell-sub">${esc(x.plate)}</div></td>
        <td class="c"><b>${x.score}</b> ${x.prev_score != null ? deltaHtml(x.score - x.prev_score, '', true) : ''}</td>
        ${['safety', 'eco', 'ontime', 'compliance'].map((k) => `<td class="c"><span class="sub-score ${tier(x.sub[k])}">${x.sub[k]}</span></td>`).join('')}
        <td class="r"><span class="bonus ${x.bonus ? '' : 'zero'}">${x.bonus ? ntd(x.bonus) : x.hold ? '暫緩' : '—'}</span>${x.hold ? `<div class="cell-sub" style="color:var(--critical)">${esc(x.hold_reason)}</div>` : ''}</td>
        <td class="small" style="color:var(--ink-2);max-width:260px">${esc(x.note)}</td></tr>`).join('')}</tbody></table></div>
    <div class="note" style="margin-top:10px">${icon('info')}獎金規則（初版，可調整）：${esc(r.bonus_rule)}。準時分數來自模擬資料。</div>`;
  $('#mr-total').innerHTML = `建議獎金合計 <b style="color:var(--ink);font-size:14px">${ntd(r.bonus_total)}</b>`;
  $('#mr-send').disabled = false;
  $('#mr-send').addEventListener('click', () => { closeModal(); toast('月報已推播至老闆 LINE（模擬）'); });
}

// =====================================================================
// 車隊績效
// =====================================================================
async function renderFleet() {
  const el = $('#page-fleet');
  const P = S.fleet.period;
  const pl = S.boot.periods.find((p) => p.id === P);
  el.innerHTML = `<div class="toolbar">${periodSeg('fl-period', P)}<span class="toolbar-label">${esc(pl.full)}</span><span class="spacer"></span>
      <div class="seg" id="fl-series">${['all', '300', '500', '700'].map((s) => `<button class="${S.fleet.series === s ? 'on' : ''}" data-s="${s}">${s === 'all' ? '全部車型' : `HINO ${s}`}</button>`).join('')}</div></div>
    <div class="card" id="fl-compare"><div class="card-bd">${skeleton(5)}</div></div>
    <div class="grid g-side mt"><div class="card" id="fl-table"></div><div class="card detail" id="fl-detail"></div></div>`;
  $$('#fl-period button').forEach((b) => b.addEventListener('click', () => { S.fleet.period = b.dataset.p; renderFleet(); }));
  $$('#fl-series button').forEach((b) => b.addEventListener('click', () => { S.fleet.series = b.dataset.s; renderFleet(); }));
  const d = await api(`/api/vehicles?period=${P}`);
  S.fleet.data = d;
  const rows = d.rows.filter((r) => S.fleet.series === 'all' || r.type === S.fleet.series);
  if (!S.fleet.sel || !rows.find((r) => r.plate === S.fleet.sel)) S.fleet.sel = [...rows].filter((r) => r.active && !r.quality).sort((a, b) => (b.vs_median ?? -99) - (a.vs_median ?? -99))[0]?.plate;
  renderFleetCompare(rows, d.benchmarks);
  renderFleetTable(rows);
  renderFleetDetail();
}

function renderFleetCompare(rows, bm) {
  const series = S.fleet.series === 'all' ? ['300', '500', '700'] : [S.fleet.series];
  $('#fl-compare').innerHTML = `<div class="card-hd"><h3>同車型油耗比較</h3><span class="sub">L/100km</span>${infoTip('黑色刻度為同車型中位數；紅色為高於中位數 20% 以上')}<div class="right">${realTag()}</div></div>
    <div class="card-bd"><div class="grid g-${series.length === 1 ? '2' : '3'}" style="gap:28px">${series.map((s) => {
      const g = rows.filter((r) => r.type === s && r.active && r.l100).sort((a, b) => b.l100 - a.l100);
      const med = bm[s].l100;
      return `<div><div class="row" style="margin-bottom:12px"><span class="s-dot s-${s}"></span><b>HINO ${s}</b><span class="muted small">${g.length} 台 · 中位數 ${fmt(med, 1)}</span></div>
        ${Charts.hbars(g.map((r) => ({ label: r.plate, value: r.l100, bad: !r.quality && r.vs_median >= 20, highlight: S.fleet.sel === r.plate, dim: !!r.quality, note: r.quality ? '資料異常，不列入比較' : `${r.driver} · ${r.vs_median > 0 ? '+' : ''}${r.vs_median}% vs 中位數` })),
          { ref: { value: med, label: '同車型中位數' }, unit: '', labelWidth: 86, digits: 1, fixed: true })}</div>`;
    }).join('')}</div></div>`;
}

function renderFleetTable(rows) {
  const sorted = [...rows].sort((a, b) => (b.active - a.active) || (!!a.quality - !!b.quality) || ((b.vs_median ?? -999) - (a.vs_median ?? -999)));
  const kk = (v) => `${(v / 1000).toFixed(1)}k`;
  const maint = (m) => (m.status === 'overdue' ? `<span class="tag critical">逾期 ${fmt(-m.km_left, 0)} km</span>` : m.status === 'soon' ? `<span class="tag warning">剩 ${fmt(m.km_left, 0)} km</span>` : `<span class="muted">剩 ${kk(m.km_left)} km</span>`);
  $('#fl-table').innerHTML = `<div class="card-hd"><h3>車輛明細</h3><span class="sub">${rows.length} 台</span>${infoTip(`柴油以每公升 NT$${S.boot.diesel_price} 估算；保養週期為模擬`)}</div>
  <div class="card-bd" style="padding:12px 8px 8px"><div class="table-wrap"><table class="t dense">
    <thead><tr><th>車輛</th><th class="r">L/100km</th><th class="r">較同型</th><th class="r">怠速占比</th><th class="r">油料成本<small>每公里</small></th><th class="r">多花油錢</th><th>保養</th><th>故障碼</th></tr></thead>
    <tbody>${sorted.map((r) => `<tr data-plate="${r.plate}" class="${S.fleet.sel === r.plate ? 'sel' : ''}">
      <td><div class="cell-main"><span class="s-dot s-${r.type}"></span> ${esc(r.plate)}</div><div class="cell-sub">${esc(r.driver)} · ${r.type}</div></td>
      ${r.active ? `<td class="r"><b>${fmt(r.l100, 1, true)}</b></td>
      <td class="r">${r.quality ? '<span class="tag" data-tip="' + esc(r.quality) + '">資料異常</span>' : r.vs_median == null ? '—' : `<span style="color:${r.vs_median >= 20 ? 'var(--critical)' : r.vs_median <= -5 ? 'var(--good)' : 'var(--ink-2)'};font-weight:600">${r.vs_median > 0 ? '+' : ''}${r.vs_median}%</span>`}</td>
      <td class="r">${pct(r.idle_share, 0)}</td>
      <td class="r">${r.cost_per_km ? `NT$${r.cost_per_km.toFixed(1)}` : '—'}</td>
      <td class="r">${r.excess_ntd ? `<b style="color:var(--critical)">${ntd(r.excess_ntd)}</b>` : '<span class="faint">—</span>'}</td>`
      : '<td class="r faint" colspan="5">此期間無行駛資料</td>'}
      <td>${maint(r.maint)}</td>
      <td>${r.maint.dtc.length ? r.maint.dtc.map((c) => `<span class="tag ${['P2002', 'P244B'].includes(c.code) ? 'warning' : ''}" data-tip="${esc(`${c.name}｜${c.count} 次，最近 ${c.last}`)}">${c.code}</span>`).join(' ') : '<span class="faint">—</span>'}</td>
    </tr>`).join('')}</tbody></table></div></div>`;
  $$('#fl-table tbody tr').forEach((tr) => tr.addEventListener('click', () => {
    S.fleet.sel = tr.dataset.plate;
    $$('#fl-table tbody tr').forEach((x) => x.classList.toggle('sel', x === tr));
    renderFleetCompare(S.fleet.data.rows.filter((r) => S.fleet.series === 'all' || r.type === S.fleet.series), S.fleet.data.benchmarks);
    renderFleetDetail();
  }));
}

async function renderFleetDetail() {
  const el = $('#fl-detail');
  const plate = S.fleet.sel;
  if (!plate) { el.innerHTML = ''; return; }
  el.innerHTML = `<div class="detail-sec">${skeleton(6)}</div>`;
  const d = await api(`/api/vehicles/${plate}?period=${S.fleet.period}`);
  if (S.fleet.sel !== plate) return;
  const f = d.fuel; const ms = d.maint;
  const maxL = f?.factors?.length ? Math.max(...f.factors.map((x) => x.liters), 0.1) : 1;
  el.innerHTML = `<div class="detail-hd">
      <div class="avatar lg" style="background:${SERIES_COLOR[d.vehicle.type]}1f;color:${SERIES_COLOR[d.vehicle.type]}">${TRUCK_SVG.replace('<svg', '<svg style="width:24px;height:24px;stroke:currentColor;fill:none;stroke-width:1.8"')}</div>
      <div class="grow"><h3>${esc(plate)}</h3><div class="muted small">${esc(d.vehicle.series)} · ${esc(d.driver.name)} · 里程 ${fmt(ms.odo, 0)} km</div></div>
    </div>
    ${f && f.excess_l != null ? `<div class="detail-sec">
      <div class="sec-title">油耗與同車型比較<span class="right muted small">${esc(f.period_label.split('（')[0])}</span></div>
      <div class="excess"><span class="n">${fmt(f.l100, 1)}</span><span class="muted">L/100km　中位數 ${fmt(f.median_l100, 1)}</span>
        ${f.excess_l > 0 ? `<span class="tag critical">高 ${f.excess_pct}%</span>` : '<span class="tag brand">優於中位數</span>'}</div>
      ${f.excess_l > 0 ? `<div class="stat-tiles" style="margin-top:12px" data-tip="${esc(`期間行駛 ${fmt(f.km, 0)} km，比照同型應用油 ${fmt(f.expected_l, 0)} 公升，實際 ${fmt(f.fuel, 0)} 公升`)}">
        <div class="stat-tile bad"><div class="n">${fmt(f.excess_l, 0)} L</div><div class="l">多耗油量</div></div>
        <div class="stat-tile bad"><div class="n">${ntd(f.excess_ntd)}</div><div class="l">多花油錢</div></div>
        <div class="stat-tile"><div class="n">${ntd(f.excess_ntd_per_day)}</div><div class="l">每營運日</div></div></div>` : ''}
    </div>
    ${f.excess_l > 0 ? `<div class="detail-sec"><div class="sec-title">多耗的油花在哪裡${infoTip('對照同車型基準估算；「其他」為行車事件無法解釋的部分（路線、載重、車況）')}<span class="right">${realTag('統計歸因')}</span></div>
      <div class="attr">${f.factors.map((x) => `<div class="attr-row" data-tip="${esc(x.detail)}">
        <div class="attr-name">${esc(x.name)}</div>
        <div class="attr-val">${ntd(x.ntd)}<small>${fmt(x.liters, 1)} L</small></div>
        <div class="attr-bar"><b class="${x.key === 'other' ? 'other' : ''}" style="width:${(x.liters / maxL) * 100}%"></b></div></div>`).join('')}</div>
      </div>` : ''}`
      : `<div class="detail-sec"><div class="callout warning">${icon('alert')}<div>${esc(f?.note || '此期間沒有足夠資料')}</div></div></div>`}
    <div class="detail-sec" id="fl-ai"><div class="ai-box"><div class="ai-box-hd">${icon('sparkles')}AI 節能建議</div>${skeleton(3)}</div></div>
    <div class="detail-sec"><div class="sec-title">各資料日油耗<span class="right muted small">全期間 · L/100km</span></div><div id="fl-days"></div></div>
    <div class="detail-sec"><div class="sec-title">保養與故障碼</div>
      <div class="kv-list">
        <span>下次保養 ${mockTag('週期模擬')}</span><b>${fmt(ms.next_service_km, 0)} km（${ms.km_left < 0 ? `<span style="color:var(--critical)">已逾期 ${fmt(-ms.km_left, 0)} km</span>` : `剩 ${fmt(ms.km_left, 0)} km`}）</b>
        <span>上次保養</span><b>${ms.last_service_date}</b>
      </div>
      ${ms.dtc.length ? `<div style="margin-top:12px;display:flex;flex-direction:column;gap:8px">${ms.dtc.map((c) => `<div class="callout ${['P2002', 'P244B'].includes(c.code) ? 'warning' : 'info'}">${icon('wrench')}<div><b>${c.code}</b>　${esc(c.name)}<div class="small" style="opacity:.8">${c.count} 次 · 最近 ${c.last}</div></div></div>`).join('')}</div>` : '<div class="muted small" style="margin-top:10px">期間內沒有故障碼</div>'}
    </div>`;
  const days = d.days.filter((x) => x.l100 != null);
  if (days.length) Charts.columns($('#fl-days'), { x: days.map((x) => md(x.date)), values: days.map((x) => x.l100), unit: 'L/100km', height: 150, xEvery: Math.ceil(days.length / 6), color: SERIES_COLOR[d.vehicle.type], tipX: (i) => `${days[i].date}（${fmt(days[i].km, 0)} km，怠速 ${days[i].idle_h} h）` });
  const ex = await api(`/api/vehicles/${plate}/explain?period=${S.fleet.period}`);
  if (S.fleet.sel !== plate) return;
  $('#fl-ai').innerHTML = `<div class="ai-box"><div class="ai-box-hd">${icon('sparkles')}AI 節能建議<span class="right">${aiTag(ex.mode)}</span></div>
    <div class="ai-headline">${esc(ex.headline)}</div>
    ${(ex.actions || []).length ? `<div class="ai-actions">${ex.actions.map((a) => `<div class="ai-action">${icon('arrow')}<span>${esc(a)}</span></div>`).join('')}</div>` : ''}
    ${ex.explain ? more('分析依據', `<div class="ai-explain">${esc(ex.explain)}</div>`) : ''}</div>`;
}

// =====================================================================
// 安全與合規
// =====================================================================
async function renderSafety(resize, timeOnly) {
  const el = $('#page-safety');
  const tab = S.safety.tab;
  if (timeOnly && tab !== 'hours') return;
  const d = await api(`/api/safety?period=${S.safety.period}&t=${S.t}`);
  S.safety.data = d;
  const pl = S.boot.periods.find((p) => p.id === S.safety.period);
  el.innerHTML = `<div class="toolbar">
      <div class="seg" id="sf-tab">${Object.entries({ hours: '工時合規', dms: '疲勞與分心', complaints: '客訴追蹤' }).map(([k, v]) => `<button class="${tab === k ? 'on' : ''}" data-k="${k}">${v}${k === 'complaints' ? ` <span class="faint">${d.complaints.filter((c) => c.status !== '已結案').length}</span>` : ''}</button>`).join('')}</div>
      <span class="spacer"></span>${tab !== 'complaints' ? `<span class="toolbar-label">歷史期間</span>${periodSeg('sf-period', S.safety.period)}` : ''}</div>
    <div id="sf-body"></div>`;
  $$('#sf-tab button').forEach((b) => b.addEventListener('click', () => { S.safety.tab = b.dataset.k; renderSafety(); }));
  $$('#sf-period button').forEach((b) => b.addEventListener('click', () => { S.safety.period = b.dataset.p; renderSafety(); }));
  ({ hours: safetyHours, dms: safetyDms, complaints: safetyComplaints })[tab](d, pl);
}

function safetyHours(d, pl) {
  const L = S.boot.limits;
  const viol = d.violations;
  const today = d.today.filter((v) => v.drive_h > 0 || v.state !== '待出車');
  const meter = (v, max, warn, unit = 'h') => {
    const cls = v >= max ? 'high' : v >= warn ? 'mid' : '';
    return `<div class="meter"><div class="trk"><b class="${cls}" style="width:${Math.min(100, (v / max) * 100)}%"></b><u style="left:${(warn / max) * 100}%"></u></div><span class="v" style="${cls === 'high' ? 'color:var(--critical)' : ''}">${fmt(v, 1)} ${unit}</span></div>`;
  };
  $('#sf-body').innerHTML = `<div class="grid g-side">
    <div class="card"><div class="card-hd"><h3>今日工時即時檢查</h3><span class="sub">截至 ${d.time}</span>${infoTip('連續駕駛 3.5 h、單日 9 h 提前提醒。以 iTRAQ「行駛中」狀態累計，停車滿 15 分鐘才算休息；屬車輛層級，無法區分同日換手')}<div class="right">${realTag()}</div></div>
      <div class="card-bd">
        <div class="hours-row hours-head"><span>司機／車輛</span><span>連續駕駛（上限 ${L.cont} h）</span><span>今日駕駛（上限 ${L.daily} h）</span><span style="text-align:right">狀態</span></div>
        ${today.map((v) => {
          const st = v.cont_h >= L.cont || v.drive_h >= L.daily ? ['critical', '已超過'] : v.cont_h >= 3.5 || v.drive_h >= 9 ? ['warning', '即將到達'] : ['', v.state];
          return `<div class="hours-row" ${S.safety.hl === v.plate ? 'style="background:var(--brand-50);margin:0 -18px;padding-left:18px;padding-right:18px"' : ''}>
            <div class="row" style="gap:10px"><div class="avatar sm ${avatarCls(v.driver_id)}">${esc(surname(v.driver))}</div><div><div class="cell-main">${esc(v.driver)}</div><div class="cell-sub">${esc(v.plate)} · ${v.depart} 出車</div></div></div>
            ${meter(v.cont_h, L.cont, 3.5)}${meter(v.drive_h, L.daily, 9)}
            <div style="text-align:right"><span class="tag ${st[0]}">${st[1]}</span></div></div>`;
        }).join('')}
      </div></div>
    <div class="card"><div class="card-hd"><h3>歷史工時違規</h3><span class="sub">${esc(pl.label)}</span>${infoTip('2026/5/8 起營業大貨車每日駕駛上限 10 小時，連續 4 小時須休息 30 分鐘；違者罰 NT$9,000–90,000。2025 年資料以新規回溯檢視')}</div>
      <div class="card-bd">
        <div class="stat-tiles">
          <div class="stat-tile ${viol.filter((v) => v.kind === 'daily').length ? 'bad' : ''}"><div class="n">${viol.filter((v) => v.kind === 'daily').length}</div><div class="l">單日超過 10 h</div></div>
          <div class="stat-tile ${viol.filter((v) => v.kind === 'continuous').length ? 'bad' : ''}"><div class="n">${viol.filter((v) => v.kind === 'continuous').length}</div><div class="l">連續超過 4 h</div></div>
          <div class="stat-tile"><div class="n">${new Set(viol.map((v) => v.plate)).size}</div><div class="l">涉及車輛</div></div>
        </div>
        <div style="margin-top:8px">${viol.length ? viol.map((v) => `<div class="viol"><span class="muted num">${md(v.date)}</span><div><b>${esc(v.driver)}</b> <span class="muted small">${esc(v.plate)}</span><div class="small" style="color:var(--ink-2)">${esc(v.label)}</div></div><span class="tag ${v.kind === 'daily' ? 'critical' : 'warning'}">${v.kind === 'daily' ? '單日' : '連續'}</span></div>`).join('') : '<div class="empty">此期間沒有違規紀錄</div>'}</div>
      </div></div></div>`;
  S.safety.hl = null;
}

function safetyDms(d, pl) {
  const dms = d.rows.filter((r) => r.has_dms);
  const top2 = [...d.dms_hours.keys()].sort((a, b) => d.dms_hours[b] - d.dms_hours[a]).slice(0, 2);
  const harsh = [...d.rows].sort((a, b) => b.harsh_100 - a.harsh_100);
  $('#sf-body').innerHTML = `<div class="grid g-2">
      <div class="card"><div class="card-hd"><h3>疲勞／分心／手機 時段</h3><span class="sub">${dms.length} 台有 DMS</span><div class="right">${realTag('DMS 事件')}</div></div>
        <div class="card-bd"><div class="peak">${icon('clock')}高峰 <b>${top2.map((h) => `${h}–${h + 1} 點`).join('、')}</b></div><div id="sf-hours"></div></div></div>
      <div class="card"><div class="card-hd"><h3>急加減速頻率</h3><span class="sub">每百公里</span>${infoTip('黑色刻度為全隊中位數；各車急減速門檻可能由客戶自行設定，請搭配該車自身歷史判讀')}<div class="right">${realTag()}</div></div>
        <div class="card-bd">${Charts.hbars(harsh.slice(0, 10).map((r, i) => ({ label: `${r.plate} ${r.driver}`, value: r.harsh_100, highlight: i < 3, note: r.series })), { ref: { value: median(d.rows.map((r) => r.harsh_100)), label: '全隊中位數' }, labelWidth: 120, valueUnit: '' })}</div></div>
    </div>
    <div class="card mt"><div class="card-hd"><h3>各車 DMS 事件頻率</h3><span class="sub">每駕駛小時</span>${infoTip('安全帶、PCS 為次數；HINO 300 系列未安裝 DMS，不列入。點選列可查看該司機的 AI 教練分析')}</div>
      <div class="card-bd" style="padding:12px 8px 8px"><div class="table-wrap"><table class="t">
        <thead><tr><th>車輛／司機</th><th class="r">駕駛時數</th><th class="r">疲勞</th><th class="r">分心</th><th class="r">使用手機</th><th class="r">車道偏離</th><th class="r">未繫安全帶</th><th class="r">PCS 預警</th></tr></thead>
        <tbody>${dms.sort((a, b) => (b.distract + b.fatigue * 3 + b.phone * 2) - (a.distract + a.fatigue * 3 + a.phone * 2)).map((r) => {
          const hot = (v, th) => `<span style="${v >= th ? 'color:var(--critical);font-weight:600' : ''}">${fmt(v, 2, true)}</span>`;
          return `<tr data-id="${r.driver_id}"><td><div class="cell-main"><span class="s-dot s-${r.series.slice(-3)}"></span> ${esc(r.plate)}</div><div class="cell-sub">${esc(r.driver)}</div></td>
          <td class="r">${fmt(r.drive_h, 1)}</td><td class="r">${hot(r.fatigue, 0.5)}</td><td class="r">${hot(r.distract, 3)}</td><td class="r">${hot(r.phone, 0.5)}</td><td class="r">${hot(r.ldws, 3)}</td><td class="r">${fmt(r.seatbelt, 0)}</td><td class="r">${fmt(r.pcs, 0)}</td></tr>`;
        }).join('')}</tbody></table></div></div></div>`;
  Charts.columns($('#sf-hours'), { x: d.dms_hours.map((_, h) => `${h}`), values: d.dms_hours, unit: '次', height: 230, highlight: top2, xEvery: 2, tipX: (h) => `${h}:00–${h + 1}:00` });
  $$('#sf-body tbody tr').forEach((tr) => tr.addEventListener('click', () => goTo('drivers', tr.dataset.id)));
}
function median(a) { const s = [...a].sort((x, y) => x - y); const m = s.length >> 1; return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2; }

function safetyComplaints(d) {
  const list = d.complaints;
  if (!S.safety.sel) S.safety.sel = list[0]?.id;
  const stCls = { 待處理: 'critical', 處理中: 'warning', 已結案: 'brand' };
  $('#sf-body').innerHTML = `<div class="grid" style="grid-template-columns:360px minmax(0,1fr);align-items:start">
    <div class="card"><div class="card-hd"><h3>客訴列表</h3><div class="right">${mockTag('客訴內容為模擬')}</div></div>
      <div style="margin-top:10px;border-top:1px solid var(--line)">${list.map((c) => `<div class="cmp ${S.safety.sel === c.id ? 'sel' : ''}" data-id="${c.id}">
        <div class="cmp-top"><span class="tag ${stCls[c.status]}">${c.status}</span><span>${esc(c.channel)}</span><span class="right num">${c.received.slice(5).replace('-', '/')}</span></div>
        <div class="cmp-name">${esc(c.customer)}</div><div class="cmp-text">${esc(c.text)}</div>
        <div class="cmp-top">${esc(c.plate)} · ${esc(c.driver_name)}</div></div>`).join('')}</div></div>
    <div class="card" id="cmp-detail"></div></div>`;
  $$('.cmp').forEach((c) => c.addEventListener('click', () => { S.safety.sel = c.dataset.id; $$('.cmp').forEach((x) => x.classList.toggle('sel', x === c)); renderComplaint(); }));
  renderComplaint();
}

async function renderComplaint() {
  const el = $('#cmp-detail');
  const id = S.safety.sel;
  const c0 = S.safety.data.complaints.find((c) => c.id === id);
  el.innerHTML = `<div class="detail-hd"><div class="grow"><h3>${esc(c0.customer)}</h3><div class="muted small">${esc(c0.channel)} · ${c0.received} · ${esc(c0.plate)}｜${esc(c0.driver_name)}</div></div></div>
    <div class="detail-sec"><div class="quote">${esc(c0.text)}</div></div>
    <div class="detail-sec"><div class="ai-box"><div class="ai-box-hd">${icon('sparkles')}客訴助理</div><div class="thinking"><span class="spinner"></span>正在調出 ${esc(c0.plate)} 當天的 iTRAQ 軌跡與事件…</div>${skeleton(3)}</div></div>`;
  const r = await api(`/api/complaints/${id}`);
  if (S.safety.sel !== id) return;
  const a = r.analysis; const ev = r.evidence;
  const sevCls = { 高: 'critical', 中: 'warning', 低: '' }[a.severity] || '';
  const hotTypes = new Set([7, 6, 8, 14, 16, 12, 19, 20]);
  el.innerHTML = `<div class="detail-hd"><div class="grow"><h3>${esc(r.complaint.customer)}</h3><div class="muted small">${esc(r.complaint.channel)} · ${r.complaint.received} · ${esc(r.complaint.plate)}｜${esc(r.complaint.driver_name)}</div></div>
      <span class="tag">${esc(a.category)}</span><span class="tag ${sevCls}">嚴重度 ${esc(a.severity)}</span></div>
    <div class="detail-sec"><div class="quote">${esc(r.complaint.text)}</div></div>
    <div class="detail-sec"><div class="ai-box"><div class="ai-box-hd">${icon('sparkles')}客訴助理判斷<span class="right">${aiTag(r.mode)}</span></div>
      <div class="ai-headline">${esc(a.judgement)}</div>
      ${(a.evidence_summary || []).length ? more('判斷依據', `<ul class="ai-list">${a.evidence_summary.map((x) => `<li>${esc(x)}</li>`).join('')}</ul>`) : ''}</div></div>
    <div class="detail-sec"><div class="grid g-2" style="gap:18px">
      <div><div class="sec-title">行程佐證<span class="right">${realTag('iTRAQ 軌跡與事件')}</span></div>
        <div class="kv-list" style="margin-bottom:12px">
          <span>任務</span><b>${esc(ev.task.customer)}</b>
          <span>預約／實際到達</span><b>${ev.task.window_end} 前／${ev.task.arrive_actual}${ev.late_min > 0 ? ` <span style="color:var(--critical)">（晚 ${ev.late_min} 分）</span>` : ''}</b>
          <span>停留時間</span><b>${ev.stop_minutes} 分（引擎運轉 ${ev.engine_on_at_stop_min} 分）</b>
          <span>期間最高車速</span><b>${ev.max_speed} km/h</b>
        </div>
        <div class="mini-map" id="cmp-map"></div></div>
      <div><div class="sec-title">事件時間軸<span class="right muted small">${ev.window}</span></div>
        <div class="timeline" style="max-height:330px;overflow-y:auto">${ev.events.length ? ev.events.map((e) => `<div class="tl ${hotTypes.has(e.type) ? 'hot' : ''}"><span class="tm">${e.time}</span><span>${esc(e.label)}</span></div>`).join('') : '<div class="muted small">這段期間沒有事件</div>'}
          <div class="tl stop"><span class="tm">${ev.task.arrive_actual}:00</span><span><b>抵達 ${esc(ev.task.customer)}</b></span></div></div></div>
    </div></div>
    <div class="detail-sec"><div class="sec-title">處理建議</div><div class="ai-actions">${(a.suggestions || []).map((s) => `<div class="ai-action">${icon('arrow')}<span>${esc(s)}</span></div>`).join('')}</div></div>
    <div class="detail-sec"><div class="sec-title">回覆客戶草稿<span class="right muted small">可直接修改</span></div>
      <textarea class="draft" id="cmp-draft">${esc(a.reply_draft)}</textarea>
      <div class="row" style="margin-top:10px;justify-content:flex-end;gap:8px">
        <button class="btn" id="cmp-progress">標記處理中</button><button class="btn line" id="cmp-reply">${icon('send')}以 LINE 回覆並結案</button></div></div>`;
  const evs = ev.events.slice().sort((x, y) => x.time.localeCompare(y.time));
  ev.events.splice(0, ev.events.length, ...evs);
  setTimeout(() => {
    if (typeof L === 'undefined') return;
    const mm = L.map('cmp-map', { zoomControl: false, attributionControl: false });
    baseLayer().addTo(mm);
    if (ev.track.length > 1) L.polyline(ev.track, { color: cssVar('--ok'), weight: 3.5 }).addTo(mm);
    ev.events.filter((e) => hotTypes.has(e.type) && e.lat).forEach((e) => L.circleMarker([e.lat, e.lon], { radius: 5, color: cssVar('--surface'), weight: 2, fillColor: cssVar('--critical'), fillOpacity: 1 }).bindTooltip(`${e.time} ${e.label}`, { className: 'vt' }).addTo(mm));
    L.marker(ev.stop, { icon: L.divIcon({ className: 'vm-wrap', html: '<div class="sm-pin">終</div>', iconSize: [22, 22], iconAnchor: [11, 11] }) }).addTo(mm);
    const b = ev.track.length ? L.latLngBounds(ev.track) : L.latLngBounds([ev.stop, ev.stop]);
    mm.fitBounds(b.pad(0.15));
  }, 30);
  const setStatus = async (status, msg) => {
    const res = await api(`/api/complaints/${id}/status`, { status });
    S.safety.data.complaints = res.complaints;
    toast(msg);
    renderSafety();
  };
  $('#cmp-progress').addEventListener('click', () => setStatus('處理中', '已標記為處理中'));
  $('#cmp-reply').addEventListener('click', () => setStatus('已結案', `已以 LINE 回覆 ${r.complaint.customer}（模擬）`));
}

// =====================================================================
// LINE 預覽（晨報、司機回饋）
// =====================================================================
function openLinePreview(kind, id) {
  if (kind === 'brief') {
    const b = S.brief;
    if (!b) return;
    const body = `${b.summary.map(esc).join('\n')}\n\n<b>今天先處理：</b>\n${b.top.map((x, i) => `${i + 1}. <b>${esc(x.title)}</b>\n${esc(x.why)}`).join('\n')}\n\n👉 打開儀表板看詳細`;
    openModal(`<div class="modal-hd"><div class="grow"><h3>LINE 晨報預覽</h3><div class="sub">每天 07:30 推播給老闆</div></div><button class="icon-btn ghost" data-close>${icon('x')}</button></div>
      <div class="modal-bd">${lineChat('車隊 AI 助理', `今天 07:30`, body)}</div>
      <div class="modal-ft"><span class="left">${aiTag(b.mode)}</span><button class="btn" data-close>關閉</button></div>`);
    return;
  }
  const adv = S.drivers.advice;
  const dv = S.boot.drivers.find((x) => x.id === id);
  openModal(`<div class="modal-hd"><div class="grow"><h3>傳給 ${esc(dv.nick)} 的 LINE 週回饋</h3><div class="sub">AI 依本期數據擬稿，先肯定、再給一個具體目標</div></div><button class="icon-btn ghost" data-close>${icon('x')}</button></div>
    <div class="modal-bd" id="fb-bd">${adv ? lineChat(S.boot.company, `今天 ${hhmm(S.t)}`, null, adv.line_message) : '<div class="thinking"><span class="spinner"></span>AI 正在擬稿…</div>'}</div>
    <div class="modal-ft"><span class="left">LINE 推播為模擬，不會真的送出</span><button class="btn ghost" data-close>取消</button><button class="btn line" id="fb-send">${icon('send')}傳送給 ${esc(dv.nick)}</button></div>`);
  const ta = $('#fb-bd textarea'); if (ta) ta.style.height = `${ta.scrollHeight}px`;
  $('#fb-send').addEventListener('click', () => { closeModal(); toast(`已傳送週回饋給${dv.nick}（模擬）`); });
}
function lineChat(sender, time, html, editable) {
  return `<div class="line-phone"><div class="line-top"><span class="line-badge">LINE</span>${esc(sender)}</div>
    <div class="line-chat"><div class="line-time">${esc(time)}</div>
      <div class="line-msg"><div class="line-ava">${TRUCK_SVG}</div><div class="grow"><div class="line-name">${esc(sender)}</div>
        <div class="row" style="align-items:flex-end;gap:4px"><div class="line-bubble">${editable != null ? `<textarea class="line-edit" rows="4">${esc(editable)}</textarea>` : html}</div><span class="line-meta">${esc(time.replace('今天 ', ''))}</span></div></div></div>
    </div></div>`;
}

// ---------------- Modal ----------------
function openModal(html, wide = false) {
  const m = $('#modal');
  m.className = `modal ${wide ? 'wide' : ''}`;
  m.innerHTML = html;
  $('#modal-wrap').classList.add('on');
  $$('[data-close]', m).forEach((b) => b.addEventListener('click', closeModal));
}
function closeModal() { $('#modal-wrap').classList.remove('on'); }

// =====================================================================
// 問 AI
// =====================================================================
const ASK_EXAMPLES = ['這個月誰最需要關心？', '上週誰最耗油？', 'ABC-1999 為什麼這麼耗油？', '今天有哪些配送可能延誤？', '現在有誰快連續開 4 小時了？', '工時新規是什麼？違規罰多少？'];
const TOOL_LABEL = {
  get_fleet_overview: '查詢車隊即時概況', get_fuel_ranking: '查詢油耗排名', get_fuel_breakdown: '拆解油耗原因',
  get_driver_ranking: '查詢司機排名', get_driver_detail: '查詢司機明細', get_safety_events: '統計安全事件',
  get_hours_compliance: '檢查駕駛工時', get_deliveries: '查詢配送與延誤預測', get_vehicle_status: '查詢車輛狀態',
  search_knowledge: '檢索法規與手冊（RAG）',
};
function bindAsk() {
  $('#btn-ask-close').addEventListener('click', closeAsk);
  $('#btn-ask-clear').addEventListener('click', () => { S.ask.history = []; renderAskEmpty(); });
  $('#ask-form').addEventListener('submit', (e) => { e.preventDefault(); const v = $('#ask-input').value.trim(); if (v) { $('#ask-input').value = ''; ask(v); } });
  renderAskEmpty();
}
function renderAskEmpty() {
  $('#ask-body').innerHTML = `<div class="ask-empty">
    <div><h4>老闆，想知道什麼？</h4><p>用口語問，AI 會判斷要查哪些數據、呼叫查詢函式取得數字，再用白話回答。數字都由分析引擎計算，不讓 AI 自己編。</p></div>
    <div class="ask-flow"><span>你的問題</span>→<span class="g">LLM 理解</span>→<span>查詢函式</span>→<span>分析引擎</span>→<span class="g">LLM 回答</span></div>
    <div class="q-list">${ASK_EXAMPLES.map((q) => `<button class="q-item" data-q="${esc(q)}">${esc(q)}${icon('arrow')}</button>`).join('')}</div></div>`;
  $('#ask-suggest').innerHTML = '';
  $$('.q-item').forEach((b) => b.addEventListener('click', () => ask(b.dataset.q)));
}
function openAsk() { $('#ask').classList.add('on'); $('#scrim').classList.add('on'); setTimeout(() => $('#ask-input').focus(), 260); }
function closeAsk() { $('#ask').classList.remove('on'); $('#scrim').classList.remove('on'); }

async function ask(q) {
  if (S.ask.busy) return;
  openAsk();
  S.ask.busy = true;
  $('#ask-form .send').disabled = true;
  const body = $('#ask-body');
  if ($('.ask-empty', body)) body.innerHTML = '';
  body.insertAdjacentHTML('beforeend', `<div class="msg-me">${esc(q)}</div><div class="msg-ai"><div class="steps"><div class="step"><span class="spinner"></span>理解問題</div></div><div class="answer"></div></div>`);
  const node = body.lastElementChild;
  const steps = $('.steps', node); const ans = $('.answer', node);
  body.scrollTop = body.scrollHeight;
  let text = ''; let charts = []; let sources = new Set(); let started = false;
  const finishStep = () => { const s = $('.step .spinner', steps); if (s) s.outerHTML = icon('check'); };
  try {
    const r = await fetch('/api/ask', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ question: q, history: S.ask.history, t: S.t }) });
    const reader = r.body.getReader(); const dec = new TextDecoder(); let buf = '';
    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;
      buf += dec.decode(value, { stream: true });
      let i;
      while ((i = buf.indexOf('\n\n')) >= 0) {
        const chunk = buf.slice(0, i); buf = buf.slice(i + 2);
        if (!chunk.startsWith('data: ')) continue;
        const ev = JSON.parse(chunk.slice(6));
        if (ev.type === 'status') { finishStep(); if (!/理解問題/.test(ev.text)) steps.insertAdjacentHTML('beforeend', `<div class="step">${icon('info')}${esc(ev.text)}</div>`); }
        else if (ev.type === 'tool_call') {
          finishStep();
          const args = Object.entries(ev.args || {}).map(([k, v]) => `${k}=${v}`).join(', ');
          steps.insertAdjacentHTML('beforeend', `<div class="step"><span class="spinner"></span><span class="nowrap">${TOOL_LABEL[ev.name] || ev.name}</span><code>${esc(ev.name)}(${esc(args)})</code></div>`);
        } else if (ev.type === 'tool_result') {
          finishStep();
          if (ev.result?.chart) charts.push(ev.result.chart);
          (ev.result?.sources || []).forEach((s) => sources.add(s));
          if (ev.result?.['資料區間']) sources.add(`資料區間：${ev.result['資料區間']}`);
        } else if (ev.type === 'delta') {
          if (!started) { finishStep(); steps.insertAdjacentHTML('beforeend', `<div class="step">${icon('sparkles')}撰寫回答</div>`); started = true; }
          text += ev.text;
          ans.innerHTML = mdLite(text); ans.classList.add('cursor');
        } else if (ev.type === 'done') {
          if (!text && ev.text) { text = ev.text; ans.innerHTML = mdLite(text); }
        }
        body.scrollTop = body.scrollHeight;
      }
    }
  } catch (e) {
    ans.innerHTML = `<div class="callout warning">${icon('alert')}<div>連線中斷，請再試一次。</div></div>`;
  }
  finishStep();
  ans.classList.remove('cursor');
  const chart = charts[charts.length - 1];
  if (chart) {
    node.insertAdjacentHTML('beforeend', `<div class="chart-card"><h5>${esc(chart.title)}</h5><div class="ask-chart"></div></div>`);
    const host = $('.ask-chart', node);
    if (chart.type === 'bar') host.innerHTML = Charts.hbars(chart.items, { unit: chart.unit === '%' ? '%' : '', valueUnit: chart.unit === '%' ? '%' : '', signed: chart.items.some((i) => i.value < 0) || chart.unit === '%', labelWidth: 130 });
    else if (chart.type === 'columns') { const vals = chart.values; const top = [...vals.keys()].sort((a, b) => vals[b] - vals[a]).slice(0, 2); Charts.columns(host, { x: chart.x, values: vals, unit: chart.unit, height: 150, highlight: top, xEvery: 3, tipX: (h) => `${h}:00–${h + 1}:00` }); }
    else if (chart.type === 'line') Charts.line(host, { x: chart.x, series: chart.series.map((s) => ({ ...s, color: cssVar('--ok') })), unit: chart.unit, height: 150, digits: 0 });
  }
  if (sources.size) node.insertAdjacentHTML('beforeend', `<div class="sources">${icon('database')}${[...sources].map((s) => `<span class="tag ${/模擬/.test(s) ? 'mock' : 'real'}">${esc(s)}</span>`).join('')}</div>`);
  S.ask.history.push({ role: 'user', content: q }, { role: 'assistant', content: text });
  $('#ask-suggest').innerHTML = ASK_EXAMPLES.filter((x) => x !== q).slice(0, 4).map((x) => `<button>${esc(x)}</button>`).join('');
  $$('#ask-suggest button').forEach((b) => b.addEventListener('click', () => ask(b.textContent)));
  body.scrollTop = body.scrollHeight;
  S.ask.busy = false;
  $('#ask-form .send').disabled = false;
}

// 時間變動時只更新跟時間有關的區塊
const _renderPage = renderPage;
renderPage = function (resize = false, timeOnly = false) {
  if (!timeOnly) return _renderPage(resize);
  if (S.page === 'home' && $('#home-kpi')) {
    api(`/api/overview?t=${S.t}`).then((ov) => { S.overview = ov; renderHomeKpi(); renderFeed(); });
  } else if (S.page === 'delivery' && $('#d-panel')) {
    updateMap();
    if (!S.delivery.task) renderDeliveryPanel(); else renderTaskDetail($('#d-panel'));
  } else if (S.page === 'safety') {
    renderSafety(false, true);
  }
};

boot();
