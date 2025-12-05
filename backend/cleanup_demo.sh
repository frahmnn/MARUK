#!/bin/bash
# Cleanup Script untuk TargetVM setelah Demo
# Script ini harus dijalankan di TargetVM setelah selesai demo untuk membersihkan konfigurasi
# 
# Fungsi:
# 1. Menghapus bandwidth limiting
# 2. Membunuh proses hping3 yang masih berjalan
# 3. Reset iptables rules ke default
# 
# Penggunaan:
#   sudo ./cleanup_demo.sh [INTERFACE]
#   
# Jika INTERFACE tidak diberikan, default adalah enp0s3

# Default values
INTERFACE="${1:-enp0s3}"

echo "=========================================="
echo "   MARUK DEMO CLEANUP - TargetVM"
echo "=========================================="
echo ""
echo "Interface: $INTERFACE"
echo ""
echo "=========================================="
echo ""

# Cek apakah script dijalankan dengan sudo
if [ "$EUID" -ne 0 ]; then
    echo "ERROR: Script ini harus dijalankan dengan sudo"
    echo "Gunakan: sudo ./cleanup_demo.sh"
    exit 1
fi

# Cek apakah interface ada
if ! ip link show "$INTERFACE" &>/dev/null; then
    echo "WARNING: Interface $INTERFACE tidak ditemukan!"
    echo ""
    echo "Interface yang tersedia:"
    ip link show | grep -E "^[0-9]+" | awk '{print "  - " $2}' | sed 's/:$//'
    echo ""
    echo "Melanjutkan cleanup untuk langkah lainnya..."
    echo ""
fi

echo "[1/3] Menghapus bandwidth limiting..."
if tc qdisc del dev "$INTERFACE" root 2>/dev/null; then
    echo "✓ Bandwidth limiting dihapus dari $INTERFACE"
else
    echo "✓ Tidak ada bandwidth limiting yang aktif"
fi
echo ""

echo "[2/3] Membunuh proses hping3 yang masih berjalan..."
if pgrep hping3 > /dev/null; then
    HPING_COUNT=$(pgrep hping3 | wc -l)
    killall hping3 2>/dev/null
    sleep 1
    
    # Verifikasi proses terbunuh
    if ! pgrep hping3 > /dev/null; then
        echo "✓ Semua proses hping3 dihentikan ($HPING_COUNT proses)"
    else
        echo "⚠ Beberapa proses hping3 masih berjalan, mencoba kill -9..."
        killall -9 hping3 2>/dev/null
        sleep 1
        if ! pgrep hping3 > /dev/null; then
            echo "✓ Semua proses hping3 dihentikan (forced)"
        else
            echo "✗ GAGAL membunuh beberapa proses hping3"
            echo "  PIDs yang masih berjalan:"
            pgrep hping3 | sed 's/^/    /'
        fi
    fi
else
    echo "✓ Tidak ada proses hping3 yang berjalan"
fi
echo ""

echo "[3/3] Reset iptables rules ke default..."
# Flush semua rules
iptables -F 2>/dev/null
iptables -X 2>/dev/null
iptables -t nat -F 2>/dev/null
iptables -t nat -X 2>/dev/null
iptables -t mangle -F 2>/dev/null
iptables -t mangle -X 2>/dev/null

# Set default policy ke ACCEPT
iptables -P INPUT ACCEPT 2>/dev/null
iptables -P FORWARD ACCEPT 2>/dev/null
iptables -P OUTPUT ACCEPT 2>/dev/null

echo "✓ iptables rules di-reset ke default"
echo "  Policy: INPUT=ACCEPT, FORWARD=ACCEPT, OUTPUT=ACCEPT"
echo ""

echo "Verifikasi iptables saat ini:"
RULE_COUNT=$(iptables -L -n | grep -v "^Chain\|^target\|^$" | wc -l)
if [ "$RULE_COUNT" -eq 0 ]; then
    echo "✓ Tidak ada rules custom (iptables bersih)"
else
    echo "⚠ Masih ada $RULE_COUNT rules aktif"
    echo "  Gunakan 'sudo iptables -L -n' untuk melihat detail"
fi
echo ""

echo "=========================================="
echo "   CLEANUP SELESAI!"
echo "=========================================="
echo ""
echo "Ringkasan:"
echo "  [✓] Bandwidth limiting: DIHAPUS"
echo "  [✓] hping3 processes: DIBERSIHKAN"
echo "  [✓] iptables rules: DIRESET"
echo ""
echo "TargetVM kembali ke kondisi normal."
echo "=========================================="
echo ""
