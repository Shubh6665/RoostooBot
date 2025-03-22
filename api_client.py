import time
import hmac
import hashlib
import urllib.request
import urllib.parse
import urllib.error
import json
import logging

logger = logging.getLogger(__name__)

class RoostooClient:
    """Client for interacting with the Roostoo mock exchange API"""
    
    def __init__(self, api_key, secret_key, base_url="https://mock-api.roostoo.com"):
        """
        Initialize the Roostoo API client
        
        Args:
            api_key (str): API key for authenticating with the Roostoo API
            secret_key (str): Secret key for signing requests
            base_url (str): Base URL for the API
        """
        self.api_key = api_key
        self.secret_key = secret_key
        self.base_url = base_url
        
    def _generate_signature(self, params):
        """Generate HMAC-SHA256 signature for authentication
        
        Args:
            params (dict): Parameters to be included in the request
            
        Returns:
            str: HMAC-SHA256 signature
        """
        # Convert params to sorted query string
        query_string = '&'.join([f"{key}={params[key]}" for key in sorted(params)])
        
        # Generate HMAC-SHA256 signature
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature
        
    def get_server_time(self):
        """Fetch server time
        
        Returns:
            dict: Server time response
        """
        url = f"{self.base_url}/v3/serverTime"
        
        try:
            with urllib.request.urlopen(url) as response:
                return json.loads(response.read().decode('utf-8'))
        except Exception as e:
            logger.error(f"Error fetching server time: {str(e)}")
            return {"Success": False, "ErrMsg": str(e)}
    
    def get_exchange_info(self):
        """Fetch exchange information
        
        Returns:
            dict: Exchange information response
        """
        url = f"{self.base_url}/v3/exchangeInfo"
        
        try:
            with urllib.request.urlopen(url) as response:
                return json.loads(response.read().decode('utf-8'))
        except Exception as e:
            logger.error(f"Error fetching exchange info: {str(e)}")
            return {"Success": False, "ErrMsg": str(e)}
    
    def get_ticker(self, pair=None):
        """Fetch market ticker data
        
        Args:
            pair (str, optional): Trading pair (e.g., "BTC/USD"). Defaults to None.
            
        Returns:
            dict: Market ticker data
        """
        # Get current timestamp in milliseconds
        timestamp = int(time.time() * 1000)
        
        params = {"timestamp": timestamp}
        if pair:
            params["pair"] = pair
        
        # Build URL with query params
        query_string = urllib.parse.urlencode(params)
        url = f"{self.base_url}/v3/ticker?{query_string}"
        
        try:
            with urllib.request.urlopen(url) as response:
                return json.loads(response.read().decode('utf-8'))
        except Exception as e:
            logger.error(f"Error fetching ticker data: {str(e)}")
            return {"Success": False, "ErrMsg": str(e)}
    
    def get_balance(self):
        """Fetch wallet balance
        
        Returns:
            dict: Wallet balance response
        """
        url = f"{self.base_url}/v3/balance"
        
        # Get current timestamp in milliseconds
        timestamp = int(time.time() * 1000)
        
        params = {"timestamp": timestamp}
        
        # Generate signature
        signature = self._generate_signature(params)
        
        # Set headers
        headers = {
            "RST-API-KEY": self.api_key,
            "MSG-SIGNATURE": signature
        }
        
        try:
            response = requests.get(url, params=params, headers=headers)
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching balance: {str(e)}")
            return {"Success": False, "ErrMsg": str(e)}
    
    def place_order(self, pair="BTC/USD", side="BUY", quantity=0.01, price=None):
        """Place an order on the exchange
        
        Args:
            pair (str, optional): Trading pair. Defaults to "BTC/USD".
            side (str, optional): Order side ("BUY" or "SELL"). Defaults to "BUY".
            quantity (float, optional): Order quantity. Defaults to 0.01.
            price (float, optional): Limit price (required for LIMIT orders). Defaults to None.
            
        Returns:
            dict: Order response
        """
        url = f"{self.base_url}/v3/place_order"
        
        # Get current timestamp in milliseconds
        timestamp = int(time.time() * 1000)
        
        # Build params dict
        params = {
            "pair": pair,
            "side": side,
            "quantity": str(quantity),
            "timestamp": str(timestamp)
        }
        
        # Set order type
        if price:
            params["type"] = "LIMIT"
            params["price"] = str(price)
        else:
            params["type"] = "MARKET"
        
        # Generate signature
        signature = self._generate_signature(params)
        
        # Set headers
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "RST-API-KEY": self.api_key,
            "MSG-SIGNATURE": signature
        }
        
        try:
            response = requests.post(url, data=params, headers=headers)
            return response.json()
        except Exception as e:
            logger.error(f"Error placing order: {str(e)}")
            return {"Success": False, "ErrMsg": str(e)}
    
    def query_order(self, order_id=None, pair=None):
        """Query order status
        
        Args:
            order_id (int, optional): Order ID. Defaults to None.
            pair (str, optional): Trading pair. Defaults to None.
            
        Returns:
            dict: Order status response
        """
        url = f"{self.base_url}/v3/query_order"
        
        # Get current timestamp in milliseconds
        timestamp = int(time.time() * 1000)
        
        # Build params dict
        params = {"timestamp": str(timestamp)}
        
        if order_id:
            params["order_id"] = str(order_id)
        
        if pair:
            params["pair"] = pair
        
        # Generate signature
        signature = self._generate_signature(params)
        
        # Set headers
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "RST-API-KEY": self.api_key,
            "MSG-SIGNATURE": signature
        }
        
        try:
            response = requests.post(url, data=params, headers=headers)
            return response.json()
        except Exception as e:
            logger.error(f"Error querying order: {str(e)}")
            return {"Success": False, "ErrMsg": str(e)}
    
    def cancel_order(self, pair="BTC/USD"):
        """Cancel orders for a trading pair
        
        Args:
            pair (str, optional): Trading pair. Defaults to "BTC/USD".
            
        Returns:
            dict: Cancellation response
        """
        url = f"{self.base_url}/v3/cancel_order"
        
        # Get current timestamp in milliseconds
        timestamp = int(time.time() * 1000)
        
        # Build params dict
        params = {
            "timestamp": str(timestamp),
            "pair": pair
        }
        
        # Generate signature
        signature = self._generate_signature(params)
        
        # Set headers
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "RST-API-KEY": self.api_key,
            "MSG-SIGNATURE": signature
        }
        
        try:
            response = requests.post(url, data=params, headers=headers)
            return response.json()
        except Exception as e:
            logger.error(f"Error cancelling order: {str(e)}")
            return {"Success": False, "ErrMsg": str(e)}
    
    def pending_count(self):
        """Get count of pending orders
        
        Returns:
            dict: Pending order count response
        """
        url = f"{self.base_url}/v3/pending_count"
        
        # Get current timestamp in milliseconds
        timestamp = int(time.time() * 1000)
        
        # Build params dict
        params = {"timestamp": str(timestamp)}
        
        # Generate signature
        signature = self._generate_signature(params)
        
        # Set headers
        headers = {
            "RST-API-KEY": self.api_key,
            "MSG-SIGNATURE": signature
        }
        
        try:
            response = requests.get(url, params=params, headers=headers)
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching pending count: {str(e)}")
            return {"Success": False, "ErrMsg": str(e)}