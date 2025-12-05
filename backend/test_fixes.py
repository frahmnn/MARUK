#!/usr/bin/env python3
"""
Manual test script to verify critical bug fixes.
This script tests the fixes without requiring actual VM environment.
"""

import sys
import subprocess
import importlib.util

def test_attack_controller_imports():
    """Test that attack_controller.py imports correctly."""
    print("Test 1: Checking attack_controller.py imports...")
    try:
        spec = importlib.util.spec_from_file_location(
            "attack_controller", 
            "attack_controller.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Check that time is imported
        assert hasattr(module, 'time'), "time module not imported"
        
        # Check that stop_attack_processes exists
        assert hasattr(module, 'stop_attack_processes'), "stop_attack_processes function not found"
        
        print("  ✓ attack_controller.py imports successfully")
        print("  ✓ time module is imported")
        print("  ✓ stop_attack_processes function exists")
        return True
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def test_mitigation_agent_imports():
    """Test that mitigation_agent.py imports correctly."""
    print("\nTest 2: Checking mitigation_agent.py imports...")
    try:
        # Note: python-iptables may not be installed, so we just check syntax
        result = subprocess.run(
            ['python3', '-m', 'py_compile', 'mitigation_agent.py'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("  ✓ mitigation_agent.py syntax is valid")
            return True
        else:
            print(f"  ✗ Syntax error: {result.stderr}")
            return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def test_pkill_command_available():
    """Test that pkill command is available."""
    print("\nTest 3: Checking pkill command availability...")
    try:
        result = subprocess.run(
            ['which', 'pkill'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"  ✓ pkill found at: {result.stdout.strip()}")
            return True
        else:
            print("  ✗ pkill command not found")
            return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def test_pgrep_command_available():
    """Test that pgrep command is available."""
    print("\nTest 4: Checking pgrep command availability...")
    try:
        result = subprocess.run(
            ['which', 'pgrep'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"  ✓ pgrep found at: {result.stdout.strip()}")
            return True
        else:
            print("  ✗ pgrep command not found")
            return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def test_code_contains_pkill():
    """Test that code uses pkill instead of killall."""
    print("\nTest 5: Verifying pkill usage in code...")
    try:
        with open('attack_controller.py', 'r') as f:
            attack_controller_content = f.read()
        
        with open('cleanup_demo.sh', 'r') as f:
            cleanup_content = f.read()
        
        # Check that killall is not used as a command (exclude comments)
        import re
        # Look for killall that's not in a comment (# or //)
        attack_killall_cmd = re.search(r"['\"]killall|subprocess.*killall|\bkillall\s+", attack_controller_content)
        cleanup_killall_cmd = re.search(r"^\s*killall\s+", cleanup_content, re.MULTILINE)
        
        # Check that pkill is used
        has_pkill_attack = 'pkill' in attack_controller_content
        has_pkill_cleanup = 'pkill' in cleanup_content
        
        if attack_killall_cmd:
            print(f"  ✗ attack_controller.py uses killall as a command")
            return False
        
        if cleanup_killall_cmd:
            print(f"  ✗ cleanup_demo.sh uses killall as a command")
            return False
        
        if not has_pkill_attack:
            print("  ✗ attack_controller.py doesn't use pkill")
            return False
        
        if not has_pkill_cleanup:
            print("  ✗ cleanup_demo.sh doesn't use pkill")
            return False
        
        print("  ✓ killall not used as command in attack_controller.py")
        print("  ✓ killall not used as command in cleanup_demo.sh")
        print("  ✓ pkill used in attack_controller.py")
        print("  ✓ pkill used in cleanup_demo.sh")
        return True
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def test_mitigation_error_handling():
    """Test that mitigation_agent.py has proper error handling."""
    print("\nTest 6: Verifying error handling in mitigation_agent.py...")
    try:
        with open('mitigation_agent.py', 'r') as f:
            content = f.read()
        
        # Check for error handling patterns
        has_try_except = content.count('try:') >= 8  # Should have many try-except blocks
        has_error_response = 'return jsonify({"status": "error"' in content
        has_status_500 = ', 500' in content
        
        # Check that hashlimit_above is not used
        has_hashlimit_above = 'hashlimit_above' in content
        
        # Check that limit module is used for UDP
        has_limit_module = 'create_match("limit")' in content
        
        if has_hashlimit_above:
            print("  ✗ Still using hashlimit_above (incompatible)")
            return False
        
        if not has_limit_module:
            print("  ✗ Not using limit module")
            return False
        
        if not has_try_except:
            print("  ✗ Insufficient try-except blocks")
            return False
        
        if not has_error_response:
            print("  ✗ Missing error JSON responses")
            return False
        
        if not has_status_500:
            print("  ✗ Missing 500 status codes for errors")
            return False
        
        print("  ✓ hashlimit_above removed")
        print("  ✓ limit module used for UDP mitigation")
        print("  ✓ Proper try-except error handling present")
        print("  ✓ JSON error responses implemented")
        print("  ✓ HTTP 500 status codes for errors")
        return True
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def test_attack_controller_time_sleep():
    """Test that attack_controller uses time.sleep for cleanup."""
    print("\nTest 7: Verifying time.sleep in stop_attack_processes...")
    try:
        with open('attack_controller.py', 'r') as f:
            content = f.read()
        
        # Check for time.sleep(1) after pkill - use regex for flexibility
        import re
        has_time_sleep = re.search(r'time\.sleep\s*\(\s*1\s*\)', content) is not None
        
        # Check for process verification
        has_pgrep_verification = 'pgrep' in content and '-f' in content
        
        if not has_time_sleep:
            print("  ✗ time.sleep(1) not found after pkill")
            return False
        
        if not has_pgrep_verification:
            print("  ✗ Process verification with pgrep not found")
            return False
        
        print("  ✓ time.sleep(1) present after pkill")
        print("  ✓ Process verification with pgrep implemented")
        return True
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("MARUK Bug Fix Verification Tests")
    print("=" * 60)
    
    tests = [
        test_attack_controller_imports,
        test_mitigation_agent_imports,
        test_pkill_command_available,
        test_pgrep_command_available,
        test_code_contains_pkill,
        test_mitigation_error_handling,
        test_attack_controller_time_sleep,
    ]
    
    results = []
    for test_func in tests:
        results.append(test_func())
    
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests Passed: {passed}/{total}")
    
    if passed == total:
        print("\n✅ All tests passed! Bug fixes verified.")
        return 0
    else:
        print(f"\n❌ {total - passed} test(s) failed. Please review the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
