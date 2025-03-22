import requests
import time
import hmac
import hashlib
import logging
from config import API_KEY, SECRET_KEY, BASE_URL

logger = logging.getLogger(__name__)

class RoostooClient:
    """Client for interacting with the Roostoo mock exchange API"""
    
    def __init__(self, api_key=API_KEY, secret_key=SECRET_KEY, base_url=BASE_URL):
        self.api_key = api_key
        self.secret_key = secret_key
        self.base_url = base_url
        logger.info(f"Initialized Roostoo API client with base URL: {base_url}")
    
    def _generate_signature(self, params):
        """Generate HMAC-SHA256 signature for authentication"""
        # Sort parameters alphabetically and create query string
        query_string = '&'.join([f"{key}={value}" for key, value in sorted(params.items())])
        
        # Create HMAC-SHA256 signature
        signature = hmac.new(
            self.secret_key.encode(),
            query_string.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def get_server_time(self):
        """Fetch server time"""
        endpoint = f"{self.base_url}/v3/serverTime"
        
        try:
            response = requests.get(endpoint)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Error fetching server time: {response.status_code} - {response.text}")
                return {"error": f"HTTP {response.status_code}: {response.text}"}
        except Exception as e:
            logger.error(f"Exception in get_server_time: {str(e)}")
            return {"error": str(e)}
    
    def get_exchange_info(self):
        """Fetch exchange information"""
        endpoint = f"{self.base_url}/v3/exchangeInfo"
        
        try:
            response = requests.get(endpoint)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Error fetching exchange info: {response.status_code} - {response.text}")
                return {"error": f"HTTP {response.status_code}: {response.text}"}
        except Exception as e:
            logger.error(f"Exception in get_exchange_info: {str(e)}")
            return {"error": str(e)}
    
    def get_ticker(self, pair=None):
        """Fetch market ticker data"""
        endpoint = f"{self.base_url}/v3/ticker"
        timestamp = int(time.time() * 1000)
        
        params = {"timestamp": timestamp}
        if pair:
            params["pair"] = pair
        
        try:
            response = requests.get(endpoint, params=params)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Error fetching ticker: {response.status_code} - {response.text}")
                return {"error": f"HTTP {response.status_code}: {response.text}"}
        except Exception as e:
            logger.error(f"Exception in get_ticker: {str(e)}")
            return {"error": str(e)}
    
    def get_balance(self):
        """Fetch wallet balance"""
        endpoint = f"{self.base_url}/v3/balance"
        timestamp = int(time.time() * 1000)
        
        params = {"timestamp": timestamp}
        signature = self._generate_signature(params)
        
        headers = {
            "RST-API-KEY": self.api_key,
            "MSG-SIGNATURE": signature,
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        try:
            response = requests.get(endpoint, params=params, headers=headers)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Error fetching balance: {response.status_code} - {response.text}")
                return {"error": f"HTTP {response.status_code}: {response.text}"}
        except Exception as e:
            logger.error(f"Exception in get_balance: {str(e)}")
            return {"error": str(e)}
    
    def place_order(self, pair="BTC/USD", side="BUY", quantity=0.01, price=None):
        """Place an order on the exchange"""
        endpoint = f"{self.base_url}/v3/place_order"
        timestamp = int(time.time() * 1000)
        
        # Prepare parameters
        params = {
            "pair": pair,
            "side": side,
            "quantity": quantity,
            "timestamp": timestamp
        }
        
        # If price is provided, it's a LIMIT order, otherwise MARKET
        if price is not None:
            params["type"] = "LIMIT"
            params["price"] = price
        else:
            params["type"] = "MARKET"
        
        # Generate signature
        signature = self._generate_signature(params)
        
        headers = {
            "RST-API-KEY": self.api_key,
            "MSG-SIGNATURE": signature,
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        try:
            response = requests.post(endpoint, data=params, headers=headers)
            if response.status_code == 200:
                result = response.json()
                if result.get("Success", False):
                    logger.info(f"Order placed successfully: {side} {quantity} {pair}")
                else:
                    logger.error(f"Error placing order: {result.get('ErrMsg', 'Unknown error')}")
                return result
            else:
                logger.error(f"Error placing order: {response.status_code} - {response.text}")
                return {"Success": False, "ErrMsg": f"HTTP {response.status_code}: {response.text}"}
        except Exception as e:
            logger.error(f"Exception in place_order: {str(e)}")
            return {"Success": False, "ErrMsg": str(e)}
    
    def query_order(self, order_id=None, pair=None):
        """Query order status"""
        endpoint = f"{self.base_url}/v3/query_order"
        timestamp = int(time.time() * 1000)
        
        params = {"timestamp": timestamp}
        
        if order_id:
            params["order_id"] = order_id
        if pair:
            params["pair"] = pair
        
        signature = self._generate_signature(params)
        
        headers = {
            "RST-API-KEY": self.api_key,
            "MSG-SIGNATURE": signature,
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        try:
            response = requests.post(endpoint, data=params, headers=headers)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Error querying order: {response.status_code} - {response.text}")
                return {"error": f"HTTP {response.status_code}: {response.text}"}
        except Exception as e:
            logger.error(f"Exception in query_order: {str(e)}")
            return {"error": str(e)}
    
    def cancel_order(self, pair="BTC/USD"):
        """Cancel orders for a trading pair"""
        endpoint = f"{self.base_url}/v3/cancel_order"
        timestamp = int(time.time() * 1000)
        
        params = {
            "timestamp": timestamp,
            "pair": pair
        }
        
        signature = self._generate_signature(params)
        
        headers = {
            "RST-API-KEY": self.api_key,
            "MSG-SIGNATURE": signature,
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        try:
            response = requests.post(endpoint, data=params, headers=headers)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Error canceling order: {response.status_code} - {response.text}")
                return {"error": f"HTTP {response.status_code}: {response.text}"}
        except Exception as e:
            logger.error(f"Exception in cancel_order: {str(e)}")
            return {"error": str(e)}
    
    def pending_count(self):
        """Get count of pending orders"""
        endpoint = f"{self.base_url}/v3/pending_count"
        timestamp = int(time.time() * 1000)
        
        params = {"timestamp": timestamp}
        signature = self._generate_signature(params)
        
        headers = {
            "RST-API-KEY": self.api_key,
            "MSG-SIGNATURE": signature,
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        try:
            response = requests.get(endpoint, params=params, headers=headers)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Error fetching pending count: {response.status_code} - {response.text}")
                return {"error": f"HTTP {response.status_code}: {response.text}"}
        except Exception as e:
            logger.error(f"Exception in pending_count: {str(e)}")
            return {"error": str(e)}
