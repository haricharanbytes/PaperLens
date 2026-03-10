// static/js/app.js
// Mirrors main.py pipeline — calls Flask API routes

const state = {
  tab:    'id',
  paper:  null,
  results: [],
};

// ── Tab switching ─────────────────────────────────────────────────────────────
document.querySelectorAll('.stab').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.stab').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    state.tab = btn.dataset.tab;

    const placeholders = {
      id:    'e.g. 2303.08774',
      url:   'e.g. https://arxiv.org/abs/2303.08774',
      title: 'e.g. attention is all you need',
    };
    document.getElementById('search-input').placeholder = placeholders[state.tab];

    hide('results-list');
    hide('paper-strip');
    state.paper   = null;
    state.results = [];
  });
});

// Model label in nav
document.getElementById('model-select').addEventListener('change', e => {
  document.getElementById('model-label').textContent = e.target.value;
});

// ── Search ────────────────────────────────────────────────────────────────────
document.getElementById('search-btn').addEventListener('click', doSearch);
document.getElementById('search-input').addEventListener('keydown', e => {
  if (e.key === 'Enter') doSearch();
});

async function doSearch() {
  const query = document.getElementById('search-input').value.trim();
  if (!query) return;

  clearError();
  hide('results-list');
  hide('paper-strip');
  hide('output');

  const btn = document.getElementById('search-btn');
  btn.disabled    = true;
  btn.textContent = '...';

  try {
    const res  = await fetch('/api/fetch', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ query }),
    });
    const data = await res.json();

    if (data.error) throw new Error(data.error);

    if (data.type === 'single') {
      setPaper(data.paper);
    } else {
      // Title search → show list
      state.results = data.papers;
      renderResultsList(data.papers);
    }
  } catch(e) {
    showError(e.message);
  } finally {
    btn.disabled    = false;
    btn.textContent = 'Search';
  }
}

function renderResultsList(papers) {
  const el = document.getElementById('results-list');
  el.innerHTML = papers.map((p, i) => `
    <div class="result-item" data-idx="${i}">
      <div class="ri-num">${i + 1}</div>
      <div>
        <div class="ri-title">${p.title}</div>
        <div class="ri-meta">
          <span>👤 ${p.authors.slice(0, 2).join(', ')}${p.authors.length > 2 ? ' et al.' : ''}</span>
          <span>📅 ${p.published}</span>
          <span>🏷 ${p.categories?.[0] || ''}</span>
        </div>
      </div>
    </div>
  `).join('');

  el.querySelectorAll('.result-item').forEach(item => {
    item.addEventListener('click', () => {
      el.querySelectorAll('.result-item').forEach(i => i.classList.remove('selected'));
      item.classList.add('selected');
      setPaper(state.results[parseInt(item.dataset.idx)]);
    });
  });

  show('results-list');
}

function setPaper(paper) {
  state.paper = paper;

  document.getElementById('ps-id').textContent    = paper.id || '';
  document.getElementById('ps-title').textContent = paper.title;
  document.getElementById('ps-meta').textContent  =
    `${paper.authors?.slice(0, 3).join(', ')}${paper.authors?.length > 3 ? ' et al.' : ''}  ·  ${paper.published}`;

  show('paper-strip');
}

// ── Run pipeline ──────────────────────────────────────────────────────────────
document.getElementById('run-btn').addEventListener('click', runPipeline);

async function runPipeline() {
  if (!state.paper) return;
  clearError();
  hide('output');

  const model   = document.getElementById('model-select').value;
  const explain = document.getElementById('toggle-explain').checked;

  // Show progress
  showProgress();
  setStep('ps-fetch', 'done');
  setStep('ps-clean', 'active');

  const runBtn = document.getElementById('run-btn');
  runBtn.disabled = true;

  try {
    // Small delay so user sees the steps animate
    await sleep(400);
    setStep('ps-clean', 'done');
    setStep('ps-sum', 'active');
    setMsg('Summarizing with ' + model + '...');

    const res  = await fetch('/api/summarize', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ paper: state.paper, model, explain }),
    });
    const data = await res.json();

    if (data.error) throw new Error(data.error);

    setStep('ps-sum', 'done');

    if (explain && data.concepts?.length) {
      setStep('ps-explain', 'active');
      setMsg('Concepts explained.');
      await sleep(300);
      setStep('ps-explain', 'done');
    }

    setMsg(`Done · ${data.meta.chunks} chunk(s) · ~${data.meta.token_count} tokens`);

    renderOutput(data);

  } catch(e) {
    showError(e.message);
    hide('progress');
  } finally {
    runBtn.disabled = false;
  }
}

