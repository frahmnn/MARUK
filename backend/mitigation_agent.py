from flask import Flask, jsonify
import iptc # Ini adalah library python-iptables

app = Flask(__name__)

# Nama chain kustom agar mudah dihapus
CHAIN_NAME = "MARUK_MITIGATION"

def get_chain():
    """Membuat atau mengambil chain kustom kita di tabel 'filter'."""
    table = iptc.Table(iptc.Table.FILTER)

    # Coba buat chain baru
    try:
        table.create_chain(CHAIN_NAME)
    except iptc.IPTCError:
        # Chain sudah ada, tidak masalah
        pass

    chain = iptc.Chain(table, CHAIN_NAME)

    # Pastikan chain kita terhubung ke INPUT
    # Kita cek dulu agar tidak duplikat
    input_chain = iptc.Chain(table, "INPUT")
    rule = iptc.Rule()
    rule.target = iptc.Target(rule, CHAIN_NAME)

    if rule not in input_chain.rules:
        input_chain.insert_rule(rule)

    return chain

@app.route('/mitigate/start_icmp_block')
def start_mitigation():
    """Memblokir semua lalu lintas ICMP (ping)."""
    try:
        chain = get_chain()

        # Buat aturan: DROP semua paket ICMP
        rule = iptc.Rule()
        rule.protocol = "icmp"
        rule.target = iptc.Target(rule, "DROP")

        # Masukkan aturan ke chain kita
        chain.insert_rule(rule)

        return jsonify({"status": "success", "message": "Aturan DROP ICMP ditambahkan."}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/mitigate/stop_icmp_block')
def stop_mitigation():
    """Menghapus aturan blokir ICMP."""
    try:
        chain = get_chain()
        rule_deleted = False

        # Loop melalui semua aturan di chain kustom kita
        # Kita harus membuat salinan list-nya [:] agar aman saat menghapus
        for rule in chain.rules[:]:
            # Cari aturan yang: protokolnya 'icmp' DAN targetnya 'DROP'
            if rule.protocol == "icmp" and rule.target.name == "DROP":
                # Temukan! Hapus aturan ini
                chain.delete_rule(rule)
                rule_deleted = True
                # Lanjutkan loop jika ada beberapa aturan (meski seharusnya tidak)

        if rule_deleted:
            return jsonify({"status": "success", "message": "Aturan DROP ICMP dihapus."}), 200
        else:
            return jsonify({"status": "error", "message": "Aturan DROP ICMP tidak ditemukan."}), 404

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    # Kita jalankan di port yang berbeda, misal 5001
    # HARUS dijalankan dengan sudo!
    app.run(host='0.0.0.0', port=5001, debug=True)
