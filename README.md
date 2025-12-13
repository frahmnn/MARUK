# Proyek MARUK (Monitoring, Attack, and Regulation Utility)

**MARUK** adalah sebuah platform edukasi keamanan siber yang terintegrasi: attack (simulasi), monitor (dashboard), regulation (mitigasi).

---

IMPORTANT CHANGES (quick summary for demo)
- The "combined" attack and "combined" mitigation endpoints/files have been removed to improve reliability.
- A new emergency "KILL ALL ATTACKS" button and API are available. This calls `sudo pkill -9 -f hping3` on the AttackVM and is intended to stop all attack processes without restarting the VM.
- Mitigation agent now ensures a MARUK_MITIGATION chain exists and inserts rules safely. Use the /mitigate/status endpoint to inspect active rules.

Quick Start (for demo)
1. Prepare VMs: MonitorVM, TargetVM, AttackVM on the same virtual network.
2. Install prerequisites on each VM:
   - sudo apt update
   - sudo apt install python3 python3-pip iperf3 hping3 iptables iproute2 -y
3. In each VM:
   - cd ~/MARUK/backend
   - python3 -m venv venv
   - source venv/bin/activate
   - pip install -r requirements.txt (if present) or pip install flask requests
4. Configure backend/config.json with correct IPs:
   {
     "TARGET_IP": "192.168.18.20",
     "MITIGATION_AGENT_URL": "http://192.168.18.20:5001",
     "ATTACK_CONTROLLER_URL": "http://192.168.18.21:5002",
     "MONITOR_IP": "192.168.18.19"
   }
5. Start services:
   - On TargetVM:
     export XT_PATH=$(sudo find / -name xtables 2>/dev/null)
     sudo XTABLES_LIBDIR="$XT_PATH" venv/bin/python mitigation_agent.py &
   - On AttackVM:
     sudo python3 attack_controller.py &    # or run inside venv with sudo
   - On MonitorVM:
     source venv/bin/activate
     python3 app.py &
6. Open dashboard in browser:
   http://<MonitorVM_IP>:5000

Demo notes
- Use the Attack Control panel to start/stop ICMP/UDP/TCP attacks.
- Use KILL ALL ATTACKS in case stop buttons do not fully terminate processes (pkill -9 -f hping3).
- Use Mitigation panel to enable/disable ICMP/UDP/TCP-SYN protections. The monitor IP can be whitelisted in config.json so pings still work when ICMP is blocked.

Safety
- The Kill-All action only targets processes named hping3. Make sure you have no other critical processes with that name.
- All networking actions are intended to run inside your isolated VirtualBox lab.

If you want, I can open a PR that:
- Replaces the old Python attack scripts with hping3 wrappers,
- Adds these updated backend/frontend files,
- Adds a test checklist to the repo README.
