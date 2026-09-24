/**
 * EcoSense — India-wide live cities overview
 */

let allCities = [];

document.addEventListener('DOMContentLoaded', () => {
    loadCities();
    document.getElementById('citySearch').addEventListener('input', filterCities);
    document.getElementById('stateFilter').addEventListener('change', filterCities);
    document.getElementById('refreshCities').addEventListener('click', () => loadCities(true));
});

async function loadCities(refresh = false) {
    document.getElementById('citiesLoading').style.display = 'block';
    document.getElementById('citiesGrid').innerHTML = '';
    const btn = document.getElementById('refreshCities');
    btn.disabled = true;
    btn.textContent = 'Fetching...';

    try {
        const url = refresh ? '/api/cities/overview?refresh=1' : '/api/cities/overview';
        const res = await fetch(url);
        const data = await res.json();
        allCities = data.cities || [];

        document.getElementById('cityCount').textContent = data.total;
        populateStateFilter(allCities);
        renderStats(data);
        filterCities();
    } catch (err) {
        document.getElementById('citiesGrid').innerHTML =
            '<p class="error-msg">Could not load city data. Please try again.</p>';
    }

    document.getElementById('citiesLoading').style.display = 'none';
    btn.disabled = false;
    btn.textContent = '↻ Refresh Live Data';
}

function populateStateFilter(cities) {
    const states = [...new Set(cities.map(c => c.state))].sort();
    const sel = document.getElementById('stateFilter');
    sel.innerHTML = '<option value="">All States</option>';
    states.forEach(s => {
        sel.innerHTML += `<option value="${s}">${s}</option>`;
    });
}

function renderStats(data) {
    const withData = data.with_data || 0;
    const good = allCities.filter(c => c.severity === 'Good').length;
    const poor = allCities.filter(c => ['Poor', 'Hazardous'].includes(c.severity)).length;
    document.getElementById('citiesStats').innerHTML = `
        <div class="stat-card"><div class="stat-number">${data.total}</div><div class="stat-label">Cities Monitored</div></div>
        <div class="stat-card stat-resolved"><div class="stat-number">${withData}</div><div class="stat-label">Live Data Available</div></div>
        <div class="stat-card"><div class="stat-number">${good}</div><div class="stat-label">Good Air Quality</div></div>
        <div class="stat-card stat-pending"><div class="stat-number">${poor}</div><div class="stat-label">Poor / Hazardous</div></div>`;
}

function filterCities() {
    const q = document.getElementById('citySearch').value.toLowerCase();
    const state = document.getElementById('stateFilter').value;
    const filtered = allCities.filter(c => {
        const matchQ = !q || c.name.toLowerCase().includes(q) || c.state.toLowerCase().includes(q) || c.city.toLowerCase().includes(q);
        const matchState = !state || c.state === state;
        return matchQ && matchState;
    });
    renderGrid(filtered);
}

function renderGrid(cities) {
    const grid = document.getElementById('citiesGrid');
    if (cities.length === 0) {
        grid.innerHTML = '<p class="empty-msg">No cities match your search.</p>';
        return;
    }

    grid.innerHTML = cities.map(c => `
        <a href="/dashboard?area=${c.id}" class="city-card ${c.severity_class || ''}">
            <div class="city-card-header">
                <h3>${c.name}</h3>
                <span class="city-state">${c.state}</span>
            </div>
            ${c.aqi ? `
                <div class="city-aqi">${c.emoji} AQI <strong>${c.aqi}</strong></div>
                <div class="city-meta">
                    <span>🌡️ ${c.temperature}°C</span>
                    <span>💧 ${c.humidity}%</span>
                </div>
                <div class="city-severity ${c.severity_class}">${c.severity}</div>
            ` : `<div class="city-no-data">Data loading...</div>`}
        </a>
    `).join('');
}
