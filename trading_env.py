import gym
from gym import spaces
import numpy as np
import pandas as pd
import ta  # For technical indicators

class TradingEnv(gym.Env):
    """
    Trading environment for reinforcement learning.
    Simulates a cryptocurrency trading environment where an agent can buy, sell, or hold.
    """
    def __init__(self, data, initial_balance=10000, window_size=20, transaction_fee=0.001):
        super(TradingEnv, self).__init__()
        
        # Store the price data and reset index for easier access
        self.data = data.reset_index(drop=True)
        
        # Initialize account parameters
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.crypto_owned = 0
        self.portfolio_value = initial_balance
        
        # Environment parameters
        self.window_size = window_size  # Look-back period for observations
        self.current_step = window_size  # Start after the window size to have a complete observation
        self.transaction_fee = transaction_fee  # Fee per transaction as a fraction (0.1% = 0.001)
        
        # Trading history for tracking performance
        self.trades = []
        self.portfolio_values = []
        
        # Define action space: 0 = HOLD, 1 = BUY, 2 = SELL
        self.action_space = spaces.Discrete(3)
        
        # Define observation space: price data, technical indicators, account state
        # We'll use 5 base features (OHLCV) + 5 technical indicators + 3 account state features
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(window_size + 13,), dtype=np.float32
        )
    
    def reset(self):
        """Reset the environment to initial state"""
        self.balance = self.initial_balance
        self.crypto_owned = 0
        self.portfolio_value = self.initial_balance
        self.current_step = self.window_size
        self.trades = []
        self.portfolio_values = []
        
        return self._get_observation()
    
    def _get_observation(self):
        """
        Construct the observation from current market data and account state.
        Includes price data, technical indicators, and account information.
        """
        # Get data frame for the current window
        frame = self.data.iloc[self.current_step - self.window_size:self.current_step].copy()
        
        # Calculate technical indicators
        frame = self._add_indicators(frame)
        
        # Get the normalized price history (past window_size OHLCV candles)
        # Use the last row's values for normalization to prevent look-ahead bias
        price_scale = frame['close'].iloc[-1]
        
        # Normalize OHLCV data
        normalized_prices = frame[['open', 'high', 'low', 'close', 'volume']].values / price_scale
        
        # Extract technical indicators
        tech_indicators = frame[['sma', 'rsi', 'macd', 'bollinger_high', 'bollinger_low']].values / price_scale
        
        # Account state features
        account_state = np.array([
            self.balance / self.initial_balance,  # Normalized cash balance
            self.crypto_owned * frame['close'].iloc[-1] / self.initial_balance,  # Normalized crypto value
            self.portfolio_value / self.initial_balance  # Normalized portfolio value
        ])
        
        # Combine all features into one observation vector
        obs = np.concatenate([
            normalized_prices.flatten(),
            tech_indicators.flatten(),
            account_state
        ])
        
        return obs.astype(np.float32)
    
    def _add_indicators(self, frame):
        """Add technical indicators to the data frame"""
        # Simple Moving Average
        frame['sma'] = ta.trend.sma_indicator(frame['close'], window=5)
        
        # Relative Strength Index
        frame['rsi'] = ta.momentum.rsi(frame['close'], window=14)
        
        # MACD
        macd = ta.trend.MACD(frame['close'])
        frame['macd'] = macd.macd()
        
        # Bollinger Bands
        bollinger = ta.volatility.BollingerBands(frame['close'])
        frame['bollinger_high'] = bollinger.bollinger_hband()
        frame['bollinger_low'] = bollinger.bollinger_lband()
        
        # Fill NaN values that may be caused by the indicators' calculation
        frame = frame.fillna(0)
        
        return frame
    
    def step(self, action):
        """
        Execute one action in the environment and return the next state, reward, done, and info
        """
        # Get current price and other info
        current_price = self.data.iloc[self.current_step]['close']
        prev_portfolio_value = self.portfolio_value
        
        # Execute the action (0: HOLD, 1: BUY, 2: SELL)
        if action == 1 and self.balance > 0:  # BUY
            # Calculate the max amount of crypto we can buy with our balance
            max_buyable = self.balance / (current_price * (1 + self.transaction_fee))
            
            # Buy all available
            self.crypto_owned += max_buyable
            self.balance = 0  # All cash used for purchase
            
            # Record the trade
            self.trades.append({
                'step': self.current_step,
                'price': current_price,
                'type': 'buy',
                'amount': max_buyable
            })
            
        elif action == 2 and self.crypto_owned > 0:  # SELL
            # Calculate the value we get from selling all crypto
            sell_value = self.crypto_owned * current_price * (1 - self.transaction_fee)
            
            # Sell all
            self.balance += sell_value
            self.crypto_owned = 0
            
            # Record the trade
            self.trades.append({
                'step': self.current_step,
                'price': current_price,
                'type': 'sell',
                'amount': self.crypto_owned
            })
        
        # Move to the next time step
        self.current_step += 1
        
        # Calculate portfolio value (cash + crypto)
        self.portfolio_value = self.balance + self.crypto_owned * current_price
        self.portfolio_values.append(self.portfolio_value)
        
        # Calculate reward as the change in portfolio value
        reward = self.portfolio_value - prev_portfolio_value
        
        # Check if episode is done (reached the end of data)
        done = self.current_step >= len(self.data) - 1
        
        # Get the new observation
        obs = self._get_observation()
        
        # Additional info
        info = {
            'portfolio_value': self.portfolio_value,
            'balance': self.balance,
            'crypto_owned': self.crypto_owned,
            'current_price': current_price
        }
        
        return obs, reward, done, info
    
    def render(self, mode='human'):
        """Render the environment state"""
        print(f"Step: {self.current_step}, "
              f"Portfolio Value: ${self.portfolio_value:.2f}, "
              f"Balance: ${self.balance:.2f}, "
              f"Crypto: {self.crypto_owned:.6f}, "
              f"Price: ${self.data.iloc[self.current_step]['close']:.2f}")
    
    def get_portfolio_stats(self):
        """Calculate portfolio statistics at the end of the episode"""
        # Calculate daily returns
        portfolio_values = np.array(self.portfolio_values)
        daily_returns = np.diff(portfolio_values) / portfolio_values[:-1]
        
        # Calculate stats
        total_return = (self.portfolio_value / self.initial_balance) - 1
        sharpe_ratio = 0
        if len(daily_returns) > 1:
            sharpe_ratio = np.mean(daily_returns) / np.std(daily_returns) if np.std(daily_returns) > 0 else 0
            
        stats = {
            'total_return': total_return,
            'sharpe_ratio': sharpe_ratio,
            'num_trades': len(self.trades),
            'final_portfolio_value': self.portfolio_value
        }
        
        return stats
