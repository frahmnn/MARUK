#!/bin/bash
# Setup Script untuk TargetVM sebelum Demo
# Script ini harus dijalankan di TargetVM sebelum melakukan demo serangan
# 
# Fungsi:
# 1. Menerapkan bandwidth limiting (PENTING untuk demo!)
# 2. Verifikasi iperf3 server berjalan
# 3. Cek apakah mitigation agent siap
# 
# Penggunaan:
#   sudo ./setup_demo.sh [INTERFACE] [BANDWIDTH]
#   
# Jika INTERFACE tidak diberikan, default adalah enp0s3
# Jika BANDWIDTH tidak diberikan, default adalah 10mbit
# Tekan Ctrl+C untuk berhenti

# Default values
INTERFACE="${1:-enp0s3}"
BANDWIDTH="${2:-10mbit}"
BURST="32kbit"
LATENCY="400ms"

echo "=========================================="
echo "   MARUK DEMO SETUP - TargetVM"
echo "=========================================="
echo ""
echo "Konfigurasi:"
echo "  Interface: $INTERFACE"
echo "  Bandwidth Limit: $BANDWIDTH"
echo "  Burst: $BURST"
echo "  Latency: $LATENCY"
echo ""
echo "=========================================="
echo ""

# Cek apakah script dijalankan dengan sudo
if [ "$EUID" -ne 0 ]; then
    echo "ERROR: Script ini harus dijalankan dengan sudo"
    echo "Gunakan: sudo ./setup_demo.sh"
    exit 1
fi

# Cek apakah interface ada
if ! ip link show "$INTERFACE" &>/dev/null; then
    echo "ERROR: Interface $INTERFACE tidak ditemukan!"
    echo ""
    echo "Interface yang tersedia:"
    ip link show | grep -E "^[0-9]+" | awk '{print "  - " $2}' | sed 's/:$//'
    echo ""
    echo "Gunakan: sudo ./setup_demo.sh [INTERFACE_NAME]"
    exit 1
fi

echo "[1/4] Menerapkan bandwidth limiting..."
# Hapus qdisc yang ada terlebih dahulu (jika ada)
tc qdisc del dev "$INTERFACE" root 2>/dev/null

# Terapkan bandwidth limit menggunakan Token Bucket Filter (TBF)
if tc qdisc add dev "$INTERFACE" root tbf rate "$BANDWIDTH" burst "$BURST" latency "$LATENCY"; then
    echo "✓ Bandwidth limiting diterapkan: $BANDWIDTH"
    echo "  - Rate: $BANDWIDTH"
    echo "  - Burst: $BURST"
    echo "  - Latency: $LATENCY"
else
    echo "✗ GAGAL menerapkan bandwidth limiting!"
    exit 1
fi
echo ""

echo "[2/4] Verifikasi iperf3 server..."
if systemctl is-active --quiet iperf3; then
    echo "✓ iperf3 server sedang berjalan"
    echo "  Status: $(systemctl status iperf3 | grep Active | awk '{print $2, $3}')"
elif pgrep -x "iperf3" > /dev/null; then
    echo "✓ iperf3 server berjalan (manual mode)"
else
    echo "⚠ WARNING: iperf3 server tidak terdeteksi!"
    echo ""
    echo "Jalankan salah satu perintah berikut:"
    echo "  - systemctl start iperf3"
    echo "  - iperf3 -s -D"
    echo ""
fi
echo ""

echo "[3/4] Cek mitigation agent..."
if pgrep -f "mitigation_agent.py" > /dev/null; then
    echo "✓ Mitigation agent sedang berjalan"
    PID=$(pgrep -f "mitigation_agent.py")
    echo "  PID: $PID"
else
    echo "⚠ WARNING: Mitigation agent tidak terdeteksi!"
    echo ""
    echo "Jalankan mitigation agent dengan:"
    echo "  cd MARUK/backend"
    echo "  source venv/bin/activate"
    echo "  export XT_PATH=\$(sudo find / -name xtables 2>/dev/null)"
    echo "  sudo XTABLES_LIBDIR=\"\$XT_PATH\" venv/bin/python mitigation_agent.py"
    echo ""
fi
echo ""

echo "[4/4] Verifikasi konfigurasi jaringan..."
echo "Interface $INTERFACE:"
tc qdisc show dev "$INTERFACE" | grep -q "tbf"
if [ $? -eq 0 ]; then
    echo "✓ Traffic control aktif:"
    tc qdisc show dev "$INTERFACE" | head -n 1 | sed 's/^/  /'
else
    echo "✗ Traffic control tidak aktif!"
fi
echo ""

echo "=========================================="
echo "   SETUP SELESAI!"
echo "=========================================="
echo ""
echo "Status ringkasan:"
echo "  [✓] Bandwidth limiting: AKTIF ($BANDWIDTH)"
if pgrep -x "iperf3" > /dev/null || systemctl is-active --quiet iperf3; then
    echo "  [✓] iperf3 server: BERJALAN"
else
    echo "  [⚠] iperf3 server: TIDAK BERJALAN"
fi
if pgrep -f "mitigation_agent.py" > /dev/null; then
    echo "  [✓] Mitigation agent: BERJALAN"
else
    echo "  [⚠] Mitigation agent: TIDAK BERJALAN"
fi
echo ""
echo "TargetVM siap untuk demo!"
echo "=========================================="
echo ""
