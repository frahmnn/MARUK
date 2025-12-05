# Deployment Guide for Bug Fixes

## Overview
All critical bugs have been fixed and tested. This guide will help you deploy the fixes to your VM environment.

## Pre-Deployment Checklist
- [ ] Pull latest changes from the `copilot/fix-attack-process-management` branch
- [ ] Backup current configuration (optional but recommended)
- [ ] Ensure VMs are accessible via SSH

## Deployment Steps

### Step 1: Update Code on All VMs

#### On MonitorVM:
```bash
cd MARUK
git checkout copilot/fix-attack-process-management
git pull
```

#### On AttackerVM:
```bash
cd MARUK
git checkout copilot/fix-attack-process-management
git pull
```

#### On TargetVM:
```bash
cd MARUK
git checkout copilot/fix-attack-process-management
git pull
```

### Step 2: Verify Changes

Run the test suite on any VM to verify the fixes:
```bash
cd MARUK/backend
python3 test_fixes.py
```

Expected output: **7/7 tests passing** ✅

### Step 3: Restart Services

#### On TargetVM (restart mitigation agent):
```bash
cd MARUK/backend
# Stop existing agent (if running)
sudo pkill -f mitigation_agent.py

# Start agent with new code
source venv/bin/activate
export XT_PATH=$(sudo find / -name xtables 2>/dev/null)
sudo XTABLES_LIBDIR="$XT_PATH" venv/bin/python mitigation_agent.py
```

#### On AttackerVM (restart attack controller):
```bash
cd MARUK/backend
# Stop existing controller (if running)
sudo pkill -f attack_controller.py

# Start controller with new code
sudo python3 attack_controller.py
```

#### On MonitorVM (restart main app):
```bash
cd MARUK/backend
# Stop existing app (if running)
pkill -f app.py

# Start app with new code
source venv/bin/activate
python3 app.py
```

### Step 4: Verify Fixes Work

#### Test 1: Attack Stops Properly
1. Open dashboard: `http://<MonitorVM_IP>:5000`
2. Click "START" on any attack (e.g., ICMP)
3. Wait 5 seconds
4. Click "STOP" on the same attack
5. On AttackerVM, verify no hping3 processes running:
   ```bash
   pgrep hping3
   ```
   Expected: No output (exit code 1) ✅

#### Test 2: UDP Mitigation Works
1. Start UDP attack from dashboard
2. Observe metrics deteriorate
3. Click "ENABLE" on UDP mitigation
4. On TargetVM, verify mitigation agent is still running:
   ```bash
   curl http://localhost:5001/mitigate/status
   ```
   Expected: JSON response with status ✅

#### Test 3: Agent Stays Running on Error
1. Try enabling multiple mitigations
2. Verify agent doesn't crash
3. Check agent logs for proper error handling
4. Verify agent still responds to requests

### Step 5: Clean Up (After Testing)

Run cleanup script on TargetVM:
```bash
cd MARUK/backend
sudo ./cleanup_demo.sh
```

This will:
- Remove bandwidth limiting
- Kill any remaining hping3 processes (using pkill now!)
- Reset iptables rules

## What Changed?

### For Attack Controller Users:
- **No changes needed** - API remains the same
- Attacks now stop more reliably
- Better process cleanup with verification

### For Mitigation Agent Users:
- **No changes needed** - API remains the same
- Agent won't crash on iptables errors
- UDP mitigation works with older iptables
- Better error messages in responses

### For System Administrators:
- Use `pkill` instead of `killall` in scripts
- Check logs for detailed error messages
- Agent stays running even during failures

## Troubleshooting

### Issue: "pkill command not found"
**Solution:** Install procps package:
```bash
sudo apt update
sudo apt install procps -y
```

### Issue: Tests fail on imports
**Solution:** Install Flask:
```bash
pip3 install Flask
```

### Issue: Mitigation agent returns errors
**Check:**
1. Agent is running with sudo privileges
2. XTABLES_LIBDIR is set correctly
3. Check logs for specific error messages
4. Verify iptables is installed

### Issue: Attacks don't stop
**Check:**
1. Attack controller is running with sudo
2. pkill command is available: `which pkill`
3. Check attack controller logs for errors

## Verification Commands

### Check all processes are cleaned up:
```bash
pgrep -a hping3
# Expected: No output
```

### Check mitigation agent status:
```bash
curl http://<TargetVM_IP>:5001/mitigate/status
# Expected: JSON with icmp/udp/tcp status
```

### Check attack controller status:
```bash
curl http://<AttackerVM_IP>:5002/attack/status
# Expected: JSON with process counts
```

### Check iptables rules:
```bash
sudo iptables -L MARUK_MITIGATION -n
# Should show active mitigation rules
```

## Rollback Plan

If you need to rollback to the previous version:

```bash
cd MARUK
git checkout <previous-branch-or-commit>
# Restart all services as shown in Step 3
```

Previous stable branch: `main` or `copilot/create-attack-controller-api`

## Support

### Logs to Check:
- Attack controller: Terminal output or stdout
- Mitigation agent: Terminal output or stdout
- Main app: Terminal output or stdout

### Common Log Messages:
- ✅ "Executed pkill -9 -f hping3 for cleanup" - Normal
- ✅ "All hping3 processes verified stopped" - Good
- ✅ "UDP rate limiting enabled (limit module)" - Good
- ⚠️ "Some hping3 processes still running" - May need investigation
- ❌ "Error enabling UDP block" - Check iptables and permissions

## Performance Notes

### Expected Behavior:
- Attacks stop within 1-2 seconds after clicking stop
- Mitigation enables immediately
- Agent responds to requests even during errors
- No process leaks or resource issues

### Monitoring:
- Watch process counts: `pgrep -c hping3`
- Monitor agent health: Regular status API calls
- Check logs for repeated errors

## Demo Script

For the demonstration, use this sequence:

1. **Show Normal State**
   - Dashboard shows green metrics
   - No attacks or mitigations active

2. **Start Attack**
   - Click "START" on TCP SYN attack
   - Metrics turn red/yellow
   - Explain the impact

3. **Enable Mitigation**
   - Click "ENABLE" on TCP mitigation
   - Metrics recover to green
   - Explain how firewall rules work

4. **Stop Attack**
   - Click "STOP" on attack
   - Verify on AttackerVM: `pgrep hping3` (no output)
   - Explain improved cleanup

5. **Test Combined Attack**
   - Click "START" on Combined attack
   - All metrics deteriorate
   - Click "ENABLE" on Block ALL
   - All metrics recover
   - Click "STOP" on Combined attack
   - Verify cleanup

## Success Criteria

✅ All attacks stop completely (pgrep shows no hping3)
✅ Mitigation agent stays running (curl responds)
✅ UDP mitigation works (no hashlimit error)
✅ Dashboard shows proper status updates
✅ No processes left behind after cleanup
✅ Error messages are informative

## Conclusion

The bug fixes have been thoroughly tested and are ready for deployment. All critical issues have been resolved:

1. ✅ Attacks stop properly (pkill implementation)
2. ✅ UDP mitigation works (limit module)
3. ✅ Agent stability (error handling)

The system is ready for a successful demo! 🚀
