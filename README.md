# MARUK (Monitoring, Attack, and Regulation Utility for Kilobits)

Laporan Praktikum 1 Infrastruktur Jaringan Komputer - Kelompok 11

> MARUK dirancang sebagai sebuah platform edukasi terintegrasi yang menyediakan lingkungan laboratorium virtual yang aman dan terkontrol. [cite_start]Dalam lingkungan ini, pengguna dapat mensimulasikan serangan jaringan, memantau dampaknya secara visual melalui dashboard interaktif, dan menerapkan berbagai teknik mitigasi untuk menstabilkan kembali jaringan. [cite: 26, 27]

---

## 👨‍💻 Tim Pengembang

* [cite_start]**Arif Rahman** (1519624018) - Project Lead & Backend Developer [cite: 7, 96]
* [cite_start]**Achtaroyan Rakabillah** (1519624042) - Frontend Developer [cite: 9, 96]
* [cite_start]**Jeremy Partahi Oloan Sianipar** (1519624027) - QA & Documentation [cite: 8, 97]

---

## 🛠️ Tumpukan Teknologi

* [cite_start]**Backend:** Python 3, Flask, Scapy [cite: 125][cite_start], iperf3 [cite: 147][cite_start], python-iptables[cite: 159], requests
* [cite_start]**Frontend:** Chart.js [cite: 138][cite_start], HTML5, CSS3, JavaScript (Fetch API) [cite: 148]
* [cite_start]**Infrastruktur:** Oracle VirtualBox [cite: 107][cite_start], Debian 13, Git & GitHub [cite: 120]

---

## 🚀 Panduan Setup Proyek

Panduan ini menjelaskan cara setup penuh lingkungan MARUK dari awal di PC baru.

### 1. Prasyarat (Di Komputer Host Anda)

Pastikan Anda telah menginstal perangkat lunak berikut di PC utama Anda:
1.  [cite_start]**Git** [cite: 120]
2.  [cite_start]**Oracle VirtualBox** [cite: 107]
3.  **SSH Client** (Bawaan Windows Terminal, PowerShell, atau terminal Linux/macOS)
4.  [cite_start]**Code Editor** (misalnya, Visual Studio Code) [cite: 119]

### 2. Setup Lingkungan Lab (VirtualBox)

Kita akan membuat 4 VM yang saling terhubung.

#### A. Konfigurasi Jaringan VirtualBox
Sebelum membuat VM, siapkan jaringannya terlebih dahulu agar semua VM bisa saling terhubung.
1.  Buka VirtualBox.
2.  Pergi ke **File > Tools > Network Manager**.
3.  Pilih tab **NAT Networks**.
4.  Klik **Create**. Beri nama (misalnya, `MarukNet`). Pastikan **DHCP Server** dalam keadaan **Enabled**.
5.  Klik **Apply**.

#### B. Buat 4 Virtual Machine
Buat 4 VM baru dengan konfigurasi berikut (disarankan 4 VM untuk simulasi "Pengguna Asli"):
1.  **`MonitorVM`** (Controller)
2.  **`TargetVM`** (Victim)
3.  **`AttackerVM`** (Attacker)
4.  **`RealUserVM`** (Pengguna Asli)

**Pengaturan untuk setiap VM:**
* **OS:** Debian 13 (Net-install, **No Desktop Environment**).
* **RAM:** Minimal 1GB (2GB disarankan).
* **Network:**
    * Pastikan **Adapter 1** terpasang ke **NAT Network**.
    * Pilih nama jaringan yang Anda buat tadi (misalnya, `MarukNet`).

#### C. Setup Awal Setiap VM
Setelah instalasi OS selesai, nyalakan **setiap VM** dan lakukan setup dasar berikut (bisa via konsol VirtualBox):
1.  Login sebagai `root` (atau `su -`).
2.  Instal *tools* dasar:
    ```bash
    apt update
    apt install sudo openssh-server git python3-venv python3-pip -y
    ```
3.  Buat *user* Anda (jika belum) dan tambahkan ke grup `sudo`:
    ```bash
    usermod -aG sudo namauseranda
    ```
4.  Cari tahu IP address setiap VM:
    ```bash
    ip a
    ```
    Catat IP untuk setiap VM (misalnya, `10.0.2.3`, `10.0.2.4`, `10.0.2.5`, `10.0.2.6`).

#### D. (Opsional) Konfigurasi SSH Port Forwarding
Untuk mempermudah akses SSH dari host Anda:
1.  Buka **File > Tools > Network Manager**.
2.  Pilih `MarukNet` Anda, lalu klik **Port Forwarding**.
3.  Tambahkan aturan untuk setiap VM:
    * **Rule 1 (Monitor):** Host Port `2222` -> Guest IP `<IP_MonitorVM>` -> Guest Port `22`
    * **Rule 2 (Target):** Host Port `2223` -> Guest IP `<IP_TargetVM>` -> Guest Port `22`
    * **Rule 3 (Attacker):** Host Port `2224` -> Guest IP `<IP_AttackerVM>` -> Guest Port `22`
    * **Rule 4 (User):** Host Port `2225` -> Guest IP `<IP_RealUserVM>` -> Guest Port `22`

Sekarang Anda bisa SSH ke VM Anda dari host, misal: `ssh namauser@127.0.0.1 -p 2222`

### 3. Setup Peran (Kloning & Instalasi)

Setiap anggota tim harus melakukan ini di VM yang sesuai dengan perannya.

#### A. Setup `MonitorVM` (Controller)
*Peran: Arif (Backend)*
```bash
# SSH ke MonitorVM
ssh user@127.0.0.1 -p 2222

# Clone repo
git clone [https://github.com/username/MARUK.git](https://github.com/username/MARUK.git)
cd MARUK/backend

# Buat venv
python3 -m venv venv
source venv/bin/activate

# Instal library Python
pip install flask icmplib iperf3 requests

# Instal library sistem (PENTING)
sudo apt install iperf3 -y
# Saat ditanya "Start Iperf3 as a daemon automatically?", pilih <No>
