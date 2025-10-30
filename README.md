-----

# MARUK (Monitoring, Attack, and Regulation Utility for Kilobits)

**Laporan Praktikum 1 Infrastruktur Jaringan Komputer - Kelompok 11**

MARUK adalah platform edukasi terintegrasi yang dirancang untuk menjembatani kesenjangan antara teori dan praktik keamanan siber[cite: 245]. Platform ini menyediakan lingkungan laboratorium virtual yang aman [cite: 242] bagi mahasiswa untuk mensimulasikan serangan jaringan (DDoS & *bandwidth hogging*), memantau dampaknya secara *real-time* melalui *dashboard* visual, dan menerapkan teknik mitigasi (seperti *firewall*) untuk memulihkan stabilitas jaringan[cite: 243, 244].

### 👥 Anggota Kelompok 11

  * **Arif Rahman** (`1519624018`) - Project Lead & Backend Developer [cite: 312]
  * **Achtaroyan Rakabillah** (`1519624042`) - Frontend Developer [cite: 312]
  * **Jeremy Partahi Oloan Sianipar** (`1519624027`) - QA & Documentation Specialist [cite: 313]

-----

## 🏛️ Arsitektur Proyek

Proyek ini berjalan dalam lingkungan lab virtual yang terdiri dari **4 Virtual Machine (VM)** [cite: 324] yang saling terhubung:

1.  🧠 **VM Monitoring (Controller):** Menjalankan server API utama (`app.py`) yang mengumpulkan metrik dan bertindak sebagai "otak" yang dapat memicu mitigasi. Ini juga akan menjadi *host* untuk *dashboard* frontend.
2.  🛡️ **VM Target (Victim):** Mesin yang menjadi sasaran serangan. Mesin ini menjalankan agen mitigasi (`mitigation_agent.py`) untuk mengaktifkan *firewall* saat diperintah.
3.  💥 **VM Penyerang (Attacker):** Mesin yang menjalankan skrip serangan `test_attack.py` (menggunakan Scapy) [cite: 341] untuk menghasilkan lalu lintas DDoS.
4.  👤 **VM Real User (Opsional):** Mesin yang bertindak sebagai pengguna biasa (menjalankan `ping` atau `curl`) untuk mendemonstrasikan dampak serangan terhadap pengguna yang sah.

-----

## 🚀 Setup Proyek (Getting Started)

Panduan ini akan memandu Anda untuk men-setup keseluruhan lingkungan MARUK di PC Anda.

### 1\. Prasyarat Sistem

  * **VirtualBox** (atau *hypervisor* lain) [cite: 323]
  * **Git** [cite: 336]
  * File `.iso` **Debian 13** (atau distro Linux server lain) [cite: 332]
  * Akses terminal / SSH client (seperti PowerShell, Windows Terminal, atau PuTTY)

### 2\. Langkah 1: Setup Lingkungan Lab (VirtualBox)

Setiap anggota tim harus melakukan ini di PC masing-masing.

1.  **Buat 4 VM**: Buat empat VM baru (Monitoring, Target, Penyerang, Real User) menggunakan VirtualBox.
      * **RAM**: Berikan **2 GB** RAM untuk setiap VM (rekomendasi).
      * **OS**: Instal Debian 13 (Netinstall, **tanpa Desktop Environment**).
2.  **Konfigurasi Jaringan (PENTING)**:
      * Pastikan semua VM dalam keadaan **mati**.
      * Untuk **setiap VM**, buka **Settings \> Network**.
      * Ubah **Attached to:** menjadi **`Bridged Adapter`**.
      * Di bawah **Name**, pilih kartu jaringan utama PC Anda (misal: `wlp...` untuk Wi-Fi atau `enp...` untuk Ethernet).
      * Ini akan membuat semua VM Anda mendapatkan IP (seperti `192.168.x.x`) dari router utama Anda, sehingga mereka bisa saling berkomunikasi.
3.  **Setup Awal di *Setiap* VM**:
      * Nyalakan semua VM dan login melalui konsol VirtualBox.
      * **Instal `sudo`**:
        ```bash
        su -
        apt update && apt install sudo
        usermod -aG sudo <username_anda>
        exit # Logout
        ```
      * **Login kembali** dan pastikan `sudo` berfungsi.
      * **Instal SSH Server & Git**:
        ```bash
        sudo apt update
        sudo apt install openssh-server git -y
        ```
      * **Cari IP Anda**: Catat IP address setiap VM dengan `ip a`.
4.  **Clone Repositori**:
      * Di **SEMUA EMPAT** VM, *clone* repositori ini:
        ```bash
        git clone <URL_GitHub_Proyek_Anda>
        cd MARUK
        ```

