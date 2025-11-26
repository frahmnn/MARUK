from flask import Flask, jsonify
from icmplib import ping
import iperf3
import time
import requests

app = Flask(__name__)

# --- KONFIGURASI ---
# Ganti dengan IP VM Target Anda
TARGET_IP = "192.168.0.134"
# ---------------------

# Ganti dengan URL agen mitigasi di VM Target
MITIGATION_AGENT_URL = "http://192.168.0.123:5001"
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

@app.route('/api/mitigate/start')
def start_mitigation_proxy():
    """Proxy untuk memulai mitigasi di VM Target."""
    try:
        # Memanggil API di mitigation_agent.py
        response = requests.get(f"{MITIGATION_AGENT_URL}/mitigate/start_icmp_block")
        response.raise_for_status() # Akan error jika status code 4xx/5xx
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"status": "error", "message": f"Gagal menghubungi agen mitigasi: {e}"}), 500

@app.route('/api/mitigate/stop')
def stop_mitigation_proxy():
    """Proxy untuk menghentikan mitigasi di VM Target."""
    try:
        # Memanggil API di mitigation_agent.py
        response = requests.get(f"{MITIGATION_AGENT_URL}/mitigate/stop_icmp_block")
        response.raise_for_status()
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"status": "error", "message": f"Gagal menghubungi agen mitigasi: {e}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
