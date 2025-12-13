#!/usr/bin/env python3
"""
mitigation_agent.py

Placed under backend/, replaces prior version. Focus:
- Separate ICMP/UDP/TCP-SYN block/unblock endpoints
- Ensures MARUK_MITIGATION chain exists and INPUT -> MARUK_MITIGATION jump is present
- Returns JSON errors instead of crashing
- Does NOT provide combined/all endpoints (per request)
"""
from flask import Flask, jsonify
import subprocess
import logging
import os
import json

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

MARUK_CHAIN = "MARUK_MITIGATION"
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")
MONITOR_IP = None

def load_config():
    global MONITOR_IP
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH,"r") as f:
                cfg = json.load(f)
            MONITOR_IP = cfg.get("MONITOR_IP", MONITOR_IP)
            logging.info("Loaded config MONITOR_IP=%s", MONITOR_IP)
        except Exception as e:
            logging.exception("load_config failed: %s", e)

def run_cmd(cmd):
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        return proc.returncode, proc.stdout.decode(errors="ignore"), proc.stderr.decode(errors="ignore")
    except Exception as e:
        logging.exception("run_cmd exception: %s", e)
        return 1,"",str(e)

def chain_exists(name):
    rc,out,err = run_cmd(["sudo","iptables","-L",name,"-n"])
    return rc==0

def ensure_chain():
    if not chain_exists(MARUK_CHAIN):
        rc,out,err = run_cmd(["sudo","iptables","-N",MARUK_CHAIN])
        if rc!=0:
            logging.error("Failed create chain %s: %s", MARUK_CHAIN, err.strip())
    rc,out,err = run_cmd(["sudo","iptables","-C","INPUT","-j",MARUK_CHAIN])
    if rc!=0:
        run_cmd(["sudo","iptables","-I","INPUT","1","-j",MARUK_CHAIN])

def rule_exists(rule_args):
    rc,out,err = run_cmd(["sudo","iptables","-C",MARUK_CHAIN] + rule_args)
    return rc==0

def add_rule(rule_args):
    return run_cmd(["sudo","iptables","-A",MARUK_CHAIN] + rule_args)

def insert_rule(rule_args):
    return run_cmd(["sudo","iptables","-I",MARUK_CHAIN] + rule_args)

def delete_rule(rule_args):
    return run_cmd(["sudo","iptables","-D",MARUK_CHAIN] + rule_args)

def list_rules():
    rc,out,err = run_cmd(["sudo","iptables","-S",MARUK_CHAIN])
    return out.splitlines() if rc==0 else []

@app.route("/mitigate/status")
def status():
    try:
        load_config()
        ensure_chain()
        rules = list_rules()
        icmp_blocked = any(("-p icmp" in r and "-j DROP" in r) for r in rules)
        udp_blocked = any(("-p udp" in r and "-j DROP" in r) for r in rules)
        tcp_blocked = any(("--dport 5201" in r and ("--syn" in r or "-j DROP" in r)) for r in rules)
        return jsonify({"status":"ok","icmp_blocked":icmp_blocked,"udp_blocked":udp_blocked,"tcp_syn_blocked":tcp_blocked,"chain_exists":chain_exists(MARUK_CHAIN),"rules":rules})
    except Exception as e:
        logging.exception("status error: %s", e)
        return jsonify({"status":"error","message":str(e)}),500

@app.route("/mitigate/block_icmp")
def block_icmp():
    try:
        load_config()
        ensure_chain()
        if MONITOR_IP:
            accept = ["-s", MONITOR_IP, "-p", "icmp", "-j", "ACCEPT"]
            if not rule_exists(accept):
                insert_rule(accept)
        drop = ["-p","icmp","-j","DROP"]
        if not rule_exists(drop):
            rc,out,err = add_rule(drop)
            if rc!=0:
                logging.error("add icmp drop failed: %s", err.strip())
                return jsonify({"status":"error","message":err.strip()}),500
        return jsonify({"status":"success","message":"ICMP block enabled"})
    except Exception as e:
        logging.exception("block_icmp error: %s", e)
        return jsonify({"status":"error","message":str(e)}),500

