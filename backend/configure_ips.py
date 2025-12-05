#!/usr/bin/env python3
"""
MARUK IP Configuration Script
This interactive script helps configure all IP addresses in the system.
"""

import re
import sys

def get_ip_input(prompt, default="192.168.0.118"):
    """Get IP address input from user with validation."""
    while True:
        ip = input(f"{prompt} [{default}]: ").strip()
        if not ip:
            return default
        
        # Simple IP validation
        pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        if re.match(pattern, ip):
            # Check each octet is 0-255
            octets = ip.split('.')
            if all(0 <= int(octet) <= 255 for octet in octets):
                return ip
        
        print("❌ Invalid IP address format. Please try again.")

def update_file(filepath, updates):
    """Update IP addresses in a file."""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        for old_value, new_value in updates.items():
            content = content.replace(old_value, new_value)
        
        with open(filepath, 'w') as f:
            f.write(content)
        
        print(f"✓ Updated {filepath}")
        return True
    except Exception as e:
        print(f"❌ Error updating {filepath}: {e}")
        return False

def main():
    print("=" * 60)
    print("   MARUK IP Configuration Tool")
    print("=" * 60)
    print()
    print("This script will help you configure all IP addresses in the system.")
    print("Press Enter to use the default value shown in brackets.")
    print()
    
    # Get IP addresses from user
    print("🎯 Step 1: Enter VM IP Addresses")
    print("-" * 60)
    target_ip = get_ip_input("Target VM IP (TargetVM)", "192.168.0.118")
    attacker_ip = get_ip_input("Attacker VM IP (AttackerVM)", "192.168.0.119")
    monitor_ip = get_ip_input("Monitor VM IP (MonitorVM)", "192.168.0.117")
    
    print()
    print("📝 Configuration Summary:")
    print("-" * 60)
    print(f"  Target VM:   {target_ip}")
    print(f"  Attacker VM: {attacker_ip}")
    print(f"  Monitor VM:  {monitor_ip}")
    print()
    
    confirm = input("Is this correct? (y/n) [y]: ").strip().lower()
    if confirm and confirm != 'y':
        print("❌ Configuration cancelled.")
        return 1
    
    print()
    print("🔧 Step 2: Updating Configuration Files")
    print("-" * 60)
    
    success = True
    
    # Update app.py (MonitorVM)
    app_updates = {
        'TARGET_IP = "192.168.0.118"': f'TARGET_IP = "{target_ip}"',
        'MITIGATION_AGENT_URL = "http://192.168.0.118:5001"': f'MITIGATION_AGENT_URL = "http://{target_ip}:5001"',
        'ATTACK_CONTROLLER_URL = "http://192.168.0.119:5002"': f'ATTACK_CONTROLLER_URL = "http://{attacker_ip}:5002"'
    }
    success = update_file('app.py', app_updates) and success
    
    # Update attack_controller.py (AttackerVM)
    attack_updates = {
        'TARGET_IP = "192.168.0.118"': f'TARGET_IP = "{target_ip}"'
    }
    success = update_file('attack_controller.py', attack_updates) and success
    
    # Update attack scripts
    for script in ['attack_tcp.sh', 'attack_icmp.sh', 'attack_udp.sh', 'attack_combined.sh']:
        script_updates = {
            'TARGET_IP="${1:-192.168.0.118}"': f'TARGET_IP="${{1:-{target_ip}}}"'
        }
        success = update_file(script, script_updates) and success
    
    print()
    if success:
        print("✅ Configuration completed successfully!")
        print()
        print("🚀 Next Steps:")
        print("-" * 60)
        print(f"1. On TargetVM ({target_ip}):")
        print("   cd MARUK/backend")
        print("   sudo ./setup_demo.sh")
        print("   source venv/bin/activate")
        print("   export XT_PATH=$(sudo find / -name xtables 2>/dev/null)")
        print('   sudo XTABLES_LIBDIR="$XT_PATH" venv/bin/python mitigation_agent.py')
        print()
        print(f"2. On AttackerVM ({attacker_ip}):")
        print("   cd MARUK/backend")
        print("   sudo python3 attack_controller.py")
        print()
        print(f"3. On MonitorVM ({monitor_ip}):")
        print("   cd MARUK/backend")
        print("   source venv/bin/activate")
        print("   python3 app.py")
        print()
        print(f"4. Open browser to: http://{monitor_ip}:5000")
        print()
        return 0
    else:
        print("❌ Some updates failed. Please check the errors above.")
        return 1

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n❌ Configuration cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
