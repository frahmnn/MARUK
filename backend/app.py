#!/usr/bin/env python3
"""
Monitor backend (app.py) - provides /api/metrics and proxies to attack/mitigation controllers.

- Reads backend/config.json for endpoints and target IPs when present.
- Non-blocking approach with timeouts for remote calls.
- Uses subprocess ping and iperf3 (if available) with reasonable timeouts.
- Serves the frontend (static files) if you host them here, otherwise frontend can be opened directly.
"""
from flask import Flask, jsonify, send_from_directory
import subprocess
import json
import os
import logging
import requests
from concurrent.futures import ThreadPoolExecutor, TimeoutError

app = Flask(__name__, static_folder="../frontend", static_url_path="/")
logging.basicConfig(level=logging.INFO)

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")
TARGET_IP = os.environ.get("TARGET_IP", "192.168.18.20")
MITIGATION_AGENT_URL = os.environ.get("MITIGATION_AGENT_URL", "http://192.168.18.20:5001")
ATTACK_CONTROLLER_URL = os.environ.get("ATTACK_CONTROLLER_URL", "http://192.168.18.21:5002")


def load_config():
    global TARGET_IP, MITIGATION_AGENT_URL, ATTACK_CONTROLLER_URL
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH) as f:
                cfg = json.load(f)
            TARGET_IP = cfg.get("TARGET_IP", TARGET_IP)
            MITIGATION_AGENT_URL = cfg.get("MITIGATION_AGENT_URL", MITIGATION_AGENT_URL)
            ATTACK_CONTROLLER_URL = cfg.get("ATTACK_CONTROLLER_URL", ATTACK_CONTROLLER_URL)
            logging.info("Loaded config: TARGET=%s MITIG=%s ATTACK=%s", TARGET_IP, MITIGATION_AGENT_URL, ATTACK_CONTROLLER_URL)
        except Exception as e:
            logging.exception("Failed to load config.json: %s", e)


def run_cmd(cmd, timeout=6):
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, check=False)
        return proc.returncode, proc.stdout.decode(errors="ignore"), proc.stderr.decode(errors="ignore")
    except subprocess.TimeoutExpired:
        return 124, "", "timeout"
    except Exception as e:
        logging.exception("run_cmd failed: %s", e)
        return 1, "", str(e)


def measure_ping(target):
    """
    Use system ping to get packet loss and avg latency.
    Returns (latency_ms_avg, packet_loss_percent)
    """
    rc, out, err = run_cmd(["ping", "-c", "3", "-w", "5", target], timeout=6)
    if rc != 0 and out == "" and err == "timeout":
        return None, None
    try:
        # parse packet loss
        loss = None
        latency = None
        for line in out.splitlines():
            if "packet loss" in line:
                parts = line.split(",")
                loss = float(parts[2].strip().split("%")[0])
            if "rtt min/avg/max/mdev" in line:
                vals = line.split("=")[1].split()[0].split("/")
                latency = float(vals[1])
        return latency, loss
    except Exception:
        return None, None


def measure_iperf3(target):
    """
    Run iperf3 client briefly and return throughput in Mbps.
    Returns throughput_mbps or None.
    """
    rc, out, err = run_cmd(["iperf3", "-c", target, "-p", "5201", "-t", "3", "-J"], timeout=8)
    if rc == 124:
        return None
    try:
        data = json.loads(out)
        # prefer end.sum_received.bits_per_second if server mode; fallback to end.sum_sent
        end = data.get("end", {})
        sum_received = end.get("sum_received") or end.get("sum_sent") or {}
        bps = sum_received.get("bits_per_second", 0)
        mbps = round(bps / 1_000_000, 2)
        return mbps
    except Exception:
        return None


executor = ThreadPoolExecutor(max_workers=2)


@app.route("/api/metrics")
def api_metrics():
    """
    Return JSON: { latency_ms, throughput_mbps, packet_loss }
    Non-blocking: uses ThreadPoolExecutor with timeouts.
    """
    load_config()
    result = {"latency_ms": None, "throughput_mbps": None, "packet_loss": None}
    try:
        future_ping = executor.submit(measure_ping, TARGET_IP)
        future_iperf = executor.submit(measure_iperf3, TARGET_IP)
        try:
            latency, loss = future_ping.result(timeout=6)
            result["latency_ms"] = latency if latency is not None else -1
            result["packet_loss"] = loss if loss is not None else -1
        except TimeoutError:
            result["latency_ms"] = -1
            result["packet_loss"] = -1
        try:
            th = future_iperf.result(timeout=10)
            result["throughput_mbps"] = th if th is not None else -1
        except TimeoutError:
            result["throughput_mbps"] = -1
        return jsonify(result)
    except Exception as e:
        logging.exception("Error in /api/metrics: %s", e)
        return jsonify({"status": "error", "message": str(e)}), 500


# Proxy endpoints for attacks (forward to AttackVM)
@app.route("/api/attack/<atype>/<action>")
def proxy_attack(atype, action):
    load_config()
    if action not in ("start", "stop"):
        return jsonify({"status": "error", "message": "invalid action"}), 400
    try:
        url = f"{ATTACK_CONTROLLER_URL}/attack/{atype}/{action}"
        resp = requests.get(url, timeout=4)
        return jsonify(resp.json()), resp.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"status": "error", "message": f"Failed to contact attack controller: {e}"}), 500


@app.route("/api/attack/kill_all")
def proxy_attack_kill_all():
    load_config()
    try:
        url = f"{ATTACK_CONTROLLER_URL}/attack/kill_all"
        resp = requests.get(url, timeout=4)
        return jsonify(resp.json()), resp.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"status": "error", "message": f"Failed to contact attack controller: {e}"}), 500


# Proxy endpoints for mitigation (forward to TargetVM)
@app.route("/api/mitigate/<action>")
def proxy_mitigate(action):
    load_config()
    mapping = {
        "block_icmp": "/mitigate/block_icmp",
        "unblock_icmp": "/mitigate/unblock_icmp",
        "block_udp": "/mitigate/block_udp",
        "unblock_udp": "/mitigate/unblock_udp",
        "block_tcp_syn": "/mitigate/block_tcp_syn",
        "unblock_tcp_syn": "/mitigate/unblock_tcp_syn",
        "flush_chain": "/mitigate/flush_chain",
        "status": "/mitigate/status"
    }
    if action not in mapping:
        return jsonify({"status": "error", "message": "invalid mitigation action"}), 400
    try:
        url = MITIGATION_AGENT_URL + mapping[action]
        resp = requests.get(url, timeout=4)
        return jsonify(resp.json()), resp.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"status": "error", "message": f"Failed to contact mitigation agent: {e}"}), 500


# Serve frontend static files (optional)
@app.route("/")
def index():
    return app.send_static_file("index.html")


if __name__ == "__main__":
    load_config()
    logging.info("Starting monitor app on port 5000")
    # enable threaded mode so a slow probe doesn't block the server entirely
    app.run(host="0.0.0.0", port=5000, threaded=True)
