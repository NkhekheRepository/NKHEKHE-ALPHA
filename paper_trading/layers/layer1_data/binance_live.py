"""
Live Binance API Connector
==========================
Connects to Binance for real trading with:
- WebSocket for real-time data
- REST API for order execution
- Account balance fetching
"""

import os
import hmac
import hashlib
import time
import asyncio
import aiohttp
from typing import Dict, Any, Optional, List, Callable
from pathlib import Path
from loguru import logger
import requests

BINANCE_WS_URL = "wss://stream.binance.com:9443/ws"
BINANCE_API_URL = "https://api.binance.com/api/v3"


class BinanceLiveClient:
    def __init__(self, api_key: str = None, api_secret: str = None, testnet: bool = False):
        self.api_key = api_key or os.getenv("BINANCE_API_KEY", "")
        self.api_secret = api_secret or os.getenv("BINANCE_SECRET_KEY", "") or os.getenv("BINANCE_API_SECRET", "")
        self.testnet = testnet
        
        if testnet:
            global BINANCE_WS_URL, BINANCE_API_URL
            BINANCE_WS_URL = "wss://testnet.binance.vision/ws"
            BINANCE_API_URL = "https://testnet.binance.vision/api/v3"
        
        self.ws = None
        self.ws_session = None
        self.connected = False
        self.subscriptions: Dict[str, Callable] = {}
        self.reconnect_delay = 5
        self.max_reconnect = 10
        
        self._account_cache = None
        self._account_cache_time = 0
        
        logger.info(f"BinanceLiveClient initialized: testnet={testnet}")
    
    def _sign(self, params: str) -> str:
        return hmac.new(
            self.api_secret.encode('utf-8'),
            params.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def _headers(self) -> Dict[str, str]:
        return {
            "X-MBX-APIKEY": self.api_key,
            "Content-Type": "application/json"
        }
    
    async def connect_ws(self, streams: List[str]):
        """Connect to WebSocket for real-time data."""
        try:
            self.ws_session = aiohttp.ClientSession()
            ws_url = f"{BINANCE_WS_URL}/{'/'.join(streams)}"
            
            async with self.ws_session.ws_connect(ws_url) as ws:
                self.ws = ws
                self.connected = True
                logger.info(f"WebSocket connected: {streams}")
                
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        data = msg.json()
                        await self._handle_message(data)
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        logger.error(f"WebSocket error: {ws.exception()}")
                        break
                    
        except Exception as e:
            logger.error(f"WebSocket connection failed: {e}")
            self.connected = False
            await self._reconnect(streams)
    
    async def _reconnect(self, streams: List[str]):
        """Reconnect with exponential backoff."""
        for attempt in range(self.max_reconnect):
            delay = self.reconnect_delay * (2 ** attempt)
            logger.info(f"Reconnecting in {delay}s (attempt {attempt+1}/{self.max_reconnect})")
            await asyncio.sleep(delay)
            
            try:
                await self.connect_ws(streams)
                if self.connected:
                    return
            except Exception as e:
                logger.error(f"Reconnect failed: {e}")
        
        logger.error("Max reconnection attempts reached")
    
    async def _handle_message(self, data: Dict[str, Any]):
        """Handle incoming WebSocket messages."""
        stream = data.get('stream') or data.get('e', 'unknown')
        
        if stream in self.subscriptions:
            callback = self.subscriptions[stream]
            try:
                callback(data)
            except Exception as e:
                logger.error(f"Callback error for {stream}: {e}")
    
    def subscribe(self, stream: str, callback: Callable):
        """Subscribe to a WebSocket stream."""
        self.subscriptions[stream] = callback
    
    async def close_ws(self):
        """Close WebSocket connection."""
        if self.ws:
            await self.ws.close()
        if self.ws_session:
            await self.ws_session.close()
        self.connected = False
    
    def get_account(self, use_cache: bool = True) -> Dict[str, Any]:
        """Get account information."""
        now = time.time()
        
        if use_cache and self._account_cache and (now - self._account_cache_time) < 5:
            return self._account_cache
        
        try:
            timestamp = int(time.time() * 1000)
            params = f"timestamp={timestamp}"
            signature = self._sign(params)
            
            response = requests.get(
                f"{BINANCE_API_URL}/account",
                params={"timestamp": timestamp, "signature": signature},
                headers=self._headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                self._account_cache = response.json()
                self._account_cache_time = now
                return self._account_cache
            else:
                logger.error(f"Account fetch failed: {response.text}")
                return {}
                
        except Exception as e:
            logger.error(f"Account fetch error: {e}")
            return {}
    
    def get_balance(self, asset: str = "USDT") -> float:
        """Get balance for specific asset."""
        account = self.get_account()
        
        if not account:
            return 0.0
        
        for balance in account.get('balances', []):
            if balance['asset'] == asset:
                return float(balance['free'])
        
        return 0.0
    
    def get_positions(self) -> List[Dict[str, Any]]:
        """Get open positions."""
        account = self.get_account()
        
        if not account:
            return []
        
        positions = []
        for balance in account.get('balances', []):
            free = float(balance['free'])
            locked = float(balance['locked'])
            
            if free + locked > 0:
                positions.append({
                    'asset': balance['asset'],
                    'free': free,
                    'locked': locked,
                    'total': free + locked
                })
        
        return positions
    
    def place_order(self, symbol: str, side: str, order_type: str,
                   quantity: float = None, price: float = None,
                   stop_price: float = None, **kwargs) -> Dict[str, Any]:
        """Place an order."""
        try:
            timestamp = int(time.time() * 1000)
            
            params = {
                "symbol": symbol.upper(),
                "side": side.upper(),
                "type": order_type.upper(),
                "timestamp": timestamp
            }
            
            if quantity:
                params["quantity"] = quantity
            
            if price:
                params["price"] = price
                params["timeInForce"] = "GTC"
            
            if stop_price:
                params["stopPrice"] = stop_price
            
            params.update(kwargs)
            
            query_string = "&".join([f"{k}={v}" for k, v in params.items()])
            signature = self._sign(query_string)
            params["signature"] = signature
            
            response = requests.post(
                f"{BINANCE_API_URL}/order",
                params=params,
                headers=self._headers(),
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"Order placed: {response.json()}")
                return response.json()
            else:
                logger.error(f"Order failed: {response.text}")
                return {"error": response.text}
                
        except Exception as e:
            logger.error(f"Order error: {e}")
            return {"error": str(e)}
    
    def market_buy(self, symbol: str, quantity: float) -> Dict[str, Any]:
        """Place market buy order."""
        return self.place_order(symbol, "BUY", "MARKET", quantity=quantity)
    
    def market_sell(self, symbol: str, quantity: float) -> Dict[str, Any]:
        """Place market sell order."""
        return self.place_order(symbol, "SELL", "MARKET", quantity=quantity)
    
    def limit_buy(self, symbol: str, quantity: float, price: float) -> Dict[str, Any]:
        """Place limit buy order."""
        return self.place_order(symbol, "BUY", "LIMIT", quantity=quantity, price=price)
    
    def limit_sell(self, symbol: str, quantity: float, price: float) -> Dict[str, Any]:
        """Place limit sell order."""
        return self.place_order(symbol, "SELL", "LIMIT", quantity=quantity, price=price)
    
    def stop_loss(self, symbol: str, quantity: float, stop_price: float) -> Dict[str, Any]:
        """Place stop loss order."""
        return self.place_order(
            symbol, "SELL", "STOP_LOSS_LIMIT",
            quantity=quantity,
            stopPrice=stop_price,
            timeInForce="GTC"
        )
    
    def cancel_order(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """Cancel an order."""
        try:
            timestamp = int(time.time() * 1000)
            params = f"symbol={symbol.upper()}&orderId={order_id}&timestamp={timestamp}"
            signature = self._sign(params)
            
            response = requests.delete(
                f"{BINANCE_API_URL}/order",
                params={"symbol": symbol.upper(), "orderId": order_id, 
                       "timestamp": timestamp, "signature": signature},
                headers=self._headers(),
                timeout=10
            )
            
            return response.json() if response.status_code == 200 else {"error": response.text}
            
        except Exception as e:
            logger.error(f"Cancel order error: {e}")
            return {"error": str(e)}
    
    def get_open_orders(self, symbol: str = None) -> List[Dict[str, Any]]:
        """Get open orders."""
        try:
            timestamp = int(time.time() * 1000)
            params = f"timestamp={timestamp}"
            signature = self._sign(params)
            
            url_params = {"timestamp": timestamp, "signature": signature}
            if symbol:
                url_params["symbol"] = symbol.upper()
            
            response = requests.get(
                f"{BINANCE_API_URL}/openOrders",
                params=url_params,
                headers=self._headers(),
                timeout=10
            )
            
            return response.json() if response.status_code == 200 else []
            
        except Exception as e:
            logger.error(f"Get orders error: {e}")
            return []
    
    def get_symbol_price(self, symbol: str) -> float:
        """Get current price for symbol - no auth required."""
        try:
            response = requests.get(
                f"{BINANCE_API_URL}/ticker/price",
                params={"symbol": symbol.upper()},
                timeout=10
            )
            
            if response.status_code == 200:
                return float(response.json()['price'])
            return 0.0
            
        except Exception as e:
            logger.error(f"Get price error: {e}")
            return 0.0
    
    def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        """Get symbol exchange info."""
        try:
            response = requests.get(
                f"{BINANCE_API_URL}/exchangeInfo",
                params={"symbol": symbol.upper()},
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            return {}
            
        except Exception as e:
            logger.error(f"Get symbol info error: {e}")
            return {}
    
    def get_klines(self, symbol: str, interval: str = "1m",
                   limit: int = 100) -> List[List[Any]]:
        """Get candlestick data."""
        try:
            response = requests.get(
                f"{BINANCE_API_URL}/klines",
                params={
                    "symbol": symbol.upper(),
                    "interval": interval,
                    "limit": limit
                },
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            return []
            
        except Exception as e:
            logger.error(f"Get klines error: {e}")
            return []


class LiveTradingEngine:
    """Live trading engine that uses Binance API."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        self.api_key = os.getenv("BINANCE_API_KEY", "")
        self.api_secret = os.getenv("BINANCE_API_SECRET", "")
        self.testnet = self.config.get('testnet', True)
        
        self.client = BinanceLiveClient(
            api_key=self.api_key,
            api_secret=self.api_secret,
            testnet=self.testnet
        )
        
        self.symbol = self.config.get('symbol', 'BTCUSDT')
        self.running = False
        
        logger.info(f"LiveTradingEngine initialized: {self.symbol} (testnet={self.testnet})")
    
    def start(self):
        """Start live trading."""
        self.running = True
        
        balance = self.client.get_balance()
        logger.info(f"Account balance: {balance} USDT")
        
        price = self.client.get_symbol_price(self.symbol)
        logger.info(f"Current {self.symbol} price: {price}")
        
        return self.get_status()
    
    def stop(self):
        """Stop live trading."""
        self.running = False
        logger.info("Live trading stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """Get trading status."""
        balance = self.client.get_balance()
        price = self.client.get_symbol_price(self.symbol)
        positions = self.client.get_positions()
        open_orders = self.client.get_open_orders(self.symbol)
        
        return {
            "running": self.running,
            "symbol": self.symbol,
            "balance": balance,
            "price": price,
            "positions": positions,
            "open_orders": len(open_orders),
            "testnet": self.testnet
        }
    
    def execute_signal(self, signal: str, quantity: float = None) -> Dict[str, Any]:
        """Execute trading signal."""
        if not self.running:
            return {"error": "Engine not running"}
        
        if signal == "buy":
            if not quantity:
                quantity = self.config.get('quantity', 0.001)
            return self.client.market_buy(self.symbol, quantity)
        
        elif signal == "sell":
            if not quantity:
                quantity = self.config.get('quantity', 0.001)
            return self.client.market_sell(self.symbol, quantity)
        
        elif signal == "close":
            positions = [p for p in self.client.get_positions() 
                       if p['asset'] == self.symbol.replace('USDT', '')]
            if positions:
                return self.client.market_sell(self.symbol, positions[0]['free'])
            return {"message": "No position to close"}
        
        return {"error": f"Unknown signal: {signal}"}
