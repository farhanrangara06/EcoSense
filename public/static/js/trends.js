/**
 * EcoSense Trends JavaScript
 * Chart.js trend visualization and analysis
 */

let trendChart = null;
let currentPeriod = '7d';

document.addEventListener('DOMContentLoaded', async () => {
    await loadAreas();
    document.getElementById('trendArea').addEventListener('change', loadTrend);
    document.getElementById('trendParam').addEventListener('change', loadTrend);
    document.querySelectorAll('.period-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.period-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentPeriod = btn.dataset.period;
            loadTrend();
        });
    });
    loadTrend();
});

async function loadAreas() {
    const res = await fetch('/api/areas');
    const data = await res.json();
    const sel = document.getElementById('trendArea');
    const byState = {};
    data.areas.forEach(a => {
        if (!byState[a.state]) byState[a.state] = [];
        byState[a.state].push(a);
    });
    let first = true;
    Object.keys(byState).sort().forEach(state => {
        const grp = document.createElement('optgroup');
        grp.label = state;
        byState[state].forEach(a => {
            const opt = document.createElement('option');
            opt.value = a.id;
            opt.textContent = a.name;
            if (first) { opt.selected = true; first = false; }
            grp.appendChild(opt);
        });
        sel.appendChild(grp);
    });
}

async function loadTrend() {
    const areaId = document.getElementById('trendArea').value;
    const param = document.getElementById('trendParam').value;
    if (!areaId) return;

    const res = await fetch(`/api/areas/${areaId}/history?period=${currentPeriod}&param=${param}`);
    const data = await res.json();

    const paramLabels = { aqi: 'AQI', temperature: 'Temperature (°C)', humidity: 'Humidity (%)' };
    const paramColors = { aqi: '#2d8f4e', temperature: '#fd7e14', humidity: '#1a73b8' };

    if (trendChart) trendChart.destroy();

    const ctx = document.getElementById('trendChart').getContext('2d');
    trendChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.labels,
            datasets: [{
                label: paramLabels[param],
                data: data.values,
                borderColor: paramColors[param],
                backgroundColor: paramColors[param] + '20',
                fill: true,
                tension: 0.3,
                pointRadius: data.labels.length > 50 ? 0 : 3,
            }],
        },
        options: {
            responsive: true,
            plugins: { legend: { display: true } },
            scales: {
                x: { ticks: { maxTicksLimit: 10, maxRotation: 45 } },
                y: { beginAtZero: param !== 'temperature' },
            },
        },
    });

    // Trend analysis
    if (data.trend) {
        const t = data.trend;
        document.getElementById('trendAnalysis').style.display = 'block';
        document.getElementById('trendResult').innerHTML = `
            <div class="trend-result">
                <span style="font-size:1.5rem">${t.emoji}</span>
                <strong style="font-size:1.3rem;margin-left:0.5rem">${t.label}</strong>
                <p style="margin-top:0.75rem">${t.summary}</p>
                <div style="margin-top:0.5rem;color:#666;font-size:0.9rem">
                    Previous average: <strong>${t.prev_avg}</strong> →
                    Current average: <strong>${t.curr_avg}</strong>
                    (${t.change_pct > 0 ? '+' : ''}${t.change_pct}%)
                </div>
            </div>`;
    }
}
