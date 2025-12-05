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
// ============================================

function initializeCharts() {
    // Latency Chart
    const latencyCtx = document.getElementById('latencyChart').getContext('2d');
    latencyChart = new Chart(latencyCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Latency (ms)',
                data: [],
                borderColor: 'rgb(255, 99, 132)',
                backgroundColor: 'rgba(255, 99, 132, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                y: {
                    beginAtZero: true,
                    title: { display: true, text: 'ms', color: '#e0e0e0' },
                    ticks: { color: '#e0e0e0' },
                    grid: { color: 'rgba(255, 255, 255, 0.1)' }
                },
                x: {
                    ticks: { color: '#e0e0e0' },
                    grid: { color: 'rgba(255, 255, 255, 0.1)' }
                }
            },
            plugins: {
                legend: {
                    labels: { color: '#e0e0e0' }
                }
            }
        }
    });

    // Throughput Chart
    const throughputCtx = document.getElementById('throughputChart').getContext('2d');
    throughputChart = new Chart(throughputCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Throughput (Mbps)',
                data: [],
                borderColor: 'rgb(75, 192, 192)',
                backgroundColor: 'rgba(75, 192, 192, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                y: {
                    beginAtZero: true,
                    title: { display: true, text: 'Mbps', color: '#e0e0e0' },
                    ticks: { color: '#e0e0e0' },
                    grid: { color: 'rgba(255, 255, 255, 0.1)' }
                },
                x: {
                    ticks: { color: '#e0e0e0' },
                    grid: { color: 'rgba(255, 255, 255, 0.1)' }
                }
            },
            plugins: {
                legend: {
                    labels: { color: '#e0e0e0' }
                }
            }
        }
    });

    // Packet Loss Chart
    const packetLossCtx = document.getElementById('packetLossChart').getContext('2d');
    packetLossChart = new Chart(packetLossCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Packet Loss (%)',
                data: [],
                borderColor: 'rgb(255, 206, 86)',
                backgroundColor: 'rgba(255, 206, 86, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    title: { display: true, text: '%', color: '#e0e0e0' },
                    ticks: { color: '#e0e0e0' },
                    grid: { color: 'rgba(255, 255, 255, 0.1)' }
                },
                x: {
                    ticks: { color: '#e0e0e0' },
                    grid: { color: 'rgba(255, 255, 255, 0.1)' }
                }
            },
            plugins: {
                legend: {
                    labels: { color: '#e0e0e0' }
                }
            }
        }
    });
}

// ============================================
// DATA COLLECTION
// ============================================

function startDataCollection() {
    fetchMetrics();
    setInterval(fetchMetrics, chartConfig.updateInterval);
}

async function fetchMetrics() {
    try {
        const response = await fetch('/api/metrics');
        const data = await response.json();
        
        // Update timestamp
        const now = new Date();
        document.getElementById('last-update').textContent = now.toLocaleTimeString();
        
        // Update metric cards
        updateMetricCard('latency', data.latency);
        updateMetricCard('throughput', data.throughput);
        updateMetricCard('packet-loss', data.packet_loss);
        
        // Update charts
        const timeLabel = now.toLocaleTimeString();
        updateChart(latencyChart, timeLabel, data.latency);
        updateChart(throughputChart, timeLabel, data.throughput);
        updateChart(packetLossChart, timeLabel, data.packet_loss);
        
        // Update connection status
        document.getElementById('connection-status').textContent = '🟢 Connected';
        document.getElementById('connection-status').className = 'connection-ok';
        
    } catch (error) {
        console.error('Failed to fetch metrics:', error);
        document.getElementById('connection-status').textContent = '🔴 Disconnected';
        document.getElementById('connection-status').className = 'connection-error';
    }
}

