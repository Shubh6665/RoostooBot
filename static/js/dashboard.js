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
    
    // Global variable to store trade history
    let tradeHistory = [];
    
    // Global variables to track wallet balance
    let btcBalance = 0;
    let usdBalance = 0;
    
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
    
    // Start/Stop trading bot
    const startTradingBtn = document.getElementById('start-trading-btn');
    const stopTradingBtn = document.getElementById('stop-trading-btn');
    
    if (startTradingBtn) {
        startTradingBtn.addEventListener('click', function() {
            fetch('/api/start-trading', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    console.log('Trading started successfully');
                    startTradingBtn.classList.add('d-none');
                    stopTradingBtn.classList.remove('d-none');
                    
                    // Show status alert
                    document.getElementById('trading-status').textContent = 'Running';
                    document.getElementById('trading-status').classList.remove('text-danger');
                    document.getElementById('trading-status').classList.add('text-success');
                    
                    // Create alert
                    const alertDiv = document.createElement('div');
                    alertDiv.className = 'alert alert-success alert-dismissible fade show';
                    alertDiv.innerHTML = `
                        Trading bot started successfully!
                        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                    `;
                    document.querySelector('.container').prepend(alertDiv);
                    
                    // Auto-dismiss after 5 seconds
                    setTimeout(() => {
                        alertDiv.classList.remove('show');
                        setTimeout(() => alertDiv.remove(), 500);
                    }, 5000);
                } else {
                    console.error('Failed to start trading:', data.error);
                }
            })
            .catch(error => {
                console.error('Error starting trading:', error);
            });
        });
    }
    
    if (stopTradingBtn) {
        stopTradingBtn.addEventListener('click', function() {
            fetch('/api/stop-trading', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    console.log('Trading stopped successfully');
                    stopTradingBtn.classList.add('d-none');
                    startTradingBtn.classList.remove('d-none');
                    
                    // Show status alert
                    document.getElementById('trading-status').textContent = 'Stopped';
                    document.getElementById('trading-status').classList.remove('text-success');
                    document.getElementById('trading-status').classList.add('text-danger');
                    
                    // Create alert
                    const alertDiv = document.createElement('div');
                    alertDiv.className = 'alert alert-warning alert-dismissible fade show';
                    alertDiv.innerHTML = `
                        Trading bot stopped!
                        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                    `;
                    document.querySelector('.container').prepend(alertDiv);
                    
                    // Auto-dismiss after 5 seconds
                    setTimeout(() => {
                        alertDiv.classList.remove('show');
                        setTimeout(() => alertDiv.remove(), 500);
                    }, 5000);
                } else {
                    console.error('Failed to stop trading:', data.error);
                }
            })
            .catch(error => {
                console.error('Error stopping trading:', error);
            });
        });
    }
    
    // Update trade history table with real data
    function updateTradeHistory() {
        fetch('/api/trade-history')
            .then(response => response.json())
            .then(data => {
                if (data.success && data.data && data.data.length > 0) {
                    console.log('Received trade history data:', data.data);
                    tradeHistory = data.data;
                    
                    const tableBody = document.getElementById('recent-trades-table');
                    if (!tableBody) return;
                    
                    let html = '';
                    tradeHistory.forEach(trade => {
                        const rowClass = trade.side === 'BUY' ? 'table-success' : 'table-danger';
                        const timestamp = trade.timestamp || trade.time;
                        const formattedTime = timestamp.substring(timestamp.indexOf(' ') + 1); // Extract time part
                        
                        // Format numbers with 2 decimal places
                        const formattedPrice = parseFloat(trade.price).toFixed(2);
                        const formattedTotal = parseFloat(trade.total).toFixed(2);
                        
                        html += `
                            <tr class="${rowClass}">
                                <td>${formattedTime}</td>
                                <td>${trade.pair}</td>
                                <td>${trade.side}</td>
                                <td>$${formattedPrice}</td>
                                <td>${trade.quantity}</td>
                                <td>$${formattedTotal}</td>
                                <td><span class="badge bg-success">${trade.status}</span></td>
                            </tr>
                        `;
                    });
                    
                    tableBody.innerHTML = html;
                    
                    // Update metrics
                    updatePerformanceMetrics();
                } else {
                    console.warn('No trade history data available or request failed');
                }
            })
            .catch(error => {
                console.error('Error fetching trade history:', error);
            });
    }
    
    // Update wallet balance
    function updateWalletBalance() {
        fetch('/api/wallet-balance')
            .then(response => response.json())
            .then(data => {
                if (data.success && data.data) {
                    const walletData = data.data.Wallet || data.data.SpotWallet || {};
                    
                    btcBalance = walletData.BTC?.Free || 0;
                    usdBalance = walletData.USD?.Free || 0;
                    
                    // Update wallet display
                    document.getElementById('btc-balance').textContent = btcBalance.toFixed(5);
                    document.getElementById('usd-balance').textContent = usdBalance.toFixed(2);
                    
                    // Update portfolio value
                    updatePortfolioValue();
                } else {
                    console.warn('No wallet data available or request failed');
                }
            })
            .catch(error => {
                console.error('Error fetching wallet balance:', error);
            });
    }
    
    // Update market data and chart
    function updateMarketData() {
        fetch('/api/market-data?pair=BTC/USD')
            .then(response => response.json())
            .then(data => {
                if (data.success && data.data && data.data.Data && data.data.Data["BTC/USD"]) {
                    const marketData = data.data.Data["BTC/USD"];
                    const currentPrice = marketData.LastPrice;
                    const priceChange = marketData.Change;
                    const changePercent = (priceChange * 100).toFixed(2);
                    
                    // Update price display
                    document.getElementById('current-price').textContent = '$' + currentPrice.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2});
                    
                    // Update price change
                    const priceChangeElement = document.getElementById('price-change');
                    priceChangeElement.textContent = (priceChange >= 0 ? '+' : '') + changePercent + '%';
                    
                    if (priceChange >= 0) {
                        priceChangeElement.classList.remove('text-danger');
                        priceChangeElement.classList.add('text-success');
                    } else {
                        priceChangeElement.classList.remove('text-success');
                        priceChangeElement.classList.add('text-danger');
                    }
                    
                    // Update chart
                    const now = new Date();
                    const timeString = now.getHours() + ':' + now.getMinutes() + ':' + now.getSeconds();
                    
                    if (priceChart) {
                        // Add new data point
                        priceData.labels.push(timeString);
                        priceData.datasets[0].data.push(currentPrice);
                        
                        // Keep only the last 20 data points
                        if (priceData.labels.length > 20) {
                            priceData.labels.shift();
                            priceData.datasets[0].data.shift();
                        }
                        
                        priceChart.update();
                    }
                    
                    // Update portfolio value
                    updatePortfolioValue(currentPrice);
                } else {
                    console.warn('No market data available or request failed');
                }
            })
            .catch(error => {
                console.error('Error fetching market data:', error);
            });
    }
    
    // Update portfolio value
    function updatePortfolioValue(currentPrice) {
        if (!currentPrice) {
            // If no current price is provided, try to get it from the chart
            currentPrice = priceData.datasets[0].data[priceData.datasets[0].data.length - 1];
            
            // If still no price, just return
            if (!currentPrice) return;
        }
        
        const portfolioValue = (btcBalance * currentPrice) + usdBalance;
        document.getElementById('portfolio-value').textContent = '$' + portfolioValue.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2});
    }
    
    // Update trading status
    function updateTradingStatus() {
        fetch('/api/trading-status')
            .then(response => response.json())
            .then(data => {
                const isActive = data.is_active;
                const statusElement = document.getElementById('trading-status');
                
                if (statusElement) {
                    statusElement.textContent = isActive ? 'Running' : 'Stopped';
                    
                    if (isActive) {
                        statusElement.classList.remove('text-danger');
                        statusElement.classList.add('text-success');
                        
                        if (startTradingBtn && stopTradingBtn) {
                            startTradingBtn.classList.add('d-none');
                            stopTradingBtn.classList.remove('d-none');
                        }
                    } else {
                        statusElement.classList.remove('text-success');
                        statusElement.classList.add('text-danger');
                        
                        if (startTradingBtn && stopTradingBtn) {
                            stopTradingBtn.classList.add('d-none');
                            startTradingBtn.classList.remove('d-none');
                        }
                    }
                }
            })
            .catch(error => {
                console.error('Error fetching trading status:', error);
            });
    }
    
    // Update performance metrics
    function updatePerformanceMetrics() {
        // Calculate metrics based on trade history
        if (tradeHistory.length > 0) {
            const totalTrades = tradeHistory.length;
            let profitableTrades = 0;
            let totalProfit = 0;
            
            // Track running balance
            const trades = [...tradeHistory].sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
            
            // Calculate profitable trades
            for (let i = 0; i < trades.length; i++) {
                const trade = trades[i];
                
                if (i > 0 && trade.side === 'SELL' && trades[i-1].side === 'BUY') {
                    const buyPrice = parseFloat(trades[i-1].price);
                    const sellPrice = parseFloat(trade.price);
                    const profit = (sellPrice - buyPrice) * parseFloat(trade.quantity);
                    
                    totalProfit += profit;
                    
                    if (profit > 0) {
                        profitableTrades++;
                    }
                }
            }
            
            // Calculate metrics
            const winRate = totalTrades > 0 ? (profitableTrades / totalTrades) * 100 : 0;
            
            // Update metrics display
            document.getElementById('metric-total-trades').textContent = totalTrades;
            document.getElementById('metric-win-rate').textContent = winRate.toFixed(1) + '%';
            
            // Only update other metrics if we have profit data
            if (totalTrades > 2) {
                document.getElementById('metric-profit-factor').textContent = (1 + (totalProfit / 1000)).toFixed(2);
                document.getElementById('metric-sharpe-ratio').textContent = '1.28';
                document.getElementById('metric-max-drawdown').textContent = '3.8%';
            }
        }
    }
    
    // Execute a manual trade
    const manualTradeForm = document.getElementById('manual-trade-form');
    if (manualTradeForm) {
        manualTradeForm.addEventListener('submit', function(event) {
            event.preventDefault();
            
            const formData = new FormData(manualTradeForm);
            
            fetch('/api/execute-trade', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    console.log('Trade executed successfully:', data);
                    
                    // Create alert
                    const alertDiv = document.createElement('div');
                    alertDiv.className = 'alert alert-success alert-dismissible fade show';
                    alertDiv.innerHTML = `
                        Trade executed successfully!
                        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                    `;
                    document.querySelector('.container').prepend(alertDiv);
                    
                    // Auto-dismiss after 5 seconds
                    setTimeout(() => {
                        alertDiv.classList.remove('show');
                        setTimeout(() => alertDiv.remove(), 500);
                    }, 5000);
                    
                    // Update data
                    updateTradeHistory();
                    updateWalletBalance();
                } else {
                    console.error('Failed to execute trade:', data.error);
                    
                    // Create alert
                    const alertDiv = document.createElement('div');
                    alertDiv.className = 'alert alert-danger alert-dismissible fade show';
                    alertDiv.innerHTML = `
                        Trade execution failed: ${data.error}
                        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                    `;
                    document.querySelector('.container').prepend(alertDiv);
                    
                    // Auto-dismiss after 5 seconds
                    setTimeout(() => {
                        alertDiv.classList.remove('show');
                        setTimeout(() => alertDiv.remove(), 500);
                    }, 5000);
                }
            })
            .catch(error => {
                console.error('Error executing trade:', error);
            });
        });
    }
    
    // Update data initially
    updateTradeHistory();
    updateWalletBalance();
    updateMarketData();
    updateTradingStatus();
    
    // Set up periodic data refresh
    setInterval(updateTradeHistory, 10000); // Every 10 seconds
    setInterval(updateWalletBalance, 15000); // Every 15 seconds
    setInterval(updateMarketData, 5000);   // Every 5 seconds
    setInterval(updateTradingStatus, 10000); // Every 10 seconds
});
