import os
import logging
from flask import Flask, render_template, request, jsonify, flash, session
import threading
import time
import random
import json
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default_secret_key_for_dev")

# Mock API configuration
API_KEY = os.getenv('API_KEY', 'sample_api_key')
SECRET_KEY = os.getenv('SECRET_KEY', 'sample_secret_key')
BASE_URL = os.getenv('BASE_URL', 'https://mock-api.roostoo.com')

# Mock trading environment and trader
is_trading_active = False
trader_thread = None

# Mock data for demonstration
mock_btc_price = 68452.75
mock_wallet = {
    "Success": True,
    "SpotWallet": {
        "BTC": {
            "Free": 0.15,
            "Lock": 0.0
        },
        "USD": {
            "Free": 25000.0,
            "Lock": 0.0
        }
    }
}

# Mock trading record
trade_history = []

def start_trading_thread():
    """Function to run trading in background thread"""
    global is_trading_active
    try:
        while is_trading_active:
            # Simulate a trading decision
            execute_mock_trading_step()
            time.sleep(10)  # Shorter interval for demo purposes
    except Exception as e:
        logger.error(f"Error in trading thread: {str(e)}")
        is_trading_active = False

def execute_mock_trading_step():
    """Execute a mock trading step with random decisions"""
    global mock_btc_price, mock_wallet, trade_history
    
    # Simulate price movement
    price_change = random.uniform(-500, 500)
    mock_btc_price += price_change
    
    # Random trading decision
    action = random.choice([0, 0, 0, 1, 2])  # 0: HOLD, 1: BUY, 2: SELL - weighted toward HOLD
    
    if action == 1:  # BUY
        if mock_wallet["SpotWallet"]["USD"]["Free"] > mock_btc_price * 0.01:
            quantity = 0.01
            cost = quantity * mock_btc_price
            mock_wallet["SpotWallet"]["USD"]["Free"] -= cost
            mock_wallet["SpotWallet"]["BTC"]["Free"] += quantity
            
            # Record the trade
            trade_history.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "side": "BUY",
                "price": mock_btc_price,
                "quantity": quantity,
                "total": cost,
                "status": "FILLED"
            })
            logger.info(f"[MOCK] Executed BUY: {quantity} BTC at ${mock_btc_price:.2f}")
            
    elif action == 2:  # SELL
        if mock_wallet["SpotWallet"]["BTC"]["Free"] >= 0.01:
            quantity = 0.01
            proceeds = quantity * mock_btc_price
            mock_wallet["SpotWallet"]["USD"]["Free"] += proceeds
            mock_wallet["SpotWallet"]["BTC"]["Free"] -= quantity
            
            # Record the trade
            trade_history.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "side": "SELL",
                "price": mock_btc_price,
                "quantity": quantity,
                "total": proceeds,
                "status": "FILLED"
            })
            logger.info(f"[MOCK] Executed SELL: {quantity} BTC at ${mock_btc_price:.2f}")

@app.route('/')
def index():
    """Main landing page"""
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    """Trading dashboard page"""
    return render_template('dashboard.html')

@app.route('/settings')
def settings():
    """Bot settings page"""
    return render_template('settings.html')

