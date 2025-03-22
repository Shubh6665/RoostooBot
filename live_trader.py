import logging
import time
import numpy as np
from stable_baselines3 import PPO
from utils import log_trade
from config import TRADE_INTERVAL, MAX_POSITION_SIZE, RISK_PERCENTAGE

logger = logging.getLogger(__name__)

class LiveTrader:
    """Class to handle live trading using the trained RL model"""
    
    def __init__(self, api_client, trading_env, model_path="ppo_trading_bot"):
        self.api_client = api_client
        self.trading_env = trading_env
        self.model_path = model_path
        self.last_trade_time = 0
        self.risk_percentage = RISK_PERCENTAGE
        self.max_position_size = MAX_POSITION_SIZE
        
        # Load the model
        try:
            self.model = PPO.load(model_path)
            logger.info(f"Loaded model from {model_path}")
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            self.model = None
            
        # Initialize environment state
        self.obs = self.trading_env.reset()
        logger.info("Initialized live trader")
    
    def _calculate_position_size(self, price):
        """Calculate appropriate position size based on portfolio and risk management"""
        try:
            # Fetch current balance
            balance_data = self.api_client.get_balance()
            
            # Get USD and BTC balances
            if "Wallet" in balance_data:
                usd_balance = balance_data["Wallet"].get("USD", {}).get("Free", 0)
                btc_balance = balance_data["Wallet"].get("BTC", {}).get("Free", 0)
            elif "SpotWallet" in balance_data:
                usd_balance = balance_data["SpotWallet"].get("USD", {}).get("Free", 0)
                btc_balance = balance_data["SpotWallet"].get("BTC", {}).get("Free", 0)
            else:
                logger.error(f"Unexpected balance data format: {balance_data}")
                return 0.01  # Default to minimum
            
            logger.info(f"Current balance - USD: {usd_balance}, BTC: {btc_balance}")
            
            # Calculate risk amount (e.g., 2% of USD balance)
            risk_amount = (self.risk_percentage / 100) * usd_balance
            
            # Calculate quantity based on risk amount and current price
            position_size = risk_amount / price
            
            # Ensure position size is within bounds
            position_size = min(position_size, self.max_position_size)
            position_size = max(position_size, 0.01)  # Minimum of 0.01 BTC
            
            logger.info(f"Calculated position size: {position_size:.8f} BTC (value: ${position_size * price:.2f}, {(position_size * price / usd_balance * 100):.2f}% of portfolio)")
            
            return position_size
        except Exception as e:
            logger.error(f"Error calculating position size: {str(e)}")
            return 0.01  # Default to minimum
    
    def execute_trading_step(self):
        """Execute one step of the trading strategy"""
        if self.model is None:
            logger.error("Model not loaded, cannot execute trading step")
            return False
        
        current_time = time.time()
        
        # Check if enough time has passed since last trade
        if current_time - self.last_trade_time < TRADE_INTERVAL:
            # Not enough time has passed, skip this step
            return False
        
        try:
            # Get market data
            ticker_data = self.api_client.get_ticker("BTC/USD")
            if "error" in ticker_data:
                logger.error(f"Error fetching ticker data: {ticker_data['error']}")
                return False
            
            # Extract current price
            current_price = ticker_data["Data"]["BTC/USD"]["LastPrice"]
            
            # Update the environment with the current price
            self.trading_env.current_price = current_price
            
            # Get current observation from the environment
            self.obs = self.trading_env._get_observation()
            
            # Predict the action using the model
            action, _states = self.model.predict(self.obs, deterministic=True)
            
            # Execute the action in the environment to update internal state
            self.obs, reward, done, info = self.trading_env.step(action)
            
            # Get balance info
            balance_data = self.api_client.get_balance()
            if "error" in balance_data:
                logger.error(f"Error fetching balance: {balance_data['error']}")
                return False
            
            # Get current wallet balances
            if "Wallet" in balance_data:
                usd_balance = balance_data["Wallet"].get("USD", {}).get("Free", 0)
                btc_balance = balance_data["Wallet"].get("BTC", {}).get("Free", 0)
            elif "SpotWallet" in balance_data:
                usd_balance = balance_data["SpotWallet"].get("USD", {}).get("Free", 0)
                btc_balance = balance_data["SpotWallet"].get("BTC", {}).get("Free", 0)
            else:
                logger.error(f"Unexpected balance data format: {balance_data}")
                return False
            
            # Convert action to trading decision
            if action == 1:  # BUY
                if usd_balance >= current_price * 0.01:  # Ensure enough balance for min order
                    # Calculate position size based on risk management
                    position_size = self._calculate_position_size(current_price)
                    
                    # Execute the trade on the exchange
                    trade_result = self.api_client.place_order("BTC/USD", "BUY", position_size)
                    
                    if trade_result.get("Success", False):
                        log_trade("BUY", current_price, position_size, usd_balance, btc_balance)
                        self.last_trade_time = current_time
                    else:
                        logger.error(f"Error executing BUY trade: {trade_result.get('ErrMsg', 'Unknown error')}")
                else:
                    logger.warning(f"Insufficient USD balance ({usd_balance}) for BUY at {current_price}")
            
            elif action == 2:  # SELL
                if btc_balance >= 0.01:  # Ensure we have BTC to sell
                    # Execute the trade on the exchange (sell all BTC)
                    trade_result = self.api_client.place_order("BTC/USD", "SELL", btc_balance)
                    
                    if trade_result.get("Success", False):
                        log_trade("SELL", current_price, btc_balance, usd_balance, btc_balance)
                        self.last_trade_time = current_time
                    else:
                        logger.error(f"Error executing SELL trade: {trade_result.get('ErrMsg', 'Unknown error')}")
                else:
                    logger.warning(f"Insufficient BTC balance ({btc_balance}) for SELL")
            
            else:  # HOLD
                logger.info(f"HOLD position at price {current_price}")
            
            return True
        
        except Exception as e:
            logger.error(f"Error in execute_trading_step: {str(e)}")
            return False
