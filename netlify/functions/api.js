const fs = require('fs');
const path = require('path');
const bcrypt = require('bcryptjs');
const { connectLambda, getStore } = require('@netlify/blobs');

const areasData = JSON.parse(
  fs.readFileSync(path.join(__dirname, 'data', 'areas.json'), 'utf8')
);

const DEMO_SCENARIOS = {
  normal: { aqi: 45, temperature: 28, humidity: 55, label: 'Normal Conditions' },
  pollution_spike: { aqi: 187, temperature: 32, humidity: 72, label: 'Pollution Spike' },
  severe_pollution: { aqi: 250, temperature: 31, humidity: 68, label: 'Severe Pollution' },
  hot_weather: { aqi: 95, temperature: 39, humidity: 45, label: 'Hot Weather' },
  high_humidity: { aqi: 110, temperature: 30, humidity: 90, label: 'High Humidity' },
};

const THRESHOLDS = {
  aqi: { good: [0, 50], moderate: [51, 100], poor: [101, 200], hazardous: [201, 9999] },
  temperature: { good: [0, 28], moderate: [29, 35], poor: [36, 40], hazardous: [41, 999] },
  humidity: { good: [30, 60], moderate: [61, 75], poor: [76, 85], hazardous: [86, 100] },
};

const SEVERITY = {
  good: { label: 'Good', emoji: '🟢', class: 'severity-good' },
  moderate: { label: 'Moderate', emoji: '🟡', class: 'severity-moderate' },
  poor: { label: 'Poor', emoji: '🟠', class: 'severity-poor' },
  hazardous: { label: 'Hazardous', emoji: '🔴', class: 'severity-hazardous' },
};

const EXPLANATIONS = {
  aqi: {
    good: 'Air quality is currently good.',
    moderate: 'Air quality is acceptable, but some people may notice discomfort.',
    poor: 'Air quality is poor. Sensitive people should consider reducing prolonged outdoor activity.',
    hazardous: 'Air pollution is very high. Follow local health guidance and avoid unnecessary outdoor exposure.',
  },
  temperature: {
    good: 'Temperature is comfortable for most outdoor activities.',
    moderate: 'Temperature is warm. Stay hydrated during outdoor activity.',
    poor: 'It is quite hot. Limit prolonged outdoor exposure.',
    hazardous: 'Extreme heat conditions. Avoid outdoor activity if possible.',
  },
  humidity: {
    good: 'Humidity levels are within a normal range.',
    moderate: 'Humidity is slightly elevated but generally acceptable.',
    poor: 'Humidity is high. It may feel uncomfortable outdoors.',
    hazardous: 'Very high humidity. Take precautions in hot conditions.',
  },
};

function json(statusCode, body, headers = {}) {
  return {
    statusCode,
    headers: { 'Content-Type': 'application/json', ...headers },
    body: JSON.stringify(body),
  };
}

function parseCookies(event) {
  const raw = event.headers.cookie || event.headers.Cookie || '';
  return raw.split(';').reduce((acc, part) => {
    const [key, ...rest] = part.trim().split('=');
    if (key) acc[key] = decodeURIComponent(rest.join('='));
    return acc;
  }, {});
}

function getSession(event) {
  const cookies = parseCookies(event);
  if (!cookies.ecosense_session) return null;
  try {
    return JSON.parse(Buffer.from(cookies.ecosense_session, 'base64url').toString('utf8'));
  } catch {
    return null;
  }
}

function sessionCookie(session) {
  const value = Buffer.from(JSON.stringify(session)).toString('base64url');
  return `ecosense_session=${value}; Path=/; HttpOnly; SameSite=Lax; Max-Age=604800`;
}

function clearSessionCookie() {
  return 'ecosense_session=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0';
}

function classify(value, thresholds) {
  for (const [level, [low, high]] of Object.entries(thresholds)) {
    if (value >= low && value <= high) return level;
  }
  return 'hazardous';
}

function getSeverity(value, paramType) {
  const level = classify(value, THRESHOLDS[paramType]);
  const info = SEVERITY[level];
  return {
    level,
    label: info.label,
    emoji: info.emoji,
    class: info.class,
    explanation: EXPLANATIONS[paramType][level],
  };
}

