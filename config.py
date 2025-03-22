import os

# Roostoo API configuration
API_KEY = os.getenv('API_KEY', 'e9WneuGa4mnfivi96myjEeCF34R9DZZ7W1e3hGX7Dd5tfqXotyMpmV3ICoZ7V1KF')
SECRET_KEY = os.getenv('SECRET_KEY', 'VfIywmdqBDCNa1XSY3qdqrWDrcFhvHVIdvo2vmi8fY3JPUjEbrIn9gtDX2WOk7d5')
BASE_URL = os.getenv('BASE_URL', 'https://mock-api.roostoo.com')

# Trading parameters
INITIAL_BALANCE = 10000.0  # Initial balance for backtest
WINDOW_SIZE = 12  # Number of time periods to consider for state

# Model parameters
MODEL_PATH = "ppo_trading_bot"