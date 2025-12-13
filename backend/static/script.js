// Minimal frontend script placed in backend/static/script.js
const POLL_INTERVAL = 2000;

function el(id){ return document.getElementById(id); }

async function fetchJson(path, opts = {}) {
  try {
    const res = await fetch(path, { ...opts });
    if (!res.ok) {
      const text = await res.text();
      console.error('Fetch error', path, res.status, text);
      return { ok:false, status:res.status, text };
    }
    const js = await res.json();
    return { ok:true, data:js };
  } catch (e) {
    console.error('Fetch exception', path, e);
    return { ok:false, error:e.message||String(e) };
  }
}

async function refreshMetrics() {
  const r = await fetchJson('/api/metrics');
  if (r.ok && r.data) {
    const m = r.data;
    el('latency').innerText = (m.latency!==undefined? `${m.latency} ms`:'--');
    el('throughput').innerText = (m.throughput!==undefined? `${m.throughput} Mbps`:'--');
    el('pktloss').innerText = (m.packet_loss!==undefined? `${m.packet_loss} %`:'--');
    el('conn-status').innerText = 'connected';
  } else {
    el('conn-status').innerText = 'metrics fetch error';
  }
}

async function refreshStatuses() {
  const at = await fetchJson('/api/attack/status');
  if (at.ok && at.data) {
    el('active-attacks').innerText = at.data.running;
  } else {
    el('active-attacks').innerText = 'ERR';
  }
  const mt = await fetchJson('/api/mitigate/status');
  if (mt.ok && mt.data) {
    let c=0;
    if (mt.data.icmp_blocked) c++;
    if (mt.data.udp_blocked) c++;
    if (mt.data.tcp_syn_blocked) c++;
    el('active-mitigations').innerText = c;
  } else {
    el('active-mitigations').innerText = 'ERR';
  }
}

// Attack buttons
document.getElementById('start-icmp').addEventListener('click', async () => {
  document.getElementById('start-icmp').disabled = true;
  await fetchJson('/api/attack/icmp/start');
  setTimeout(()=>document.getElementById('start-icmp').disabled=false,2000);
});
document.getElementById('start-udp').addEventListener('click', async () => {
  document.getElementById('start-udp').disabled = true;
  await fetchJson('/api/attack/udp/start');
  setTimeout(()=>document.getElementById('start-udp').disabled=false,2000);
});
document.getElementById('start-tcp').addEventListener('click', async () => {
  document.getElementById('start-tcp').disabled = true;
  await fetchJson('/api/attack/tcp/start');
  setTimeout(()=>document.getElementById('start-tcp').disabled=false,2000);
});
document.getElementById('kill-all').addEventListener('click', async () => {
  if (!confirm("Kill all attack processes?")) return;
  document.getElementById('kill-all').disabled = true;
  await fetchJson('/api/attack/kill_all');
  setTimeout(()=>document.getElementById('kill-all').disabled=false,2000);
});

// Mitigation buttons
document.getElementById('enable-icmp').addEventListener('click', async () => { document.getElementById('enable-icmp').disabled=true; await fetchJson('/api/mitigate/block_icmp'); setTimeout(()=>document.getElementById('enable-icmp').disabled=false,2000); });
document.getElementById('disable-icmp').addEventListener('click', async () => { document.getElementById('disable-icmp').disabled=true; await fetchJson('/api/mitigate/unblock_icmp'); setTimeout(()=>document.getElementById('disable-icmp').disabled=false,2000); });

document.getElementById('enable-udp').addEventListener('click', async () => { document.getElementById('enable-udp').disabled=true; await fetchJson('/api/mitigate/block_udp'); setTimeout(()=>document.getElementById('enable-udp').disabled=false,2000); });
document.getElementById('disable-udp').addEventListener('click', async () => { document.getElementById('disable-udp').disabled=true; await fetchJson('/api/mitigate/unblock_udp'); setTimeout(()=>document.getElementById('disable-udp').disabled=false,2000); });

document.getElementById('enable-tcp').addEventListener('click', async () => { document.getElementById('enable-tcp').disabled=true; await fetchJson('/api/mitigate/block_tcp_syn'); setTimeout(()=>document.getElementById('enable-tcp').disabled=false,2000); });
document.getElementById('disable-tcp').addEventListener('click', async () => { document.getElementById('disable-tcp').disabled=true; await fetchJson('/api/mitigate/unblock_tcp_syn'); setTimeout(()=>document.getElementById('disable-tcp').disabled=false,2000); });

// polling
setInterval(()=>{ refreshMetrics(); refreshStatuses(); }, POLL_INTERVAL);
refreshMetrics(); refreshStatuses();
