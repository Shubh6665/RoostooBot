import os

# API Configuration
API_KEY = os.getenv('API_KEY', 'e9WneuGa4mnfivi96myjEeCF34R9DZZ7W1e3hGX7Dd5tfqXotyMpmV3ICoZ7V1KF')
SECRET_KEY = os.getenv('SECRET_KEY', 'VfIywmdqBDCNa1XSY3qdqrWDrcFhvHVIdvo2vmi8fY3JPUjEbrIn9gtDX2WOk7d5')
BASE_URL = os.getenv('BASE_URL', 'https://mock-api.roostoo.com')

# Trading Configuration
DEFAULT_TRADING_PAIR = 'BTC/USD'
DEFAULT_QUANTITY = 0.01  # Default trade size in BTC
MAX_POSITION_SIZE = 0.1  # Maximum position size in BTC
RISK_PERCENTAGE = 2.0    # Risk as % of portfolio
TRADE_INTERVAL = 300     # 5 minutes between trades in seconds

# RL Model Configuration
WINDOW_SIZE = 12         # Number of time periods to look back for state construction
INITIAL_BALANCE = 10000  # Initial balance for training environment
REWARD_SCALING = 100.0   # Scale rewards to help training
MODEL_PATH = 'ppo_trading_bot'  # Path to save/load the trained model

# Technical Indicators
SMA_PERIODS = [5, 20]    # Simple Moving Average periods
RSI_PERIOD = 14          # Relative Strength Index period

# Database Configuration
SQLALCHEMY_DATABASE_URI = 'sqlite:///trading_bot.db'
SQLALCHEMY_TRACK_MODIFICATIONS = False