function timeAgo(date) {
  const minutes = Math.floor((Date.now() - date.getTime()) / 60000);
  if (minutes < 1) return 'just now';
  if (minutes < 60) return `${minutes} minute${minutes === 1 ? '' : 's'} ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours} hour${hours === 1 ? '' : 's'} ago`;
  const days = Math.floor(hours / 24);
  return `${days} day${days === 1 ? '' : 's'} ago`;
}

function enrichReading(reading) {
  const ts = new Date(reading.timestamp);
  return {
    ...reading,
    aqi_info: getSeverity(Number(reading.aqi), 'aqi'),
    temp_info: getSeverity(Number(reading.temperature), 'temperature'),
    humidity_info: getSeverity(Number(reading.humidity), 'humidity'),
    freshness: 'live',
    time_ago: timeAgo(ts),
    timestamp_str: ts.toLocaleString('en-IN', {
      day: '2-digit', month: 'short', year: 'numeric',
      hour: '2-digit', minute: '2-digit', hour12: true,
    }),
    source_label: reading.demo ? 'Demo scenario (not real data)' : 'Live data from Open-Meteo',
  };
}

async function fetchJson(url) {
  const response = await fetch(url, { headers: { 'User-Agent': 'EcoSense/1.0' } });
  if (!response.ok) return null;
  return response.json();
}

async function fetchLiveReading(latitude, longitude) {
  const weatherUrl = `https://api.open-meteo.com/v1/forecast?latitude=${latitude}&longitude=${longitude}&current=temperature_2m,relative_humidity_2m&timezone=auto`;
  const aqiUrl = `https://air-quality-api.open-meteo.com/v1/air-quality?latitude=${latitude}&longitude=${longitude}&current=us_aqi&timezone=auto`;
  const [weather, aqiData] = await Promise.all([fetchJson(weatherUrl), fetchJson(aqiUrl)]);
  if (!weather?.current) return null;
  return {
    aqi: aqiData?.current?.us_aqi ?? 0,
    temperature: weather.current.temperature_2m,
    humidity: weather.current.relative_humidity_2m,
    timestamp: weather.current.time || new Date().toISOString(),
    source: 'open-meteo',
  };
}

async function fetchHistory(latitude, longitude, days, param) {
  const end = new Date();
  const start = new Date(end.getTime() - days * 86400000);
  const format = (d) => d.toISOString().slice(0, 10);
  const weatherUrl = `https://api.open-meteo.com/v1/forecast?latitude=${latitude}&longitude=${longitude}&hourly=temperature_2m,relative_humidity_2m&start_date=${format(start)}&end_date=${format(end)}&timezone=auto`;
  const aqiUrl = `https://air-quality-api.open-meteo.com/v1/air-quality?latitude=${latitude}&longitude=${longitude}&hourly=us_aqi&start_date=${format(start)}&end_date=${format(end)}&timezone=auto`;
  const [weather, aqiData] = await Promise.all([fetchJson(weatherUrl), fetchJson(aqiUrl)]);
  const labels = weather?.hourly?.time || [];
  const values = labels.map((_, i) => {
    if (param === 'aqi') return aqiData?.hourly?.us_aqi?.[i] ?? 0;
    if (param === 'temperature') return weather?.hourly?.temperature_2m?.[i] ?? 0;
    return weather?.hourly?.relative_humidity_2m?.[i] ?? 0;
  });
  return { labels, values };
}

