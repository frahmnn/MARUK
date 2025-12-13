#!/usr/bin/env python3
"""
mitigation_agent.py

Lightweight Flask agent running on the Target VM that enables/disables
simple iptables-based mitigations for demos.

- Uses subprocess + iptables commands (robust across iptables versions)
- Ensures a MARUK_MITIGATION chain exists and INPUT jumps to it
- Provides endpoints to block/unblock ICMP, UDP, TCP-SYN (port 5201)
- Provides a /mitigate/status endpoint reporting active mitigations
- Returns JSON errors instead of crashing on iptables failures
- Note: block_all/unblock_all endpoints are intentionally omitted per request
"""

from flask import Flask, jsonify
import subprocess
import logging
import os
import json

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

MARUK_CHAIN = "MARUK_MITIGATION"
MONITOR_IP = None  # set via config.json if desired
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")


def load_config():
    global MONITOR_IP
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                cfg = json.load(f)
            MONITOR_IP = cfg.get("MONITOR_IP", MONITOR_IP)
            logging.info("Config loaded: MONITOR_IP=%s", MONITOR_IP)
        except Exception as e:
            logging.exception("Failed to load config.json: %s", e)


def run_cmd(cmd):
    """Run a shell command and return (rc, stdout, stderr)."""
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        return proc.returncode, proc.stdout.decode(errors="ignore"), proc.stderr.decode(errors="ignore")
    except Exception as e:
        logging.exception("Subprocess run failed: %s", e)
        return 1, "", str(e)


def chain_exists(chain_name):
    rc, out, err = run_cmd(["sudo", "iptables", "-L", chain_name, "-n"])
    return rc == 0


def ensure_chain():
    """
    Ensure MARUK_CHAIN exists and INPUT jumps to it.
    Idempotent - safe to call multiple times.
    """
    if not chain_exists(MARUK_CHAIN):
        rc, out, err = run_cmd(["sudo", "iptables", "-N", MARUK_CHAIN])
        if rc != 0:
            logging.error("Failed to create chain %s: %s", MARUK_CHAIN, err.strip())
    rc, out, err = run_cmd(["sudo", "iptables", "-C", "INPUT", "-j", MARUK_CHAIN])
    if rc != 0:
        rc2, out2, err2 = run_cmd(["sudo", "iptables", "-I", "INPUT", "1", "-j", MARUK_CHAIN])
        if rc2 != 0:
            logging.error("Failed to insert INPUT -> %s jump: %s", MARUK_CHAIN, err2.strip())


def rule_exists(rule_args):
    cmd = ["sudo", "iptables", "-C", MARUK_CHAIN] + rule_args
    rc, out, err = run_cmd(cmd)
    return rc == 0


def add_rule(rule_args):
    cmd = ["sudo", "iptables", "-A", MARUK_CHAIN] + rule_args
    rc, out, err = run_cmd(cmd)
    return rc, out, err


def insert_rule(rule_args):
    cmd = ["sudo", "iptables", "-I", MARUK_CHAIN] + rule_args
    rc, out, err = run_cmd(cmd)
    return rc, out, err


def delete_rule(rule_args):
    cmd = ["sudo", "iptables", "-D", MARUK_CHAIN] + rule_args
    rc, out, err = run_cmd(cmd)
    return rc, out, err


def list_chain_rules():
    rc, out, err = run_cmd(["sudo", "iptables", "-S", MARUK_CHAIN])
    if rc == 0:
        return out.splitlines()
    return []


