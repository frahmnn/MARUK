// Konfigurasi Awal Grafik
const ctx = document.getElementById('trafficChart').getContext('2d');
const trafficChart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: [], // Waktu (Sumbu X)
        datasets: [
            {
                label: 'Throughput (Mbps)',
                data: [],
                borderColor: 'rgb(75, 192, 192)',
                yAxisID: 'y',
            },
            {
                label: 'Latency (ms)',
                data: [],
                borderColor: 'rgb(255, 99, 132)',
                yAxisID: 'y1',
            }
        ]
    },
    options: {
        responsive: true,
        scales: {
            y: {
                type: 'linear',
                display: true,
                position: 'left',
                title: { display: true, text: 'Throughput (Mbps)' }
            },
            y1: {
                type: 'linear',
                display: true,
                position: 'right',
                grid: { drawOnChartArea: false }, // Agar grid tidak tumpang tindih
                title: { display: true, text: 'Latency (ms)' }
            }
        }
    }
});

// Fungsi untuk mengambil data dari Backend
async function fetchData() {
    try {
        const response = await fetch('/api/metrics');
        const data = await response.json();

        const now = new Date().toLocaleTimeString();

        // Tambahkan data baru ke grafik
        if (trafficChart.data.labels.length > 20) {
            trafficChart.data.labels.shift(); // Hapus data terlama jika sudah penuh
            trafficChart.data.datasets[0].data.shift();
            trafficChart.data.datasets[1].data.shift();
        }

        trafficChart.data.labels.push(now);
        trafficChart.data.datasets[0].data.push(data.throughput);
        trafficChart.data.datasets[1].data.push(data.latency);

        trafficChart.update();
    } catch (error) {
        console.error('Gagal mengambil data:', error);
    }
}

// Fungsi Kontrol Mitigasi
async function toggleMitigation(action) {
    const btnStart = document.getElementById('btn-start');
    const btnStop = document.getElementById('btn-stop');
    const statusText = document.getElementById('mitigation-status');

    try {
        // Panggil API backend (/api/mitigate/start atau /stop)
        const response = await fetch(`/api/mitigate/${action}`);
        const result = await response.json();

        if (result.status === 'success') {
            if (action === 'start') {
                statusText.innerText = "AKTIF (Memblokir Serangan)";
                statusText.style.color = "green";
                btnStart.disabled = true;
                btnStop.disabled = false;
            } else {
                statusText.innerText = "Non-Aktif";
                statusText.style.color = "red";
                btnStart.disabled = false;
                btnStop.disabled = true;
            }
            alert(result.message);
        } else {
            alert("Gagal: " + result.message);
        }
    } catch (error) {
        console.error('Error mitigasi:', error);
        alert("Gagal menghubungi server.");
    }
}

// Jalankan fungsi fetchData setiap 2 detik
setInterval(fetchData, 2000);
