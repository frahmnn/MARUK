// Minimal frontend JS to control attacks and mitigations and poll metrics
const POLL_INTERVAL = 2000;

function log(msg) {
  const el = document.getElementById('logarea');
  const now = new Date().toLocaleTimeString();
  el.textContent = `[${now}] ${msg}\n` + el.textContent;
}

async function api(path, opts = {}) {
  try {
    const res = await fetch(path, opts);
    const json = await res.json();
    return { ok: res.ok, status: res.status, json };
  } catch (e) {
    return { ok: false, status: 0, json: { message: e.toString() } };
  }
}

async function fetchMetrics() {
  const r = await api('/api/metrics');
  if (r.ok) {
    document.getElementById('latency').textContent = r.json.latency_ms === -1 ? 'timeout' : (r.json.latency_ms || '--');
    document.getElementById('throughput').textContent = r.json.throughput_mbps === -1 ? 'timeout' : (r.json.throughput_mbps || '--');
    document.getElementById('loss').textContent = r.json.packet_loss === -1 ? 'timeout' : (r.json.packet_loss || '--');
  } else {
    log("Metrics error: " + (r.json.message || r.status));
  }
}

async function startAttack(type) {
  log(`Starting ${type} attack...`);
  const r = await api(`/api/attack/${type}/start`);
  if (r.ok) {
    log(`Started ${type}: ${JSON.stringify(r.json)}`);
  } else {
    log(`Start ${type} failed: ${r.json.message || r.status}`);
  }
}

async function stopAttack(type) {
  log(`Stopping ${type} attack...`);
  const r = await api(`/api/attack/${type}/stop`);
  if (r.ok) {
    log(`Stopped ${type}: ${JSON.stringify(r.json)}`);
  } else {
    log(`Stop ${type} failed: ${r.json.message || r.status}`);
  }
}

async function killAllAttacks() {
  if (!confirm("Kill all hping3 attack processes on AttackVM? This forcibly terminates attack processes.")) return;
  log("Sending KILL ALL request...");
  const r = await api('/api/attack/kill_all');
  if (r.ok) {
    log("Kill-All result: " + JSON.stringify(r.json));
  } else {
    log("Kill-All failed: " + (r.json.message || r.status));
  }
  // refresh metrics immediately
  await fetchMetrics();
}

async function mitigate(action) {
  log("Mitigation: " + action);
  const r = await api(`/api/mitigate/${action}`);
  if (r.ok) {
    log(`Mitigate ${action}: ${JSON.stringify(r.json)}`);
  } else {
    log(`Mitigate ${action} failed: ${r.json.message || r.status}`);
  }
}

async function init() {
  // show target ip from config endpoint (fallback to config.json values served by monitor)
  const cfgResp = await api('/api/metrics'); // metrics includes nothing but we use to check connectivity
  fetchMetrics();
  setInterval(fetchMetrics, POLL_INTERVAL);
}

window.onload = init;
