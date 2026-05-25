/**
 * Showcase demo-MVP page — vertical cards, live playground, lead form.
 */
(function () {
  'use strict';

  const NODE_LABELS = {
    trg: 'Webhook-триггер',
    r1: 'Research: продукт и pricing',
    r2: 'Research: новости и funding',
    merge: 'Объединение данных',
    an: 'SWOT + 3 actions',
    doc: 'Генерация DOCX',
    n8n: 'Триггер n8n',
  };

  const STATUS_LABELS = { live: 'Production', lab: 'R&D Lab' };

  let showcaseData = null;
  let pollTimer = null;
  let nodeOrder = Object.keys(NODE_LABELS);

  const cardsEl = document.getElementById('showcaseCards');
  const marketplaceEl = document.getElementById('marketplaceGrid');
  const presetsEl = document.getElementById('playgroundPresets');
  const playgroundForm = document.getElementById('playgroundForm');
  const runBtn = document.getElementById('playgroundRunBtn');
  const stepper = document.getElementById('playgroundStepper');
  const timeline = document.getElementById('playgroundTimeline');
  const skeleton = document.getElementById('playgroundSkeleton');
  const metricsEl = document.getElementById('playgroundMetrics');
  const resultsEl = document.getElementById('playgroundResults');
  const errorEl = document.getElementById('showcaseError');
  const leadForm = document.getElementById('leadForm');
  const leadThankyou = document.getElementById('leadThankyou');
  const verticalSelect = document.getElementById('leadVertical');

  function showError(msg) {
    if (!errorEl) return;
    errorEl.textContent = msg;
    errorEl.classList.add('visible');
  }

  function hideError() {
    if (errorEl) errorEl.classList.remove('visible');
  }

  function formatTokens(n) {
    if (n >= 1000) return (n / 1000).toFixed(1) + 'k';
    return String(n);
  }

  function getLogMessage(log) {
    const d = log.detail;
    if (typeof d === 'string') return d;
    if (d && typeof d.message === 'string') return d.message;
    if (d && d.output && typeof d.output.summary === 'string') {
      return d.output.summary.slice(0, 80) + '…';
    }
    return '';
  }

  function renderStepper(order, labels, logs, status) {
    if (!stepper) return;
    const completed = new Set();
    let running = null;
    const logByNode = {};

    for (const log of logs) {
      if (log.node_id) logByNode[log.node_id] = log;
      if (log.event === 'completed' && log.node_id) completed.add(log.node_id);
      if (log.event === 'started' && log.node_id && !completed.has(log.node_id)) {
        running = log.node_id;
      }
    }
    if (status === 'success') order.forEach((id) => completed.add(id));

    stepper.innerHTML = order
      .map((id) => {
        const label = labels[id] || NODE_LABELS[id] || id;
        let cls = 'demo-step';
        let marker = '○';
        if (completed.has(id)) {
          cls += ' done';
          marker = '✓';
        } else if (running === id) {
          cls += ' running';
          marker = '●';
        }
        const log = logByNode[id];
        const snippet = log ? getLogMessage(log) : '';
        return `<div class="${cls}" data-node="${id}">
          <div class="demo-step-marker">${marker}</div>
          <div>
            <div class="demo-step-label">${label}</div>
            ${snippet ? `<div class="demo-step-log">${snippet}</div>` : ''}
          </div>
        </div>`;
      })
      .join('');
  }

  function renderCard(card) {
    const statusClass = card.status === 'live' ? 'showcase-badge--live' : 'showcase-badge--lab';
    const statusLabel = STATUS_LABELS[card.status] || card.status;
    const snippets = (card.persona.snippets || [])
      .map(
        (s) =>
          `<div class="persona-snippet" data-type="${s.type || 'default'}">${escapeHtml(s.text)}</div>`,
      )
      .join('');

    const ctaHref = card.cta_url || (card.id === 'my-agent' ? '#playground' : null);
    const ctaBtn = ctaHref
      ? `<a href="${escapeHtml(ctaHref)}" class="btn btn-primary">${escapeHtml(card.cta_label)}</a>`
      : `<span class="btn btn-secondary" style="opacity:0.7;cursor:default">${escapeHtml(card.cta_label)}</span>`;

    return `<article class="showcase-card reveal" data-status="${card.status}" data-id="${card.id}">
      <div class="showcase-card-header">
        <div class="showcase-card-icon">
          <img src="/welcome-assets/assets/icons/${card.icon}.svg" alt="" width="44" height="44">
        </div>
        <div class="showcase-card-meta">
          <div class="showcase-card-vertical">${escapeHtml(card.vertical)}</div>
          <h3 class="showcase-card-title">${escapeHtml(card.title)}</h3>
        </div>
      </div>
      <div class="showcase-badges">
        <span class="showcase-badge ${statusClass}">${statusLabel}</span>
        <span class="showcase-badge">${escapeHtml(card.platform)}</span>
        <span class="showcase-badge">${escapeHtml(card.llm)}</span>
      </div>
      <p class="showcase-card-desc">${escapeHtml(card.one_liner)}</p>
      <p class="showcase-card-metric">${escapeHtml(card.metric)}</p>
      <details class="persona-accordion">
        <summary>Persona YAML preview</summary>
        <div class="persona-accordion-body">
          <div class="persona-role">${escapeHtml(card.persona.role)}</div>
          <div class="persona-voice">${escapeHtml(card.persona.voice)}</div>
          ${snippets}
        </div>
      </details>
      <div class="showcase-card-cta">${ctaBtn}</div>
    </article>`;
  }

  function renderMarketplaceCard(tpl) {
    return `<div class="marketplace-mini-card reveal">
      <div class="category">${escapeHtml(tpl.category)}</div>
      <h3>${escapeHtml(tpl.name)}</h3>
      <p>${escapeHtml(tpl.description)}</p>
      <div class="nodes">${tpl.nodes} nodes</div>
    </div>`;
  }

  function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  function populateVerticalSelect(cards) {
    if (!verticalSelect) return;
    cards.forEach((c) => {
      const opt = document.createElement('option');
      opt.value = c.id;
      opt.textContent = c.title;
      verticalSelect.appendChild(opt);
    });
  }

  function initStats(meta) {
    ['live', 'personas', 'templates'].forEach((key) => {
      const el = document.querySelector(`[data-stat="${key}"]`);
      if (!el) return;
      const map = {
        live: meta.live_deployments,
        personas: meta.personas,
        templates: meta.templates,
      };
      el.textContent = map[key];
    });
  }

  async function loadShowcaseData() {
    const res = await fetch('/welcome-assets/data/showcase.json');
    if (!res.ok) throw new Error('Не удалось загрузить showcase data');
    showcaseData = await res.json();

    initStats(showcaseData.meta);

    if (cardsEl) {
      cardsEl.innerHTML = showcaseData.cards.map(renderCard).join('');
    }

    if (marketplaceEl) {
      marketplaceEl.innerHTML = showcaseData.featured_templates.map(renderMarketplaceCard).join('');
    }

    populateVerticalSelect(showcaseData.cards);

    if (presetsEl && showcaseData.playground_presets) {
      presetsEl.innerHTML = showcaseData.playground_presets
        .map(
          (p, i) =>
            `<button type="button" class="preset-chip${i === 0 ? ' active' : ''}" data-target="${escapeHtml(p.target)}" data-our="${escapeHtml(p.our_company)}" data-id="${p.id}">${escapeHtml(p.label)}</button>`,
        )
        .join('');

      const first = showcaseData.playground_presets[0];
      const targetInput = document.getElementById('playgroundTarget');
      const ourInput = document.getElementById('playgroundOur');
      if (targetInput) targetInput.value = first.target;
      if (ourInput) ourInput.value = first.our_company;
    }

    document.querySelectorAll('.showcase-grid .reveal, .marketplace-mini-grid .reveal').forEach((el) => {
      el.classList.add('visible');
    });
  }

  function pollRun(runId, labels) {
    pollTimer = window.setInterval(async () => {
      try {
        const res = await fetch(`/api/demo/public/runs/${runId}`);
        if (!res.ok) throw new Error('Run not found');
        const data = await res.json();
        const order = data.node_order || nodeOrder;
        const lbl = data.node_labels || labels;
        renderStepper(order, lbl, data.logs || [], data.status);

        if (data.status === 'success' || data.status === 'failed') {
          clearInterval(pollTimer);
          pollTimer = null;
          if (skeleton) skeleton.classList.remove('visible');
          if (runBtn) {
            runBtn.disabled = false;
            runBtn.textContent = 'Запустить demo';
          }

          if (data.summary && metricsEl) {
            metricsEl.hidden = false;
            const costEl = document.getElementById('pgMetricCost');
            const tokensEl = document.getElementById('pgMetricTokens');
            const savedEl = document.getElementById('pgMetricSaved');
            if (costEl) costEl.textContent = '$' + (data.summary.estimated_cost_usd || 0.42).toFixed(2);
            if (tokensEl) tokensEl.textContent = formatTokens(data.summary.tokens_used || 18420);
            if (savedEl) savedEl.textContent = '~' + (data.summary.hours_saved || 4) + 'ч';
          }

          if (resultsEl) {
            resultsEl.hidden = false;
          }

          if (data.status === 'failed') showError('Demo завершился с ошибкой.');
        }
      } catch (e) {
        clearInterval(pollTimer);
        pollTimer = null;
        if (skeleton) skeleton.classList.remove('visible');
        if (runBtn) {
          runBtn.disabled = false;
          runBtn.textContent = 'Запустить demo';
        }
        showError(e.message || 'Ошибка polling');
      }
    }, 500);
  }

  if (presetsEl) {
    presetsEl.addEventListener('click', (e) => {
      const chip = e.target.closest('.preset-chip');
      if (!chip) return;
      presetsEl.querySelectorAll('.preset-chip').forEach((c) => c.classList.remove('active'));
      chip.classList.add('active');
      const targetInput = document.getElementById('playgroundTarget');
      const ourInput = document.getElementById('playgroundOur');
      if (targetInput) targetInput.value = chip.dataset.target || '';
      if (ourInput) ourInput.value = chip.dataset.our || '';
    });
  }

  if (playgroundForm) {
    playgroundForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      hideError();
      if (pollTimer) clearInterval(pollTimer);

      const target = document.getElementById('playgroundTarget').value.trim() || 'Notion';
      const ourCompany = document.getElementById('playgroundOur').value.trim() || 'Linear';

      runBtn.disabled = true;
      runBtn.textContent = 'Запуск…';
      if (metricsEl) metricsEl.hidden = true;
      if (resultsEl) resultsEl.hidden = true;
      if (skeleton) skeleton.classList.add('visible');
      if (timeline) timeline.hidden = false;

      try {
        const res = await fetch('/api/demo/public/run', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ target, our_company: ourCompany, real: false }),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Не удалось запустить demo');

        nodeOrder = data.node_order || nodeOrder;
        const labels = {};
        nodeOrder.forEach((id) => {
          labels[id] = NODE_LABELS[id] || id;
        });
        renderStepper(nodeOrder, labels, [], 'running');
        pollRun(data.run_id, labels);
      } catch (err) {
        if (skeleton) skeleton.classList.remove('visible');
        runBtn.disabled = false;
        runBtn.textContent = 'Запустить demo';
        showError(err.message || 'Ошибка запуска');
      }
    });
  }

  if (leadForm) {
    leadForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      hideError();

      const telegram = document.getElementById('leadTelegram').value.trim();
      const vertical = verticalSelect ? verticalSelect.value : 'ararat';
      const email = document.getElementById('leadEmail').value.trim();

      if (!telegram || !email) {
        showError('Заполните Telegram и email');
        return;
      }

      const submitBtn = leadForm.querySelector('button[type="submit"]');
      submitBtn.disabled = true;
      submitBtn.textContent = 'Отправка…';

      try {
        const res = await fetch('/api/leads/showcase', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ telegram, vertical, email }),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Ошибка отправки');

        leadForm.hidden = true;
        leadThankyou.hidden = false;

        const tgLink = document.getElementById('leadTelegramLink');
        if (tgLink) {
          tgLink.href = `https://t.me/my_agent_demo_bot?start=preset_${vertical}`;
        }
      } catch (err) {
        showError(err.message || 'Ошибка отправки');
        submitBtn.disabled = false;
        submitBtn.textContent = 'Получить AI-оператора';
      }
    });
  }

  loadShowcaseData().catch((err) => {
    showError(err.message || 'Ошибка загрузки страницы');
  });
})();