function analyzeTrend(values, param) {
  if (!values.length) {
    return {
      direction: 'stable', emoji: '🟡', label: 'Stable',
      summary: 'Not enough data for trend analysis.', prev_avg: 0, curr_avg: 0, change_pct: 0,
    };
  }
  const midpoint = Math.floor(values.length / 2) || 1;
  const prev = values.slice(0, midpoint);
  const curr = values.slice(midpoint);
  const avg = (arr) => arr.reduce((a, b) => a + b, 0) / arr.length;
  const prevAvg = avg(prev);
  const currAvg = avg(curr);
  const changePct = prevAvg ? ((currAvg - prevAvg) / prevAvg) * 100 : 0;
  let direction = 'stable';
  if (changePct > 5) direction = 'worsening';
  if (changePct < -5) direction = 'improving';
  const label = direction === 'worsening' ? 'Worsening' : direction === 'improving' ? 'Improving' : 'Stable';
  const emoji = direction === 'worsening' ? '🔴' : direction === 'improving' ? '🟢' : '🟡';
  const unit = param === 'temperature' ? '°C' : param === 'humidity' ? '%' : '';
  return {
    direction,
    emoji,
    label,
    summary: `${label} ${param} trend over the selected period${unit ? ` (${unit})` : ''}.`,
    prev_avg: Math.round(prevAvg * 10) / 10,
    curr_avg: Math.round(currAvg * 10) / 10,
    change_pct: Math.round(changePct * 10) / 10,
  };
}

async function getStoreData(event) {
  connectLambda(event);
  const store = getStore('ecosense');
  const users = await store.get('users', { type: 'json' });
  const reports = await store.get('reports', { type: 'json' });
  const history = await store.get('history', { type: 'json' });
  return {
    store,
    users: users || [],
    reports: reports || [],
    history: history || [],
  };
}

async function ensureSeedData(store, users) {
  if (users.length) return users;
  const password = await bcrypt.hash('admin123', 10);
  const seeded = [{
    id: 1,
    name: 'Admin',
    email: 'admin@ecosense.in',
    password,
    role: 'admin',
  }];
  await store.setJSON('users', seeded);
  await store.setJSON('reports', []);
  await store.setJSON('history', []);
  return seeded;
}

function formatReportId(id) {
  return `EW-${String(id).padStart(3, '0')}`;
}

function getAreaById(areaId) {
  return areasData.areas.find((area) => String(area.id) === String(areaId));
}

function routePath(event) {
  const raw = event.path || '';
  const cleaned = raw.replace(/^\/\.netlify\/functions\/api/, '').replace(/\/$/, '') || '/';
  return cleaned;
}

