// ============================================
// MARUK Dashboard - Complete Control System
// ============================================

// Chart configurations
const chartConfig = {
    maxDataPoints: 60,
    updateInterval: 2000,  // 2 seconds
    statusInterval: 3000   // 3 seconds
};

// Initialize charts
let latencyChart, throughputChart, packetLossChart;

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeCharts();
    startDataCollection();
    startStatusPolling();
});

// ============================================
// CHART INITIALIZATION
// + ... (no changes to chart initialization section) ...

// (Chart initialization code unchanged - OMITTED HERE FOR BREVITY; use your existing code above.)

// ============================================
// DATA COLLECTION, STATUS POLLING, etc.
// (Unchanged from above, except attack status polling and button logic updated.)

// ============================================
// ATTACK CONTROL
// ============================================

async function controlAttack(type, action) {
    const button = event.target;
    button.disabled = true;
    try {
        const response = await fetch(`/api/attack/${type}/${action}`);
        const result = await response.json();
        if (result.status === 'success') {
            showToast(`${type.toUpperCase()} attack ${action}ed successfully!`, 'success');
            setTimeout(fetchAttackStatus, 500);
        } else {
            showToast(`Failed to ${action} ${type.toUpperCase()} attack: ${result.message}`, 'error');
        }
    } catch (error) {
        showToast(`Error: Failed to contact attack controller`, 'error');
    } finally {
        setTimeout(() => button.disabled = false, 1000);
    }
}

async function killAllAttacksHandler() {
    // New function to handle KILL ALL button
    const btns = document.querySelectorAll(".btn.btn-danger");
    btns.forEach(btn => btn.disabled = true);
    try {
        const response = await fetch(`/api/attack/killall`, { method: "POST" });
        const result = await response.json();
        if (result.status === "success") {
            showToast(`All attack processes killed.`, "success");
            setTimeout(fetchAttackStatus, 800);
        } else {
            showToast(`Failed to kill all attacks: ${result.message}`, "error");
        }
    } catch (error) {
        showToast(`Error: Failed to contact attack controller`, 'error');
    } finally {
        setTimeout(() => btns.forEach(btn => btn.disabled = false), 1000);
    }
}

// ============================================
// The rest of DATA, METRIC, CHART, STATUS etc
// (Unchanged; use your existing code above.)
// ============================================

// MITIGATION CONTROL and TOAST unchanged
// Just ensure only KILL ALL button (with killAllAttacksHandler) is in HTML & no per-attack STOP buttons
