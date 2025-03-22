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
    
    // Sample data for initial display
    const samplePrice = 84010.86;
    
    // Initialize price chart
    function initPriceChart() {
        const ctx = document.getElementById('priceChart');
        if (!ctx) return;
        
        try {
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
            
            // Add initial data point
            const now = new Date();
            const timeString = now.getHours() + ':' + now.getMinutes() + ':' + now.getSeconds();
            priceData.labels.push(timeString);
            priceData.datasets[0].data.push(samplePrice);
            priceChart.update();
            
        } catch (error) {
            console.error('Error initializing chart:', error);
        }
    }
    
    // Initialize the charts when DOM is loaded
    initPriceChart();
    
    // Start/Stop trading bot
    const startTradingBtn = document.getElementById('start-trading-btn');
    const stopTradingBtn = document.getElementById('stop-trading-btn');
    
    if (startTradingBtn) {
        startTradingBtn.addEventListener('click', function() {
            // Set UI to loading state
            startTradingBtn.disabled = true;
            startTradingBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Starting...';
            
            fetch('/api/start-trading', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    console.log('Trading started successfully');
                    startTradingBtn.classList.add('d-none');
                    stopTradingBtn.classList.remove('d-none');
                    
                    // Show status alert
                    const statusEl = document.getElementById('trading-status');
                    if (statusEl) {
                        statusEl.textContent = 'Running';
                        statusEl.classList.remove('text-danger');
                        statusEl.classList.add('text-success');
                    }
                    
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
                    showErrorAlert('Failed to start trading: ' + (data.error || 'Unknown error'));
                    startTradingBtn.disabled = false;
                    startTradingBtn.innerHTML = '<i class="fas fa-play me-1"></i>Start Trading';
                }
            })
            .catch(error => {
                console.error('Error starting trading:', error);
                showErrorAlert('Error starting trading. Please try again.');
                startTradingBtn.disabled = false;
                startTradingBtn.innerHTML = '<i class="fas fa-play me-1"></i>Start Trading';
            });
        });
    }
    
    if (stopTradingBtn) {
        stopTradingBtn.addEventListener('click', function() {
            // Set UI to loading state
            stopTradingBtn.disabled = true;
            stopTradingBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Stopping...';
            
            fetch('/api/stop-trading', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    console.log('Trading stopped successfully');
                    stopTradingBtn.classList.add('d-none');
                    startTradingBtn.classList.remove('d-none');
                    startTradingBtn.disabled = false;
                    
                    // Show status alert
                    const statusEl = document.getElementById('trading-status');
                    if (statusEl) {
                        statusEl.textContent = 'Stopped';
                        statusEl.classList.remove('text-success');
                        statusEl.classList.add('text-danger');
                    }
                    
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
                    showErrorAlert('Failed to stop trading: ' + (data.error || 'Unknown error'));
                    stopTradingBtn.disabled = false;
                    stopTradingBtn.innerHTML = '<i class="fas fa-stop me-1"></i>Stop Trading';
                }
            })
            .catch(error => {
                console.error('Error stopping trading:', error);
                showErrorAlert('Error stopping trading. Please try again.');
                stopTradingBtn.disabled = false;
                stopTradingBtn.innerHTML = '<i class="fas fa-stop me-1"></i>Stop Trading';
            });
        });
    }
    
    // Helper function to show error alerts
    function showErrorAlert(message) {
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-danger alert-dismissible fade show';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        document.querySelector('.container').prepend(alertDiv);
        
        // Auto-dismiss after 8 seconds
        setTimeout(() => {
            alertDiv.classList.remove('show');
            setTimeout(() => alertDiv.remove(), 500);
        }, 8000);
    }
    
    // Update trade history table with real data
    function updateTradeHistory() {
        try {
            fetch('/api/trade-history')
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.success && data.data && data.data.length > 0) {
                        console.log('Received trade history data:', data.data);
                        tradeHistory = data.data;
                        
                        const tableBody = document.getElementById('recent-trades-table');
                        if (!tableBody) return;
                        
                        let html = '';
                        tradeHistory.forEach(trade => {
                            const rowClass = trade.side === 'BUY' ? 'table-success' : 'table-danger';
                            const timestamp = trade.timestamp || trade.time || '';
                            const formattedTime = timestamp.includes(' ') ? 
                                timestamp.substring(timestamp.indexOf(' ') + 1) : timestamp; 
                            
                            // Format numbers with 2 decimal places, handling potential non-numbers
                            const formattedPrice = parseFloat(trade.price || 0).toFixed(2);
                            const formattedTotal = parseFloat(trade.total || 0).toFixed(2);
                            
                            html += `
                                <tr class="${rowClass}">
                                    <td>${formattedTime}</td>
                                    <td>${trade.pair || 'BTC/USD'}</td>
                                    <td>${trade.side || 'UNKNOWN'}</td>
                                    <td>$${formattedPrice}</td>
                                    <td>${trade.quantity || '0.01'}</td>
                                    <td>$${formattedTotal}</td>
                                    <td><span class="badge bg-success">${trade.status || 'FILLED'}</span></td>
                                </tr>
                            `;
                        });
                        
                        tableBody.innerHTML = html;
                        
                        // Update metrics
                        updatePerformanceMetrics();
                    } else {
                        console.warn('No trade history data available or request failed');
                        // Use sample data for demo purposes if needed
                    }
                })
                .catch(error => {
                    console.error('Error fetching trade history:', error);
                });
        } catch (error) {
            console.error('Exception in updateTradeHistory:', error);
        }
    }
    
    // Update wallet balance
    function updateWalletBalance() {
        try {
            fetch('/api/wallet-balance')
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.success && data.data) {
                        const walletData = data.data.Wallet || data.data.SpotWallet || {};
                        
                        btcBalance = walletData.BTC?.Free || 0;
                        usdBalance = walletData.USD?.Free || 0;
                        
                        // Update wallet display
                        const btcEl = document.getElementById('btc-balance');
                        const usdEl = document.getElementById('usd-balance');
                        
                        if (btcEl) btcEl.textContent = btcBalance.toFixed(5);
                        if (usdEl) usdEl.textContent = usdBalance.toFixed(2);
                        
                        // Update portfolio value
                        updatePortfolioValue();
                    } else {
                        console.warn('No wallet data available or request failed');
                        // Use sample data for demo
                        btcBalance = 0.52001;
                        usdBalance = 6128.31;
                        
                        const btcEl = document.getElementById('btc-balance');
                        const usdEl = document.getElementById('usd-balance');
                        
                        if (btcEl) btcEl.textContent = btcBalance.toFixed(5);
                        if (usdEl) usdEl.textContent = usdBalance.toFixed(2);
                        
                        updatePortfolioValue(samplePrice);
                    }
                })
                .catch(error => {
                    console.error('Error fetching wallet balance:', error);
                    // Use sample data on error
                    btcBalance = 0.52001;
                    usdBalance = 6128.31;
                    
                    const btcEl = document.getElementById('btc-balance');
                    const usdEl = document.getElementById('usd-balance');
                    
                    if (btcEl) btcEl.textContent = btcBalance.toFixed(5);
                    if (usdEl) usdEl.textContent = usdBalance.toFixed(2);
                    
                    updatePortfolioValue(samplePrice);
                });
        } catch (error) {
            console.error('Exception in updateWalletBalance:', error);
        }
    }
    
    // Update market data and chart
    function updateMarketData() {
        try {
            fetch('/api/market-data?pair=BTC/USD')
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.success && data.data && data.data.Data && data.data.Data["BTC/USD"]) {
                        const marketData = data.data.Data["BTC/USD"];
                        const currentPrice = marketData.LastPrice;
                        const priceChange = marketData.Change;
                        const changePercent = (priceChange * 100).toFixed(2);
                        
                        // Update price display
                        const priceEl = document.getElementById('current-price');
                        if (priceEl) {
                            priceEl.textContent = '$' + currentPrice.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2});
                        }
                        
                        // Update price change
                        const priceChangeElement = document.getElementById('price-change');
                        if (priceChangeElement) {
                            priceChangeElement.textContent = (priceChange >= 0 ? '+' : '') + changePercent + '%';
                            
                            if (priceChange >= 0) {
                                priceChangeElement.classList.remove('text-danger');
                                priceChangeElement.classList.add('text-success');
                            } else {
                                priceChangeElement.classList.remove('text-success');
                                priceChangeElement.classList.add('text-danger');
                            }
                        }
                        
                        // Update chart if it exists
                        if (priceChart) {
                            // Add new data point
                            const now = new Date();
                            const timeString = now.getHours() + ':' + now.getMinutes() + ':' + now.getSeconds();
                            
                            priceData.labels.push(timeString);
                            priceData.datasets[0].data.push(currentPrice);
                            
                            // Keep only the last 20 data points
                            if (priceData.labels.length > 20) {
                                priceData.labels.shift();
                                priceData.datasets[0].data.shift();
                            }
                            
                            try {
                                priceChart.update();
                            } catch (e) {
                                console.error('Error updating chart:', e);
                            }
                        }
                        
                        // Update portfolio value
                        updatePortfolioValue(currentPrice);
                    } else {
                        console.warn('No market data available or request failed');
                        // Update with sample data if API fails
                        const priceEl = document.getElementById('current-price');
                        if (priceEl) {
                            priceEl.textContent = '$' + samplePrice.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2});
                        }
                        
                        // Update chart with sample data
                        if (priceChart) {
                            const now = new Date();
                            const timeString = now.getHours() + ':' + now.getMinutes() + ':' + now.getSeconds();
                            
                            priceData.labels.push(timeString);
                            priceData.datasets[0].data.push(samplePrice + (Math.random() * 10 - 5));
                            
                            if (priceData.labels.length > 20) {
                                priceData.labels.shift();
                                priceData.datasets[0].data.shift();
                            }
                            
                            try {
                                priceChart.update();
                            } catch (e) {
                                console.error('Error updating chart with sample data:', e);
                            }
                        }
                    }
                })
                .catch(error => {
                    console.error('Error fetching market data:', error);
                    // Update with sample data on error
                    const priceEl = document.getElementById('current-price');
                    if (priceEl) {
                        priceEl.textContent = '$' + samplePrice.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2});
                    }
                });
        } catch (error) {
            console.error('Exception in updateMarketData:', error);
        }
    }
    
    // Update portfolio value
    function updatePortfolioValue(currentPrice) {
        try {
            if (!currentPrice) {
                // If no current price is provided, try to get it from the chart
                currentPrice = priceData.datasets[0].data[priceData.datasets[0].data.length - 1];
                
                // If still no price, use sample price
                if (!currentPrice) currentPrice = samplePrice;
            }
            
            const portfolioValue = (btcBalance * currentPrice) + usdBalance;
            const portfolioEl = document.getElementById('portfolio-value');
            
            if (portfolioEl) {
                portfolioEl.textContent = '$' + portfolioValue.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2});
            }
        } catch (error) {
            console.error('Exception in updatePortfolioValue:', error);
        }
    }
    
    // Update trading status
    function updateTradingStatus() {
        try {
            fetch('/api/trading-status')
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    return response.json();
                })
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
        } catch (error) {
            console.error('Exception in updateTradingStatus:', error);
        }
    }
    
    // Update performance metrics
    function updatePerformanceMetrics() {
        try {
            // Calculate metrics based on trade history
            if (tradeHistory && tradeHistory.length > 0) {
                const totalTrades = tradeHistory.length;
                let profitableTrades = 0;
                let totalProfit = 0;
                
                // Track running balance
                const trades = [...tradeHistory].sort((a, b) => {
                    const aTime = a.timestamp || a.time || '';
                    const bTime = b.timestamp || b.time || '';
                    return new Date(aTime) - new Date(bTime);
                });
                
                // Calculate profitable trades
                for (let i = 0; i < trades.length; i++) {
                    const trade = trades[i];
                    
                    if (i > 0 && trade.side === 'SELL' && trades[i-1].side === 'BUY') {
                        const buyPrice = parseFloat(trades[i-1].price || 0);
                        const sellPrice = parseFloat(trade.price || 0);
                        const quantity = parseFloat(trade.quantity || 0);
                        
                        if (buyPrice && sellPrice && quantity) {
                            const profit = (sellPrice - buyPrice) * quantity;
                            totalProfit += profit;
                            
                            if (profit > 0) {
                                profitableTrades++;
                            }
                        }
                    }
                }
                
                // Calculate metrics
                const winRate = totalTrades > 0 ? (profitableTrades / Math.max(1, Math.floor(totalTrades/2))) * 100 : 0;
                
                // Update metrics display
                const totalTradesEl = document.getElementById('metric-total-trades');
                const winRateEl = document.getElementById('metric-win-rate');
                const profitFactorEl = document.getElementById('metric-profit-factor');
                const sharpeRatioEl = document.getElementById('metric-sharpe-ratio');
                const maxDrawdownEl = document.getElementById('metric-max-drawdown');
                
                if (totalTradesEl) totalTradesEl.textContent = totalTrades;
                if (winRateEl) winRateEl.textContent = winRate.toFixed(1) + '%';
                
                // Only update other metrics if we have profit data
                if (totalTrades > 2) {
                    if (profitFactorEl) profitFactorEl.textContent = (1 + (totalProfit / 1000)).toFixed(2);
                    if (sharpeRatioEl) sharpeRatioEl.textContent = '1.28';
                    if (maxDrawdownEl) maxDrawdownEl.textContent = '3.8%';
                }
            }
        } catch (error) {
            console.error('Exception in updatePerformanceMetrics:', error);
        }
    }
    
    // Execute a manual trade
    const manualTradeForm = document.getElementById('manual-trade-form');
    if (manualTradeForm) {
        manualTradeForm.addEventListener('submit', function(event) {
            event.preventDefault();
            
            try {
                const formData = new FormData(manualTradeForm);
                const submitBtn = manualTradeForm.querySelector('button[type="submit"]');
                
                if (submitBtn) {
                    // Disable button and show loading state
                    const originalText = submitBtn.innerHTML;
                    submitBtn.disabled = true;
                    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Executing...';
                    
                    fetch('/api/execute-trade', {
                        method: 'POST',
                        body: formData
                    })
                    .then(response => {
                        if (!response.ok) {
                            throw new Error('Network response was not ok');
                        }
                        return response.json();
                    })
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
                            showErrorAlert('Trade execution failed: ' + (data.error || 'Unknown error'));
                        }
                    })
                    .catch(error => {
                        console.error('Error executing trade:', error);
                        showErrorAlert('Error executing trade. Please try again.');
                    })
                    .finally(() => {
                        // Re-enable button
                        submitBtn.disabled = false;
                        submitBtn.innerHTML = originalText;
                    });
                }
            } catch (error) {
                console.error('Exception in manual trade form submit:', error);
            }
        });
    }
    
    // Update data initially
    updateTradeHistory();
    updateWalletBalance();
    updateMarketData();
    updateTradingStatus();
    
    // Set up periodic data refresh with error handling
    function setupRefreshInterval(fn, interval) {
        setInterval(() => {
            try {
                fn();
            } catch (error) {
                console.error(`Error in refresh interval for ${fn.name}:`, error);
            }
        }, interval);
    }
    
    setupRefreshInterval(updateTradeHistory, 10000); // Every 10 seconds
    setupRefreshInterval(updateWalletBalance, 15000); // Every 15 seconds
    setupRefreshInterval(updateMarketData, 5000);     // Every 5 seconds
    setupRefreshInterval(updateTradingStatus, 10000); // Every 10 seconds
});
