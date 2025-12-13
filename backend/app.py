from flask import Flask, jsonify, render_template, request
from icmplib import ping
import iperf3
import time
import requests

app = Flask(__name__)

# --- KONFIGURASI ---
# Ganti dengan IP VM Target Anda
TARGET_IP = "192.168.18.20"
# ---------------------

# Ganti dengan URL agen mitigasi di VM Target
MITIGATION_AGENT_URL = "http://192.168.18.20:5001"
# ---------------------

# Ganti dengan URL attack controller di VM Attacker
ATTACK_CONTROLLER_URL = "http://192.168.18.18:5002"
# ---------------------

def measure_latency_packet_loss():
    """Mengukur latency dan packet loss menggunakan ICMP (ping)."""
    try:
        # Mengirim 4 paket ping, interval 0.2 detik, timeout 1 detik
        host = ping(TARGET_IP, count=4, interval=0.2, timeout=1, privileged=False)

        return {
            "latency_avg_ms": host.avg_rtt,
            "packet_loss_percent": host.packet_loss * 100 # Konversi 0.0-1.0 ke 0-100
        }
    except Exception as e:
        # Jika target mati atau tidak terjangkau
        print(f"Error ping: {e}")
        return {
            "latency_avg_ms": -1, # -1 menandakan error
            "packet_loss_percent": 100
        }

def measure_throughput():
    """Mengukur throughput (bandwidth) menggunakan iperf3."""
    client = iperf3.Client()
    client.server_hostname = TARGET_IP
    client.port = 5201 # Port default iperf3
    client.protocol = 'tcp'
    client.duration = 2 # Tes selama 2 detik

    try:
        result = client.run()
        # Mengambil data throughput dalam Megabits per second (Mbps)
        throughput_mbps = result.sent_Mbps

        return {
            "throughput_mbps": round(throughput_mbps, 2)
        }
    except Exception as e:
        # Jika server iperf3 di target tidak berjalan
        print(f"Error iperf3: {e}")
        return {
            "throughput_mbps": -1 # -1 menandakan error
        }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/metrics')
def get_metrics():
    """Endpoint API untuk mengambil semua metrik."""

    # 1. Ukur Latency & Packet Loss
    ping_data = measure_latency_packet_loss()

    # 2. Ukur Throughput
    iperf_data = measure_throughput()

    # 3. Gabungkan hasilnya
    metrics = {
        "latency": ping_data["latency_avg_ms"],
        "packet_loss": ping_data["packet_loss_percent"],
        "throughput": iperf_data["throughput_mbps"]
    }

    return jsonify(metrics)

# ============================================
# ATTACK CONTROL PROXY ENDPOINTS (INDIVIDUAL)
# ============================================

@app.route('/api/attack/icmp/start')
def attack_icmp_start_proxy():
    """Proxy to start ICMP attack on AttackVM."""
    try:
        response = requests.get(f"{ATTACK_CONTROLLER_URL}/attack/icmp/start", timeout=5)
        response.raise_for_status()
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"status": "error", "message": f"Failed to contact attack controller: {e}"}), 500

@app.route('/api/attack/udp/start')
def attack_udp_start_proxy():
    """Proxy to start UDP attack on AttackVM."""
    try:
        response = requests.get(f"{ATTACK_CONTROLLER_URL}/attack/udp/start", timeout=5)
        response.raise_for_status()
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"status": "error", "message": f"Failed to contact attack controller: {e}"}), 500

@app.route('/api/attack/tcp/start')
def attack_tcp_start_proxy():
    """Proxy to start TCP SYN attack on AttackVM."""
    try:
        response = requests.get(f"{ATTACK_CONTROLLER_URL}/attack/tcp/start", timeout=5)
        response.raise_for_status()
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"status": "error", "message": f"Failed to contact attack controller: {e}"}), 500

# KILL ALL ATTACKS: This is the "STOP ALL" button/function!
@app.route('/api/attack/killall', methods=['POST'])
def attack_killall_proxy():
    """Proxy to kill all attacks on AttackVM."""
    try:
        response = requests.post(f"{ATTACK_CONTROLLER_URL}/attack/killall", timeout=5)
        response.raise_for_status()
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"status": "error", "message": f"Failed to contact attack controller: {e}"}), 500

@app.route('/api/attack/status')
def attack_status_proxy():
    """Proxy to get attack status from AttackVM."""
    try:
        response = requests.get(f"{ATTACK_CONTROLLER_URL}/attack/status", timeout=5)
        response.raise_for_status()
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"status": "error", "message": f"Failed to contact attack controller: {e}"}), 500

# ============================================
# ENHANCED MITIGATION PROXY ENDPOINTS
# ============================================

@app.route('/api/mitigate/block_icmp')
def mitigate_block_icmp_proxy():
    """Proxy to block ICMP on TargetVM."""
    try:
        response = requests.get(f"{MITIGATION_AGENT_URL}/mitigate/block_icmp", timeout=5)
        response.raise_for_status()
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"status": "error", "message": f"Failed to contact mitigation agent: {e}"}), 500

@app.route('/api/mitigate/unblock_icmp')
def mitigate_unblock_icmp_proxy():
    """Proxy to unblock ICMP on TargetVM."""
    try:
        response = requests.get(f"{MITIGATION_AGENT_URL}/mitigate/unblock_icmp", timeout=5)
        response.raise_for_status()
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"status": "error", "message": f"Failed to contact mitigation agent: {e}"}), 500

@app.route('/api/mitigate/block_udp')
def mitigate_block_udp_proxy():
    """Proxy to block UDP on TargetVM."""
    try:
        response = requests.get(f"{MITIGATION_AGENT_URL}/mitigate/block_udp", timeout=5)
        response.raise_for_status()
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"status": "error", "message": f"Failed to contact mitigation agent: {e}"}), 500

@app.route('/api/mitigate/unblock_udp')
def mitigate_unblock_udp_proxy():
    """Proxy to unblock UDP on TargetVM."""
    try:
        response = requests.get(f"{MITIGATION_AGENT_URL}/mitigate/unblock_udp", timeout=5)
        response.raise_for_status()
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"status": "error", "message": f"Failed to contact mitigation agent: {e}"}), 500

@app.route('/api/mitigate/block_tcp')
def mitigate_block_tcp_proxy():
    """Proxy to block TCP SYN on TargetVM."""
    try:
        response = requests.get(f"{MITIGATION_AGENT_URL}/mitigate/block_tcp_syn", timeout=5)
        response.raise_for_status()
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"status": "error", "message": f"Failed to contact mitigation agent: {e}"}), 500

@app.route('/api/mitigate/unblock_tcp')
def mitigate_unblock_tcp_proxy():
    """Proxy to unblock TCP SYN on TargetVM."""
    try:
        response = requests.get(f"{MITIGATION_AGENT_URL}/mitigate/unblock_tcp_syn", timeout=5)
        response.raise_for_status()
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"status": "error", "message": f"Failed to contact mitigation agent: {e}"}), 500

@app.route('/api/mitigate/status')
def mitigate_status_proxy():
    """Proxy to get mitigation status from TargetVM."""
    try:
        response = requests.get(f"{MITIGATION_AGENT_URL}/mitigate/status", timeout=5)
        response.raise_for_status()
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"status": "error", "message": f"Failed to contact mitigation agent: {e}"}), 500

if __name__ == '__main__':
    debug_mode = True
    app.run(host='0.0.0.0', port=5000, debug=debug_mode, threaded=True)
