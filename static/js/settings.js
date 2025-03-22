// Settings JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize form event listeners
    const settingsForm = document.getElementById('settings-form');
    settingsForm.addEventListener('submit', saveSettings);
    
    // Risk level slider
    const riskSlider = document.getElementById('risk-level');
    const riskValue = document.getElementById('risk-value');
    riskSlider.addEventListener('input', function() {
        riskValue.textContent = `${this.value}%`;
    });
    
    // Stop loss slider
    const stopLossSlider = document.getElementById('stop-loss');
    const stopLossValue = document.getElementById('stop-loss-value');
    stopLossSlider.addEventListener('input', function() {
        stopLossValue.textContent = `${this.value}%`;
    });
    
    // Training steps slider
    const stepsSlider = document.getElementById('training-steps');
    const stepsValue = document.getElementById('steps-value');
    stepsSlider.addEventListener('input', function() {
        const steps = getTrainingSteps(this.value);
        stepsValue.textContent = formatNumber(steps);
    });
    
    // Training frequency dropdown
    const frequencySelect = document.getElementById('trading-frequency');
    const frequencyValue = document.getElementById('frequency-value');
    frequencySelect.addEventListener('change', function() {
        const minutes = parseInt(this.value);
        frequencyValue.textContent = formatFrequency(minutes);
    });
    
    // Train model button
    const trainButton = document.getElementById('train-model-btn');
    trainButton.addEventListener('click', trainModel);
});

// Save settings
function saveSettings(event) {
    event.preventDefault();
    
    // Get form values
    const tradingPair = document.getElementById('trading-pair').value;
    const riskLevel = parseFloat(document.getElementById('risk-level').value) / 100; // Convert to decimal
    const modelSelection = document.getElementById('model-selection').value;
    
    // Additional settings
    const tradingFrequency = parseInt(document.getElementById('trading-frequency').value);
    const stopLoss = parseFloat(document.getElementById('stop-loss').value) / 100; // Convert to decimal
    const reinvestProfits = document.getElementById('reinvest-profits').checked;
    
    // Create settings object
    const settings = {
        trading_pair: tradingPair,
        risk_level: riskLevel,
        model_selection: modelSelection,
        trading_frequency: tradingFrequency,
        stop_loss: stopLoss,
        reinvest_profits: reinvestProfits
    };
    
    // Save settings
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
            showNotification('Settings saved and bot started', 'success');
            
            // Redirect to dashboard after saving
            setTimeout(() => {
                window.location.href = '/dashboard';
            }, 1500);
        } else {
            showNotification(`Failed to save settings: ${data.message}`, 'danger');
        }
    })
    .catch(error => {
        console.error('Error saving settings:', error);
        showNotification('Error saving settings', 'danger');
    });
}

// Train model
function trainModel() {
    const tradingPair = document.getElementById('trading-pair').value;
    const trainingPeriod = document.getElementById('training-period').value;
    const trainingSteps = getTrainingSteps(document.getElementById('training-steps').value);
    
    // Show progress elements
    const progressContainer = document.getElementById('training-progress-container');
    const progressBar = document.getElementById('training-progress');
    const statusText = document.getElementById('training-status');
    
    progressContainer.classList.remove('d-none');
    statusText.classList.remove('d-none');
    progressBar.style.width = '0%';
    statusText.textContent = 'Preparing training data...';
    
    // Disable train button
    const trainButton = document.getElementById('train-model-btn');
    trainButton.disabled = true;
    
    // Simulate training progress (in a real implementation, this would connect to a websocket or poll an endpoint)
    let progress = 0;
    const interval = setInterval(() => {
        progress += Math.random() * 3;
        if (progress >= 100) {
            progress = 100;
            clearInterval(interval);
            
            // Complete training
            statusText.textContent = 'Training complete! Model saved.';
            showNotification('Model training complete', 'success');
            
            // Re-enable train button
            trainButton.disabled = false;
        } else if (progress >= 70) {
            statusText.textContent = 'Optimizing model parameters...';
        } else if (progress >= 30) {
            statusText.textContent = 'Training in progress...';
        }
        
        progressBar.style.width = `${progress}%`;
        progressBar.setAttribute('aria-valuenow', progress);
    }, 500);
    
    // In a real implementation, this would be an actual API call:
    /*
    fetch('/api/train_model', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            trading_pair: tradingPair,
            period: trainingPeriod,
            steps: trainingSteps
        })
    })
    .then(response => response.json())
    .then(data => {
        // Handle response
    })
    .catch(error => {
        console.error('Error training model:', error);
        clearInterval(interval);
        statusText.textContent = 'Error during training';
        showNotification('Error training model', 'danger');
        trainButton.disabled = false;
    });
    */
}

// Format frequency text
function formatFrequency(minutes) {
    if (minutes === 1) {
        return 'Every minute';
    } else if (minutes === 60) {
        return 'Every hour';
    } else {
        return `Every ${minutes} minutes`;
    }
}

// Get training steps based on slider value
function getTrainingSteps(value) {
    const steps = {
        '1': 10000,
        '2': 50000,
        '3': 100000,
        '4': 250000,
        '5': 500000
    };
    
    return steps[value] || 100000;
}

// Format number with commas
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
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
