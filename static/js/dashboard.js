// Dashboard JavaScript

// Price data for chart
const priceData = {
    labels: [],
    datasets: [{
        label: 'BTC/USD Price',
        data: [],
        borderColor: '#0dcaf0',
        backgroundColor: 'rgba(13, 202, 240, 0.1)',
        fill: true,
        tension: 0.3
    }]
};

// Chart configuration
const chartConfig = {
    type: 'line',
    data: priceData,
    options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            x: {
                grid: {
                    color: 'rgba(255, 255, 255, 0.1)'
                }
            },
            y: {
                grid: {
                    color: 'rgba(255, 255, 255, 0.1)'
                }
            }
        },
        animation: {
            duration: 500
        },
        plugins: {
            legend: {
                display: true,
                position: 'top'
            },
            tooltip: {
                mode: 'index',
                intersect: false
            }
        }
    }
};

// Initialize chart
let priceChart;

document.addEventListener('DOMContentLoaded', function() {
    // Initialize the price chart
    const ctx = document.getElementById('price-chart').getContext('2d');
    priceChart = new Chart(ctx, chartConfig);
    
    // Start data updates
    fetchBotStatus();
    fetchMarketData();
    fetchWalletBalance();
    
    // Set up event listeners for buttons
    document.getElementById('start-bot-btn').addEventListener('click', startBot);
    document.getElementById('stop-bot-btn').addEventListener('click', stopBot);
    
    // Set up intervals for data updates
    setInterval(fetchBotStatus, 10000); // Update bot status every 10 seconds
    setInterval(fetchMarketData, 30000); // Update market data every 30 seconds
    setInterval(fetchWalletBalance, 60000); // Update wallet balance every minute
});

// Fetch bot status
function fetchBotStatus() {
    fetch('/api/bot_status')
        .then(response => response.json())
        .then(data => {
            updateBotStatus(data.status);
            updatePerformanceMetrics(data.metrics);
            updateLastTrade(data.last_trade);
        })
        .catch(error => console.error('Error fetching bot status:', error));
}

// Fetch market data
function fetchMarketData() {
    const pair = 'BTC/USD'; // Default to BTC/USD
    fetch(`/api/market_data?pair=${pair}`)
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                updatePriceDisplay(data.data);
                updatePriceChart(data.data);
            } else {
                console.error('Error fetching market data:', data.message);
            }
        })
        .catch(error => console.error('Error fetching market data:', error));
}

// Fetch wallet balance
function fetchWalletBalance() {
    fetch('/api/wallet_balance')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                updateWalletTable(data.data);
            } else {
                console.error('Error fetching wallet balance:', data.message);
            }
        })
        .catch(error => console.error('Error fetching wallet balance:', error));
}

// Start the trading bot
function startBot() {
    // Default settings
    const settings = {
        trading_pair: 'BTC/USD',
        risk_level: 0.02
    };
    
    fetch('/api/start_bot', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(settings)
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            updateBotStatus('running');
            showNotification('Bot started successfully', 'success');
        } else {
            showNotification(`Failed to start bot: ${data.message}`, 'danger');
        }
    })
    .catch(error => {
        console.error('Error starting bot:', error);
        showNotification('Error starting bot', 'danger');
    });
}

// Stop the trading bot
function stopBot() {
    fetch('/api/stop_bot', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            updateBotStatus('stopped');
            showNotification('Bot stopped successfully', 'success');
        } else {
            showNotification(`Failed to stop bot: ${data.message}`, 'danger');
        }
    })
    .catch(error => {
        console.error('Error stopping bot:', error);
        showNotification('Error stopping bot', 'danger');
    });
}

// Update bot status display
function updateBotStatus(status) {
    const statusIndicator = document.querySelector('.status-indicator');
    const statusText = document.getElementById('bot-status-indicator');
    const startBtn = document.getElementById('start-bot-btn');
    const stopBtn = document.getElementById('stop-bot-btn');
    
    statusText.textContent = status.charAt(0).toUpperCase() + status.slice(1);
    
    if (status === 'running') {
        statusIndicator.classList.remove('status-stopped');
        statusIndicator.classList.add('status-running');
        startBtn.disabled = true;
        stopBtn.disabled = false;
    } else {
        statusIndicator.classList.remove('status-running');
        statusIndicator.classList.add('status-stopped');
        startBtn.disabled = false;
        stopBtn.disabled = true;
    }
}

// Update performance metrics
function updatePerformanceMetrics(metrics) {
    if (!metrics) return;
    
    document.getElementById('portfolio-value').textContent = `$${metrics.current_balance.toFixed(2)}`;
    
    const profitLoss = metrics.profit_loss;
    const profitLossIndicator = document.getElementById('profit-loss-indicator');
    const profitProgress = document.getElementById('profit-progress');
    
    profitLossIndicator.textContent = `${profitLoss >= 0 ? '+' : ''}$${profitLoss.toFixed(2)}`;
    profitLossIndicator.className = `badge ${profitLoss >= 0 ? 'bg-success' : 'bg-danger'}`;
    
    profitProgress.className = `progress-bar ${profitLoss >= 0 ? 'bg-success' : 'bg-danger'}`;
    const progressPercentage = Math.abs((profitLoss / metrics.initial_balance) * 100);
    profitProgress.style.width = `${Math.min(progressPercentage, 100)}%`;
    
    document.getElementById('win-rate').textContent = `${metrics.win_rate.toFixed(2)}%`;
    document.getElementById('trades-executed').textContent = metrics.trades_executed;
}

