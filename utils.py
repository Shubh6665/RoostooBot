import numpy as np
import pandas as pd
from datetime import datetime
import time
import logging

logger = logging.getLogger(__name__)

def calculate_sharpe_ratio(returns, risk_free_rate=0.001):
    """
    Calculate the Sharpe ratio of a returns series.
    
    Args:
        returns (numpy.array): Array of returns
        risk_free_rate (float): Risk-free rate (0.1% by default)
    
    Returns:
        float: Sharpe ratio
    """
    if len(returns) < 2:
        return 0
    
    # Calculate excess returns
    excess_returns = returns - risk_free_rate
    
    # Calculate Sharpe ratio
    if np.std(excess_returns) == 0:
        return 0
    
    sharpe = np.mean(excess_returns) / np.std(excess_returns)
    
    # Annualize if returns are not already annualized
    # Assuming returns are daily and there are 252 trading days in a year
    sharpe_annualized = sharpe * np.sqrt(252)
    
    return sharpe_annualized

def calculate_returns(portfolio_values):
    """
    Calculate returns from a series of portfolio values.
    
    Args:
        portfolio_values (list): List of portfolio values over time
    
    Returns:
        numpy.array: Array of returns
    """
    if len(portfolio_values) < 2:
        return np.array([])
    
    values = np.array(portfolio_values)
    returns = np.diff(values) / values[:-1]
    
    return returns

def timestamp_to_datetime(timestamp_ms):
    """
    Convert millisecond timestamp to datetime.
    
    Args:
        timestamp_ms (int): Timestamp in milliseconds
    
    Returns:
        datetime: Datetime object
    """
    return datetime.fromtimestamp(timestamp_ms / 1000.0)

def format_price(price, precision=2):
    """
    Format price with appropriate precision.
    
    Args:
        price (float): Price to format
        precision (int): Decimal precision
    
    Returns:
        str: Formatted price
    """
    return f"{price:.{precision}f}"

def calculate_position_size(portfolio_value, risk_percentage, current_price, stop_loss_percentage=0.02):
    """
    Calculate position size based on risk management principles.
    
    Args:
        portfolio_value (float): Total portfolio value
        risk_percentage (float): Percentage of portfolio to risk (e.g., 0.01 for 1%)
        current_price (float): Current asset price
        stop_loss_percentage (float): Stop loss percentage
    
    Returns:
        float: Position size in units
    """
    risk_amount = portfolio_value * risk_percentage
    stop_loss_amount = current_price * stop_loss_percentage
    
    if stop_loss_amount == 0:
        return 0
    
    position_size = risk_amount / stop_loss_amount
    
    return position_size

def calculate_portfolio_metrics(initial_value, current_value, transactions):
    """
    Calculate portfolio performance metrics.
    
    Args:
        initial_value (float): Initial portfolio value
        current_value (float): Current portfolio value
        transactions (list): List of transaction dictionaries
    
    Returns:
        dict: Performance metrics
    """
    total_return = (current_value / initial_value) - 1
    
    # Calculate returns
    returns = []
    values = [initial_value]
    
    for tx in sorted(transactions, key=lambda x: x['timestamp']):
        if 'portfolio_value' in tx:
            values.append(tx['portfolio_value'])
    
    if len(values) > 1:
        values = np.array(values)
        returns = np.diff(values) / values[:-1]
    
    # Calculate metrics
    metrics = {
        'total_return': total_return,
        'total_return_pct': total_return * 100,
        'num_trades': len(transactions)
    }
    
    if len(returns) > 1:
        metrics['sharpe_ratio'] = calculate_sharpe_ratio(returns)
        metrics['volatility'] = np.std(returns) * 100
    else:
        metrics['sharpe_ratio'] = 0
        metrics['volatility'] = 0
    
    return metrics
