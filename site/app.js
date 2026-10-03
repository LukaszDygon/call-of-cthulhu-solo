/* Call of Cthulhu Solo: a YAML-driven solo gamebook engine with d100 roll-under checks.
   Adventures live in site/adventures/*.yaml; index.yaml lists them. Format: docs/adventure-format.md. */
(() => {
  const root = document.getElementById('gb-app');
  if (!root) return;
  const INDEX = root.dataset.index;
  const BASE = INDEX.slice(0, INDEX.lastIndexOf('/') + 1);
  const SAVE_KEY = 'cthulhu-solo:save:v1';
  const CHARACTERISTICS = ['STR', 'CON', 'SIZ', 'DEX', 'APP', 'INT', 'POW', 'EDU'];
  const RANK = { fumble: 0, failure: 1, regular: 2, hard: 3, extreme: 4, critical: 5 };
  const GRADE_LABEL = {
    critical: 'Critical success', extreme: 'Extreme success', hard: 'Hard success',
    regular: 'Regular success', failure: 'Failure', fumble: 'Fumble',
  };
  const ENDING_LABEL = {
    triumph: 'Triumph', escape: 'Escape', bittersweet: 'Bittersweet', choir: 'Claimed',
    madness: 'Madness', death: 'Death', lost: 'Lost',
  };
  const REDUCED_MOTION = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  let catalogue = [];   // [{file, adventure, source}]
  let adv = null;       // the adventure being played
  let advSource = '';
  let state = null;
  let sheetOpen = !window.matchMedia('(max-width: 900px)').matches; // collapsed by default on phones

  // ---------- small helpers ----------
  const rand = (n) => Math.floor(Math.random() * n);
  const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
  const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);
  const inline = (s) => esc(s).replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>').replace(/\*(.+?)\*/g, '<em>$1</em>');
  const paragraphs = (text) => String(text ?? '').trim().split(/\n\s*\n/).filter(Boolean)
    .map((p) => `<p>${inline(p.replace(/\s*\n\s*/g, ' '))}</p>`).join('');
  const el = (html) => { const t = document.createElement('template'); t.innerHTML = html.trim(); return t.content.firstElementChild; };

  const store = {
    load() { try { return JSON.parse(localStorage.getItem(SAVE_KEY) || 'null'); } catch { return null; } },
    save(s) { try { localStorage.setItem(SAVE_KEY, JSON.stringify(s)); } catch { /* storage may be blocked */ } },
    clear() { try { localStorage.removeItem(SAVE_KEY); } catch { /* ignore */ } },
  };

  // ---------- dice ----------
  /** "1D6", "-1D4", "+2", "2D3+1" -> signed total. */
  function rollExpr(expr) {
    let s = String(expr).replace(/\s/g, '').toUpperCase();
    let sign = 1;
    if (s[0] === '-') { sign = -1; s = s.slice(1); } else if (s[0] === '+') s = s.slice(1);
    let total = 0;
    for (const term of s.split('+')) {
      const m = term.match(/^(\d*)D(\d+)$/);
      if (m) for (let i = 0; i < Number(m[1] || 1); i++) total += 1 + rand(Number(m[2]));
      else total += Number(term) || 0;
    }
    return sign * total;
  }

  /** d100 with bonus (>0) or penalty (<0) tens dice. */
  function d100(bonus = 0) {
    const units = rand(10);
    const tens = Array.from({ length: 1 + Math.abs(bonus) }, () => rand(10));
    const values = tens.map((t) => (t === 0 && units === 0 ? 100 : t * 10 + units));
    const value = bonus > 0 ? Math.min(...values) : bonus < 0 ? Math.max(...values) : values[0];
    return { units, tens, values, value, kept: values.indexOf(value) };
  }

  function gradeOf(roll, skill) {
    if (roll === 1) return 'critical';
    if (roll === 100 || (skill < 50 && roll >= 96)) return 'fumble';
    if (roll <= Math.floor(skill / 5)) return 'extreme';
    if (roll <= Math.floor(skill / 2)) return 'hard';
    if (roll <= skill) return 'regular';
    return 'failure';
  }
  const targetFor = (skill, difficulty) => (difficulty === 'extreme' ? Math.floor(skill / 5) : difficulty === 'hard' ? Math.floor(skill / 2) : skill);

  // ---------- adventure lookups ----------
  const investigator = () => adv.investigators.find((i) => i.id === state.investigator);
  const section = (id) => adv.sections[String(id)];
  const itemName = (id) => adv.items?.[id]?.name ?? id;
  const companionDef = (id) => adv.companions.find((c) => c.id === id);
  const companionName = (id) => companionDef(id)?.short ?? companionDef(id)?.name ?? id;

  function skillValue(name) {
    const inv = investigator();
    if (CHARACTERISTICS.includes(name)) return inv.characteristics[name];
    if (name === 'Luck') return state.luck;
    if (name === 'Dodge') return inv.skills?.Dodge ?? Math.floor(inv.characteristics.DEX / 2);
    return inv.skills?.[name] ?? adv.skills?.[name] ?? 0;
  }
  function bestSkill(skills) {
    return [].concat(skills).map((name) => ({ name, value: skillValue(name) })).reduce((a, b) => (b.value > a.value ? b : a));
  }

  // ---------- conditions ----------
  function check(req) {
    if (!req) return true;
    if (Array.isArray(req)) return req.every(check);
    const st = (id) => state.companions[id]?.status;
    const tests = {
      any: (v) => v.some(check),
      item: (v) => state.items.includes(v),
      no_item: (v) => !state.items.includes(v),
      note: (v) => state.notes.includes(v),
      no_note: (v) => !state.notes.includes(v),
      with: (v) => st(v) === 'with',
      broken: (v) => st(v) === 'broken',
      gone: (v) => st(v) === 'lost' || st(v) === 'dead',
      skill: (v) => skillValue(v) >= (req.min ?? 50),
      investigator: (v) => [].concat(v).includes(state.investigator),
    };
    return Object.keys(req).every((k) => (tests[k] ? tests[k](req[k]) : true));
  }

  function tagsFor(req) {
    if (!req) return [];
    if (Array.isArray(req)) return req.flatMap(tagsFor);
    if (req.any) return tagsFor(req.any.find(check));
    const tags = [];
    if (req.item) tags.push(itemName(req.item));
    if (req.note) tags.push(`Journal: ${req.note}`);
    if (req.skill) tags.push(req.skill);
    if (req.with) tags.push(companionName(req.with));
    if (req.broken) tags.push(`${companionName(req.broken)}, broken`);
    return tags;
  }

  // ---------- effects ----------
  function sanityLoss(spec, current) {
    const [pass, fail] = String(spec).split('/');
    const roll = d100().value;
    const ok = roll <= current;
    return { roll, ok, loss: Math.max(0, rollExpr(ok ? pass : fail)) };
  }

  function applyEffects(list, out) {
    for (const e of [].concat(list || [])) {
      if (e.companion) { companionEffect(e, out); continue; }
      if (e.san !== undefined) {
        const max = investigator().san;
        if (String(e.san).includes('/')) {
          const r = sanityLoss(e.san, state.san);
          state.san = clamp(state.san - r.loss, 0, max);
          out.push(`Sanity roll (${e.san}): ${r.roll} against ${state.san + r.loss}, ${r.ok ? 'passed' : 'failed'}. ${r.loss ? `You lose ${r.loss} Sanity.` : 'Your mind holds.'}`);
          if (r.loss >= 5 && state.san > 0) {
            state.penalty = 1;
            const bout = adv.bouts?.length ? adv.bouts[rand(adv.bouts.length)] : 'The world tilts.';
            out.push(`Bout of madness. ${bout} Your next roll takes a penalty die.`);
          }
        } else {
          const d = rollExpr(e.san);
          state.san = clamp(state.san + d, 0, max);
          out.push(d >= 0 ? `You regain ${d} Sanity.` : `You lose ${-d} Sanity.`);
        }
      }
      if (e.hp !== undefined) {
        const d = rollExpr(e.hp);
        state.hp = clamp(state.hp + d, 0, investigator().hp);
        out.push(d >= 0 ? `You recover ${d} hit point${d === 1 ? '' : 's'}.` : `You take ${-d} damage.`);
      }
      if (e.luck !== undefined) {
        const d = rollExpr(e.luck);
        state.luck = clamp(state.luck + d, 0, 99);
        out.push(d >= 0 ? `Luck rises by ${d}.` : `Luck falls by ${-d}.`);
      }
      if (e.gain && !state.items.includes(e.gain)) { state.items.push(e.gain); out.push(`Gained: ${itemName(e.gain)}.`); }
      if (e.lose && state.items.includes(e.lose)) { state.items = state.items.filter((i) => i !== e.lose); out.push(`Lost: ${itemName(e.lose)}.`); }
      if (e.note && !state.notes.includes(e.note)) { state.notes.push(e.note); out.push(`Note the word ${e.note} in your journal.`); }
      if (e.unnote) state.notes = state.notes.filter((n) => n !== e.unnote);
    }
  }

  function companionEffect(e, out) {
    const ids = e.companion === 'all'
      ? Object.keys(state.companions).filter((id) => state.companions[id].status === 'with')
      : [e.companion];
    for (const id of ids) {
      const c = state.companions[id];
      if (!c) continue;
      if (e.status && c.status !== e.status) {
        c.status = e.status;
        const verb = { lost: 'is lost to you', dead: 'is dead', with: 'is with you again', broken: 'has broken' }[e.status];
        out.push(`${companionName(id)} ${verb}.`);
      }
      if (e.san !== undefined && c.status === 'with') {
        const max = companionDef(id).san;
        let loss;
        if (String(e.san).includes('/')) {
          const r = sanityLoss(e.san, c.san);
          loss = r.loss;
        } else loss = -rollExpr(e.san);
        c.san = clamp(c.san - loss, 0, max);
        if (loss > 0) out.push(`${companionName(id)} loses ${loss} Sanity.`);
        else if (loss < 0) out.push(`${companionName(id)} regains ${-loss} Sanity.`);
        if (c.san <= 0) {
          c.status = 'broken';
          out.push(`${companionName(id)} breaks. ${companionDef(id).breaks ?? ''}`.trim());
        }
      }
    }
  }

  // ---------- game flow ----------
  function newGame(invId) {
    const inv = adv.investigators.find((i) => i.id === invId);
    state = {
      adventure: catalogue.find((c) => c.adventure === adv).file,
      investigator: invId,
      hp: inv.hp, san: inv.san, luck: inv.luck,
      items: [...(inv.kit || [])],
      notes: [],
      companions: Object.fromEntries(adv.companions.map((c) => [c.id, { san: c.san, status: 'with' }])),
      section: null, log: [], entry: [], pending: null, penalty: 0,
    };
    enter(adv.start);
  }

  function enter(id, carry = []) {
    const sec = section(id);
    if (!sec) { showError(`Section ${id} is missing from the adventure file.`); return; }
    state.section = String(id);
    state.log.push(String(id));
    state.pending = null;
    // `entry` is what led here (your roll, what you took); `after` is what this section does to you,
    // shown below its text so a Sanity roll never comes before the thing that caused it.
    const after = [];
    applyEffects(sec.effects, after);
    state.entry = [...carry];
    state.after = after;
    const out = [...carry, ...after];
    if (!sec.ending) {
      if (state.hp <= 0 && adv.on_death && String(adv.on_death) !== String(id)) return enter(adv.on_death, out);
      if (state.san <= 0 && adv.on_madness && String(adv.on_madness) !== String(id)) return enter(adv.on_madness, out);
    }
    store.save(state);
    renderPlay(true);
  }

  function choose(index) {
    const sec = section(state.section);
    const choice = visibleChoices(sec)[index];
    if (!choice) return;
    const carry = [];
    applyEffects(choice.effects, carry);
    if (!choice.roll) { enter(choice.to, carry); return; }
    const r = choice.roll;
    const skill = bestSkill(r.skill);
    const difficulty = r.difficulty || 'regular';
    const itemBonus = state.items.some((i) => (adv.items?.[i]?.bonus || []).includes(skill.name)) ? 1 : 0;
    const bonus = clamp((r.bonus || 0) + itemBonus - (state.penalty || 0), -2, 2);
    state.penalty = 0;
    const dice = d100(bonus);
    const grade = gradeOf(dice.value, skill.value);
    const target = targetFor(skill.value, difficulty);
    state.pending = {
      index, text: choice.text, skill: skill.name, value: skill.value, difficulty, target, bonus, dice, grade,
      success: RANK[grade] >= RANK[difficulty], luckSpent: 0, carry,
    };
    store.save(state);
    renderPlay(false, true);
  }

  function spendLuck() {
    const p = state.pending;
    const cost = p.dice.value - p.target;
    if (p.success || p.grade === 'fumble' || cost > state.luck) return;
    state.luck -= cost;
    p.luckSpent = cost;
    p.success = true;
    store.save(state);
    renderPlay(false);
  }

  function continueRoll() {
    const p = state.pending;
    const r = visibleChoices(section(state.section))[p.index].roll;
    const next = p.success ? r.success : (p.grade === 'fumble' && r.fumble) ? r.fumble : r.failure;
    const summary = `${p.skill} ${p.target}: rolled ${p.dice.value}, ${GRADE_LABEL[p.grade].toLowerCase()}${p.luckSpent ? `, ${p.luckSpent} Luck spent to pass` : ''}.`;
    enter(next, [summary, ...p.carry]);
  }

  const visibleChoices = (sec) => (sec.choices || []).filter((c) => check(c.requires));

  // ---------- rendering: shell screens ----------
  function showError(msg) {
    applyImmersive(false);
    root.innerHTML = '';
    root.append(el(`<div class="gb-card gb-error" role="alert"><h2 class="gb-deco">The charts are torn</h2><p>${esc(msg)}</p></div>`));
  }

  function renderTitle(focus = false) {
    const saved = store.load();
    applyImmersive(false);
    root.innerHTML = '';
    const wrap = el('<div class="gb-title-screen"></div>');
    const covers = el('<div class="gb-covers"></div>');
    for (const entry of catalogue) {
      const a = entry.adventure;
      const canContinue = saved && saved.adventure === entry.file && a.sections[saved.section];
      const card = el(`
        <article class="gb-card gb-cover">
          <p class="gb-kicker">${esc(a.series ?? 'A solo adventure')}</p>
          <h2 class="gb-deco gb-cover-title" tabindex="-1">${esc(a.title)}</h2>
          <p class="gb-cover-sub">${esc(a.subtitle ?? '')}</p>
          <div class="gb-prose">${paragraphs(a.blurb)}</div>
          <ul class="gb-facts" role="list">
            <li><strong>${Object.keys(a.sections).length}</strong> sections</li>
            <li><strong>${a.investigators.length}</strong> investigators</li>
            <li><strong>${Object.values(a.sections).filter((s) => s.ending).length}</strong> endings</li>
          </ul>
          <div class="gb-actions">
            ${canContinue ? `<button type="button" class="gb-btn gb-btn-primary" data-act="continue">Continue at section ${esc(saved.section)}</button>` : ''}
            <button type="button" class="gb-btn ${canContinue ? '' : 'gb-btn-primary'}" data-act="begin">${canContinue ? 'Start afresh' : 'Choose your investigator'}</button>
            <button type="button" class="gb-btn" data-act="source">Read the adventure file</button>
          </div>
        </article>`);
      card.querySelector('[data-act="begin"]').addEventListener('click', () => { use(entry); renderInvestigators(); });
      card.querySelector('[data-act="source"]').addEventListener('click', () => { use(entry); openSource(); });
      card.querySelector('[data-act="continue"]')?.addEventListener('click', () => { use(entry); state = saved; renderPlay(true); });
      covers.append(card);
    }
    wrap.append(covers);
    wrap.append(el(`<aside class="gb-card gb-howto">
      <h3 class="gb-deco">How to play</h3>
      <p>Read each numbered section and choose what to do. Some choices call for a <strong>d100 roll</strong>: roll your skill or lower to succeed. Hard checks need half your skill, extreme ones a fifth.</p>
      <p>A failed roll can be bought back with <strong>Luck</strong>, point for point. Sanity cannot. Lose five or more Sanity at once and a bout of madness takes you.</p>
      <p>Keep your companions sane, keep what you find, and mind the words you note in your journal. The island remembers.</p>
      <p>Once you are playing, press <strong>Full screen</strong> above the story: only the story scrolls, and your sheet stays in view.</p>
    </aside>`));
    root.append(wrap);
    if (focus) wrap.querySelector('.gb-cover-title').focus();
  }

  function use(entry) { adv = entry.adventure; advSource = entry.source; }

  function renderInvestigators() {
    applyImmersive(false);
    root.innerHTML = '';
    const screen = el(`<div class="gb-pick">
      <div class="gb-pick-head">
        <button type="button" class="gb-btn gb-btn-small" data-act="back">Back</button>
        <h2 class="gb-deco" tabindex="-1">Choose your investigator</h2>
        <p>${esc(adv.investigator_intro ?? '')}</p>
      </div>
      <div class="gb-pick-grid"></div>
    </div>`);
    screen.querySelector('[data-act="back"]').addEventListener('click', () => renderTitle(true));
    const grid = screen.querySelector('.gb-pick-grid');
    for (const inv of adv.investigators) {
      const top = Object.entries(inv.skills || {}).sort((a, b) => b[1] - a[1]).slice(0, 6);
      const card = el(`
        <article class="gb-card gb-inv">
          <p class="gb-kicker">${esc(inv.occupation)}</p>
          <h3 class="gb-inv-name">${esc(inv.name)}<span>, ${esc(inv.age)}</span></h3>
          <p class="gb-inv-bio">${inline(inv.bio)}</p>
          <dl class="gb-inv-stats">
            <div><dt>HP</dt><dd>${inv.hp}</dd></div><div><dt>SAN</dt><dd>${inv.san}</dd></div><div><dt>Luck</dt><dd>${inv.luck}</dd></div>
          </dl>
          <ul class="gb-inv-skills" role="list">${top.map(([k, v]) => `<li><span>${esc(k)}</span><b>${v}%</b></li>`).join('')}</ul>
          <p class="gb-inv-kit"><strong>Kit:</strong> ${(inv.kit || []).map((i) => esc(itemName(i))).join(', ') || 'the clothes on their back'}</p>
          <button type="button" class="gb-btn gb-btn-primary">Play as ${esc(inv.name.split(' ').slice(-1)[0])}</button>
        </article>`);
      card.querySelector('button').addEventListener('click', () => newGame(inv.id));
      grid.append(card);
    }
    root.append(screen);
    screen.querySelector('h2').focus();
  }

  // ---------- rendering: play screen ----------
  function renderPlay(scroll = false, animate = false) {
    const sec = section(state.section);
    if (!sec) { renderTitle(); return; }
    const prevScroll = root.querySelector('.gb-page')?.scrollTop ?? 0;
    root.innerHTML = '';
    const layout = el(`<div class="gb-play">
      <div class="gb-book-col">
        <div class="gb-toolbar">
          <span class="gb-toolbar-title">${esc(adv.title)}</span>
          <button type="button" class="gb-btn gb-btn-small" data-act="immersive" aria-pressed="${immersive}">${immersive ? 'Exit<span class="gb-wide-only"> full screen</span>' : 'Full screen'}</button>
          <button type="button" class="gb-btn gb-btn-small" data-act="source" aria-label="Adventure file"><span class="gb-wide-only">Adventure&nbsp;</span>file</button>
          <button type="button" class="gb-btn gb-btn-small" data-act="restart">Restart</button>
        </div>
        <article class="gb-page" aria-labelledby="gb-sec-heading"></article>
      </div>
      <aside class="gb-sheet" aria-label="Investigator sheet"></aside>
    </div>`);
    layout.querySelector('[data-act="immersive"]').addEventListener('click', () => setImmersive(!immersive));
    layout.querySelector('[data-act="source"]').addEventListener('click', openSource);
    layout.querySelector('[data-act="restart"]').addEventListener('click', () => {
      if (window.confirm('Abandon this investigation and start again?')) { store.clear(); renderTitle(true); }
    });
    const page = layout.querySelector('.gb-page');
    renderPage(page, sec, animate);
    renderSheet(layout.querySelector('.gb-sheet'));
    root.append(layout);
    applyImmersive(true);
    const smooth = REDUCED_MOTION ? 'auto' : 'smooth';
    if (scroll) {
      layout.querySelector('#gb-sec-heading').focus({ preventScroll: true });
      if (!immersive) {
        // Bring the new section's page under the site's sticky header.
        const head = headerHeight();
        const top = page.getBoundingClientRect().top;
        if (top < head || top > window.innerHeight * 0.5) window.scrollTo({ top: top + window.scrollY - head - 12, behavior: smooth });
      }
    } else page.scrollTop = prevScroll; // same section re-rendered (a roll, Luck spent): keep the reader's place
    if (state.pending) layout.querySelector('.gb-roll').scrollIntoView({ block: 'nearest', behavior: smooth });
  }

  // ---------- full screen: the story scrolls inside its page, the sheet stays put ----------
  const IMMERSIVE_KEY = 'cthulhu-solo:immersive';
  let immersive = (() => { try { return localStorage.getItem(IMMERSIVE_KEY) === '1'; } catch { return false; } })();

  function setImmersive(on) {
    immersive = on;
    try { localStorage.setItem(IMMERSIVE_KEY, on ? '1' : '0'); } catch { /* storage may be blocked */ }
    // Browser fullscreen hides the browser chrome too; the overlay works without it (e.g. iPhone Safari).
    if (on && !document.fullscreenElement) root.requestFullscreen?.().catch(() => {});
    renderPlay(false);
    root.querySelector('[data-act="immersive"]').focus();
  }

  /** The overlay only covers the play screen; the cover and the investigator picker stay in the page. */
  function applyImmersive(onPlayScreen) {
    const on = immersive && onPlayScreen;
    root.classList.toggle('is-immersive', on);
    document.documentElement.classList.toggle('gb-lock', on);
    if (!on && document.fullscreenElement === root) document.exitFullscreen?.().catch(() => {});
  }

  document.addEventListener('fullscreenchange', () => {
    // Esc in browser fullscreen leaves full screen mode altogether.
    if (!document.fullscreenElement && root.classList.contains('is-immersive')) setImmersive(false);
  });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && root.classList.contains('is-immersive') && !document.fullscreenElement && !dialog?.open) setImmersive(false);
  });

  /** The site header is sticky: keep the sheet and scroll targets clear of it. */
  function headerHeight() {
    const header = document.querySelector('body > header');
    const h = header && getComputedStyle(header).position === 'sticky' ? header.offsetHeight : 0;
    root.style.setProperty('--gb-head', `${h}px`);
    return h;
  }

  function renderPage(page, sec, animate) {
    const shown = (sec.extra || []).filter((x) => check(x.requires));
    const extras = (before) => shown.filter((x) => !!x.before === before).map((x) => paragraphs(x.text)).join('');
    page.innerHTML = `
      <header class="gb-sec-head">
        <span class="gb-sec-num" aria-hidden="true">${esc(state.section)}</span>
        <div>
          <p class="gb-kicker">${sec.ending ? `Ending // ${esc(ENDING_LABEL[sec.ending] ?? sec.ending.charAt(0).toUpperCase() + sec.ending.slice(1))}` : `Section ${esc(state.section)}`}</p>
          <h2 id="gb-sec-heading" class="gb-deco gb-sec-title" tabindex="-1">${esc(sec.title ?? `Section ${state.section}`)}</h2>
        </div>
      </header>
      ${ledger(state.entry, 'What just happened')}
      <div class="gb-prose">${extras(true)}${paragraphs(sec.text)}${extras(false)}</div>
      ${ledger(state.after ?? [], 'What it costs you', 'gb-ledger-after')}`;
    if (sec.ending) page.append(renderEnding(sec));
    else if (state.pending) page.append(renderRoll(animate));
    else page.append(renderChoices(sec));
  }

  const ledger = (lines, label, cls = '') => (lines.length
    ? `<ul class="gb-ledger ${cls}" role="list" aria-label="${label}">${lines.map((m) => `<li>${esc(m)}</li>`).join('')}</ul>` : '');

  function renderChoices(sec) {
    const list = el('<ol class="gb-choices" role="list" aria-label="What do you do?"></ol>');
    const choices = visibleChoices(sec);
    choices.forEach((c, i) => {
      const tags = tagsFor(c.requires);
      let rollTag = '';
      if (c.roll) {
        const s = bestSkill(c.roll.skill);
        const diff = c.roll.difficulty || 'regular';
        rollTag = `<span class="gb-roll-tag">Roll ${esc(s.name)} ${targetFor(s.value, diff)}%${diff !== 'regular' ? ` (${diff})` : ''}</span>`;
      }
      const li = el(`<li><button type="button" class="gb-choice">
        <span class="gb-choice-text">${inline(c.text)}</span>
        <span class="gb-choice-meta">${tags.map((t) => `<span class="gb-tag">${esc(t)}</span>`).join('')}${rollTag}<span class="gb-turn">${c.roll ? 'Roll' : `Turn to ${esc(c.to)}`}</span></span>
      </button></li>`);
      li.querySelector('button').addEventListener('click', () => choose(i));
      list.append(li);
    });
    if (!choices.length) list.append(el('<li class="gb-dead-end">The way is shut. (This section has no open choices: a flaw in the adventure file.)</li>'));
    return list;
  }

  function diceFaces(p) {
    const tens = p.dice.tens.map((t, i) => {
      const kept = i === p.dice.kept;
      return `<span class="gb-die gb-die-tens${kept ? '' : ' gb-die-dropped'}">${t}0</span>`;
    }).join('');
    return `${tens}<span class="gb-die">${p.dice.units}</span>`;
  }

  function renderRoll(animate) {
    const p = state.pending;
    const cost = p.dice.value - p.target;
    const canLuck = !p.success && p.grade !== 'fumble' && p.skill !== 'Luck' && cost <= state.luck;
    const outcome = p.luckSpent ? 'Passed with Luck' : p.success ? GRADE_LABEL[p.grade] : (p.grade === 'fumble' ? 'Fumble' : 'Failure');
    const bonusNote = p.bonus > 0 ? `${p.bonus} bonus die` : p.bonus < 0 ? `${-p.bonus} penalty die` : '';
    const box = el(`<div class="gb-roll" role="group" aria-label="Dice roll">
      <p class="gb-roll-what">${inline(p.text)}</p>
      <p class="gb-roll-need">${esc(p.skill)} ${p.value}%. Need ${p.target} or less${p.difficulty !== 'regular' ? ` (${p.difficulty})` : ''}${bonusNote ? `, ${bonusNote}` : ''}.</p>
      <div class="gb-dice" aria-hidden="true">${diceFaces(p)}</div>
      <p class="gb-roll-result ${p.success ? 'is-pass' : 'is-fail'}" tabindex="-1"><span class="gb-roll-value">${p.dice.value}</span> ${esc(outcome)}</p>
      <div class="gb-actions"></div>
    </div>`);
    const actions = box.querySelector('.gb-actions');
    if (canLuck) {
      const b = el(`<button type="button" class="gb-btn">Spend ${cost} Luck to pass (you have ${state.luck})</button>`);
      b.addEventListener('click', spendLuck);
      actions.append(b);
    }
    const go = el('<button type="button" class="gb-btn gb-btn-primary">Turn the page</button>');
    go.addEventListener('click', continueRoll);
    actions.append(go);
    if (animate && !REDUCED_MOTION) {
      box.classList.add('is-rolling');
      const faces = box.querySelectorAll('.gb-die');
      let ticks = 0;
      const timer = setInterval(() => {
        faces.forEach((f, i) => { f.textContent = i < faces.length - 1 ? `${rand(10)}0` : rand(10); });
        if (++ticks > 9) {
          clearInterval(timer);
          box.querySelector('.gb-dice').innerHTML = diceFaces(p);
          box.classList.remove('is-rolling');
          box.querySelector('.gb-roll-result').focus();
        }
      }, 55);
    } else queueMicrotask(() => box.querySelector('.gb-roll-result').focus());
    return box;
  }

  function renderEnding(sec) {
    const fates = adv.companions.map((c) => {
      const s = state.companions[c.id];
      const label = { with: 'came through', broken: 'broken in mind', lost: 'lost on the island', dead: 'dead' }[s.status];
      return `<li><span>${esc(c.name)}</span><b>${label}</b></li>`;
    }).join('');
    const box = el(`<div class="gb-ending">
      <p class="gb-ending-stamp">The End</p>
      <ul class="gb-fates" role="list">${fates}</ul>
      <p class="gb-ending-count">You read ${state.log.length} of ${Object.keys(adv.sections).length} sections. Every other path is still out there in the fog.</p>
      <div class="gb-actions">
        <button type="button" class="gb-btn gb-btn-primary" data-act="again">Play again</button>
        <button type="button" class="gb-btn" data-act="title">Back to the cover</button>
      </div>
    </div>`);
    box.querySelector('[data-act="again"]').addEventListener('click', () => { store.clear(); renderInvestigators(); });
    box.querySelector('[data-act="title"]').addEventListener('click', () => { store.clear(); renderTitle(true); });
    return box;
  }

  function bar(label, value, max, cls, name = label) {
    const pct = max ? clamp(Math.round((value / max) * 100), 0, 100) : 0;
    return `<div class="gb-bar ${cls}">
      <div class="gb-bar-label"><span>${label}</span><b>${value}<small>/${max}</small></b></div>
      <div class="gb-bar-track" role="meter" aria-label="${esc(name)}" aria-valuemin="0" aria-valuemax="${max}" aria-valuenow="${value}" aria-valuetext="${value} of ${max}"><div style="width:${pct}%"></div></div>
    </div>`;
  }

  function renderSheet(sheet) {
    const inv = investigator();
    const skills = Object.entries(inv.skills || {}).sort((a, b) => b[1] - a[1]);
    const party = adv.companions.map((c) => {
      const s = state.companions[c.id];
      const status = { with: '', broken: 'Broken', lost: 'Lost', dead: 'Dead' }[s.status];
      return `<li class="gb-party-${s.status}">
        <div class="gb-party-name"><strong>${esc(c.name)}</strong>${status ? `<em>${status}</em>` : ''}</div>
        <p>${esc(c.role)}</p>
        ${s.status === 'with' ? bar('SAN', s.san, c.san, 'gb-bar-san', `${c.short ?? c.name} sanity`) : ''}
      </li>`;
    }).join('');
    const block = (cls, title, inner) => `<div class="gb-block ${cls}">${title ? `<h3 class="gb-sheet-h">${title}</h3>` : ''}${inner}</div>`;
    // Two groups: in full screen on a wide display they become two columns; otherwise CSS order interleaves them.
    sheet.innerHTML = `
      <details class="gb-sheet-inner"${sheetOpen ? ' open' : ''}>
        <summary>
          <span class="gb-kicker">Investigator</span> <span class="gb-sheet-name">${esc(inv.name)}</span> <span class="gb-sheet-occ">${esc(inv.occupation)}</span>
          <span class="gb-sheet-quick">HP ${state.hp}/${inv.hp} · SAN ${state.san}/${inv.san} · Luck ${state.luck}</span>
        </summary>
        <div class="gb-sheet-body">
          <div class="gb-sheet-a">
            ${block('gb-block-vitals', '', `${bar('Hit points', state.hp, inv.hp, 'gb-bar-hp')}
              ${bar('Sanity', state.san, inv.san, 'gb-bar-san')}
              ${bar('Luck', state.luck, 99, 'gb-bar-luck')}
              ${state.penalty ? '<p class="gb-warn">Shaken: your next roll takes a penalty die.</p>' : ''}`)}
            ${block('gb-block-chars', 'Characteristics', `<dl class="gb-chars">${CHARACTERISTICS.map((c) => `<div><dt>${c}</dt><dd>${inv.characteristics[c]}</dd></div>`).join('')}</dl>`)}
            ${block('gb-block-skills', 'Skills', `<ul class="gb-skill-list" role="list">${skills.map(([k, v]) => `<li><span>${esc(k)}</span><b>${v}%</b></li>`).join('')}
              <li class="gb-skill-base"><span>Dodge</span><b>${skillValue('Dodge')}%</b></li></ul>`)}
          </div>
          <div class="gb-sheet-b">
            ${block('gb-block-party', 'Your party', `<ul class="gb-party" role="list">${party}</ul>`)}
            ${block('gb-block-items', 'Possessions', `<ul class="gb-items" role="list">${state.items.map((i) => `<li><strong>${esc(itemName(i))}</strong><span>${esc(adv.items?.[i]?.text ?? '')}</span></li>`).join('') || '<li class="gb-empty">Nothing but wet clothes.</li>'}</ul>`)}
            ${block('gb-block-journal', 'Journal', `<ul class="gb-notes" role="list">${state.notes.map((n) => `<li><strong>${esc(n)}</strong><span>${esc(adv.journal?.[n] ?? '')}</span></li>`).join('') || '<li class="gb-empty">No words noted yet.</li>'}</ul>`)}
            <p class="gb-sheet-foot gb-block-foot">Sections read: ${state.log.length}</p>
          </div>
        </div>
      </details>`;
    sheet.querySelector('details').addEventListener('toggle', (e) => { sheetOpen = e.target.open; });
  }

  // ---------- source viewer ----------
  const dialog = document.getElementById('gb-source');
  function openSource() {
    document.getElementById('gb-source-text').textContent = advSource;
    if (dialog.showModal) dialog.showModal(); else dialog.setAttribute('open', '');
  }
  dialog?.querySelector('[data-close]').addEventListener('click', () => dialog.close());

  // ---------- boot ----------
  async function load(file) {
    const res = await fetch(BASE + file);
    if (!res.ok) throw new Error(`Could not load ${file} (${res.status}).`);
    return res.text();
  }

  async function boot() {
    if (!window.jsyaml) { showError('The YAML reader (js-yaml) did not load. Check your connection and reload.'); return; }
    try {
      const index = window.jsyaml.load(await load(INDEX.slice(BASE.length)));
      catalogue = await Promise.all(index.adventures.map(async (a) => {
        const source = await load(a.file);
        return { file: a.file, source, adventure: window.jsyaml.load(source) };
      }));
    } catch (err) {
      showError(err.message);
      return;
    }
    use(catalogue[0]);
    renderTitle();
  }
  headerHeight();
  window.addEventListener('resize', headerHeight);
  boot();
})();
