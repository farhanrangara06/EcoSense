/**
 * EcoSense Dashboard — real-time city environmental data
 */

let areas = [];
let selectedAreaId = null;

document.addEventListener('DOMContentLoaded', async () => {
    await loadAreas();
    await loadDemoScenarios();

    document.getElementById('areaSelect').addEventListener('change', (e) => {
        selectedAreaId = e.target.value;
        loadReading(selectedAreaId);
    });
    document.getElementById('stateFilter').addEventListener('change', populateCityDropdown);
    document.getElementById('citySearch').addEventListener('input', populateCityDropdown);
    document.getElementById('demoOff').addEventListener('click', exitDemoMode);

    // Pre-select city from URL ?area=ID
    const params = new URLSearchParams(window.location.search);
    const areaParam = params.get('area');
    if (areaParam) {
        selectedAreaId = areaParam;
        document.getElementById('areaSelect').value = areaParam;
        loadReading(areaParam);
    }
});

async function loadAreas() {
    try {
        const res = await fetch('/api/areas');
        const data = await res.json();
        areas = data.areas || [];

        const stateSel = document.getElementById('stateFilter');
        (data.states || []).forEach(s => {
            stateSel.innerHTML += `<option value="${s}">${s}</option>`;
        });

        populateCityDropdown();
        if (!selectedAreaId && areas.length) {
            selectedAreaId = areas[0].id;
            loadReading(selectedAreaId);
        }
    } catch (err) {
        showError('Environmental data is temporarily unavailable. Please try again later.');
    }
}

function populateCityDropdown() {
    const state = document.getElementById('stateFilter').value;
    const q = document.getElementById('citySearch').value.toLowerCase();
    const select = document.getElementById('areaSelect');
    const filtered = areas.filter(a => {
        const matchState = !state || a.state === state;
        const matchQ = !q || a.name.toLowerCase().includes(q) || a.city.toLowerCase().includes(q);
        return matchState && matchQ;
    });

    select.innerHTML = '';
    filtered.forEach(a => {
        const opt = document.createElement('option');
        opt.value = a.id;
        opt.textContent = `${a.name}, ${a.state}`;
        if (String(a.id) === String(selectedAreaId)) opt.selected = true;
        select.appendChild(opt);
    });

    if (filtered.length && !filtered.find(a => String(a.id) === String(selectedAreaId))) {
        selectedAreaId = filtered[0].id;
        loadReading(selectedAreaId);
    }
}

async function loadReading(areaId) {
    if (!areaId) return;
    selectedAreaId = areaId;
    document.getElementById('loadingMsg').style.display = 'block';
    document.getElementById('dashboardContent').style.display = 'none';
    document.getElementById('errorMsg').style.display = 'none';

    const area = areas.find(a => String(a.id) === String(areaId));
    if (area) {
        document.getElementById('areaInfo').textContent = `${area.name}, ${area.state}`;
    }

    try {
        const res = await fetch(`/api/areas/${areaId}/latest`);
        const data = await res.json();

        if (!data.available || !data.reading) {
            showError('No environmental readings available for this city.');
            return;
        }

        renderReadings(data.reading);
        document.getElementById('loadingMsg').style.display = 'none';
        document.getElementById('dashboardContent').style.display = 'block';
    } catch (err) {
        showError('Environmental data is temporarily unavailable.');
    }
}

function renderReadings(r) {
    const grid = document.getElementById('readingsGrid');
    const demoBanner = document.getElementById('demoBanner');
    const staleWarning = document.getElementById('staleWarning');

    if (r.demo) {
        demoBanner.style.display = 'block';
        demoBanner.innerHTML = `🎬 <strong>Demo Mode Active:</strong> ${r.demo_label || 'Scenario'}`;
    } else {
        demoBanner.style.display = 'none';
    }

    if (r.freshness && r.freshness.warning) {
        staleWarning.style.display = 'block';
        staleWarning.innerHTML = `⚠️ <strong>${r.freshness.warning_text}</strong> — Last reading ${r.freshness.message}.`;
    } else {
        staleWarning.style.display = 'none';
    }

    const badgeEl = document.getElementById('liveSourceBadge');
    if (r.source_label && badgeEl) {
        const badgeClass = r.demo ? 'demo-badge' : r.freshness?.warning ? 'stale-badge' : 'live-ok';
        const icon = r.demo ? '🎬' : r.freshness?.warning ? '⚠️' : '🟢';
        badgeEl.className = `live-source-badge ${badgeClass}`;
        badgeEl.innerHTML = `${icon} ${r.source_label}`;
        badgeEl.style.display = 'inline-flex';
    }

    const cards = [
        { title: 'Air Quality', value: r.aqi, unit: 'AQI', info: r.aqi_info },
        { title: 'Temperature', value: r.temperature, unit: '°C', info: r.temp_info },
        { title: 'Humidity', value: r.humidity, unit: '%', info: r.humidity_info },
    ];

    grid.innerHTML = cards.map(c => `
        <div class="reading-card">
            <h3>${c.title}</h3>
            <div class="reading-value">${c.value}<span class="reading-unit"> ${c.unit}</span></div>
            <div class="reading-status ${c.info.class}">${c.info.emoji} ${c.info.label}</div>
            <p class="reading-explanation">${c.info.explanation}</p>
            <div class="reading-updated">Last updated: ${r.time_ago || 'unknown'}</div>
        </div>
    `).join('');
}

function showError(msg) {
    document.getElementById('loadingMsg').style.display = 'none';
    const el = document.getElementById('errorMsg');
    el.style.display = 'block';
    el.textContent = msg;
}

async function loadDemoScenarios() {
    const res = await fetch('/api/demo-scenarios');
    const data = await res.json();
    const container = document.getElementById('demoButtons');
    Object.entries(data.scenarios).forEach(([key, scenario]) => {
        const btn = document.createElement('button');
        btn.className = 'demo-btn';
        btn.textContent = scenario.label;
        btn.addEventListener('click', () => activateDemo(key, btn));
        container.appendChild(btn);
    });
}

async function activateDemo(scenario, btn) {
    await fetch('/api/demo-mode', { method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scenario }) });
    document.querySelectorAll('.demo-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    if (selectedAreaId) loadReading(selectedAreaId);
}

async function exitDemoMode() {
    await fetch('/api/demo-mode', { method: 'DELETE' });
    document.querySelectorAll('.demo-btn').forEach(b => b.classList.remove('active'));
    if (selectedAreaId) loadReading(selectedAreaId);
}
