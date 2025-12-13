// ============================================
// MARUK Dashboard - Control System (No Combined, Has Kill All)
// ============================================

// Chart configurations
const chartConfig = {
    maxDataPoints: 60,
    updateInterval: 2000,
    statusInterval: 3000
};
let latencyChart, throughputChart, packetLossChart;

document.addEventListener('DOMContentLoaded', function() {
    initializeCharts();
    startDataCollection();
    startStatusPolling();
});

// CHART INITIALIZATION (unchanged)
function initializeCharts() { /* ... SAME ... */ }
// -- snipped for brevity; your chart initialize code stays exactly the same --

// DATA COLLECTION (unchanged)
function startDataCollection() { fetchMetrics(); setInterval(fetchMetrics, chartConfig.updateInterval); }
async function fetchMetrics() { /* ... SAME ... */ }
function updateMetricCard(type, value) { /* ... SAME ... */ }
function updateChart(chart, label, value) { /* ... SAME ... */ }

// STATUS POLLING (slightly cleaned)
function startStatusPolling() {
    fetchAttackStatus();
    fetchMitigationStatus();
    setInterval(fetchAttackStatus, chartConfig.statusInterval);
    setInterval(fetchMitigationStatus, chartConfig.statusInterval);
}
async function fetchAttackStatus() {
    try {
        const response = await fetch('/api/attack/status');
        const data = await response.json();
        updateStatusIndicator('icmp-attack-status', data.icmp.active);
        updateStatusIndicator('udp-attack-status', data.udp.active);
        updateStatusIndicator('tcp-attack-status', data.tcp.active);
        // Remove combined!
        const activeCount = [data.icmp.active, data.udp.active, data.tcp.active].filter(Boolean).length;
        document.getElementById('active-attacks-count').textContent = activeCount;
    } catch (error) {
        console.error('Failed to fetch attack status:', error);
    }
}
async function fetchMitigationStatus() {
    try {
        const response = await fetch('/api/mitigate/status');
        const data = await response.json();
        updateStatusIndicator('icmp-mitigation-status', data.icmp, true);
        updateStatusIndicator('udp-mitigation-status', data.udp, true);
        updateStatusIndicator('tcp-mitigation-status', data.tcp, true);
        // Remove ALL mitigation!
        const activeCount = [data.icmp, data.udp, data.tcp].filter(Boolean).length;
        document.getElementById('active-mitigations-count').textContent = activeCount;
    } catch (error) {
        console.error('Failed to fetch mitigation status:', error);
    }
}
function updateStatusIndicator(elementId, isActive, isMitigation = false) {
    const element = document.getElementById(elementId);
    if (element)
        element.textContent = isActive ? (isMitigation ? '🟢' : '🔴') : '⚪';
}

// ============================================
// ATTACK CONTROL (No per-STOP, NEW Kill All)
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
        console.error(`Error controlling ${type} attack:`, error);
        showToast(`Error: Failed to contact attack controller`, 'error');
    } finally {
        setTimeout(() => button.disabled = false, 1000);
    }
}

// NEW: KILL ALL ATTACKS
async function killAllAttacks() {
    const button = event.target;
    button.disabled = true;
    try {
        const response = await fetch(`/api/attack/killall`);
        const result = await response.json();
        if (result.status === 'success') {
            showToast("All attack processes killed!", 'success');
            setTimeout(fetchAttackStatus, 500);
        } else {
            showToast(`Failed to kill attacks: ${result.message}`, 'error');
        }
    } catch (error) {
        console.error("Error killing all attacks:", error);
        showToast(`Error: Could not send killall`, 'error');
    } finally {
        setTimeout(() => button.disabled = false, 1000);
    }
}

// MITIGATION CONTROL (unchanged)
async function controlMitigation(type, action) { /* ... SAME ... */ }

// TOAST NOTIFICATIONS (unchanged)
function showToast(message, type = 'info') { /* ... SAME ... */ }