function updateMetricCard(type, value) {
    const valueElement = document.getElementById(`${type}-value`);
    const statusElement = document.getElementById(`${type}-status`);
    const cardElement = document.getElementById(`${type}-card`);
    
    // Remove all status classes
    cardElement.classList.remove('status-good', 'status-warning', 'status-critical');
    
    if (value === -1 || value === null) {
        valueElement.textContent = '-- ' + (type === 'throughput' ? 'Mbps' : type === 'latency' ? 'ms' : '%');
        statusElement.textContent = 'Error';
        cardElement.classList.add('status-critical');
        return;
    }
    
    switch (type) {
        case 'latency':
            valueElement.textContent = value.toFixed(2) + ' ms';
            if (value < 30) {
                statusElement.textContent = 'Excellent';
                cardElement.classList.add('status-good');
            } else if (value < 100) {
                statusElement.textContent = 'Moderate';
                cardElement.classList.add('status-warning');
            } else {
                statusElement.textContent = 'Critical';
                cardElement.classList.add('status-critical');
            }
            break;
            
        case 'throughput':
            valueElement.textContent = value.toFixed(2) + ' Mbps';
            if (value > 5) {
                statusElement.textContent = 'Good';
                cardElement.classList.add('status-good');
            } else if (value > 2) {
                statusElement.textContent = 'Degraded';
                cardElement.classList.add('status-warning');
            } else {
                statusElement.textContent = 'Critical';
                cardElement.classList.add('status-critical');
            }
            break;
            
        case 'packet-loss':
            valueElement.textContent = value.toFixed(2) + ' %';
            if (value < 5) {
                statusElement.textContent = 'Normal';
                cardElement.classList.add('status-good');
            } else if (value < 20) {
                statusElement.textContent = 'High';
                cardElement.classList.add('status-warning');
            } else {
                statusElement.textContent = 'Critical';
                cardElement.classList.add('status-critical');
            }
            break;
    }
}

function updateChart(chart, label, value) {
    // Add new data
    chart.data.labels.push(label);
    chart.data.datasets[0].data.push(value);
    
    // Remove old data if exceeds max
    if (chart.data.labels.length > chartConfig.maxDataPoints) {
        chart.data.labels.shift();
        chart.data.datasets[0].data.shift();
    }
    
    chart.update('none'); // Update without animation for better performance
}

// ============================================
// STATUS POLLING
// ============================================

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
        
        // Update status indicators
        updateStatusIndicator('icmp-attack-status', data.icmp.active);
        updateStatusIndicator('udp-attack-status', data.udp.active);
        updateStatusIndicator('tcp-attack-status', data.tcp.active);
        
        // Update combined status
        const combinedActive = data.icmp.active && data.udp.active && data.tcp.active;
        updateStatusIndicator('combined-attack-status', combinedActive);
        
        // Update total count
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
        
        // Update status indicators
        updateStatusIndicator('icmp-mitigation-status', data.icmp, true);
        updateStatusIndicator('udp-mitigation-status', data.udp, true);
        updateStatusIndicator('tcp-mitigation-status', data.tcp, true);
        
        // Update all mitigation status
        const allActive = data.icmp && data.udp && data.tcp;
        updateStatusIndicator('all-mitigation-status', allActive, true);
        
        // Update total count
        const activeCount = [data.icmp, data.udp, data.tcp].filter(Boolean).length;
        document.getElementById('active-mitigations-count').textContent = activeCount;
        
    } catch (error) {
        console.error('Failed to fetch mitigation status:', error);
    }
}

function updateStatusIndicator(elementId, isActive, isMitigation = false) {
    const element = document.getElementById(elementId);
    if (isActive) {
        element.textContent = isMitigation ? '🟢' : '🔴';
    } else {
        element.textContent = '⚪';
    }
}

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
            // Immediately update status
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

// ============================================
// MITIGATION CONTROL
// ============================================

async function controlMitigation(type, action) {
    const button = event.target;
    button.disabled = true;
    
    try {
        const endpoint = action === 'block' ? `${action}_${type}` : `un${action}_${type}`;
        const response = await fetch(`/api/mitigate/${endpoint}`);
        const result = await response.json();
        
        if (result.status === 'success') {
            const actionText = action === 'block' ? 'enabled' : 'disabled';
            showToast(`${type.toUpperCase()} mitigation ${actionText} successfully!`, 'success');
            // Immediately update status
            setTimeout(fetchMitigationStatus, 500);
        } else {
            showToast(`Failed to ${action} ${type.toUpperCase()} mitigation: ${result.message}`, 'error');
        }
    } catch (error) {
        console.error(`Error controlling ${type} mitigation:`, error);
        showToast(`Error: Failed to contact mitigation agent`, 'error');
    } finally {
        setTimeout(() => button.disabled = false, 1000);
    }
}

// ============================================
// TOAST NOTIFICATIONS
// ============================================

function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const icon = type === 'success' ? '✓' : type === 'error' ? '✗' : 'ℹ';
    toast.innerHTML = `<span style="font-size: 1.5rem;">${icon}</span><span>${message}</span>`;
    
    container.appendChild(toast);
    
    // Auto remove after 3 seconds
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}
