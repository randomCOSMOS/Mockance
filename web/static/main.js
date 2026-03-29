/* ── Navigation ── */
const navItems = document.querySelectorAll('.nav-item');
const views    = document.querySelectorAll('.view');

navItems.forEach(btn => {
  btn.addEventListener('click', () => {
    const target = btn.dataset.view;
    navItems.forEach(b => b.classList.remove('active'));
    views.forEach(v => v.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById(`view-${target}`).classList.add('active');

    if (target === 'wallet')    loadWallet();
    if (target === 'positions') loadPositions();
  });
});

let selectedSide = 'BUY';
let selectedType = 'MARKET';

document.querySelectorAll('#side-toggle .toggle-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('#side-toggle .toggle-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    selectedSide = btn.dataset.val;
    updateSubmitBtn();
  });
});

document.querySelectorAll('#type-toggle .toggle-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('#type-toggle .toggle-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    selectedType = btn.dataset.val;
    updateConditionalFields();
  });
});

function updateConditionalFields() {
  const priceField = document.getElementById('field-price');
  priceField.classList.remove('visible');
  if (selectedType === 'LIMIT') priceField.classList.add('visible');
  const priceLabel = priceField.querySelector('label');
  if (selectedType === 'LIMIT') priceLabel.childNodes[0].textContent = 'Limit Price ';
}

function updateSubmitBtn() {
  const btn     = document.getElementById('submit-btn');
  const btnText = btn.querySelector('.btn-text');
  const isDry   = document.getElementById('dry-run').checked;
  const sideLbl = selectedSide === 'BUY' ? 'Buy' : 'Sell';
  if (btnText) btnText.textContent = isDry ? `Dry Run — ${sideLbl}` : `${sideLbl} ${selectedType.replace('-', ' ')}`;
  btn.style.background = isDry
    ? 'var(--surface2)'
    : selectedSide === 'BUY' ? 'var(--green)' : 'var(--red)';
  btn.style.color = isDry ? 'var(--text)' : '#000';
}

document.getElementById('dry-run').addEventListener('change', updateSubmitBtn);
updateConditionalFields();
updateSubmitBtn();

