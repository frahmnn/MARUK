# MARUK Demo Guide

This guide provides step-by-step instructions for demonstrating the MARUK DDoS Monitoring & Control Dashboard.

## 🎯 Demo Objectives

1. Show real-time network monitoring (Latency, Throughput, Packet Loss)
2. Demonstrate various DDoS attack types from dashboard
3. Show mitigation effectiveness for each attack type
4. Highlight combined attack and full mitigation capabilities

## 🛠️ Pre-Demo Setup

### Prerequisites Check
✓ All three VMs are running  
✓ TargetVM has bandwidth limiting applied (`sudo ./setup_demo.sh`)  
✓ Mitigation Agent running on TargetVM (port 5001)  
✓ Attack Controller running on AttackerVM (port 5002)  
✓ Monitor API running on MonitorVM (port 5000)  
✓ Dashboard is accessible in browser

### Quick Setup Commands

**On TargetVM:**
```bash
cd MARUK/backend
sudo ./setup_demo.sh
source venv/bin/activate
export XT_PATH=$(sudo find / -name xtables 2>/dev/null)
sudo XTABLES_LIBDIR="$XT_PATH" venv/bin/python mitigation_agent.py
```

**On AttackerVM:**
```bash
cd MARUK/backend
sudo python3 attack_controller.py
```

**On MonitorVM:**
```bash
cd MARUK/backend
source venv/bin/activate
python3 app.py
```

**Open Dashboard:**
```
http://<MonitorVM_IP>:5000
```

## 📊 Demo Flow

### Part 1: Initial State (2 minutes)

**What to Show:**
- Dashboard with clean, modern interface
- Three metric cards showing healthy values:
  - ✅ Latency: < 30ms (Green - Excellent)
  - ✅ Throughput: > 5 Mbps (Green - Good)
  - ✅ Packet Loss: < 5% (Green - Normal)
- Three real-time graphs updating every 2 seconds
- Attack Control Panel (all inactive - ⚪)
- Mitigation Control Panel (all inactive - ⚪)

**Talking Points:**
> "This is our MARUK dashboard showing real-time network metrics from the target VM. You can see latency, throughput, and packet loss are all in healthy ranges. The system monitors these metrics continuously, taking measurements every 2 seconds."

> "Notice we have full control over attacks and mitigations directly from this dashboard - no need for terminal commands."

[📸 Screenshot Placeholder: Dashboard Initial State]

---

### Part 2: ICMP Flood Attack (3 minutes)

**Steps:**
1. Point to ICMP Flood row in Attack Control Panel
2. Click **START** button
3. Wait 5-10 seconds
4. Observe metrics change:
   - 📈 Latency increases dramatically (Red - Critical)
   - 📉 Packet Loss increases
   - Status indicator turns red (🔴)
   - "Active Attacks: 1" in status bar

**Talking Points:**
> "Let's start with an ICMP flood attack. This sends thousands of ping packets per second from 5 parallel processes with randomized source IPs."

> "Watch the latency spike - it's now over 100ms and showing as critical. The packet loss is also increasing. This simulates a basic volumetric DDoS attack."

[📸 Screenshot Placeholder: ICMP Attack Active]

**Steps (Mitigation):**
1. Click **ENABLE** on Block ICMP in Mitigation Control Panel
2. Wait 5-10 seconds
3. Observe recovery:
   - 📉 Latency returns to normal
   - 📉 Packet Loss decreases
   - Mitigation indicator turns green (🟢)
   - "Active Mitigations: 1" in status bar

**Talking Points:**
> "Now I'll enable ICMP mitigation. This uses iptables firewall rules to drop incoming ICMP packets at the network level."

> "See how quickly the metrics recover? The attack is still running, but the firewall is blocking it effectively."

[📸 Screenshot Placeholder: ICMP Mitigation Active]

**Steps (Cleanup):**
1. Click **STOP** on ICMP Flood attack
2. Click **DISABLE** on Block ICMP mitigation
3. Verify metrics return to baseline

---

### Part 3: TCP SYN Flood Attack (3 minutes)

**Steps:**
1. Point to TCP SYN Flood row
2. Click **START** button
3. Wait 5-10 seconds
4. Observe metrics change:
   - 📉 Throughput drops significantly (Red - Critical)
   - 📈 Latency increases moderately
   - Status indicator turns red (🔴)

**Talking Points:**
> "The TCP SYN flood is particularly effective because it targets port 5201 - the same port our iperf3 throughput measurement uses."

> "Notice how throughput drops dramatically while latency is also affected. This simulates an attack on a critical service."

[📸 Screenshot Placeholder: TCP SYN Attack Active]

**Steps (Mitigation):**
1. Click **ENABLE** on Block TCP SYN
2. Observe recovery:
   - 📈 Throughput recovers
   - 📉 Latency improves
   - Mitigation indicator turns green (🟢)

**Talking Points:**
> "TCP SYN mitigation blocks SYN packets to port 5201, protecting our iperf3 service. The recovery is immediate."

[📸 Screenshot Placeholder: TCP SYN Mitigation Active]

**Steps (Cleanup):**
1. Click **STOP** on TCP SYN Flood
2. Click **DISABLE** on Block TCP SYN

---

### Part 4: UDP Flood Attack (2 minutes)

**Steps:**
1. Click **START** on UDP Flood
2. Observe mixed impact on metrics
3. Click **ENABLE** on Block UDP
4. Observe recovery with rate limiting effect