// ── Render output ─────────────────────────────────────────────────────────────
function renderOutput(data) {
  const paper = state.paper;

  document.getElementById('out-title').textContent = paper.title;

  // Parse and render summary cards
  const sections = parseSummary(data.summary);
  const grid     = document.getElementById('cards-grid');

  grid.innerHTML = Object.entries(sections).map(([key, s]) => {
    const isList = key === 'contrib';
    let body = s.content || '—';

    if (isList) {
      const lines = body.split('\n').filter(l => l.trim());
      body = `<ul>${lines.map(l => `<li>${l.replace(/^[•·\-\*›]\s*/, '')}</li>`).join('')}</ul>`;
    }

    return `
      <div class="sum-card">
        <div class="sum-card-label">${s.emoji} &nbsp;${s.label}</div>
        <div class="sum-card-body">${body}</div>
      </div>`;
  }).join('');

  // Render concepts
  const conSection = document.getElementById('concepts-section');
  const conGrid    = document.getElementById('concepts-grid');

  if (data.concepts?.length) {
    conGrid.innerHTML = data.concepts.map(c => `
      <div class="concept-card">
        <div class="concept-term">${c.term}</div>
        <div class="concept-section">
          <div class="concept-section-label">📖 Definition</div>
          <div class="concept-section-text">${c.definition || c.explanation || '—'}</div>
        </div>
        <div class="concept-section">
          <div class="concept-section-label">🔗 Analogy</div>
          <div class="concept-section-text">${c.analogy || '—'}</div>
        </div>
        <div class="concept-section">
          <div class="concept-section-label">🔬 In this paper</div>
          <div class="concept-section-text">${c.in_paper || '—'}</div>
        </div>
      </div>`).join('');
    show('concepts-section');
  } else {
    hide('concepts-section');
  }

  show('output');
  hide('progress');
  document.getElementById('output').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// ── Parse LLM summary into sections ──────────────────────────────────────────
function parseSummary(text) {
  const sections = {
    what:    { emoji: '🎯', label: 'WHAT IS IT ABOUT',  content: '' },
    contrib: { emoji: '🔬', label: 'KEY CONTRIBUTIONS', content: '' },
    method:  { emoji: '⚙️', label: 'METHODOLOGY',       content: '' },
    results: { emoji: '📊', label: 'RESULTS & IMPACT',  content: '' },
  };

  const whatM    = text.match(/WHAT[^?\n]*\?\s*([\s\S]*?)(?=🔬|KEY CONTRIB|⚙️|HOW DID|📊|RESULTS|$)/i);
  const contribM = text.match(/KEY CONTRIBUTIONS?\s*([\s\S]*?)(?=⚙️|HOW DID|📊|RESULTS|$)/i);
  const methodM  = text.match(/HOW DID[\s\S]*?\n([\s\S]*?)(?=📊|RESULTS|$)/i);
  const resultsM = text.match(/(?:RESULTS|IMPACT)[^\n]*\n([\s\S]*?)$/i);

  if (whatM)    sections.what.content    = whatM[1].trim();
  if (contribM) sections.contrib.content = contribM[1].trim();
  if (methodM)  sections.method.content  = methodM[1].trim();
  if (resultsM) sections.results.content = resultsM[1].trim();

  // Fallback
  if (!sections.what.content) {
    const parts = text.split(/\n\n+/);
    ['what','contrib','method','results'].forEach((k, i) => {
      if (parts[i]) sections[k].content = parts[i].trim();
    });
  }

  return sections;
}

// ── Progress helpers ──────────────────────────────────────────────────────────
function showProgress() {
  ['ps-fetch','ps-clean','ps-sum','ps-explain'].forEach(id => {
    const el = document.getElementById(id);
    el.classList.remove('active','done');
  });
  setStep('ps-fetch', 'active');
  setMsg('Fetching paper...');
  show('progress');
}

function setStep(id, state) {
  const el = document.getElementById(id);
  el.classList.remove('active','done');
  if (state) el.classList.add(state);
}

function setMsg(msg) {
  document.getElementById('progress-msg').textContent = msg;
}

// ── Utility ───────────────────────────────────────────────────────────────────
function show(id) { document.getElementById(id).classList.remove('hidden'); }
function hide(id) { document.getElementById(id).classList.add('hidden'); }

function showError(msg) {
  const el = document.getElementById('error-box');
  el.textContent = '⚠ ' + msg;
  el.classList.remove('hidden');
}

function clearError() {
  document.getElementById('error-box').classList.add('hidden');
}

const sleep = ms => new Promise(r => setTimeout(r, ms));