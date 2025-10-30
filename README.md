-----

# Proyek MARUK (Monitoring, Attack, and Regulation Utility)

**MARUK** adalah sebuah platform edukasi keamanan siber yang terintegrasi. Proyek ini menyediakan lingkungan laboratorium virtual yang aman dan terkontrol bagi mahasiswa dan praktisi TI untuk mensimulasikan, memantau, dan memitigasi serangan jaringan berbasis volume (DDoS) secara *real-time*.

Proyek ini menjembatani kesenjangan antara teori keamanan jaringan dan keterampilan praktis dengan menggabungkan tiga pilar utama ke dalam satu utilitas terpadu.

## 🚀 Fitur Utama

1.  **Attack (Simulasi Serangan)**: Mesin serangan berbasis **Scapy** yang mampu menghasilkan lalu lintas serangan DDoS (seperti ICMP/UDP/TCP Flood) dengan teknik IP Spoofing untuk mensimulasikan serangan terdistribusi.
2.  **Monitor (Pemantauan Real-time)**: *Dashboard* terpusat berbasis **Flask** dan **Chart.js** yang memantau metrik kinerja jaringan (Latency, Throughput, Packet Loss) dari target secara *real-time*.
3.  **Regulation (Mitigasi Serangan)**: Agen mitigasi berbasis **Flask** & **python-iptables** yang dapat dikontrol dari jarak jauh. Agen ini dapat secara dinamis menerapkan atau mencabut aturan *firewall* (`iptables`) di VM Target untuk memblokir serangan.

## 🛠️ Tumpukan Teknologi (Tech Stack)

  * **Backend & Skrip**: Python 3.11+
  * **API & Web Server**: Flask
  * **Simulasi Serangan**: Scapy
  * **Monitoring Metrik**: `icmplib`, `iperf3`
  * **Mitigasi Firewall**: `python-iptables`
  * **Visualisasi Frontend**: Chart.js, HTML/CSS/JavaScript
  * **Lingkungan Virtualisasi**: Oracle VirtualBox
  * **Sistem Operasi VM**: Debian 13 (Trixie) / Ubuntu Server

## ⚙️ Panduan Setup Lingkungan

Panduan ini akan memandu Anda untuk menyiapkan seluruh topologi lab MARUK.

### Bagian 1: Prasyarat

1.  **Oracle VirtualBox**: Pastikan Anda telah menginstal versi terbaru.
2.  **`.iso` OS**: Siapkan file `.iso` Debian 13 (atau Ubuntu Server).
3.  **Git**: Terinstal di mesin host Anda.

### Bagian 2: Setup Jaringan VirtualBox

Kita perlu membuat jaringan virtual agar semua VM kita dapat saling berkomunikasi.

1.  Buka VirtualBox.
2.  Pergi ke **File \> Tools \> Network Manager**.
3.  Pilih tab **NAT Networks**.
4.  Klik **Create**. Sebuah jaringan baru bernama `NatNetwork` akan muncul.
5.  Pastikan `NatNetwork` ini memiliki **DHCP Server Enabled**.

### Bagian 3: Setup VM (Lakukan untuk SEMUA VM)

Buat VM dasar pertama Anda (misal, bernama "Debian-Template") dengan spesifikasi berikut:

  * **RAM**: 2GB
  * **Penyimpanan**: 10GB (Dinamis)
  * **Network**: Set ke **NAT Network** (gunakan `NatNetwork` yang baru saja Anda buat).
  * **Instalasi OS**: Lakukan instalasi minimal Debian 13. **JANGAN** instal Desktop Environment (DE).
  * **User**: Buat pengguna non-root (misal, `vboxuser`).

Setelah VM terinstal, **buat 3 klon** dari VM template ini dan beri nama:

1.  `MonitorVM` (Controller / Otak)
2.  `TargetVM` (Victim / Perisai)
3.  `AttackerVM` (Penyerang / Tombak)

### Bagian 4: Konfigurasi Awal Tiap VM

Nyalakan **setiap VM** dan lakukan konfigurasi dasar berikut di dalamnya.

1.  **Instal `sudo` dan `git`**:

    ```bash
    su -
    apt update
    apt install sudo git -y
    usermod -aG sudo <nama_user_anda>
    exit
    ```

    (Logout dan login kembali agar `sudo` aktif).

2.  **Instal Paket Dasar Python**:

    ```bash
    sudo apt update
    sudo apt install python3 python3-pip python3-venv -y
    ```

3.  **Clone Repositori Proyek**:

    ```bash
    git clone <URL_REPO_GITHUB_ANDA>
    cd MARUK
    ```

### Bagian 5: Setup Spesifik per VM

Masuk ke folder `MARUK/backend` di setiap VM dan jalankan setup spesifik di bawah ini.

#### 1\. 🖥️ Di `TargetVM` (Victim / Perisai)

Mesin ini perlu menjalankan agen mitigasi dan server `iperf3`.

```bash
cd MARUK/backend

# Instal dependensi kompilasi & firewall
sudo apt update
sudo apt install build-essential python3-dev iperf3 iptables -y

# Buat venv dan instal paket Python
python3 -m venv venv
source venv/bin/activate
pip install Flask python-iptables

# Jalankan iperf3 sebagai server
# Saat ditanya "Start Iperf3 as a daemon automatically?", pilih <Yes>
```

