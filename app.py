import os
import logging
from flask import Flask, render_template, request, jsonify, flash, session
import threading
import time
from datetime import datetime
from config import API_KEY, SECRET_KEY, BASE_URL
from api_client import RoostooClient

# Set up logging
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default_secret_key_for_dev")

# Initialize API client
api_client = RoostooClient(API_KEY, SECRET_KEY, BASE_URL)

# Trading environment variables
is_trading_active = False
trader_thread = None
trade_history = []

def start_trading_thread():
    """Function to run trading in background thread"""
    global is_trading_active
    try:
        while is_trading_active:
            # Execute trading logic
            execute_trading_step()
            time.sleep(300)  # 5-minute interval between trading decisions
    except Exception as e:
        logger.error(f"Error in trading thread: {str(e)}")
        is_trading_active = False

def execute_trading_step():
    """Execute a trading step based on market conditions"""
    try:
        # Get current market data
        market_data = api_client.get_ticker("BTC/USD")
        
        if not market_data.get("Success", False):
            logger.error(f"Failed to get market data: {market_data.get('ErrMsg', 'Unknown error')}")
            return
        
        # Get current wallet balance
        balance_data = api_client.get_balance()
        
        if not balance_data.get("Success", False):
            logger.error(f"Failed to get wallet balance: {balance_data.get('ErrMsg', 'Unknown error')}")
            return
        
        # Extract price and balance information
        price_data = market_data["Data"]["BTC/USD"]
        current_price = price_data["LastPrice"]
        
        # Wallet data could be in different formats depending on API version
        wallet_data = balance_data.get("Wallet", balance_data.get("SpotWallet", {}))
        btc_balance = wallet_data.get("BTC", {}).get("Free", 0)
        usd_balance = wallet_data.get("USD", {}).get("Free", 0)
        
        # Simple trading strategy based on price movement
        # This is just a placeholder - replace with your actual trading logic
        price_change = price_data.get("Change", 0)
        
        if price_change > 0.01 and usd_balance > current_price * 0.01:  # Uptrend, BUY
            quantity = 0.01  # Fixed quantity for demonstration
            result = api_client.place_order("BTC/USD", "BUY", quantity)
            
            if result.get("Success", False):
                logger.info(f"Executed BUY: {quantity} BTC at ${current_price:.2f}")
                
                # Record trade in history
                order_detail = result.get("OrderDetail", {})
                trade_history.append({
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "pair": order_detail.get("Pair", "BTC/USD"),
                    "side": "BUY",
                    "price": current_price,
                    "quantity": quantity,
                    "total": quantity * current_price,
                    "status": order_detail.get("Status", "FILLED")
                })
            else:
                logger.error(f"Failed to execute BUY: {result.get('ErrMsg', 'Unknown error')}")
                
        elif price_change < -0.01 and btc_balance >= 0.01:  # Downtrend, SELL
            quantity = 0.01  # Fixed quantity for demonstration
            result = api_client.place_order("BTC/USD", "SELL", quantity)
            
            if result.get("Success", False):
                logger.info(f"Executed SELL: {quantity} BTC at ${current_price:.2f}")
                
                # Record trade in history
                order_detail = result.get("OrderDetail", {})
                trade_history.append({
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "pair": order_detail.get("Pair", "BTC/USD"),
                    "side": "SELL",
                    "price": current_price,
                    "quantity": quantity,
                    "total": quantity * current_price,
                    "status": order_detail.get("Status", "FILLED")
                })
            else:
                logger.error(f"Failed to execute SELL: {result.get('ErrMsg', 'Unknown error')}")

    except Exception as e:
        logger.error(f"Error executing trading step: {str(e)}")

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
        market_data = api_client.get_ticker(pair)
        return jsonify({"success": True, "data": market_data})
    except Exception as e:
        logger.error(f"Error fetching market data: {str(e)}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/wallet-balance')
def get_wallet_balance():
    """API endpoint to fetch wallet balance"""
    try:
        balance = api_client.get_balance()
        return jsonify({"success": True, "data": balance})
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
    try:
        pair = request.form.get('pair', 'BTC/USD')
        side = request.form.get('side', 'BUY')
        quantity = float(request.form.get('quantity', 0.01))
        
        # Execute the trade using the API client
        result = api_client.place_order(pair, side, quantity)
        
        if result.get("Success", False):
            # Record the trade in history
            order_detail = result.get("OrderDetail", {})
            trade_history.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "pair": order_detail.get("Pair", pair),
                "side": side,
                "price": order_detail.get("Price", 0),
                "quantity": quantity,
                "total": quantity * order_detail.get("Price", 0),
                "status": order_detail.get("Status", "FILLED")
            })
            
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
        "environment_ready": True,
        "trader_ready": True
    })

@app.route('/api/trade-history')
def get_trade_history():
    """API endpoint to get trade history"""
    global trade_history
    
    try:
        # If we don't have any recorded trades yet, try to fetch from the API
        if not trade_history:
            # Query recent orders
            orders = api_client.query_order(pair="BTC/USD")
            
            if orders.get("Success", False) and "OrderList" in orders:
                for order in orders["OrderList"]:
                    if order.get("Status") in ["FILLED", "PARTIALLY_FILLED"]:
                        trade_history.append({
                            "timestamp": datetime.fromtimestamp(order.get("CreateTimestamp", 0)/1000).strftime("%Y-%m-%d %H:%M:%S"),
                            "pair": order.get("Pair", "BTC/USD"),
                            "side": order.get("Side", "BUY"),
                            "price": order.get("FilledAverPrice", 0),
                            "quantity": order.get("FilledQuantity", 0),
                            "total": order.get("FilledQuantity", 0) * order.get("FilledAverPrice", 0),
                            "status": order.get("Status", "FILLED")
                        })
        
        return jsonify({"success": True, "data": trade_history})
    except Exception as e:
        logger.error(f"Error fetching trade history: {str(e)}")
        return jsonify({"success": False, "error": str(e)})

@app.errorhandler(404)
def page_not_found(e):
    return render_template('index.html'), 404

@app.errorhandler(500)
def server_error(e):
    logger.error(f"Server error: {str(e)}")
    return render_template('index.html'), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