@app.route("/mitigate/status")
def status():
    try:
        load_config()
        ensure_chain()
        rules = list_chain_rules()
        icmp_blocked = any(("-p icmp" in r and "-j DROP" in r) for r in rules)
        udp_blocked = any(("-p udp" in r and "-j DROP" in r) for r in rules)
        tcp_blocked = any(("--dport 5201" in r and ("--syn" in r or "-j DROP" in r)) for r in rules)
        return jsonify({
            "status": "ok",
            "icmp_blocked": icmp_blocked,
            "udp_blocked": udp_blocked,
            "tcp_syn_blocked": tcp_blocked,
            "chain_exists": chain_exists(MARUK_CHAIN),
            "rules": rules
        })
    except Exception as e:
        logging.exception("Error in /mitigate/status: %s", e)
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/mitigate/block_icmp")
def block_icmp():
    try:
        load_config()
        ensure_chain()
        # Whitelist Monitor IP for ICMP if configured
        if MONITOR_IP:
            accept_rule = ["-s", MONITOR_IP, "-p", "icmp", "-j", "ACCEPT"]
            if not rule_exists(accept_rule):
                rc, out, err = insert_rule(accept_rule)
                if rc != 0:
                    logging.error("Failed to insert accept rule for monitor %s: %s", MONITOR_IP, err.strip())
        drop_rule = ["-p", "icmp", "-j", "DROP"]
        if not rule_exists(drop_rule):
            rc, out, err = add_rule(drop_rule)
            if rc != 0:
                logging.error("Failed to add icmp DROP: %s", err.strip())
                return jsonify({"status": "error", "message": err.strip()}), 500
        return jsonify({"status": "success", "message": "ICMP block enabled"})
    except Exception as e:
        logging.exception("Error enabling ICMP block: %s", e)
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/mitigate/unblock_icmp")
def unblock_icmp():
    try:
        ensure_chain()
        drop_rule = ["-p", "icmp", "-j", "DROP"]
        while rule_exists(drop_rule):
            rc, out, err = delete_rule(drop_rule)
            if rc != 0:
                logging.error("Failed to delete icmp DROP: %s", err.strip())
                break
        return jsonify({"status": "success", "message": "ICMP block removed"})
    except Exception as e:
        logging.exception("Error disabling ICMP block: %s", e)
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/mitigate/block_udp")
def block_udp():
    try:
        ensure_chain()
        drop_rule = ["-p", "udp", "-j", "DROP"]
        if not rule_exists(drop_rule):
            rc, out, err = add_rule(drop_rule)
            if rc != 0:
                logging.error("Failed to add udp DROP: %s", err.strip())
                return jsonify({"status": "error", "message": err.strip()}), 500
        return jsonify({"status": "success", "message": "UDP block enabled"})
    except Exception as e:
        logging.exception("Error enabling UDP block: %s", e)
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/mitigate/unblock_udp")
def unblock_udp():
    try:
        ensure_chain()
        drop_rule = ["-p", "udp", "-j", "DROP"]
        while rule_exists(drop_rule):
            rc, out, err = delete_rule(drop_rule)
            if rc != 0:
                logging.error("Failed to delete udp DROP: %s", err.strip())
                break
        return jsonify({"status": "success", "message": "UDP block removed"})
    except Exception as e:
        logging.exception("Error disabling UDP block: %s", e)
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/mitigate/block_tcp_syn")
def block_tcp_syn():
    try:
        ensure_chain()
        drop_rule = ["-p", "tcp", "--dport", "5201", "--syn", "-j", "DROP"]
        if not rule_exists(drop_rule):
            rc, out, err = add_rule(drop_rule)
            if rc != 0:
                logging.error("Failed to add tcp syn DROP: %s", err.strip())
                fallback = ["-p", "tcp", "--dport", "5201", "-j", "DROP"]
                if not rule_exists(fallback):
                    rc2, out2, err2 = add_rule(fallback)
                    if rc2 != 0:
                        logging.error("Fallback tcp drop also failed: %s", err2.strip())
                        return jsonify({"status": "error", "message": err2.strip()}), 500
        return jsonify({"status": "success", "message": "TCP SYN block enabled"})
    except Exception as e:
        logging.exception("Error enabling TCP SYN block: %s", e)
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/mitigate/unblock_tcp_syn")
def unblock_tcp_syn():
    try:
        ensure_chain()
        drop_rule = ["-p", "tcp", "--dport", "5201", "--syn", "-j", "DROP"]
        fallback = ["-p", "tcp", "--dport", "5201", "-j", "DROP"]
        while rule_exists(drop_rule):
            rc, out, err = delete_rule(drop_rule)
            if rc != 0:
                logging.error("Failed to delete tcp syn DROP: %s", err.strip())
                break
        while rule_exists(fallback):
            rc, out, err = delete_rule(fallback)
            if rc != 0:
                logging.error("Failed to delete tcp fallback DROP: %s", err.strip())
                break
        return jsonify({"status": "success", "message": "TCP SYN block removed"})
    except Exception as e:
        logging.exception("Error disabling TCP SYN block: %s", e)
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/mitigate/flush_chain")
def flush_chain():
    try:
        rc, out, err = run_cmd(["sudo", "iptables", "-C", "INPUT", "-j", MARUK_CHAIN])
        if rc == 0:
            run_cmd(["sudo", "iptables", "-D", "INPUT", "-j", MARUK_CHAIN])
        run_cmd(["sudo", "iptables", "-F", MARUK_CHAIN])
        run_cmd(["sudo", "iptables", "-X", MARUK_CHAIN])
        return jsonify({"status": "success", "message": "Chain flushed and removed"})
    except Exception as e:
        logging.exception("Error flushing chain: %s", e)
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    load_config()
    logging.info("Starting mitigation_agent on port 5001 (MARUK chain: %s)", MARUK_CHAIN)
    app.run(host="0.0.0.0", port=5001)