// Update last trade information
function updateLastTrade(trade) {
    const lastTradeInfo = document.getElementById('last-trade-info');
    
    if (trade) {
        lastTradeInfo.innerHTML = `
            <p class="mb-1">
                <span class="badge ${trade.action === 'BUY' ? 'bg-success' : 'bg-danger'}">
                    ${trade.action}
                </span>
                <span class="text-muted">${trade.timestamp}</span>
            </p>
            <p class="mb-1">Price: $${parseFloat(trade.price).toFixed(2)}</p>
            <p class="mb-0">Quantity: ${parseFloat(trade.quantity).toFixed(6)} BTC</p>
        `;
        
        // Add to trading history
        addTradeToHistory(trade);
    } else {
        lastTradeInfo.innerHTML = `<p class="text-center text-muted">No trades executed yet</p>`;
    }
}

// Update price display
function updatePriceDisplay(tickerData) {
    if (!tickerData) return;
    
    const currentPrice = document.getElementById('current-price');
    const priceChange = document.getElementById('price-change');
    const priceUpdated = document.getElementById('price-updated');
    
    const price = tickerData.LastPrice;
    const change = tickerData.Change * 100; // Convert to percentage
    
    currentPrice.textContent = `$${price.toFixed(2)}`;
    priceChange.textContent = `${change >= 0 ? '+' : ''}${change.toFixed(2)}%`;
    priceChange.className = `badge ${change >= 0 ? 'bg-success' : 'bg-danger'}`;
    
    const now = new Date();
    priceUpdated.textContent = `Last updated: ${now.toLocaleTimeString()}`;
}

// Update price chart with new data
function updatePriceChart(tickerData) {
    if (!tickerData || !priceChart) return;
    
    const price = tickerData.LastPrice;
    const now = new Date();
    const timeStr = now.toLocaleTimeString();
    
    // Add new data point
    priceChart.data.labels.push(timeStr);
    priceChart.data.datasets[0].data.push(price);
    
    // Keep only the last 20 data points for better visualization
    if (priceChart.data.labels.length > 20) {
        priceChart.data.labels.shift();
        priceChart.data.datasets[0].data.shift();
    }
    
    priceChart.update();
}

// Update wallet balance table
function updateWalletTable(walletData) {
    if (!walletData) return;
    
    const tableBody = document.querySelector('#wallet-table tbody');
    let tableHtml = '';
    
    // Sort assets alphabetically but with USD first
    const assets = Object.keys(walletData).sort((a, b) => {
        if (a === 'USD') return -1;
        if (b === 'USD') return 1;
        return a.localeCompare(b);
    });
    
    for (const asset of assets) {
        const data = walletData[asset];
        const free = parseFloat(data.Free);
        const locked = parseFloat(data.Lock || 0);
        const total = free + locked;
        
        // Calculate USD value
        let usdValue = 0;
        if (asset === 'USD') {
            usdValue = total;
        } else {
            // Assume 1:1 for simplicity, in reality we would fetch the current price
            usdValue = total * 1; // replace with actual price later
        }
        
        tableHtml += `
            <tr>
                <td>${asset}</td>
                <td>${free.toFixed(6)}</td>
                <td>${locked.toFixed(6)}</td>
                <td>${total.toFixed(6)}</td>
                <td>$${usdValue.toFixed(2)}</td>
            </tr>
        `;
    }
    
    if (tableHtml === '') {
        tableHtml = '<tr><td colspan="5" class="text-center">No assets found</td></tr>';
    }
    
    tableBody.innerHTML = tableHtml;
}

// Add a trade to the trading history
function addTradeToHistory(trade) {
    const historyContainer = document.getElementById('trading-history');
    const emptyHistory = document.getElementById('empty-history');
    
    if (emptyHistory) {
        emptyHistory.style.display = 'none';
    }
    
    const tradeElement = document.createElement('div');
    tradeElement.className = 'border-bottom pb-2 mb-2';
    tradeElement.innerHTML = `
        <div class="d-flex justify-content-between align-items-center">
            <span class="badge ${trade.action === 'BUY' ? 'bg-success' : 'bg-danger'}">${trade.action}</span>
            <small class="text-muted">${trade.timestamp}</small>
        </div>
        <div class="d-flex justify-content-between">
            <span>Price:</span>
            <span>$${parseFloat(trade.price).toFixed(2)}</span>
        </div>
        <div class="d-flex justify-content-between">
            <span>Quantity:</span>
            <span>${parseFloat(trade.quantity).toFixed(6)} BTC</span>
        </div>
    `;
    
    // Add as the first child
    historyContainer.insertBefore(tradeElement, historyContainer.firstChild);
}

// Show notification
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 end-0 m-3`;
    notification.role = 'alert';
    notification.style.zIndex = '1050';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Add to document
    document.body.appendChild(notification);
    
    // Remove after 5 seconds
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 150);
    }, 5000);
}
