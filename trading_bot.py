import os
import numpy as np
import pandas as pd
import yfinance as yf
import time
from datetime import datetime, timedelta
import logging
from stable_baselines3 import PPO
import ta

from trading_env import TradingEnv
from api_client import RoostooClient
from data_processor import preprocess_data, fetch_historical_data

logger = logging.getLogger(__name__)

class TradingBot:
    """
    Trading bot that uses a trained PPO model to make trading decisions.
    """
    def __init__(self, api_client, trading_pair="BTC/USD", risk_level=0.02):
        self.api_client = api_client
        self.trading_pair = trading_pair
        self.risk_level = risk_level
        self.coin = trading_pair.split('/')[0]
        self.base = trading_pair.split('/')[1]
        
        # Model parameters
        self.model = None
        self.env = None
        self.window_size = 20
        
        # Trading state
        self.last_action = 0  # 0: HOLD, 1: BUY, 2: SELL
        self.position = 0  # 0: no position, 1: long position
        self.last_observation = None
        
        # Initialize by loading or training a model
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the trading model by loading or training a new one"""
        model_path = f"ppo_trading_{self.coin.lower()}"
        
        # Try to load a pre-trained model
        if os.path.exists(f"{model_path}.zip"):
            logger.info(f"Loading pre-trained model from {model_path}.zip")
            try:
                self.model = PPO.load(model_path)
                logger.info("Model loaded successfully")
            except Exception as e:
                logger.error(f"Error loading model: {str(e)}")
                self._train_new_model(model_path)
        else:
            logger.info("No pre-trained model found, training a new one")
            self._train_new_model(model_path)
    
    def _train_new_model(self, model_path):
        """Train a new PPO model on historical data"""
        logger.info("Fetching historical data for training...")
        
        try:
            # Fetch and preprocess historical data
            symbol = f"{self.coin}-USD"  # Format for yfinance
            historical_data = fetch_historical_data(symbol, period="1y", interval="1d")
            
            if historical_data is None or len(historical_data) < 100:
                logger.error("Not enough historical data for training")
                raise ValueError("Insufficient historical data")
            
            preprocessed_data = preprocess_data(historical_data)
            
            # Create and configure the trading environment
            self.env = TradingEnv(
                data=preprocessed_data,
                initial_balance=10000,
                window_size=self.window_size
            )
            
            # Configure and create the PPO model
            self.model = PPO(
                "MlpPolicy",
                self.env,
                learning_rate=3e-4,
                gamma=0.99,
                verbose=1
            )
            
            # Train the model
            logger.info("Training model...")
            self.model.learn(total_timesteps=100000)
            
            # Save the trained model
            self.model.save(model_path)
            logger.info(f"Model trained and saved as {model_path}.zip")
            
        except Exception as e:
            logger.error(f"Error in model training: {str(e)}")
            # Create a basic model anyway for minimal functionality
            self.env = TradingEnv(
                data=pd.DataFrame({
                    'open': [1.0] * 100,
                    'high': [1.0] * 100,
                    'low': [1.0] * 100,
                    'close': [1.0] * 100,
                    'volume': [1.0] * 100
                }),
                initial_balance=10000,
                window_size=self.window_size
            )
            self.model = PPO("MlpPolicy", self.env, verbose=0)
    
    def _prepare_observation(self, market_data):
        """Prepare the observation vector from market data"""
        try:
            # Extract price data
            current_price = market_data.get("LastPrice", 0)
            price_history = self._get_price_history()
            
            if len(price_history) < self.window_size:
                logger.warning(f"Not enough price history data. Needed: {self.window_size}, Got: {len(price_history)}")
                # Pad with current price if we don't have enough history
                padding = [current_price] * (self.window_size - len(price_history))
                price_history = padding + price_history
            
            # Get wallet balance
            balance_data = self.api_client.get_balance()
            if not balance_data.get("Success", False):
                logger.error(f"Failed to get balance: {balance_data.get('ErrMsg', 'Unknown error')}")
                return None
                
            wallet = balance_data.get("Wallet", {})
            base_balance = wallet.get(self.base, {}).get("Free", 0)
            coin_balance = wallet.get(self.coin, {}).get("Free", 0)
            
            # Create observation as expected by the model
            df = pd.DataFrame({
                'open': price_history,
                'high': price_history,
                'low': price_history,
                'close': price_history,
                'volume': [1.0] * len(price_history)  # Placeholder volume
            })
            
            # Process the data to add technical indicators
            df = self._add_indicators(df)
            
            # Normalize OHLCV data
            price_scale = df['close'].iloc[-1]
            normalized_prices = df[['open', 'high', 'low', 'close', 'volume']].values / price_scale
            
            # Extract technical indicators
            tech_indicators = df[['sma', 'rsi', 'macd', 'bollinger_high', 'bollinger_low']].values / price_scale
            
            # Account state features
            initial_balance = 10000  # Placeholder value consistent with training
            portfolio_value = base_balance + coin_balance * current_price
            
            account_state = np.array([
                base_balance / initial_balance,  # Normalized cash balance
                coin_balance * current_price / initial_balance,  # Normalized crypto value
                portfolio_value / initial_balance  # Normalized portfolio value
            ])
            
            # Combine all features into one observation vector
            obs = np.concatenate([
                normalized_prices.flatten(),
                tech_indicators.flatten(),
                account_state
            ])
            
            return obs.astype(np.float32)
            
        except Exception as e:
            logger.error(f"Error preparing observation: {str(e)}")
            return None
    
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
    
    def _get_price_history(self):
        """Get price history for the window size period"""
        # In a real implementation, you would fetch this from the API or a data provider
        # For simplicity, we'll use a placeholder
        return [100.0] * self.window_size
    
    def execute_trading_cycle(self):
        """Execute one cycle of trading logic"""
        try:
            # 1. Fetch current market data
            market_data = self.api_client.get_ticker(self.trading_pair)
            if not market_data.get("Success", False):
                logger.error(f"Failed to get ticker: {market_data.get('ErrMsg', 'Unknown error')}")
                return "HOLD", 0, 0, 0
            
            ticker_data = market_data.get("Data", {}).get(self.trading_pair, {})
            current_price = ticker_data.get("LastPrice", 0)
            
            # 2. Prepare observation for the model
            observation = self._prepare_observation(ticker_data)
            if observation is None:
                logger.error("Failed to prepare observation")
                return "HOLD", current_price, 0, 0
            
            # 3. Get model prediction
            self.last_observation = observation
            action, _states = self.model.predict(observation, deterministic=True)
            
            # 4. Get current wallet balance
            balance_data = self.api_client.get_balance()
            if not balance_data.get("Success", False):
                logger.error(f"Failed to get balance: {balance_data.get('ErrMsg', 'Unknown error')}")
                return "HOLD", current_price, 0, 0
                
            wallet = balance_data.get("Wallet", {})
            base_balance = wallet.get(self.base, {}).get("Free", 0)
            coin_balance = wallet.get(self.coin, {}).get("Free", 0)
            
            # 5. Calculate portfolio value
            portfolio_value = base_balance + coin_balance * current_price
            
            # 6. Execute trade based on action with risk management
            if action == 1 and base_balance > 0:  # BUY
                # Calculate position size based on risk level
                risk_amount = portfolio_value * self.risk_level
                position_size = risk_amount / current_price
                
                # Ensure we don't exceed available balance
                max_buyable = base_balance / current_price
                quantity = min(position_size, max_buyable)
                
                if quantity * current_price >= 1.0:  # Minimum order value check
                    logger.info(f"Placing BUY order for {quantity} {self.coin} at {current_price}")
                    order_result = self.api_client.place_order(
                        self.trading_pair, "BUY", quantity
                    )
                    
                    if order_result.get("Success", False):
                        logger.info(f"BUY order executed: {order_result}")
                        self.position = 1
                        self.last_action = 1
                        return "BUY", current_price, quantity, portfolio_value
                    else:
                        logger.error(f"BUY order failed: {order_result.get('ErrMsg', 'Unknown error')}")
                else:
                    logger.info(f"BUY signal received but order too small: {quantity * current_price} {self.base}")
            
            elif action == 2 and coin_balance > 0:  # SELL
                # Calculate sell quantity
                quantity = coin_balance  # Sell all
                
                if quantity * current_price >= 1.0:  # Minimum order value check
                    logger.info(f"Placing SELL order for {quantity} {self.coin} at {current_price}")
                    order_result = self.api_client.place_order(
                        self.trading_pair, "SELL", quantity
                    )
                    
                    if order_result.get("Success", False):
                        logger.info(f"SELL order executed: {order_result}")
                        self.position = 0
                        self.last_action = 2
                        return "SELL", current_price, quantity, portfolio_value
                    else:
                        logger.error(f"SELL order failed: {order_result.get('ErrMsg', 'Unknown error')}")
                else:
                    logger.info(f"SELL signal received but order too small: {quantity * current_price} {self.base}")
            
            # No trade execution
            self.last_action = 0
            return "HOLD", current_price, 0, portfolio_value
            
        except Exception as e:
            logger.error(f"Error in trading cycle: {str(e)}")
            return "HOLD", 0, 0, 0
