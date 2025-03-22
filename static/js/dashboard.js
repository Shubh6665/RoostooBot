/**
 * Dashboard JavaScript for the Trading Bot
 * Handles updating the UI with real-time data
 */

document.addEventListener('DOMContentLoaded', function() {
    // Global variables for price chart
    let priceChart;
    let priceData = {
        labels: [],
        datasets: [{
            label: 'BTC/USD Price',
            data: [],
            borderColor: 'rgba(75, 192, 192, 1)',
            borderWidth: 2,
            pointRadius: 0,
            tension: 0.1,
            fill: false
        }]
    };
    
    // Initialize price chart
    function initPriceChart() {
        const ctx = document.getElementById('priceChart');
        if (!ctx) return;
        
        const ctxObj = ctx.getContext('2d');
        priceChart = new Chart(ctxObj, {
            type: 'line',
            data: priceData,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        grid: {
                            display: false
                        }
                    },
                    y: {
                        grid: {
                            color: 'rgba(200, 200, 200, 0.1)'
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    }
                },
                animation: {
                    duration: 0
                }
            }
        });
    }
    
    // Initialize the charts when DOM is loaded
    initPriceChart();
    
    // Set up mock transactions for the recent trades table
    function setupMockTradeHistory() {
        const tradeData = [
            { time: '12:30:15', pair: 'BTC/USD', side: 'BUY', price: '64125.50', quantity: '0.015', total: '961.88', status: 'FILLED' },
            { time: '11:45:22', pair: 'BTC/USD', side: 'SELL', price: '64017.85', quantity: '0.010', total: '640.18', status: 'FILLED' },
            { time: '10:12:05', pair: 'BTC/USD', side: 'BUY', price: '63985.25', quantity: '0.020', total: '1279.71', status: 'FILLED' }
        ];
        
        const tableBody = document.getElementById('recent-trades-table');
        if (!tableBody) return;
        
        let html = '';
        tradeData.forEach(trade => {
            const rowClass = trade.side === 'BUY' ? 'table-success' : 'table-danger';
            html += `
                <tr class="${rowClass}">
                    <td>${trade.time}</td>
                    <td>${trade.pair}</td>
                    <td>${trade.side}</td>
                    <td>$${trade.price}</td>
                    <td>${trade.quantity}</td>
                    <td>$${trade.total}</td>
                    <td><span class="badge bg-success">${trade.status}</span></td>
                </tr>
            `;
        });
        
        tableBody.innerHTML = html;
    }
    
    // Setup performance metrics with sample data
    function setupPerformanceMetrics() {
        document.getElementById('metric-total-trades')?.textContent = '15';
        document.getElementById('metric-win-rate')?.textContent = '73.3%';
        document.getElementById('metric-profit-factor')?.textContent = '2.45';
        document.getElementById('metric-sharpe-ratio')?.textContent = '1.85';
        document.getElementById('metric-max-drawdown')?.textContent = '4.2%';
    }
    
    // Initialize with sample data
    setupMockTradeHistory();
    setupPerformanceMetrics();
});