### 3\. Langkah 2: Setup Masing-Masing VM (Dependencies)

Sekarang, kita akan menginstal paket khusus untuk peran setiap VM.

#### 🧠 VM Monitoring (Controller)

*Tugas: Menjalankan `app.py`*

```bash
# Instal paket sistem yang dibutuhkan
sudo apt install python3-venv iperf3 -y

# Masuk ke folder backend
cd ~/MARUK/backend

# Buat & aktifkan virtual environment
python3 -m venv venv
source venv/bin/activate

# Instal library Python
pip install Flask icmplib iperf3 requests

# Simpan dependensi (opsional, tapi bagus)
pip freeze > requirements.txt

# KONFIGURASI PENTING:
# Edit file app.py
nano app.py

# Pastikan variabel ini benar:
# TARGET_IP = "<IP_VM_Target_Anda>"
# MITIGATION_AGENT_URL = "http://<IP_VM_Target_Anda>:5001"
#
# Dan pastikan fungsi ping() menggunakan privileged=False:
# host = ping(..., privileged=False)
```

#### 🛡️ VM Target (Victim)

*Tugas: Menjalankan `mitigation_agent.py` dan server `iperf3`*

```bash
# Instal paket sistem yang dibutuhkan (ini krusial!)
sudo apt install python3-venv iperf3 build-essential python3-dev iptables -y

# Set iperf3 untuk berjalan sebagai server (daemon)
# Saat instalasi, akan muncul pop-up. Pilih <Yes>

# Masuk ke folder backend
cd ~/MARUK/backend

# Buat & aktifkan virtual environment
python3 -m venv venv
source venv/bin/activate

# Instal library Python (ini akan dikompilasi)
pip install Flask python-iptables
```

#### 💥 VM Penyerang (Attacker)

*Tugas: Menjalankan `test_attack.py`*

```bash
# Instal paket sistem
sudo apt install python3-venv -y

# Masuk ke folder backend
cd ~/MARUK/backend

# Buat & aktifkan virtual environment
python3 -m venv venv
source venv/bin/activate

# Instal Scapy
pip install scapy
```

#### 👤 VM Real User

*Tugas: Menjalankan `ping` atau `curl`*

  * Tidak perlu setup khusus. Cukup pastikan `ping` dan `curl` terinstal (`sudo apt install curl inetutils-ping`).

-----

## 🏁 Cara Menjalankan Simulasi Penuh

Setelah semua setup selesai, ikuti urutan ini untuk menjalankan demo:

1.  **Di VM Target (Victim)**:

      * Pastikan server `iperf3` berjalan (jika tidak memilih `<Yes>` saat instal, jalankan `iperf3 -s &`).
      * Jalankan Agen Mitigasi. **Path `XTABLES_LIBDIR` ini WAJIB**:
        ```bash
        cd ~/MARUK/backend
        source venv/bin/activate
        sudo XTABLES_LIBDIR="/usr/lib/x86_64-linux-gnu/xtables" venv/bin/python mitigation_agent.py
        ```

2.  **Di VM Monitoring (Controller)**:

      * Jalankan API Server Utama:
        ```bash
        cd ~/MARUK/backend
        source venv/bin/activate
        python3 app.py
        ```

3.  **Di VM Real User**:

      * Mulai ping berkelanjutan untuk melihat dampak:
        ```bash
        ping <IP_VM_TARGET>
        ```

4.  **Di PC Host Anda (Akses Frontend)**:

      * Buka browser dan arahkan ke *dashboard* yang dibuat oleh tim Frontend.
      * *Dashboard* akan memanggil `http://<IP_VM_MONITOR>:5000/api/metrics` dan menampilkan grafik.

5.  **Di VM Penyerang (Attacker)**:

      * Mulai serangan\!
        ```bash
        cd ~/MARUK/backend
        source venv/bin/activate
        sudo venv/bin/python test_attack.py
        ```
      * **Amati**: Lihat *dashboard* dan terminal `ping` di VM Real User. Metrik akan anjlok.

6.  **Di PC Host Anda (Tindakan Mitigasi)**:

      * Picu mitigasi *firewall* dengan memanggil API di VM Monitoring:
        ```bash
        curl http://<IP_VM_MONITOR>:5000/api/mitigate/start
        ```
      * **Amati**: Metrik di *dashboard* akan pulih, dan `ping` akan gagal (karena kita memblokir ICMP).
      * Untuk menghentikan mitigasi:
        ```bash
        curl http://<IP_VM_MONITOR>:5000/api/mitigate/stop
        ```
