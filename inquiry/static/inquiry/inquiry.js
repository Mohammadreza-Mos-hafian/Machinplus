(() => {
  'use strict';
  const $ = s => document.querySelector(s);
  const CFG = window.INQUIRY;
  const BUDGETS = JSON.parse(document.getElementById('budgets-data').textContent);
  const toEn = s => s.replace(/[۰-۹]/g, d => '۰۱۲۳۴۵۶۷۸۹'.indexOf(d)).replace(/[٠-٩]/g, d => '٠١٢٣٤٥٦٧٨٩'.indexOf(d));

  const PATHS = {
    production: { label: 'راه‌اندازی خط تولید', amt: 'بالای ۲ میلیارد', team: 'خط تولید' },
    trading: { label: 'بازرگانی', amt: 'زیر ۲ میلیارد', team: 'بازرگانی' }
  };
  const SEG = { intro: 1, production: 2, trading: 2 };
  // Subtitles: [startSec, endSec, text] per video. Fill when the transcripts are ready.
  const CAPTIONS = { intro: [], production: [], trading: [] };
  const CITIES = ['تهران','کرج','مشهد','اصفهان','شیراز','تبریز','قم','اهواز','کرمانشاه','ارومیه','رشت','زاهدان','کرمان','همدان','یزد','اردبیل','بندرعباس','اراک','قزوین','زنجان','سنندج','گرگان','ساری','خرم‌آباد','بوشهر','بیرجند','سمنان','شهرکرد','یاسوج','ایلام','کاشان','ساوه'];
  $('#cities').innerHTML = CITIES.map(c => `<option value="${c}">`).join('');

  const qs = new URLSearchParams(location.search);
  const state = { path: null, budget: null, muted: true, playing: null, introWatched: false, pathWatched: false };
  const real = $('#real');
  const stage = $('#stage');
  // budget value -> path, so the direct form (no path chosen) can still send a valid path
  const PATH_OF = {};
  Object.entries(BUDGETS).forEach(([p, list]) => list.forEach(b => { PATH_OF[b.value] = p; }));

  // ---------- sound ----------
  const ICON_OFF = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 9h4l5-4v14l-5-4H4z"/><path d="M17 9l5 6M22 9l-5 6"/></svg>';
  const ICON_ON = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 9h4l5-4v14l-5-4H4z"/><path d="M17 8a5 5 0 0 1 0 8M19.5 5.5a8.5 8.5 0 0 1 0 13"/></svg>';
  function renderMute() {
    $('#mute').innerHTML = state.muted ? ICON_OFF : ICON_ON;
    $('#mute').setAttribute('aria-label', state.muted ? 'روشن کردن صدا' : 'بی‌صدا کردن');
    $('#tap-sound').innerHTML = ICON_OFF + 'برای صدا ضربه بزنید';
    const vis = state.muted && state.playing;
    $('#tap-sound').style.opacity = vis ? 1 : 0;
    $('#tap-sound').style.pointerEvents = vis ? 'auto' : 'none';
  }
  const toggleMute = () => { state.muted = !state.muted; real.muted = state.muted; renderMute(); };
  $('#mute').onclick = toggleMute; $('#tap-sound').onclick = toggleMute;

  // ---------- player ----------
  function play(key) {
    hideAll();
    stage.classList.remove('direct');
    state.playing = key;
    $('#tap-play').hidden = true;
    ['seg1', 'seg2', 'seg3'].forEach((id, i) => { $('#' + id).style.width = (i + 1 < SEG[key]) ? '100%' : '0'; });
    const v = CFG.videos[key];
    if (!real.src.endsWith(v.src)) { real.src = v.src; real.poster = v.poster; }
    real.currentTime = 0; real.muted = state.muted;
    renderMute();
    real.play().catch(() => { $('#tap-play').hidden = false; });
  }
  real.addEventListener('timeupdate', () => {
    const key = state.playing; if (!key || !real.duration) return;
    $('#seg' + SEG[key]).style.width = (real.currentTime / real.duration * 100) + '%';
    const c = CAPTIONS[key].find(([s, e]) => real.currentTime >= s && real.currentTime < e);
    $('#cc').innerHTML = c ? `<span>${c[2]}</span>` : '';
  });
  real.addEventListener('ended', () => {
    const key = state.playing; if (!key) return;
    $('#seg' + SEG[key]).style.width = '100%';
    if (key === 'intro') state.introWatched = true; else state.pathWatched = true;
    track('video_complete', { video: key });
    state.playing = null; renderMute(); $('#cc').innerHTML = '';
    if (key === 'intro') show('#ov-choice'); else { prepForm(state.path); show('#ov-form'); }
  });
  $('#tap-play').onclick = () => { $('#tap-play').hidden = true; real.play().catch(() => { $('#tap-play').hidden = false; }); };

  function prefetch(src) {
    if (document.querySelector(`link[data-pf="${src}"]`)) return;
    const l = document.createElement('link'); l.rel = 'preload'; l.as = 'video'; l.href = src; l.dataset.pf = src;
    document.head.appendChild(l);
  }
  function resetChoice() {
    state.path = null; state.budget = null;
    document.querySelectorAll('.choice').forEach(x => { x.classList.remove('picked'); x.disabled = false; });
  }
  function show(sel) {
    hideAll();
    if (sel === '#ov-choice') { resetChoice(); prefetch(CFG.videos.production.src); prefetch(CFG.videos.trading.src); }
    const o = $(sel); o.classList.add('show'); o.setAttribute('aria-hidden', 'false');
    setTimeout(() => o.querySelector('button,input')?.focus({ preventScroll: true }), 460);
  }
  function hideAll() { document.querySelectorAll('.overlay').forEach(o => { o.classList.remove('show'); o.setAttribute('aria-hidden', 'true'); }); }

  document.querySelectorAll('.choice').forEach(b => b.onclick = () => {
    if (state.path) return;
    state.path = b.dataset.path;
    document.querySelectorAll('.choice').forEach(x => { x.classList.toggle('picked', x === b); x.disabled = true; });
    track('path_selected', { path: state.path });
    setTimeout(() => play(state.path), 180);
  });
  document.querySelectorAll('[data-replay]').forEach(b => b.onclick = () => play(b.dataset.replay === 'intro' ? 'intro' : state.path));

  // ---------- landing ----------
  const landing = $('#landing');
  function leaveLanding() { landing.classList.add('gone'); landing.setAttribute('aria-hidden', 'true'); }
  function openForm(path, cta) {
    real.pause(); state.playing = null; renderMute(); $('#cc').innerHTML = '';
    stage.classList.add('direct');
    prepForm(path);
    show('#ov-form');
    track('form_open', { from: cta });
  }
  $('#cta-video').onclick = () => {
    leaveLanding(); resetChoice();
    state.muted = false; // the click is a user gesture, so sound is allowed
    track('cta_video', {});
    play('intro');
  };
  $('#cta-form').onclick = () => { leaveLanding(); resetChoice(); openForm(null, 'landing'); };
  // video is never mandatory: jump to the form at any point while it plays
  $('#skip').onclick = () => openForm(state.playing && state.playing !== 'intro' ? state.playing : null, 'skip_' + (state.playing || ''));
  $('#form-back').onclick = () => {
    real.pause(); state.playing = null; renderMute(); hideAll();
    stage.classList.remove('direct');
    landing.classList.remove('gone'); landing.setAttribute('aria-hidden', 'false');
    landing.scrollTop = 0; $('#cta-form').focus({ preventScroll: true });
  };

  // ---------- form ----------
  // path known (after the path video): its 3 ranges. Direct entry: all ranges, smallest first.
  function prepForm(path) {
    $('#seg3').style.width = '0';
    state.budget = null;
    $('[data-replay="path"]').hidden = !path;
    $('#form-back').hidden = !!path;
    const list = path ? BUDGETS[path] : [...BUDGETS.trading, ...BUDGETS.production];
    $('#budget').innerHTML = list.map(b => `<button type="button" class="chip" role="radio" aria-checked="false" data-v="${b.value}">${b.label}</button>`).join('');
    $('#budget').querySelectorAll('.chip').forEach(c => c.onclick = () => {
      state.budget = c.dataset.v;
      $('#budget').querySelectorAll('.chip').forEach(x => x.setAttribute('aria-checked', String(x === c)));
      setErr('budget', '');
    });
  }
  const phone = $('#f-phone');
  phone.addEventListener('input', () => { phone.value = toEn(phone.value).replace(/[^\d+]/g, ''); });
  const normPhone = v => { v = toEn(v).replace(/\D/g, ''); if (v.startsWith('98')) v = '0' + v.slice(2); if (v.length === 10 && v[0] === '9') v = '0' + v; return v; };
  function setErr(k, m) { const e = $('#e-' + k); if (!e) return; e.textContent = m || ''; e.parentElement.classList.toggle('invalid', !!m); }
  const checks = {
    name: () => $('#f-name').value.trim().length >= 2 ? '' : 'نام را حداقل با ۲ حرف وارد کنید.',
    phone: () => /^09\d{9}$/.test(normPhone(phone.value)) ? '' : 'شماره موبایل باید ۱۱ رقم و با ۰۹ شروع شود.',
    city: () => $('#f-city').value.trim() ? '' : 'شهر خود را بنویسید یا انتخاب کنید.',
    budget: () => state.budget ? '' : 'یکی از بازه‌ها را انتخاب کنید.'
  };
  ['name', 'phone', 'city'].forEach(k => $('#f-' + k).addEventListener('blur', () => setErr(k, checks[k]())));

  const csrf = () => (document.cookie.match(/(?:^|; )csrftoken=([^;]+)/) || [])[1] || '';

  $('#lead-form').addEventListener('submit', async e => {
    e.preventDefault();
    $('#form-msg').textContent = '';
    let first = null;
    Object.keys(checks).forEach(k => { const m = checks[k](); setErr(k, m); if (m && !first) first = k; });
    if (first) { (document.getElementById('f-' + first) || $('#budget .chip'))?.focus(); return; }

    const btn = $('#submit'); btn.disabled = true; btn.innerHTML = '<span class="spinner"></span>در حال ثبت…';
    const body = {
      name: $('#f-name').value.trim(), phone: normPhone(phone.value), city: $('#f-city').value.trim(),
      path: PATH_OF[state.budget], budget: state.budget, website: $('#f-website').value,
      intro_watched: state.introWatched, path_watched: state.pathWatched,
      utm_source: qs.get('utm_source') || '', utm_medium: qs.get('utm_medium') || '', utm_campaign: qs.get('utm_campaign') || '',
      referrer: document.referrer || ''
    };
    try {
      const res = await fetch(CFG.submitUrl, {
        method: 'POST', credentials: 'same-origin',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf() },
        body: JSON.stringify(body)
      });
      const data = await res.json().catch(() => ({}));
      if (res.ok && data.ok) {
        const path = PATH_OF[state.budget];
        track('lead_submit', { path, budget: state.budget, intro_watched: state.introWatched });
        $('#seg3').style.width = '100%';
        $('#d-team').textContent = PATHS[path].team;
        show('#ov-done');
        return;
      }
      if (data.errors) Object.entries(data.errors).forEach(([k, m]) => setErr(k, m));
      $('#form-msg').textContent = data.message || 'ثبت انجام نشد. دوباره تلاش کنید.';
    } catch (err) {
      $('#form-msg').textContent = 'اتصال برقرار نشد. اینترنت را بررسی کنید و دوباره بزنید.';
    } finally {
      btn.disabled = false; btn.textContent = 'درخواست تماس کارشناس';
    }
  });

  // ---------- analytics hook (GA4 / Matomo / Yektanet: wire here) ----------
  function track(event, params) {
    try { window.gtag?.('event', event, params); window._paq?.push(['trackEvent', 'inquiry', event, JSON.stringify(params)]); } catch (e) {}
  }

  // ---------- start ----------
  $('#lead-form').reset(); resetChoice();
})();
