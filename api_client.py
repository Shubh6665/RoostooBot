import requests
import hmac
import hashlib
import time
import logging
import json

logger = logging.getLogger(__name__)

class RoostooClient:
    """
    Client for interacting with the Roostoo Mock Exchange API.
    """
    def __init__(self, api_key, secret_key, base_url="https://mock-api.roostoo.com"):
        self.api_key = api_key
        self.secret_key = secret_key
        self.base_url = base_url
        logger.info("Initialized Roostoo API client")
    
    def _generate_signature(self, params):
        """Generate HMAC SHA256 signature for API authentication"""
        # Sort parameters by key and create query string
        query_string = '&'.join([f"{k}={params[k]}" for k in sorted(params.keys())])
        
        # Create signature using HMAC SHA256
        signature = hmac.new(
            self.secret_key.encode(),
            query_string.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def get_server_time(self):
        """Get the server time from the Roostoo API"""
        try:
            response = requests.get(f"{self.base_url}/v3/serverTime")
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching server time: {str(e)}")
            return {"Success": False, "ErrMsg": str(e)}
    
    def get_exchange_info(self):
        """Get exchange information including trading pairs and rules"""
        try:
            response = requests.get(f"{self.base_url}/v3/exchangeInfo")
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching exchange info: {str(e)}")
            return {"Success": False, "ErrMsg": str(e)}
    
    def get_ticker(self, pair=None):
        """
        Get market ticker data for a specific trading pair or all pairs.
        
        Args:
            pair (str, optional): Trading pair (e.g., "BTC/USD"). If None, returns all tickers.
        
        Returns:
            dict: Ticker data
        """
        try:
            # Prepare parameters
            params = {"timestamp": int(time.time() * 1000)}
            if pair:
                params["pair"] = pair
            
            # Make the request
            response = requests.get(f"{self.base_url}/v3/ticker", params=params)
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching ticker data: {str(e)}")
            return {"Success": False, "ErrMsg": str(e)}
    
    def get_balance(self):
        """
        Get current wallet balance.
        
        Returns:
            dict: Wallet balance data
        """
        try:
            # Prepare parameters
            params = {"timestamp": int(time.time() * 1000)}
            
            # Generate signature
            signature = self._generate_signature(params)
            
            # Prepare headers
            headers = {
                "RST-API-KEY": self.api_key,
                "MSG-SIGNATURE": signature,
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            # Make the request
            response = requests.get(
                f"{self.base_url}/v3/balance",
                params=params,
                headers=headers
            )
            
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching balance: {str(e)}")
            return {"Success": False, "ErrMsg": str(e)}
    
    def place_order(self, pair, side, quantity, price=None):
        """
        Place a trading order on the exchange.
        
        Args:
            pair (str): Trading pair (e.g., "BTC/USD")
            side (str): Order side ("BUY" or "SELL")
            quantity (float): Order quantity
            price (float, optional): Limit price. If None, places a market order.
        
        Returns:
            dict: Order response data
        """
        try:
            # Prepare parameters
            params = {
                "pair": pair,
                "side": side,
                "quantity": quantity,
                "timestamp": int(time.time() * 1000)
            }
            
            # Set order type
            if price is None:
                params["type"] = "MARKET"
            else:
                params["type"] = "LIMIT"
                params["price"] = price
            
            # Generate signature
            signature = self._generate_signature(params)
            
            # Prepare headers
            headers = {
                "RST-API-KEY": self.api_key,
                "MSG-SIGNATURE": signature,
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            # Make the request
            response = requests.post(
                f"{self.base_url}/v3/place_order",
                data=params,
                headers=headers
            )
            
            return response.json()
        except Exception as e:
            logger.error(f"Error placing order: {str(e)}")
            return {"Success": False, "ErrMsg": str(e)}
    
    def cancel_order(self, pair):
        """
        Cancel orders for a specific trading pair.
        
        Args:
            pair (str): Trading pair (e.g., "BTC/USD")
        
        Returns:
            dict: Cancellation response data
        """
        try:
            # Prepare parameters
            params = {
                "pair": pair,
                "timestamp": int(time.time() * 1000)
            }
            
            # Generate signature
            signature = self._generate_signature(params)
            
            # Prepare headers
            headers = {
                "RST-API-KEY": self.api_key,
                "MSG-SIGNATURE": signature,
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            # Make the request
            response = requests.post(
                f"{self.base_url}/v3/cancel_order",
                data=params,
                headers=headers
            )
            
            return response.json()
        except Exception as e:
            logger.error(f"Error cancelling order: {str(e)}")
            return {"Success": False, "ErrMsg": str(e)}
    
    def query_order(self, order_id=None, pair=None):
        """
        Query orders by ID or pair.
        
        Args:
            order_id (str, optional): Order ID to query
            pair (str, optional): Trading pair to query orders for
        
        Returns:
            dict: Order data
        """
        try:
            # Prepare parameters
            params = {"timestamp": int(time.time() * 1000)}
            
            if order_id:
                params["order_id"] = order_id
            elif pair:
                params["pair"] = pair
            
            # Generate signature
            signature = self._generate_signature(params)
            
            # Prepare headers
            headers = {
                "RST-API-KEY": self.api_key,
                "MSG-SIGNATURE": signature,
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            # Make the request
            response = requests.post(
                f"{self.base_url}/v3/query_order",
                data=params,
                headers=headers
            )
            
            return response.json()
        except Exception as e:
            logger.error(f"Error querying order: {str(e)}")
            return {"Success": False, "ErrMsg": str(e)}
    
    def pending_count(self):
        """
        Get count of pending orders.
        
        Returns:
            dict: Pending order count data
        """
        try:
            # Prepare parameters
            params = {"timestamp": int(time.time() * 1000)}
            
            # Generate signature
            signature = self._generate_signature(params)
            
            # Prepare headers
            headers = {
                "RST-API-KEY": self.api_key,
                "MSG-SIGNATURE": signature,
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            # Make the request
            response = requests.get(
                f"{self.base_url}/v3/pending_count",
                params=params,
                headers=headers
            )
            
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching pending count: {str(e)}")
            return {"Success": False, "ErrMsg": str(e)}
