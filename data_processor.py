import pandas as pd
import numpy as np
import yfinance as yf
import logging
import time
from datetime import datetime, timedelta
import ta

logger = logging.getLogger(__name__)

def fetch_historical_data(symbol, period="1y", interval="1d"):
    """
    Fetch historical price data using yfinance.
    
    Args:
        symbol (str): Symbol to fetch data for (e.g., "BTC-USD")
        period (str): Time period to fetch (e.g., "1y" for 1 year)
        interval (str): Data interval (e.g., "1d" for daily)
    
    Returns:
        pd.DataFrame: DataFrame with historical price data
    """
    try:
        logger.info(f"Fetching historical data for {symbol} ({period}, {interval})")
        
        # Retry mechanism for robustness
        max_retries = 3
        for attempt in range(max_retries):
            try:
                data = yf.download(symbol, period=period, interval=interval)
                
                if data is not None and len(data) > 0:
                    logger.info(f"Successfully fetched {len(data)} data points")
                    return data
                
                logger.warning(f"No data returned (attempt {attempt+1}/{max_retries})")
                time.sleep(2)  # Wait before retrying
                
            except Exception as e:
                logger.error(f"Error in attempt {attempt+1}/{max_retries}: {str(e)}")
                time.sleep(2)  # Wait before retrying
        
        logger.error(f"Failed to fetch data after {max_retries} attempts")
        return None
        
    except Exception as e:
        logger.error(f"Error fetching historical data: {str(e)}")
        return None

def preprocess_data(data):
    """
    Preprocess historical price data for the trading environment.
    
    Args:
        data (pd.DataFrame): Raw historical price data
    
    Returns:
        pd.DataFrame: Preprocessed data ready for the trading environment
    """
    try:
        if data is None or len(data) == 0:
            logger.error("No data to preprocess")
            return None
        
        # Create a copy to avoid modifying the original data
        df = data.copy()
        
        # Rename columns to lowercase for consistency
        df.columns = [col.lower() for col in df.columns]
        
        # If 'adj close' exists, use it as 'close'
        if 'adj close' in df.columns:
            df['close'] = df['adj close']
            df.drop('adj close', axis=1, inplace=True)
        
        # Ensure we have all required columns
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in required_columns:
            if col not in df.columns:
                logger.error(f"Missing required column: {col}")
                return None
        
        # Reset index if it's a DatetimeIndex to have date as a column
        if isinstance(df.index, pd.DatetimeIndex):
            df.reset_index(inplace=True)
            df.rename(columns={'index': 'date'}, inplace=True)
        
        # Calculate returns
        df['returns'] = df['close'].pct_change()
        
        # Add technical indicators
        # Momentum
        df['rsi'] = ta.momentum.rsi(df['close'], window=14)
        
        # Trend
        df['sma'] = ta.trend.sma_indicator(df['close'], window=20)
        df['ema'] = ta.trend.ema_indicator(df['close'], window=20)
        
        macd = ta.trend.MACD(df['close'])
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()
        df['macd_diff'] = macd.macd_diff()
        
        # Volatility
        bollinger = ta.volatility.BollingerBands(df['close'])
        df['bollinger_high'] = bollinger.bollinger_hband()
        df['bollinger_low'] = bollinger.bollinger_lband()
        
        # Volume
        df['volume_sma'] = ta.volume.sma_volume(df['volume'], window=20)
        
        # Fill NaN values
        df.fillna(0, inplace=True)
        
        # Normalize data
        # This is done in the environment itself, so we just return the preprocessed data
        
        logger.info(f"Preprocessed data shape: {df.shape}")
        return df
        
    except Exception as e:
        logger.error(f"Error preprocessing data: {str(e)}")
        return None

def update_live_data(df, new_data_point):
    """
    Update the dataset with a new data point for live trading.
    
    Args:
        df (pd.DataFrame): Existing dataset
        new_data_point (dict): New data point to add
    
    Returns:
        pd.DataFrame: Updated dataset
    """
    try:
        # Create a new row
        new_row = pd.DataFrame([new_data_point])
        
        # Append to existing data and recalculate indicators
        updated_df = pd.concat([df, new_row], ignore_index=True)
        
        # Reprocess to update all indicators
        return preprocess_data(updated_df)
        
    except Exception as e:
        logger.error(f"Error updating live data: {str(e)}")
        return df  # Return original on error
