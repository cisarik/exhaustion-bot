// Initialize Chart
const chartOptions = {
    layout: {
        textColor: '#d1d4dc',
        background: { type: 'solid', color: 'transparent' }
    },
    grid: {
        vertLines: { color: 'rgba(42, 46, 57, 0.5)' },
        horzLines: { color: 'rgba(42, 46, 57, 0.5)' },
    }
};
const chart = LightweightCharts.createChart(document.getElementById('chart-container'), chartOptions);
const candleSeries = chart.addCandlestickSeries({
    upColor: '#26a69a', downColor: '#ef5350', borderVisible: false, wickUpColor: '#26a69a', wickDownColor: '#ef5350',
});

// Mock Data for Chart
const currentDate = new Date();
const data = [];
for (let i = 0; i < 100; i++) {
    const time = new Date(currentDate.getTime() - (100 - i) * 15 * 60 * 1000).getTime() / 1000;
    const open = 1.0 + Math.random() * 0.1;
    const close = 1.0 + Math.random() * 0.1;
    data.push({ time, open, high: Math.max(open, close) + 0.02, low: Math.min(open, close) - 0.02, close });
}
candleSeries.setData(data);

// API Interactions
async function fetchConfig() {
    const res = await fetch('/config');
    const config = await res.json();

    // Update UI
    document.getElementById('status-display').innerText = config.status;
    document.getElementById('status-display').className = `status-badge status-${config.status.toLowerCase()}`;

    document.getElementById('level1').value = config.strategy.level1;
    document.getElementById('level2').value = config.strategy.level2;
    document.getElementById('level3').value = config.strategy.level3;

    document.getElementById('sl').value = config.risk.stop_loss_pct;
    document.getElementById('tp').value = config.risk.take_profit_pct;

    document.getElementById('target-ada').value = config.profit.target_ada;
    document.getElementById('withdraw-addr').value = config.profit.withdraw_address;
}

async function updateStrategy(e) {
    e.preventDefault();
    const body = {
        level1: parseInt(document.getElementById('level1').value),
        level2: parseInt(document.getElementById('level2').value),
        level3: parseInt(document.getElementById('level3').value),
        lookback1: 4, lookback2: 3, lookback3: 2 // Defaults for now
    };
    await fetch('/config/strategy', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
    });
    alert('Strategy Updated!');
}

async function updateRisk(e) {
    e.preventDefault();
    const body = {
        stop_loss_pct: parseFloat(document.getElementById('sl').value),
        take_profit_pct: parseFloat(document.getElementById('tp').value),
        risk_per_trade: 0.02
    };
    await fetch('/config/risk', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
    });
    alert('Risk Config Updated!');
}

async function updateProfit(e) {
    e.preventDefault();
    const body = {
        target_ada: parseFloat(document.getElementById('target-ada').value),
        reserve_ada: 500.0,
        auto_withdraw: true,
        withdraw_address: document.getElementById('withdraw-addr').value
    };
    await fetch('/config/profit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
    });
    alert('Profit Settings Saved!');
}

async function startBot() {
    await fetch('/bot/start', { method: 'POST' });
    fetchConfig();
}

async function stopBot() {
    await fetch('/bot/stop', { method: 'POST' });
    fetchConfig();
}

async function fetchWallets() {
    const res = await fetch('/wallets');
    const wallets = await res.json();
    const list = document.getElementById('wallet-list');
    list.innerHTML = '';

    wallets.forEach(w => {
        // Auto-Hide if payout reached (e.g., > 100% progress and processed)
        // User said "strati sa z overview" if payout happens.
        // Let's assume if progress >= 100% it might be processing or done.
        // For visual demo, let's show it Green if >= 100%, maybe hide if > 110%?
        // Or strictly follow: "ak nastala hodnota payout strati sa".
        // Let's hide if it's effectively "done" (e.g. we simulate it disappearing).
        // But for the user to SEE it turning green, we should keep it until it's actually withdrawn.

        // Dynamic Color Logic
        let borderColor = 'var(--glass-border)';
        let glow = 'none';

        if (w.progress_pct >= 100) {
            borderColor = 'var(--success)';
            glow = '0 0 15px var(--success)';
        } else if (w.progress_pct >= 80) {
            borderColor = '#ffcc00'; // Yellow/Orange
            glow = '0 0 10px #ffcc00';
        }

        const div = document.createElement('div');
        div.className = 'wallet-item';
        div.style.border = `1px solid ${borderColor}`;
        div.style.boxShadow = glow;
        div.style.transition = 'all 0.5s ease';

        div.innerHTML = `
            <div style="display:flex; flex-direction:column; width: 100%;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-weight:600;">${w.name}</span>
                    <span style="font-size:0.8rem; color:${w.progress_pct >= 100 ? 'var(--success)' : 'var(--text-secondary)'}">
                        ${w.balance_ada.toFixed(1)} / ${w.target_ada} ADA
                    </span>
                </div>
                <div class="wallet-addr" title="${w.address}">${w.address}</div>
                <div style="width: 100%; height: 4px; background: rgba(255,255,255,0.1); margin-top: 8px; border-radius: 2px;">
                    <div style="width: ${Math.min(w.progress_pct, 100)}%; height: 100%; background: ${borderColor}; border-radius: 2px; transition: width 1s;"></div>
                </div>
            </div>
            <a href="/qr/${w.name}" target="_blank" style="margin-left: 10px; color: var(--accent-color);">
                <img src="/qr/${w.name}" style="width: 40px; height: 40px; border-radius: 4px; border: 1px solid ${borderColor};">
            </a>
        `;
        list.appendChild(div);
    });
}

async function restoreWallet(e) {
    e.preventDefault();
    const name = document.getElementById('restore-name').value;
    const fileInput = document.getElementById('restore-file');

    if (fileInput.files.length === 0) return;

    const formData = new FormData();
    formData.append('wallet_name', name);
    formData.append('file', fileInput.files[0]);

    try {
        const res = await fetch('/wallet/restore', {
            method: 'POST',
            body: formData
        });

        if (res.ok) {
            alert('Wallet Restored Successfully!');
            fetchWallets();
            document.getElementById('restore-form').reset();
        } else {
            const err = await res.json();
            alert('Restore Failed: ' + err.detail);
        }
    } catch (err) {
        alert('Error: ' + err);
    }
}

// Init
fetchConfig();
fetchWallets();
