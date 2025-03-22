import os
import logging
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
import threading
import time
from datetime import datetime, timedelta
import json

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "crypto_trading_bot_secret")

# Configure SQLite database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///crypto_trading.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize the app with the extension
db.init_app(app)

# Bot state variables
bot_running = False
bot_thread = None
bot_status = "stopped"
last_trade = None
performance_metrics = {
    "initial_balance": 10000,
    "current_balance": 10000,
    "profit_loss": 0,
    "win_rate": 0,
    "trades_executed": 0,
    "successful_trades": 0
}

# Import trading bot components after app initialization
from trading_bot import TradingBot
from api_client import RoostooClient

# Initialize API client with keys from environment variables
api_key = os.environ.get("API_KEY", "e9WneuGa4mnfivi96myjEeCF34R9DZZ7W1e3hGX7Dd5tfqXotyMpmV3ICoZ7V1KF")
secret_key = os.environ.get("SECRET_KEY", "VfIywmdqBDCNa1XSY3qdqrWDrcFhvHVIdvo2vmi8fY3JPUjEbrIn9gtDX2WOk7d5")
api_client = RoostooClient(api_key, secret_key)

# Initialize trading bot
trading_bot = None

def bot_worker():
    """Background thread function for running the trading bot"""
    global bot_status, performance_metrics, last_trade, bot_running
    
    logger.info("Starting trading bot thread")
    
    try:
        # Get initial balance to track performance
        balance_data = api_client.get_balance()
        if balance_data.get("Success", False):
            wallet = balance_data.get("Wallet", {})
            usd_balance = wallet.get("USD", {}).get("Free", 10000)
            performance_metrics["initial_balance"] = usd_balance
            performance_metrics["current_balance"] = usd_balance
        
        bot_status = "running"
        
        while bot_running:
            try:
                # Execute trading logic
                action, price, quantity, balance = trading_bot.execute_trading_cycle()
                
                # Update performance metrics
                if action in ["BUY", "SELL"]:
                    performance_metrics["trades_executed"] += 1
                    last_trade = {
                        "action": action,
                        "price": price,
                        "quantity": quantity,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                
                # Update current balance
                performance_metrics["current_balance"] = balance
                performance_metrics["profit_loss"] = balance - performance_metrics["initial_balance"]
                
                if performance_metrics["trades_executed"] > 0:
                    performance_metrics["win_rate"] = (performance_metrics["successful_trades"] / 
                                                     performance_metrics["trades_executed"]) * 100
                
                # Wait for next cycle
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in trading cycle: {str(e)}")
                time.sleep(30)  # Wait on error before retrying
    
    except Exception as e:
        logger.error(f"Bot thread terminated with error: {str(e)}")
    
    finally:
        bot_status = "stopped"
        bot_running = False
        logger.info("Trading bot thread stopped")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html', 
                           bot_status=bot_status,
                           metrics=performance_metrics,
                           last_trade=last_trade)

@app.route('/settings')
def settings():
    return render_template('settings.html')

@app.route('/api/start_bot', methods=['POST'])
def start_bot():
    global bot_running, bot_thread, trading_bot
    
    if not bot_running:
        # Get settings from the request
        data = request.json
        trading_pair = data.get('trading_pair', 'BTC/USD')
        risk_level = float(data.get('risk_level', 0.02))  # Default 2% risk
        
        # Initialize trading bot with settings
        from trading_env import TradingEnv
        trading_bot = TradingBot(api_client, trading_pair, risk_level)
        
        # Start bot in a separate thread
        bot_running = True
        bot_thread = threading.Thread(target=bot_worker)
        bot_thread.daemon = True
        bot_thread.start()
        
        return jsonify({"status": "success", "message": "Trading bot started"})
    else:
        return jsonify({"status": "error", "message": "Bot is already running"})

@app.route('/api/stop_bot', methods=['POST'])
def stop_bot():
    global bot_running
    
    if bot_running:
        bot_running = False
        # Wait for the thread to finish (with timeout)
        if bot_thread:
            bot_thread.join(timeout=5.0)
        
        return jsonify({"status": "success", "message": "Trading bot stopped"})
    else:
        return jsonify({"status": "error", "message": "Bot is not running"})

@app.route('/api/bot_status', methods=['GET'])
def get_bot_status():
    return jsonify({
        "status": bot_status,
        "metrics": performance_metrics,
        "last_trade": last_trade
    })

@app.route('/api/market_data', methods=['GET'])
def get_market_data():
    trading_pair = request.args.get('pair', 'BTC/USD')
    
    try:
        ticker_data = api_client.get_ticker(trading_pair)
        if ticker_data.get("Success", False):
            return jsonify({
                "status": "success",
                "data": ticker_data.get("Data", {}).get(trading_pair, {})
            })
        else:
            return jsonify({
                "status": "error",
                "message": ticker_data.get("ErrMsg", "Failed to fetch market data")
            })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        })

@app.route('/api/wallet_balance', methods=['GET'])
def get_wallet_balance():
    try:
        balance_data = api_client.get_balance()
        if balance_data.get("Success", False):
            return jsonify({
                "status": "success",
                "data": balance_data.get("Wallet", {})
            })
        else:
            return jsonify({
                "status": "error",
                "message": balance_data.get("ErrMsg", "Failed to fetch wallet balance")
            })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        })

# Make sure to import the models here for table creation
with app.app_context():
    import models
    db.create_all()