@app.route("/mitigate/unblock_icmp")
def unblock_icmp():
    try:
        ensure_chain()
        drop = ["-p","icmp","-j","DROP"]
        while rule_exists(drop):
            rc,out,err = delete_rule(drop)
            if rc!=0:
                logging.error("delete icmp drop failed: %s", err.strip())
                break
        return jsonify({"status":"success","message":"ICMP block removed"})
    except Exception as e:
        logging.exception("unblock_icmp error: %s", e)
        return jsonify({"status":"error","message":str(e)}),500

@app.route("/mitigate/block_udp")
def block_udp():
    try:
        ensure_chain()
        drop = ["-p","udp","-j","DROP"]
        if not rule_exists(drop):
            rc,out,err = add_rule(drop)
            if rc!=0:
                logging.error("add udp drop failed: %s", err.strip())
                return jsonify({"status":"error","message":err.strip()}),500
        return jsonify({"status":"success","message":"UDP block enabled"})
    except Exception as e:
        logging.exception("block_udp error: %s", e)
        return jsonify({"status":"error","message":str(e)}),500

@app.route("/mitigate/unblock_udp")
def unblock_udp():
    try:
        ensure_chain()
        drop = ["-p","udp","-j","DROP"]
        while rule_exists(drop):
            rc,out,err = delete_rule(drop)
            if rc!=0:
                logging.error("delete udp drop failed: %s", err.strip())
                break
        return jsonify({"status":"success","message":"UDP block removed"})
    except Exception as e:
        logging.exception("unblock_udp error: %s", e)
        return jsonify({"status":"error","message":str(e)}),500

@app.route("/mitigate/block_tcp_syn")
def block_tcp_syn():
    try:
        ensure_chain()
        drop = ["-p","tcp","--dport","5201","--syn","-j","DROP"]
        if not rule_exists(drop):
            rc,out,err = add_rule(drop)
            if rc!=0:
                logging.error("add tcp syn drop failed: %s", err.strip())
                # fallback without --syn
                fallback = ["-p","tcp","--dport","5201","-j","DROP"]
                if not rule_exists(fallback):
                    rc2,out2,err2 = add_rule(fallback)
                    if rc2!=0:
                        logging.error("fallback tcp drop failed: %s", err2.strip())
                        return jsonify({"status":"error","message":err2.strip()}),500
        return jsonify({"status":"success","message":"TCP SYN block enabled"})
    except Exception as e:
        logging.exception("block_tcp_syn error: %s", e)
        return jsonify({"status":"error","message":str(e)}),500

@app.route("/mitigate/unblock_tcp_syn")
def unblock_tcp_syn():
    try:
        ensure_chain()
        drop = ["-p","tcp","--dport","5201","--syn","-j","DROP"]
        fallback = ["-p","tcp","--dport","5201","-j","DROP"]
        while rule_exists(drop):
            rc,out,err = delete_rule(drop)
            if rc!=0:
                logging.error("delete tcp syn drop failed: %s", err.strip())
                break
        while rule_exists(fallback):
            rc,out,err = delete_rule(fallback)
            if rc!=0:
                logging.error("delete tcp fallback failed: %s", err.strip())
                break
        return jsonify({"status":"success","message":"TCP SYN block removed"})
    except Exception as e:
        logging.exception("unblock_tcp_syn error: %s", e)
        return jsonify({"status":"error","message":str(e)}),500

@app.route("/mitigate/flush_chain")
def flush_chain():
    try:
        rc,out,err = run_cmd(["sudo","iptables","-C","INPUT","-j",MARUK_CHAIN])
        if rc==0:
            run_cmd(["sudo","iptables","-D","INPUT","-j",MARUK_CHAIN])
        run_cmd(["sudo","iptables","-F",MARUK_CHAIN])
        run_cmd(["sudo","iptables","-X",MARUK_CHAIN])
        return jsonify({"status":"success","message":"Chain flushed and removed"})
    except Exception as e:
        logging.exception("flush_chain error: %s", e)
        return jsonify({"status":"error","message":str(e)}),500

if __name__ == "__main__":
    load_config()
    logging.info("Starting mitigation_agent on port 5001 (chain=%s)", MARUK_CHAIN)
    app.run(host="0.0.0.0", port=5001)