document.getElementById('order-form').addEventListener('submit', async e => {
  e.preventDefault();
  const errorEl   = document.getElementById('form-error');
  const submitBtn = document.getElementById('submit-btn');
  const btnText   = submitBtn.querySelector('.btn-text');
  const btnLoader = submitBtn.querySelector('.btn-loader');
  const isDry     = document.getElementById('dry-run').checked;

  errorEl.classList.add('hidden');
  submitBtn.disabled = true;
  btnText.classList.add('hidden');
  btnLoader.classList.remove('hidden');

  const body = {
    symbol:    document.getElementById('symbol').value.trim().toUpperCase(),
    side:      selectedSide,
    orderType: selectedType,
    quantity:  document.getElementById('quantity').value,
    price:     document.getElementById('price').value || null,
    dryRun:    isDry,
  };

  try {
    const res  = await fetch('/api/order', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    const data = await res.json();

    if (isDry && data.ok) {
      renderDryRun(body);
    } else if (data.ok) {
      renderOrderResult(data.order);
    } else {
      errorEl.textContent = data.msg || 'Unknown error';
      errorEl.classList.remove('hidden');
    }
  } catch (err) {
    errorEl.textContent = 'Network error — is the server running?';
    errorEl.classList.remove('hidden');
  } finally {
    submitBtn.disabled = false;
    btnText.classList.remove('hidden');
    btnLoader.classList.add('hidden');
  }
});

function renderOrderResult(order) {
  const empty   = document.querySelector('.result-empty');
  const content = document.getElementById('result-content');
  empty.classList.add('hidden');
  content.classList.remove('hidden');

  const status   = order.status || 'UNKNOWN';
  const badgeCls = status === 'FILLED' ? 'filled' : 'pending';
  const avgPrice = parseFloat(order.avgPrice || '0');
  const side     = order.side || '';

  content.innerHTML = `
    <div class="result-badge ${badgeCls}">${status}</div>
    ${row('Order ID',   `#${order.orderId}`)}
    ${row('Symbol',     order.symbol, '')}
    ${row('Side',       side, side === 'BUY' ? 'green' : 'red')}
    ${row('Type',       order.type, '')}
    ${row('Qty',        order.origQty, '')}
    ${row('Exec Qty',   order.executedQty, '')}
    ${row('Avg Price',  avgPrice > 0 ? avgPrice.toFixed(2) : '—', avgPrice > 0 ? 'accent' : '')}
  `;
}

function renderDryRun(body) {
  const empty   = document.querySelector('.result-empty');
  const content = document.getElementById('result-content');
  empty.classList.add('hidden');
  content.classList.remove('hidden');

  content.innerHTML = `
    <div class="result-badge dry">DRY RUN</div>
    <p style="color:var(--text-muted);font-size:13px;margin-bottom:14px">
      Validation passed — no request sent to Binance.
    </p>
    ${row('Symbol', body.symbol)}
    ${row('Side',   body.side, body.side === 'BUY' ? 'green' : 'red')}
    ${row('Type',   body.orderType)}
    ${row('Qty',    body.quantity)}
    ${body.price ? row('Price', body.price) : ''}
  `;
}

function row(label, value, valClass = '') {
  return `<div class="result-row">
    <span class="result-key">${label}</span>
    <span class="result-val ${valClass}">${value}</span>
  </div>`;
}

async function loadWallet() {
  const wrap = document.getElementById('wallet-table-wrap');
  const summ = document.getElementById('wallet-summary');
  wrap.innerHTML = '<div class="loading-state">Loading</div>';
  summ.innerHTML = '';

  try {
    const res  = await fetch('/api/balances');
    const data = await res.json();

    if (!data.ok) {
      wrap.innerHTML = `<div class="empty-state" style="color:var(--red)">${data.msg}</div>`;
      return;
    }

    const totalWallet   = parseFloat(data.totalWalletBalance   || '0').toFixed(2);
    const avail         = parseFloat(data.availableBalance     || '0').toFixed(2);
    const upnl          = parseFloat(data.totalUnrealizedProfit || '0');
    const upnlFmt       = (upnl >= 0 ? '+' : '') + upnl.toFixed(4);
    const upnlCls       = upnl >= 0 ? 'green' : 'red';

    summ.innerHTML = `
      <div class="summary-card"><div class="s-label">Total Wallet</div><div class="s-value">${totalWallet} <small style="font-size:12px;color:var(--text-muted)">USDT</small></div></div>
      <div class="summary-card"><div class="s-label">Available</div><div class="s-value">${avail} <small style="font-size:12px;color:var(--text-muted)">USDT</small></div></div>
      <div class="summary-card"><div class="s-label">Unrealized PnL</div><div class="s-value ${upnlCls}">${upnlFmt}</div></div>
    `;

    if (!data.balances.length) {
      wrap.innerHTML = '<div class="empty-state">No assets with non-zero balance.</div>';
      return;
    }

    wrap.innerHTML = `<table>
      <thead><tr>
        <th>Asset</th><th>Wallet Balance</th><th>Available</th><th>Unrealized PnL</th>
      </tr></thead>
      <tbody>
        ${data.balances.map(a => {
          const pnl    = parseFloat(a.unrealizedProfit || '0');
          const pnlFmt = (pnl >= 0 ? '+' : '') + pnl.toFixed(4);
          const pnlCls = pnl >= 0 ? 'green' : 'red';
          return `<tr>
            <td style="font-weight:600">${a.asset}</td>
            <td>${parseFloat(a.walletBalance || '0').toFixed(4)}</td>
            <td>${parseFloat(a.availableBalance || '0').toFixed(4)}</td>
            <td style="color:var(--${pnlCls})">${pnlFmt}</td>
          </tr>`;
        }).join('')}
      </tbody>
    </table>`;
  } catch {
    wrap.innerHTML = '<div class="empty-state" style="color:var(--red)">Network error</div>';
  }
}

document.getElementById('refresh-wallet').addEventListener('click', loadWallet);

async function loadPositions() {
  const wrap = document.getElementById('positions-table-wrap');
  wrap.innerHTML = '<div class="loading-state">Loading</div>';

  try {
    const res  = await fetch('/api/positions');
    const data = await res.json();

    if (!data.ok) {
      wrap.innerHTML = `<div class="empty-state" style="color:var(--red)">${data.msg}</div>`;
      return;
    }

    if (!data.positions.length) {
      wrap.innerHTML = '<div class="empty-state">No open positions.</div>';
      return;
    }

    wrap.innerHTML = `<table>
      <thead><tr>
        <th>Symbol</th><th>Size</th><th>Entry Price</th><th>Unrealized PnL</th>
      </tr></thead>
      <tbody>
        ${data.positions.map(p => {
          const pnl    = parseFloat(p.unrealizedProfit || '0');
          const pnlFmt = (pnl >= 0 ? '+' : '') + pnl.toFixed(4);
          const pnlCls = pnl >= 0 ? 'green' : 'red';
          return `<tr>
            <td style="font-weight:600">${p.symbol}</td>
            <td>${parseFloat(p.positionAmt).toFixed(4)}</td>
            <td>${p.entryPrice}</td>
            <td style="color:var(--${pnlCls})">${pnlFmt}</td>
          </tr>`;
        }).join('')}
      </tbody>
    </table>`;
  } catch {
    wrap.innerHTML = '<div class="empty-state" style="color:var(--red)">Network error</div>';
  }
}

document.getElementById('refresh-positions').addEventListener('click', loadPositions);

document.getElementById('history-fetch').addEventListener('click', loadHistory);
document.getElementById('history-symbol').addEventListener('keydown', e => { if (e.key === 'Enter') loadHistory(); });

async function loadHistory() {
  const symbol = document.getElementById('history-symbol').value.trim().toUpperCase();
  const limit  = document.getElementById('history-limit').value;
  const wrap   = document.getElementById('history-table-wrap');
  if (!symbol) return;

  wrap.innerHTML = '<div class="loading-state">Loading</div>';

  try {
    const res  = await fetch(`/api/history?symbol=${symbol}&limit=${limit}`);
    const data = await res.json();

    if (!data.ok) {
      wrap.innerHTML = `<div class="empty-state" style="color:var(--red)">${data.msg}</div>`;
      return;
    }
    if (!data.orders.length) {
      wrap.innerHTML = '<div class="empty-state">No orders found.</div>';
      return;
    }

    wrap.innerHTML = `<table>
      <thead><tr>
        <th>ID</th><th>Side</th><th>Type</th><th>Status</th><th>Qty</th><th>Price</th>
      </tr></thead>
      <tbody>
        ${data.orders.map(o => {
          const sideCls   = o.side === 'BUY' ? 'tag-buy' : 'tag-sell';
          const statusCls = o.status === 'FILLED' ? 'tag-filled'
                          : o.status === 'NEW'    ? 'tag-open'
                          : o.status === 'CANCELED' ? 'tag-canceled' : 'tag-neutral';
          return `<tr>
            <td style="color:var(--text-muted)">#${o.orderId}</td>
            <td><span class="tag ${sideCls}">${o.side}</span></td>
            <td class="td-label">${o.type}</td>
            <td><span class="tag ${statusCls}">${o.status}</span></td>
            <td>${o.origQty}</td>
            <td>${parseFloat(o.price || '0') > 0 ? parseFloat(o.price).toFixed(2) : '—'}</td>
          </tr>`;
        }).join('')}
      </tbody>
    </table>`;
  } catch {
    wrap.innerHTML = '<div class="empty-state" style="color:var(--red)">Network error</div>';
  }
}