@app.route('/api/market-data')
def get_market_data():
    """API endpoint to fetch market data"""
    try:
        pair = request.args.get('pair', 'BTC/USD')
        
        # Mock market data
        market_data = {
            "Success": True,
            "ServerTime": int(time.time() * 1000),
            "Data": {
                "BTC/USD": {
                    "MaxBid": mock_btc_price - 10,
                    "MinAsk": mock_btc_price + 10,
                    "LastPrice": mock_btc_price,
                    "Change": 0.0132,
                    "CoinTradeValue": 4320.15,
                    "UnitTradeValue": 295843215.67
                }
            }
        }
        
        return jsonify({"success": True, "data": market_data})
    except Exception as e:
        logger.error(f"Error fetching market data: {str(e)}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/wallet-balance')
def get_wallet_balance():
    """API endpoint to fetch wallet balance"""
    try:
        return jsonify({"success": True, "data": mock_wallet})
    except Exception as e:
        logger.error(f"Error fetching wallet balance: {str(e)}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/start-trading', methods=['POST'])
def start_trading():
    """API endpoint to start automated trading"""
    global trader_thread, is_trading_active
    
    try:
        # Start trading thread if not already running
        if not is_trading_active:
            is_trading_active = True
            trader_thread = threading.Thread(target=start_trading_thread)
            trader_thread.daemon = True
            trader_thread.start()
            flash('Trading bot started successfully!', 'success')
            return jsonify({"success": True, "message": "Trading bot started"})
        else:
            return jsonify({"success": False, "error": "Trading bot is already running"})
            
    except Exception as e:
        logger.error(f"Error starting trading bot: {str(e)}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/stop-trading', methods=['POST'])
def stop_trading():
    """API endpoint to stop automated trading"""
    global is_trading_active
    
    try:
        is_trading_active = False
        flash('Trading bot stopped successfully!', 'success')
        return jsonify({"success": True, "message": "Trading bot stopped"})
    except Exception as e:
        logger.error(f"Error stopping trading bot: {str(e)}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/execute-trade', methods=['POST'])
def execute_manual_trade():
    """API endpoint to execute a manual trade"""
    global mock_wallet, mock_btc_price, trade_history
    
    try:
        pair = request.form.get('pair', 'BTC/USD')
        side = request.form.get('side', 'BUY')
        quantity = float(request.form.get('quantity', 0.01))
        
        # Execute mock trade
        if side == "BUY":
            cost = quantity * mock_btc_price
            if mock_wallet["SpotWallet"]["USD"]["Free"] >= cost:
                mock_wallet["SpotWallet"]["USD"]["Free"] -= cost
                mock_wallet["SpotWallet"]["BTC"]["Free"] += quantity
                
                # Record the trade
                trade_history.append({
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "side": "BUY",
                    "price": mock_btc_price,
                    "quantity": quantity,
                    "total": cost,
                    "status": "FILLED"
                })
                
                result = {
                    "Success": True,
                    "OrderDetail": {
                        "Pair": pair,
                        "OrderID": random.randint(1000, 9999),
                        "Status": "FILLED",
                        "Side": side,
                        "Type": "MARKET",
                        "Price": mock_btc_price,
                        "Quantity": quantity,
                        "FilledQuantity": quantity
                    }
                }
            else:
                result = {
                    "Success": False,
                    "ErrMsg": "Insufficient USD balance"
                }
        else:  # SELL
            if mock_wallet["SpotWallet"]["BTC"]["Free"] >= quantity:
                proceeds = quantity * mock_btc_price
                mock_wallet["SpotWallet"]["USD"]["Free"] += proceeds
                mock_wallet["SpotWallet"]["BTC"]["Free"] -= quantity
                
                # Record the trade
                trade_history.append({
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "side": "SELL",
                    "price": mock_btc_price,
                    "quantity": quantity,
                    "total": proceeds,
                    "status": "FILLED"
                })
                
                result = {
                    "Success": True,
                    "OrderDetail": {
                        "Pair": pair,
                        "OrderID": random.randint(1000, 9999),
                        "Status": "FILLED",
                        "Side": side,
                        "Type": "MARKET",
                        "Price": mock_btc_price,
                        "Quantity": quantity,
                        "FilledQuantity": quantity
                    }
                }
            else:
                result = {
                    "Success": False,
                    "ErrMsg": "Insufficient BTC balance"
                }
        
        if result.get("Success", False):
            flash(f'Trade executed successfully: {side} {quantity} {pair}', 'success')
            return jsonify({"success": True, "data": result})
        else:
            error_msg = result.get("ErrMsg", "Unknown error")
            flash(f'Error executing trade: {error_msg}', 'danger')
            return jsonify({"success": False, "error": error_msg})
            
    except Exception as e:
        logger.error(f"Error executing trade: {str(e)}")
        flash(f'Error executing trade: {str(e)}', 'danger')
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/trading-status')
def trading_status():
    """API endpoint to get trading bot status"""
    global is_trading_active
    
    return jsonify({
        "is_active": is_trading_active,
        "environment_ready": True,  # Mock values
        "trader_ready": True
    })

@app.route('/api/trade-history')
def get_trade_history():
    """API endpoint to get trade history"""
    global trade_history
    return jsonify({"success": True, "data": trade_history})

@app.errorhandler(404)
def page_not_found(e):
    return render_template('index.html'), 404

@app.errorhandler(500)
def server_error(e):
    logger.error(f"Server error: {str(e)}")
    return render_template('index.html'), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