#### 2\. 📊 Di `MonitorVM` (Controller / Otak)

Mesin ini perlu menjalankan API monitoring utama.

```bash
cd MARUK/backend

# Instal dependensi (iperf3 dibutuhkan untuk library-nya)
sudo apt update
sudo apt install iperf3 -y
# Saat ditanya "Start Iperf3 as a daemon automatically?", pilih <No>

# Buat venv dan instal paket Python
python3 -m venv venv
source venv/bin/activate
pip install Flask icmplib iperf3 requests
```

#### 3\. 💣 Di `AttackerVM` (Penyerang / Tombak)

Mesin ini hanya perlu `scapy`.

```bash
cd MARUK/backend

# Buat venv dan instal paket Python
python3 -m venv venv
source venv/bin/activate
pip install scapy
```

-----

## 🚀 Menjalankan Proyek (Alur Demo)

### Langkah 1: Dapatkan IP Address

Nyalakan semua VM Anda. Login ke setiap VM dan jalankan `ip a` untuk menemukan IP address mereka (misal, `10.0.2.x`).

**PENTING**: Catat IP dari `MonitorVM` dan `TargetVM`.

### Langkah 2: Edit File Konfigurasi

Di `MonitorVM`, edit file `MARUK/backend/app.py`:

```bash
nano MARUK/backend/app.py
```

Ubah variabel `TARGET_IP` dan `MITIGATION_AGENT_URL` dengan IP address `TargetVM` Anda yang sebenarnya.

### Langkah 3: Jalankan Semua Server Backend

Buka 3 terminal SSH terpisah dari Host Anda untuk menjalankan semua layanan.

1.  **Di Terminal 1 (SSH ke `TargetVM`)**:
    Jalankan Agen Mitigasi.

    ```bash
    cd MARUK/backend
    source venv/bin/activate

    # Temukan path xtables (wajib)
    export XT_PATH=$(sudo find / -name xtables 2>/dev/null)

    # Jalankan agen dengan sudo dan path xtables
    sudo XTABLES_LIBDIR="$XT_PATH" venv/bin/python mitigation_agent.py
    ```

    *(Server ini akan berjalan di port `5001`)*

2.  **Di Terminal 2 (SSH ke `MonitorVM`)**:
    Jalankan Server Monitoring Utama.

    ```bash
    cd MARUK/backend
    source venv/bin/activate
    python3 app.py
    ```

    *(Server ini akan berjalan di port `5000`)*

3.  **Di Terminal 3 (Opsional - untuk verifikasi)**:
    Buka SSH ke `TargetVM` lagi dan jalankan `tcpdump` untuk melihat serangan.

    ```bash
    sudo tcpdump -n icmp
    ```

### Langkah 4: Jalankan Frontend (Dashboard)

1.  Di komputer **Host** Anda, buka folder `frontend`.
2.  Buka file `index.html` di browser Anda.
3.  (Jika perlu) Edit `frontend/script.js` untuk memastikan URL API mengarah ke `http://<IP_MonitorVM>:5000`.

### Langkah 5: Skenario Demo

1.  **Lihat Dashboard**: Perhatikan metrik (Latency, Throughput) dalam keadaan normal.
2.  **Mulai Serangan**:
      * Buka terminal SSH ke `AttackerVM`.
      * `cd MARUK/backend`
      * `source venv/bin/activate`
      * `sudo venv/bin/python test_attack.py` (Ganti IP target di dalam skrip jika perlu)
3.  **Lihat Dampak**: Perhatikan *dashboard*. Latency akan melonjak dan Throughput akan anjlok. `tcpdump` akan dipenuhi paket.
4.  **Aktifkan Mitigasi**:
      * Klik tombol "Start Mitigation" di *dashboard* (atau jalankan `curl http://<IP_MonitorVM>:5000/api/mitigate/start`).
5.  **Lihat Pemulihan**:
      * Metrik di *dashboard* akan kembali normal.
      * `tcpdump` akan menunjukkan paket *request* masih masuk, tetapi paket *reply* berhenti (tanda *firewall* `DROP` berhasil).
6.  **Hentikan Mitigasi**:
      * Klik tombol "Stop Mitigation" (atau jalankan `curl http://<IP_MonitorVM>:5000/api/mitigate/stop`).
      * Metrik akan kembali kacau, membuktikan serangan masih berjalan.

-----

## 🚨 Troubleshooting Umum

  * **SSH `timeout` atau `connection refused`**:

    1.  Pastikan semua VM ada di `NAT Network` yang sama.
    2.  Pastikan layanan `ssh` berjalan (`sudo systemctl status ssh`).
    3.  Periksa aturan Port Forwarding jika Anda menggunakan mode `NAT` standar.

  * **VM Mendapat IP `169.254.x.x`**:

      * VM Anda gagal mendapatkan IP dari DHCP. Jalankan `sudo reboot` di dalam VM tersebut. Jika masih gagal, periksa pengaturan `NAT Network` Anda di VirtualBox.

  * **Error `setcap` atau `privileged` saat `ping`**:

      * File `app.py` sudah diatur untuk menggunakan `privileged=False` pada `icmplib`, yang menghindari masalah ini.

  * **Error `XTABLES_LIBDIR`**:

      * Pastikan Anda menjalankan `mitigation_agent.py` menggunakan perintah `sudo XTABLES_LIBDIR="..." ...` seperti di atas.
