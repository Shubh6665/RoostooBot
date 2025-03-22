import gym
from gym import spaces
import numpy as np
import pandas as pd
import ta
import logging
import time
from config import WINDOW_SIZE, INITIAL_BALANCE, REWARD_SCALING

logger = logging.getLogger(__name__)

class TradingEnv(gym.Env):
    """Custom Gym environment for crypto trading with RL"""
    
    def __init__(self, api_client=None, data=None, initial_balance=INITIAL_BALANCE, window_size=WINDOW_SIZE, pair='BTC/USD'):
        super(TradingEnv, self).__init__()
        
        self.api_client = api_client  # For live trading
        self.pair = pair
        self.initial_balance = initial_balance
        self.window_size = window_size
        
        # For backtesting/training mode
        self.data = data
        if data is not None:
            self.data = data.reset_index(drop=True)
            self.prices = self.data['close'].values
        else:
            self.prices = None
            
        # Initialize portfolio state
        self.balance = initial_balance
        self.crypto_owned = 0
        self.current_step = window_size
        
        # Define action space: 0 = HOLD, 1 = BUY, 2 = SELL
        self.action_space = spaces.Discrete(3)
        
        # Define observation space (normalized price history, balance, position, technical indicators)
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(window_size + 8,), dtype=np.float32
        )
        
        self.last_action_time = 0
        self.current_price = None
        self.history = []
        
    def reset(self):
        """Reset the environment to the initial state"""
        self.balance = self.initial_balance
        self.crypto_owned = 0
        
        if self.data is not None:
            # For backtesting/training mode
            self.current_step = self.window_size
        else:
            # For live trading, we don't reset the step
            pass
            
        return self._get_observation()
        
    def step(self, action):
        """Execute a step in the environment by applying an action"""
        # Store previous portfolio value
        prev_portfolio_value = self._get_portfolio_value()
        
        # Get current price (either from data or live API)
        if self.data is not None and self.current_step < len(self.data):
            # For backtesting/training mode
            current_price = self.prices[self.current_step]
            self.current_price = current_price
        else:
            # For live trading
            if self.api_client is not None:
                try:
                    ticker_data = self.api_client.get_ticker(self.pair)
                    current_price = ticker_data['Data'][self.pair]['LastPrice']
                    self.current_price = current_price
                except Exception as e:
                    logger.error(f"Error getting current price: {e}")
                    # Return the previous state with negative reward if price fetching fails
                    return self._get_observation(), -1.0, False, {'error': str(e)}
        
        # Execute action (0: HOLD, 1: BUY, 2: SELL)
        if action == 1:  # BUY
            if self.balance >= current_price * 0.01:  # Minimum order size
                # Calculate quantity based on available balance
                qty_to_buy = min(0.01, self.balance / current_price)  # At least 0.01 BTC or what we can afford
                self.crypto_owned += qty_to_buy
                self.balance -= qty_to_buy * current_price
                logger.info(f"BUY {qty_to_buy} at {current_price}")
                
                # Record transaction in history
                self.history.append({
                    'timestamp': time.time(),
                    'action': 'BUY',
                    'price': current_price,
                    'quantity': qty_to_buy,
                    'balance': self.balance,
                    'crypto_owned': self.crypto_owned
                })
                
        elif action == 2:  # SELL
            if self.crypto_owned > 0:
                # Sell all owned crypto
                self.balance += self.crypto_owned * current_price
                
                logger.info(f"SELL {self.crypto_owned} at {current_price}")
                
                # Record transaction in history
                self.history.append({
                    'timestamp': time.time(),
                    'action': 'SELL',
                    'price': current_price,
                    'quantity': self.crypto_owned,
                    'balance': self.balance,
                    'crypto_owned': 0
                })
                
                self.crypto_owned = 0
        
        # Move to next step (for backtesting/training)
        if self.data is not None:
            self.current_step += 1
            done = self.current_step >= len(self.data) - 1
        else:
            # For live trading, we're never "done"
            done = False
            
        # Calculate reward as change in portfolio value
        new_portfolio_value = self._get_portfolio_value()
        reward = (new_portfolio_value - prev_portfolio_value) * REWARD_SCALING
        
        # Get new state
        obs = self._get_observation()
        
        # Additional info
        info = {
            'portfolio_value': new_portfolio_value,
            'balance': self.balance,
            'crypto_owned': self.crypto_owned,
            'current_price': current_price
        }
        
        return obs, reward, done, info
    
    def _get_portfolio_value(self):
        """Calculate total portfolio value"""
        if self.current_price is None:
            return self.balance
        return self.balance + (self.crypto_owned * self.current_price)
    
    def _get_price_history(self):
        """Get price history for observation"""
        if self.data is not None:
            # For backtesting/training mode
            start_idx = max(0, self.current_step - self.window_size)
            end_idx = self.current_step
            return self.data.iloc[start_idx:end_idx]['close'].values
        else:
            # For live trading, we need to fetch historical data from API
            if self.api_client is not None:
                try:
                    # This would need to be implemented in the API client
                    # For now, we'll just use the current price repeated
                    return np.ones(self.window_size) * self.current_price
                except Exception as e:
                    logger.error(f"Error getting price history: {e}")
                    return np.zeros(self.window_size)
            else:
                return np.zeros(self.window_size)
    
    def _get_observation(self):
        """Construct the observation (state) for the agent"""
        if self.data is not None:
            # For backtesting/training mode
            price_history = self._get_price_history()
            
            # Normalize the price history
            if len(price_history) > 0 and price_history.max() > 0:
                price_history = price_history / price_history.max()
            
            # Get technical indicators
            if self.current_step >= self.window_size:
                frame = self.data.iloc[self.current_step - self.window_size:self.current_step].copy()
                frame['sma5'] = ta.trend.sma_indicator(frame['close'], window=5)
                frame['sma20'] = ta.trend.sma_indicator(frame['close'], window=20)
                frame['rsi'] = ta.momentum.rsi(frame['close'], window=14)
                
                # Fill NaN values
                frame = frame.fillna(0)
                
                # Get the latest indicators
                sma5 = frame['sma5'].iloc[-1] / frame['close'].max() if frame['close'].max() > 0 else 0
                sma20 = frame['sma20'].iloc[-1] / frame['close'].max() if frame['close'].max() > 0 else 0
                rsi = frame['rsi'].iloc[-1] / 100.0  # Normalize RSI to [0, 1]
                
                # Calculate MACD
                macd = ta.trend.macd(frame['close'], window_slow=26, window_fast=12, window_sign=9)
                macd_line = macd.iloc[-1] / frame['close'].max() if frame['close'].max() > 0 else 0
                
                # Volume indicators if available
                volume_sma = 0
                if 'volume' in frame.columns:
                    volume_sma = ta.volume.volume_sma_indicator(frame['close'], frame['volume'], window=5)
                    volume_sma = volume_sma.iloc[-1] if not pd.isna(volume_sma.iloc[-1]) else 0
            else:
                sma5, sma20, rsi, macd_line, volume_sma = 0, 0, 0, 0, 0
        else:
            # For live trading without historical data
            # We'd need to implement this to fetch and calculate indicators from API
            price_history = np.zeros(self.window_size)
            sma5, sma20, rsi, macd_line, volume_sma = 0, 0, 0, 0, 0
        
        # Combine all features
        balance_norm = self.balance / self.initial_balance if self.initial_balance > 0 else 0
        crypto_owned_norm = self.crypto_owned
        
        # Create observation vector
        obs = np.concatenate([
            price_history,
            [balance_norm, crypto_owned_norm, sma5, sma20, rsi, macd_line, volume_sma, 
             1 if self.crypto_owned > 0 else 0]  # Binary flag for holding position
        ])
        
        return obs.astype(np.float32)
    
    def render(self, mode='human'):
        """Render the current state of the environment"""
        portfolio_value = self._get_portfolio_value()
        
        print(f"Step: {self.current_step}, "
              f"Price: {self.current_price:.2f}, "
              f"Balance: {self.balance:.2f}, "
              f"Crypto: {self.crypto_owned:.8f}, "
              f"Portfolio: {portfolio_value:.2f}")
        
        return
