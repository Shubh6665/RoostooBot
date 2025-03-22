import pandas as pd
import numpy as np
import yfinance as yf
import logging
from datetime import datetime, timedelta
import ta
from config import SMA_PERIODS, RSI_PERIOD

logger = logging.getLogger(__name__)

def fetch_historical_data(symbol="BTC-USD", period="1mo", interval="5m"):
    """Fetch historical price data from Yahoo Finance"""
    try:
        data = yf.download(symbol, period=period, interval=interval)
        data.columns = [col.lower() for col in data.columns]  # Convert column names to lowercase
        data = data.reset_index()
        data.rename(columns={"date": "timestamp"}, inplace=True)
        logger.info(f"Successfully fetched {len(data)} rows of historical data for {symbol}")
        return data
    except Exception as e:
        logger.error(f"Error fetching historical data: {str(e)}")
        return pd.DataFrame()

def preprocess_data(data):
    """Preprocess and calculate technical indicators for the data"""
    if data.empty:
        logger.error("Cannot preprocess empty data")
        return data
    
    try:
        # Calculate returns
        data['returns'] = data['close'].pct_change()
        
        # Calculate Simple Moving Averages
        for period in SMA_PERIODS:
            data[f'sma_{period}'] = ta.trend.sma_indicator(data['close'], window=period)
        
        # Calculate Relative Strength Index
        data['rsi'] = ta.momentum.rsi(data['close'], window=RSI_PERIOD)
        
        # Calculate MACD
        macd = ta.trend.macd(data['close'], window_slow=26, window_fast=12, window_sign=9)
        data['macd'] = macd
        data['macd_signal'] = ta.trend.macd_signal(data['close'], window_slow=26, window_fast=12, window_sign=9)
        data['macd_diff'] = ta.trend.macd_diff(data['close'], window_slow=26, window_fast=12, window_sign=9)
        
        # Calculate Bollinger Bands
        bollinger = ta.volatility.BollingerBands(data['close'], window=20, window_dev=2)
        data['bollinger_mavg'] = bollinger.bollinger_mavg()
        data['bollinger_hband'] = bollinger.bollinger_hband()
        data['bollinger_lband'] = bollinger.bollinger_lband()
        
        # Calculate Average True Range
        data['atr'] = ta.volatility.average_true_range(data['high'], data['low'], data['close'], window=14)
        
        # Fill NaN values
        data.fillna(0, inplace=True)
        
        logger.info(f"Preprocessed data with {len(data.columns)} features")
        return data
    except Exception as e:
        logger.error(f"Error preprocessing data: {str(e)}")
        return data

def normalize_data(data):
    """Normalize the data for ML model input"""
    if data.empty:
        logger.error("Cannot normalize empty data")
        return data
    
    try:
        # Copy the dataframe to avoid modifying the original
        normalized_data = data.copy()
        
        # Columns to normalize
        numeric_columns = ['open', 'high', 'low', 'close', 'volume', 'returns']
        
        # Normalize price and volume data
        for col in numeric_columns:
            if col in normalized_data.columns:
                # Check for non-zero values to avoid division by zero
                if normalized_data[col].max() > 0:
                    normalized_data[col] = normalized_data[col] / normalized_data[col].max()
        
        logger.info("Data normalized successfully")
        return normalized_data
    except Exception as e:
        logger.error(f"Error normalizing data: {str(e)}")
        return data

def calculate_sharpe_ratio(returns, risk_free_rate=0.001):
    """Calculate Sharpe ratio from returns"""
    if len(returns) == 0:
        return 0
    
    try:
        # Convert to numpy array if it's a pandas Series
        if isinstance(returns, pd.Series):
            returns = returns.values
        
        # Calculate annualized Sharpe ratio
        # For 5-minute data, multiply by sqrt(252*24*12) to annualize
        excess_returns = returns - risk_free_rate / (252 * 24 * 12)
        sharpe_ratio = np.mean(excess_returns) / (np.std(excess_returns) + 1e-10) * np.sqrt(252 * 24 * 12)
        
        return sharpe_ratio
    except Exception as e:
        logger.error(f"Error calculating Sharpe ratio: {str(e)}")
        return 0

def split_data_train_test(data, test_size=0.2):
    """Split data into training and testing sets"""
    if data.empty:
        logger.error("Cannot split empty data")
        return None, None
    
    try:
        # Calculate the split index
        split_idx = int(len(data) * (1 - test_size))
        
        # Split the data
        train_data = data.iloc[:split_idx].copy()
        test_data = data.iloc[split_idx:].copy()
        
        logger.info(f"Split data into training set ({len(train_data)} rows) and testing set ({len(test_data)} rows)")
        return train_data, test_data
    except Exception as e:
        logger.error(f"Error splitting data: {str(e)}")
        return None, None

def log_trade(side, price, quantity, balance, crypto_owned):
    """Log a trade with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"[{timestamp}] {side} {quantity:.8f} BTC at ${price:.2f} - Balance: ${balance:.2f}, BTC: {crypto_owned:.8f}")