**Talking Points:**
> "UDP flooding sends random UDP packets to random ports. Our mitigation uses rate limiting - allowing up to 100 UDP packets per second while dropping the rest."

[📸 Screenshot Placeholder: UDP Attack and Mitigation]

**Steps (Cleanup):**
1. Click **STOP** on UDP Flood
2. Click **DISABLE** on Block UDP

---

### Part 5: Combined Attack - The Grand Finale (4 minutes)

**Steps:**
1. Point to Combined Attack row
2. Click **START** button
3. Wait 10 seconds
4. Observe catastrophic metrics:
   - 🔴 All three metrics in critical state
   - 📈 Latency: 200+ ms
   - 📉 Throughput: < 1 Mbps
   - 📈 Packet Loss: > 50%
   - "Active Attacks: 3" in status bar
   - All attack indicators red (🔴🔴🔴)

**Talking Points:**
> "Now for the ultimate test - a combined attack running all three attack types simultaneously. That's 15 parallel hping3 processes flooding the target."

> "Look at the complete degradation across all metrics. This is what a real DDoS attack looks like - the network is essentially unusable."

[📸 Screenshot Placeholder: Combined Attack Devastation]

**Steps (Full Mitigation):**
1. Dramatic pause for effect...
2. Click **ENABLE** on Block ALL
3. Watch the metrics recover in real-time:
   - 📉 Latency drops
   - 📈 Throughput increases
   - 📉 Packet Loss decreases
   - All mitigation indicators turn green (🟢🟢🟢)
   - "Active Mitigations: 3" in status bar

**Talking Points:**
> "With one click, we can enable all mitigations simultaneously. Watch the dashboard as our defense mechanisms kick in."

> "Within seconds, all metrics return to healthy levels. The attacks are still running, but our firewall is effectively protecting the target VM."

[📸 Screenshot Placeholder: Full Recovery with All Mitigations]

**Steps (Final Cleanup):**
1. Click **STOP** on Combined Attack
2. Click **DISABLE** on Block ALL
3. Show dashboard returning to peaceful green state

---

## 🎤 Key Talking Points for Q&A

### Technical Implementation

**Q: How does the attack controller work?**
> "The attack controller is a Flask API running on the AttackerVM. When we click START, it spawns 5 hping3 processes using subprocess.Popen(). We track all PIDs and can terminate them on demand with os.kill()."

**Q: How do the mitigations work?**
> "We use python-iptables to manipulate iptables rules on the TargetVM. For ICMP, we drop all ICMP packets. For UDP, we use hashlimit module for rate limiting. For TCP, we drop SYN packets to port 5201."

**Q: Why is bandwidth limiting important?**
> "The bandwidth limit creates a bottleneck that makes attacks visible. Without it, a 1 Gbps network link wouldn't be affected by our virtual attacks. The 10 Mbps limit simulates a constrained network."

### Architecture

**Q: Why three VMs?**
> "This mimics real-world network separation: MonitorVM is the control center, TargetVM is the victim/protected server, and AttackerVM represents external threats. It demonstrates defense-in-depth."

**Q: How does real-time monitoring work?**
> "The dashboard polls the MonitorVM API every 2 seconds. MonitorVM measures latency with icmplib ping, throughput with iperf3, and calculates packet loss. It's pushed to Chart.js for visualization."

### Educational Value

**Q: What do students learn?**
> "Students learn to recognize DDoS attack patterns, understand how different attack types affect different metrics, and practice incident response with mitigation tools. They also learn system integration, API design, and network security fundamentals."

## 🚨 Troubleshooting During Demo

### Issue: Dashboard shows "Disconnected"
**Fix:** Check if app.py is running on MonitorVM (port 5000)

### Issue: Attacks don't affect metrics
**Fix:** Ensure bandwidth limiting is applied: `sudo ./setup_demo.sh` on TargetVM

### Issue: "Failed to contact attack controller"
**Fix:** Verify attack_controller.py is running with sudo on AttackerVM

### Issue: Mitigation doesn't work
**Fix:** Check mitigation_agent.py is running with proper XTABLES_LIBDIR

### Issue: Graphs not updating
**Fix:** Check browser console for JavaScript errors, refresh page

## ✅ Post-Demo Cleanup

```bash
# On TargetVM
cd MARUK/backend
sudo ./cleanup_demo.sh

# Stop all services with Ctrl+C
# On TargetVM: Stop mitigation_agent.py
# On AttackerVM: Stop attack_controller.py
# On MonitorVM: Stop app.py
```

## 📝 Demo Script Quick Reference

1. **Introduction** (30 sec) - Show clean dashboard
2. **ICMP Attack & Mitigation** (3 min) - Latency impact
3. **TCP SYN Attack & Mitigation** (3 min) - Throughput impact
4. **UDP Attack & Mitigation** (2 min) - Rate limiting
5. **Combined Attack** (2 min) - Total devastation
6. **Full Mitigation** (2 min) - Complete recovery
7. **Q&A** (remaining time)

**Total Time: ~15 minutes + Q&A**

---

## 🎓 Educational Notes

### Learning Objectives Demonstrated
- ✅ Volumetric DDoS attack recognition
- ✅ Different attack vectors (ICMP, UDP, TCP)
- ✅ Firewall-based mitigation strategies
- ✅ Real-time network monitoring
- ✅ Incident response procedures
- ✅ System integration and API design

### Key Concepts Covered
- IP Spoofing (--rand-source flag)
- SYN Flood attacks
- Rate limiting vs. complete blocking
- Defense in depth
- Network metrics interpretation

---

**Good luck with your presentation! 🚀**
