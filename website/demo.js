/**
 * Public live demo — stepper timeline with RU labels.
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

  const form = document.getElementById('demoForm');
  const runBtn = document.getElementById('runBtn');
  const errorEl = document.getElementById('demoError');
  const timeline = document.getElementById('timeline');
  const stepper = document.getElementById('demoStepper');
  const skeleton = document.getElementById('demoSkeleton');
  const metrics = document.getElementById('metrics');
  const resultActions = document.getElementById('resultActions');
  const stickyCta = document.getElementById('stickyCta');
  const presets = document.getElementById('demoPresets');

  let pollTimer = null;
  let nodeOrder = Object.keys(NODE_LABELS);

  function showError(msg) {
    errorEl.textContent = msg;
    errorEl.classList.add('visible');
  }

  function hideError() {
    errorEl.classList.remove('visible');
  }

  function formatTokens(n) {
    if (n >= 1000) return (n / 1000).toFixed(1) + 'k';
    return String(n);
  }

  function getLogMessage(log) {
    const d = log.detail;
    if (typeof d === 'string') return d;
    if (d && typeof d.message === 'string') return d.message;
    if (d && d.output && typeof d.output.summary === 'string') return d.output.summary.slice(0, 80) + '…';
    return '';
  }

  function renderStepper(order, labels, logs, status) {
    const completed = new Set();
    let running = null;
    const logByNode = {};

    for (const log of logs) {
      if (log.node_id) logByNode[log.node_id] = log;
      if (log.event === 'completed' && log.node_id) completed.add(log.node_id);
      if (log.event === 'started' && log.node_id && !completed.has(log.node_id)) running = log.node_id;
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
          <div class="demo-step-label">${label}</div>
          ${snippet ? `<div class="demo-step-log">${snippet}</div>` : ''}
        </div>`;
      })
      .join('');
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
          skeleton.classList.remove('visible');
          runBtn.disabled = false;
          runBtn.textContent = 'Запустить за 90 сек';

          if (data.summary) {
            document.getElementById('metricCost').textContent =
              '$' + (data.summary.estimated_cost_usd || 0.42).toFixed(2);
            document.getElementById('metricTokens').textContent = formatTokens(data.summary.tokens_used || 18420);
          }

          metrics.classList.add('visible');
          resultActions.hidden = false;
          setTimeout(() => stickyCta.classList.add('visible'), 400);

          if (data.status === 'failed') showError('Demo завершился с ошибкой. Попробуйте снова.');
        }
      } catch (e) {
        clearInterval(pollTimer);
        pollTimer = null;
        skeleton.classList.remove('visible');
        runBtn.disabled = false;
        runBtn.textContent = 'Запустить за 90 сек';
        showError(e.message || 'Ошибка polling');
      }
    }, 500);
  }

  if (presets) {
    presets.addEventListener('click', (e) => {
      const chip = e.target.closest('.preset-chip');
      if (!chip) return;
      presets.querySelectorAll('.preset-chip').forEach((c) => c.classList.remove('active'));
      chip.classList.add('active');
      document.getElementById('target').value = chip.dataset.target || '';
      document.getElementById('ourCompany').value = chip.dataset.our || '';
    });
  }

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    hideError();
    if (pollTimer) clearInterval(pollTimer);

    const target = document.getElementById('target').value.trim() || 'Notion';
    const ourCompany = document.getElementById('ourCompany').value.trim() || 'Linear';

    runBtn.disabled = true;
    runBtn.textContent = 'Запуск…';
    metrics.classList.remove('visible');
    resultActions.hidden = true;
    stickyCta.classList.remove('visible');
    skeleton.classList.add('visible');
    timeline.hidden = false;

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
      nodeOrder.forEach((id) => { labels[id] = NODE_LABELS[id] || id; });
      renderStepper(nodeOrder, labels, [], 'running');
      pollRun(data.run_id, labels);
    } catch (err) {
      skeleton.classList.remove('visible');
      runBtn.disabled = false;
      runBtn.textContent = 'Запустить за 90 сек';
      showError(err.message || 'Ошибка запуска');
    }
  });
})();
