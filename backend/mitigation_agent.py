from flask import Flask, jsonify
import iptc # Ini adalah library python-iptables
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Nama chain kustom agar mudah dihapus
CHAIN_NAME = "MARUK_MITIGATION"

# Track active mitigations
active_mitigations = {
    "icmp": False,
    "udp": False,
    "tcp": False
}

def get_chain():
    """Membuat atau mengambil chain kustom kita di tabel 'filter'."""
    try:
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
    except Exception as e:
        logger.error(f"Error getting chain: {e}")
        raise

@app.route('/mitigate/start_icmp_block')
def start_icmp_block():
    """Memblokir semua lalu lintas ICMP (ping)."""
    try:
        chain = get_chain()

        # Buat aturan: DROP semua paket ICMP
        rule = iptc.Rule()
        rule.protocol = "icmp"
        rule.target = iptc.Target(rule, "DROP")

        # Masukkan aturan ke chain kita
        chain.insert_rule(rule)
        active_mitigations["icmp"] = True
        logger.info("ICMP blocking enabled")

        return jsonify({"status": "success", "message": "Aturan DROP ICMP ditambahkan."}), 200
    except Exception as e:
        logger.error(f"Error enabling ICMP block: {e}")
        # Don't crash - return error response
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/mitigate/stop_icmp_block')
def stop_icmp_block():
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
            active_mitigations["icmp"] = False
            logger.info("ICMP blocking disabled")
            return jsonify({"status": "success", "message": "Aturan DROP ICMP dihapus."}), 200
        else:
            active_mitigations["icmp"] = False
            return jsonify({"status": "error", "message": "Aturan DROP ICMP tidak ditemukan."}), 404

    except Exception as e:
        logger.error(f"Error disabling ICMP block: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# New endpoints for comprehensive mitigation control

@app.route('/mitigate/block_icmp')
def block_icmp():
    """Block ICMP traffic (alias for start_icmp_block)."""
    return start_icmp_block()

@app.route('/mitigate/unblock_icmp')
def unblock_icmp():
    """Remove ICMP block (alias for stop_icmp_block)."""
    return stop_icmp_block()

@app.route('/mitigate/block_udp')
def block_udp():
    """Block UDP flood traffic with rate limiting using limit module."""
    try:
        chain = get_chain()

        # Create rule: Rate limit UDP packets using limit module (more compatible)
        # This accepts up to 100/sec, drops the rest
        rule = iptc.Rule()
        rule.protocol = "udp"
        
        # Use limit module (simpler and more compatible than hashlimit)
        match = rule.create_match("limit")
        match.limit = "100/sec"
        match.limit_burst = "50"
        
        # Accept packets within the limit
        rule.target = iptc.Target(rule, "ACCEPT")
        chain.insert_rule(rule)
        
        # Drop all other UDP packets that exceed the limit
        drop_rule = iptc.Rule()
        drop_rule.protocol = "udp"
        drop_rule.target = iptc.Target(drop_rule, "DROP")
        chain.insert_rule(drop_rule)
        
        active_mitigations["udp"] = True
        logger.info("UDP rate limiting enabled (limit module)")

        return jsonify({"status": "success", "message": "UDP rate limiting enabled (max 100/sec)."}), 200
    except Exception as e:
        logger.error(f"Error enabling UDP block: {e}")
        # Don't crash - return error response
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/mitigate/unblock_udp')
def unblock_udp():
    """Remove UDP block."""
    try:
        chain = get_chain()
        rule_deleted = False

        # Remove all UDP rules (both ACCEPT with limit and DROP)
        for rule in chain.rules[:]:
            if rule.protocol == "udp":
                chain.delete_rule(rule)
                rule_deleted = True

        if rule_deleted:
            active_mitigations["udp"] = False
            logger.info("UDP rate limiting disabled")
            return jsonify({"status": "success", "message": "UDP rate limiting removed."}), 200
        else:
            active_mitigations["udp"] = False
            return jsonify({"status": "error", "message": "UDP rule not found."}), 404

    except Exception as e:
        logger.error(f"Error disabling UDP block: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/mitigate/block_tcp_syn')
def block_tcp_syn():
    """Block TCP SYN packets to port 5201."""
    try:
        chain = get_chain()

        # Create rule: DROP TCP SYN to port 5201
        rule = iptc.Rule()
        rule.protocol = "tcp"
        
        # Match destination port 5201
        match = rule.create_match("tcp")
        match.dport = "5201"
        
        # Match SYN flag
        match.syn = True
        
        rule.target = iptc.Target(rule, "DROP")
        chain.insert_rule(rule)
        active_mitigations["tcp"] = True
        logger.info("TCP SYN blocking enabled for port 5201")

        return jsonify({"status": "success", "message": "TCP SYN blocking enabled for port 5201."}), 200
    except Exception as e:
        logger.error(f"Error enabling TCP SYN block: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/mitigate/unblock_tcp_syn')
def unblock_tcp_syn():
    """Remove TCP SYN block."""
    try:
        chain = get_chain()
        rule_deleted = False

        for rule in chain.rules[:]:
            if rule.protocol == "tcp" and rule.target.name == "DROP":
                chain.delete_rule(rule)
                rule_deleted = True

        if rule_deleted:
            active_mitigations["tcp"] = False
            logger.info("TCP SYN blocking disabled")
            return jsonify({"status": "success", "message": "TCP SYN blocking removed."}), 200
        else:
            active_mitigations["tcp"] = False
            return jsonify({"status": "error", "message": "TCP SYN rule not found."}), 404

    except Exception as e:
        logger.error(f"Error disabling TCP SYN block: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/mitigate/block_all')
def block_all():
    """Enable all three mitigations."""
    results = {}
    overall_success = True
    
    # Block ICMP
    try:
        chain = get_chain()
        rule = iptc.Rule()
        rule.protocol = "icmp"
        rule.target = iptc.Target(rule, "DROP")
        chain.insert_rule(rule)
        active_mitigations["icmp"] = True
        results["icmp"] = {"status": "success"}
        logger.info("ICMP blocking enabled (block_all)")
    except Exception as e:
        results["icmp"] = {"status": "error", "message": str(e)}
        overall_success = False
        logger.error(f"Error enabling ICMP in block_all: {e}")
    
    # Block UDP
    try:
        chain = get_chain()
        # Use limit module
        rule = iptc.Rule()
        rule.protocol = "udp"
        match = rule.create_match("limit")
        match.limit = "100/sec"
        match.limit_burst = "50"
        rule.target = iptc.Target(rule, "ACCEPT")
        chain.insert_rule(rule)
        
        drop_rule = iptc.Rule()
        drop_rule.protocol = "udp"
        drop_rule.target = iptc.Target(drop_rule, "DROP")
        chain.insert_rule(drop_rule)
        
        active_mitigations["udp"] = True
        results["udp"] = {"status": "success"}
        logger.info("UDP rate limiting enabled (block_all)")
    except Exception as e:
        results["udp"] = {"status": "error", "message": str(e)}
        overall_success = False
        logger.error(f"Error enabling UDP in block_all: {e}")
    
    # Block TCP SYN
    try:
        chain = get_chain()
        rule = iptc.Rule()
        rule.protocol = "tcp"
        match = rule.create_match("tcp")
        match.dport = "5201"
        match.syn = True
        rule.target = iptc.Target(rule, "DROP")
        chain.insert_rule(rule)
        active_mitigations["tcp"] = True
        results["tcp"] = {"status": "success"}
        logger.info("TCP SYN blocking enabled (block_all)")
    except Exception as e:
        results["tcp"] = {"status": "error", "message": str(e)}
        overall_success = False
        logger.error(f"Error enabling TCP in block_all: {e}")
    
    logger.info(f"All mitigations enabled: {results}")
    status_code = 200 if overall_success else 500
    return jsonify({
        "status": "success" if overall_success else "partial",
        "message": "All mitigations enabled" if overall_success else "Some mitigations failed",
        "details": results
    }), status_code

@app.route('/mitigate/unblock_all')
def unblock_all():
    """Remove all mitigations."""
    results = {}
    overall_success = True
    
    # Unblock ICMP
    try:
        chain = get_chain()
        rule_deleted = False
        for rule in chain.rules[:]:
            if rule.protocol == "icmp" and rule.target.name == "DROP":
                chain.delete_rule(rule)
                rule_deleted = True
        active_mitigations["icmp"] = False
        results["icmp"] = {"status": "success"}
        logger.info("ICMP blocking disabled (unblock_all)")
    except Exception as e:
        results["icmp"] = {"status": "error", "message": str(e)}
        overall_success = False
        logger.error(f"Error disabling ICMP in unblock_all: {e}")
    
    # Unblock UDP
    try:
        chain = get_chain()
        rule_deleted = False
        for rule in chain.rules[:]:
            if rule.protocol == "udp":
                chain.delete_rule(rule)
                rule_deleted = True
        active_mitigations["udp"] = False
        results["udp"] = {"status": "success"}
        logger.info("UDP rate limiting disabled (unblock_all)")
    except Exception as e:
        results["udp"] = {"status": "error", "message": str(e)}
        overall_success = False
        logger.error(f"Error disabling UDP in unblock_all: {e}")
    
    # Unblock TCP SYN
    try:
        chain = get_chain()
        rule_deleted = False
        for rule in chain.rules[:]:
            if rule.protocol == "tcp" and rule.target.name == "DROP":
                chain.delete_rule(rule)
                rule_deleted = True
        active_mitigations["tcp"] = False
        results["tcp"] = {"status": "success"}
        logger.info("TCP SYN blocking disabled (unblock_all)")
    except Exception as e:
        results["tcp"] = {"status": "error", "message": str(e)}
        overall_success = False
        logger.error(f"Error disabling TCP in unblock_all: {e}")
    
    logger.info(f"All mitigations disabled: {results}")
    status_code = 200 if overall_success else 500
    return jsonify({
        "status": "success" if overall_success else "partial",
        "message": "All mitigations removed" if overall_success else "Some mitigations failed to remove",
        "details": results
    }), status_code

@app.route('/mitigate/status')
def get_mitigation_status():
    """Return JSON with active mitigations."""
    return jsonify({
        "icmp": active_mitigations["icmp"],
        "udp": active_mitigations["udp"],
        "tcp": active_mitigations["tcp"]
    }), 200

if __name__ == '__main__':
    # Kita jalankan di port yang berbeda, misal 5001
    # HARUS dijalankan dengan sudo!
    # Debug mode should be disabled in production for security
    # Set FLASK_DEBUG=1 environment variable to enable debug mode in development
    import os
    debug_mode = os.environ.get('FLASK_DEBUG', '0') == '1'
    app.run(host='0.0.0.0', port=5001, debug=debug_mode)
