from flask import Flask, jsonify

# Inisialisasi aplikasi Flask
app = Flask(__name__)

# Definisikan route untuk API kita
@app.route('/api/metrics')
def get_metrics():
    # Ini adalah data DUMMY untuk tim frontend
    # Nanti kita akan ganti dengan data monitoring asli
    dummy_data = {
        "latency": 15,
        "throughput": 850,
        "packet_loss": 0
    }

    # Kembalikan data sebagai JSON
    return jsonify(dummy_data)

# Jalankan server
if __name__ == '__main__':
    # PENTING: host='0.0.0.0' membuat server bisa diakses
    # dari IP VM, bukan hanya dari localhost.
    app.run(host='0.0.0.0', port=5000, debug=True)