exports.handler = async (event, context) => {
  const method = event.httpMethod;
  const path = routePath(event);
  const session = getSession(event);
  const demoScenario = parseCookies(event).ecosense_demo || null;

  if (path === '/api/logout' && (method === 'GET' || method === 'POST')) {
    return json(200, { success: true, redirect: '/' }, { 'Set-Cookie': clearSessionCookie() });
  }

  if (path === '/api/areas' && method === 'GET') {
    return json(200, areasData);
  }

  if (path === '/api/session' && method === 'GET') {
    return json(200, {
      logged_in: Boolean(session?.user_id),
      user_name: session?.user_name || null,
      role: session?.role || null,
      demo_scenario: demoScenario,
    });
  }

  if (path === '/api/demo-scenarios' && method === 'GET') {
    return json(200, { scenarios: DEMO_SCENARIOS });
  }

  if (path === '/api/demo-mode' && method === 'POST') {
    const body = JSON.parse(event.body || '{}');
    const scenario = body.scenario;
    const cookie = scenario && DEMO_SCENARIOS[scenario]
      ? `ecosense_demo=${scenario}; Path=/; SameSite=Lax; Max-Age=3600`
      : 'ecosense_demo=; Path=/; SameSite=Lax; Max-Age=0';
    return json(200, {
      success: true,
      demo: Boolean(scenario && DEMO_SCENARIOS[scenario]),
      scenario: DEMO_SCENARIOS[scenario] || null,
    }, { 'Set-Cookie': cookie });
  }

  if (path === '/api/demo-mode' && method === 'DELETE') {
    return json(200, { success: true, demo: false }, {
      'Set-Cookie': 'ecosense_demo=; Path=/; SameSite=Lax; Max-Age=0',
    });
  }

  const latestMatch = path.match(/^\/api\/areas\/(\d+)\/latest$/);
  if (latestMatch && method === 'GET') {
    const area = getAreaById(latestMatch[1]);
    if (!area) return json(404, { error: 'Area not found', available: false });
    if (demoScenario && DEMO_SCENARIOS[demoScenario]) {
      const scenario = DEMO_SCENARIOS[demoScenario];
      const reading = enrichReading({
        aqi: scenario.aqi,
        temperature: scenario.temperature,
        humidity: scenario.humidity,
        timestamp: new Date().toISOString(),
        source: 'demo_mode',
        demo: true,
        demo_label: scenario.label,
      });
      return json(200, { reading, available: true });
    }
    const live = await fetchLiveReading(area.latitude, area.longitude);
    if (!live) return json(404, { error: 'No readings available', available: false });
    return json(200, { reading: enrichReading(live), available: true });
  }

  const historyMatch = path.match(/^\/api\/areas\/(\d+)\/history$/);
  if (historyMatch && method === 'GET') {
    const area = getAreaById(historyMatch[1]);
    const params = event.queryStringParameters || {};
    const period = params.period || '7d';
    const param = params.param || 'aqi';
    const days = period === '24h' ? 1 : period === '30d' ? 30 : 7;
    if (!area) return json(200, { labels: [], values: [], param, period, trend: analyzeTrend([], param), source: 'open-meteo' });
    const history = await fetchHistory(area.latitude, area.longitude, days, param);
    let { labels, values } = history;
    if (period === '24h' && values.length > 24) {
      labels = labels.slice(-24);
      values = values.slice(-24);
    }
    return json(200, {
      labels,
      values,
      param,
      period,
      trend: analyzeTrend(values, param),
      source: 'open-meteo',
    });
  }

  if (path === '/api/cities/overview' && method === 'GET') {
    const cities = [];
    for (const area of areasData.areas.slice(0, 40)) {
      const live = await fetchLiveReading(area.latitude, area.longitude);
      cities.push({
        id: area.id,
        name: area.name,
        city: area.city,
        state: area.state,
        latitude: area.latitude,
        longitude: area.longitude,
        aqi: live?.aqi ?? null,
        temperature: live?.temperature ?? null,
        humidity: live?.humidity ?? null,
        severity: live ? getSeverity(live.aqi, 'aqi') : null,
      });
    }
    return json(200, {
      cities,
      total: areasData.total,
      source: 'open-meteo',
      with_data: cities.filter((city) => city.aqi !== null).length,
    });
  }

  const { store, users, reports, history } = await getStoreData(event);
  const allUsers = await ensureSeedData(store, users);

  if (path === '/api/login' && method === 'POST') {
    const body = JSON.parse(event.body || '{}');
    const user = allUsers.find((entry) => entry.email === (body.email || '').trim());
    const valid = user && await bcrypt.compare(body.password || '', user.password);
    if (!valid) return json(401, { error: 'Invalid email or password.' });
    const cookie = sessionCookie({
      user_id: user.id,
      user_name: user.name,
      role: user.role,
    });
    const redirect = user.role === 'admin' ? '/admin' : '/dashboard';
    return json(200, { success: true, redirect }, { 'Set-Cookie': cookie });
  }

  if (path === '/api/register' && method === 'POST') {
    const body = JSON.parse(event.body || '{}');
    const name = (body.name || '').trim();
    const email = (body.email || '').trim();
    const password = body.password || '';
    if (!name || !email || !password) return json(400, { error: 'All fields are required.' });
    if (allUsers.some((entry) => entry.email === email)) {
      return json(400, { error: 'Email already registered.' });
    }
    const nextUser = {
      id: allUsers.length + 1,
      name,
      email,
      password: await bcrypt.hash(password, 10),
      role: 'citizen',
    };
    await store.setJSON('users', [...allUsers, nextUser]);
    return json(200, { success: true, redirect: '/login' });
  }

  if (path === '/api/reports' && method === 'POST') {
    if (!session?.user_id) return json(401, { error: 'Login required.' });
    const body = JSON.parse(event.body || '{}');
    let photo = null;
    if (body.photo_data && body.photo_type) {
      photo = `data:${body.photo_type};base64,${body.photo_data}`;
    }
    const nextReport = {
      id: reports.length + 1,
      user_id: session.user_id,
      area_id: Number(body.area_id),
      issue_type: body.issue_type,
      description: body.description,
      photo,
      status: 'Pending',
      created_at: new Date().toISOString(),
    };
    const area = getAreaById(nextReport.area_id);
    const stored = [...reports, nextReport];
    await store.setJSON('reports', stored);
    await store.setJSON('history', [
      ...history,
      {
        id: history.length + 1,
        report_id: nextReport.id,
        status: 'Pending',
        admin_note: 'Report submitted by citizen',
        changed_by: session.user_id,
        changed_at: nextReport.created_at,
      },
    ]);
    return json(200, {
      success: true,
      report_id: formatReportId(nextReport.id),
      id: nextReport.id,
      area_name: area?.name,
    });
  }

  const reportDetailMatch = path.match(/^\/api\/reports\/(\d+)$/);
  if (reportDetailMatch && method === 'GET') {
    if (!session?.user_id) return json(401, { error: 'Login required.' });
    const reportId = Number(reportDetailMatch[1]);
    const report = reports.find((entry) => entry.id === reportId);
    if (!report) return json(404, { error: 'Report not found' });
    if (session.role !== 'admin' && report.user_id !== session.user_id) {
      return json(403, { error: 'Access denied' });
    }
    const user = allUsers.find((entry) => entry.id === report.user_id);
    const reportHistory = history
      .filter((entry) => entry.report_id === reportId)
      .map((entry) => {
        const admin = allUsers.find((u) => u.id === entry.changed_by);
        return { ...entry, admin_name: admin?.name || null };
      });
    return json(200, {
      report: {
        ...report,
        report_code: formatReportId(report.id),
        area_name: getAreaById(report.area_id)?.name || 'Unknown',
        user_name: user?.name || 'Unknown',
      },
      history: reportHistory,
    });
  }

  if (path === '/api/my-reports' && method === 'GET') {
    if (!session?.user_id) return json(401, { error: 'Login required.' });
    const mine = reports
      .filter((report) => report.user_id === session.user_id)
      .map((report) => ({
        ...report,
        report_code: formatReportId(report.id),
        area_name: getAreaById(report.area_id)?.name || 'Unknown',
      }));
    return json(200, { reports: mine });
  }

  if (path === '/api/admin/reports' && method === 'GET') {
    if (session?.role !== 'admin') return json(403, { error: 'Admin access required.' });
    const enriched = reports.map((report) => {
      const user = allUsers.find((entry) => entry.id === report.user_id);
      return {
        ...report,
        report_code: formatReportId(report.id),
        area_name: getAreaById(report.area_id)?.name || 'Unknown',
        user_name: user?.name || 'Unknown',
      };
    });
    const stats = { total: enriched.length, pending: 0, reviewed: 0, resolved: 0 };
    enriched.forEach((report) => {
      stats[report.status.toLowerCase()] = (stats[report.status.toLowerCase()] || 0) + 1;
    });
    return json(200, { reports: enriched, stats });
  }

  const adminReportMatch = path.match(/^\/api\/admin\/reports\/(\d+)$/);
  if (adminReportMatch && method === 'PUT') {
    if (session?.role !== 'admin') return json(403, { error: 'Admin access required.' });
    const reportId = Number(adminReportMatch[1]);
    const body = JSON.parse(event.body || '{}');
    const updatedReports = reports.map((report) =>
      report.id === reportId ? { ...report, status: body.status } : report
    );
    await store.setJSON('reports', updatedReports);
    await store.setJSON('history', [
      ...history,
      {
        id: history.length + 1,
        report_id: reportId,
        status: body.status,
        admin_note: body.admin_note || '',
        changed_by: session.user_id,
        changed_at: new Date().toISOString(),
      },
    ]);
    return json(200, { success: true });
  }

  if (path === '/api/admin/areas' && (method === 'POST' || method === 'PUT')) {
    if (session?.role !== 'admin') return json(403, { error: 'Admin access required.' });
    return json(200, { success: true });
  }

  if (path === '/api/admin/readings' && method === 'POST') {
    if (session?.role !== 'admin') return json(403, { error: 'Admin access required.' });
    return json(200, { success: true });
  }

  return json(404, { error: 'Not found' });
};
