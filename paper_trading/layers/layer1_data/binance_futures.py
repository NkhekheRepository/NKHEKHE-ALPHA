"""
Binance Futures Trading API Client
================================
Supports 75x leverage, margin trading, and position management.
"""

import os
import hmac
import hashlib
import time
import requests
from typing import Dict, Any, Optional, List
from loguru import logger

FUTURES_API_URL = "https://fapi.binance.com"
FUTURES_WS_URL = "wss://fstream.binance.com/ws"


class BinanceFuturesClient:
    def __init__(self, api_key: str = None, api_secret: str = None, testnet: bool = False):
        self.api_key = api_key or os.getenv('BINANCE_API_KEY', '')
        self.api_secret = api_secret or os.getenv('BINANCE_SECRET_KEY', '') or os.getenv('BINANCE_API_SECRET', '')
        self.testnet = testnet
        
        if testnet:
            global FUTURES_API_URL, FUTURES_WS_URL
            FUTURES_API_URL = "https://testnet.binancefuture.com"
            FUTURES_WS_URL = "https://testnet.binancefuture.com/ws"
        
        self.leverage = 75
        self.margin_type = 'ISOLATED'
        
        logger.info(f"BinanceFuturesClient initialized: leverage={self.leverage}x, testnet={testnet}")
    
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
    
    def set_leverage(self, symbol: str, leverage: int) -> Dict[str, Any]:
        """Set leverage for a symbol."""
        try:
            timestamp = int(time.time() * 1000)
            params = f"symbol={symbol}&leverage={leverage}&timestamp={timestamp}"
            signature = self._sign(params)
            
            response = requests.post(
                f"{FUTURES_API_URL}/fapi/v1/leverage",
                params={"symbol": symbol, "leverage": leverage, "timestamp": timestamp, "signature": signature},
                headers=self._headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                self.leverage = leverage
                logger.info(f"Leverage set to {leverage}x for {symbol}")
                return response.json()
            else:
                logger.error(f"Set leverage failed: {response.text}")
                return {"error": response.text}
                
        except Exception as e:
            logger.error(f"Set leverage error: {e}")
            return {"error": str(e)}
    
    def set_margin_type(self, symbol: str, margin_type: str = 'ISOLATED') -> Dict[str, Any]:
        """Set margin type: ISOLATED or CROSSED."""
        try:
            timestamp = int(time.time() * 1000)
            params = f"symbol={symbol}&marginType={margin_type}&timestamp={timestamp}"
            signature = self._sign(params)
            
            response = requests.post(
                f"{FUTURES_API_URL}/fapi/v1/marginType",
                params={"symbol": symbol, "marginType": margin_type, "timestamp": timestamp, "signature": signature},
                headers=self._headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                self.margin_type = margin_type
                logger.info(f"Margin type set to {margin_type} for {symbol}")
                return response.json()
            else:
                logger.error(f"Set margin type failed: {response.text}")
                return {"error": response.text}
                
        except Exception as e:
            logger.error(f"Set margin type error: {e}")
            return {"error": str(e)}
    
    def place_order(self, symbol: str, side: str, order_type: str = 'MARKET',
                   quantity: float = None, price: float = None,
                   stop_price: float = None, reduce_only: bool = False) -> Dict[str, Any]:
        """Place a futures order."""
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
            
            if reduce_only:
                params["reduceOnly"] = "true"
            
            query_string = "&".join([f"{k}={v}" for k, v in params.items()])
            signature = self._sign(query_string)
            params["signature"] = signature
            
            response = requests.post(
                f"{FUTURES_API_URL}/fapi/v1/order",
                params=params,
                headers=self._headers(),
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"Futures order placed: {response.json()}")
                return response.json()
            else:
                logger.error(f"Order failed: {response.text}")
                return {"error": response.text}
                
        except Exception as e:
            logger.error(f"Order error: {e}")
            return {"error": str(e)}
    
    def long(self, symbol: str, quantity: float) -> Dict[str, Any]:
        """Open LONG position."""
        return self.place_order(symbol, 'BUY', 'MARKET', quantity=quantity)
    
    def short(self, symbol: str, quantity: float) -> Dict[str, Any]:
        """Open SHORT position."""
        return self.place_order(symbol, 'SELL', 'MARKET', quantity=quantity)
    
    def close_position(self, symbol: str) -> Dict[str, Any]:
        """Close entire position."""
        position = self.get_position(symbol)
        
        if not position or position.get('positionAmt', 0) == 0:
            return {"message": "No position to close"}
        
        position_amt = float(position['positionAmt'])
        
        if position_amt > 0:
            return self.place_order(symbol, 'SELL', 'MARKET', quantity=abs(position_amt), reduce_only=True)
        elif position_amt < 0:
            return self.place_order(symbol, 'BUY', 'MARKET', quantity=abs(position_amt), reduce_only=True)
        
        return {"message": "No position"}
    
    def get_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get position information."""
        try:
            timestamp = int(time.time() * 1000)
            params = f"symbol={symbol.upper()}&timestamp={timestamp}"
            signature = self._sign(params)
            
            response = requests.get(
                f"{FUTURES_API_URL}/fapi/v2/positionRisk",
                params={"symbol": symbol.upper(), "timestamp": timestamp, "signature": signature},
                headers=self._headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                positions = response.json()
                for pos in positions:
                    if pos['symbol'] == symbol.upper():
                        return pos
                return None
            else:
                logger.error(f"Get position failed: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Get position error: {e}")
            return None
    
    def get_all_positions(self) -> List[Dict[str, Any]]:
        """Get all open positions."""
        try:
            timestamp = int(time.time() * 1000)
            params = f"timestamp={timestamp}"
            signature = self._sign(params)
            
            response = requests.get(
                f"{FUTURES_API_URL}/fapi/v2/positionRisk",
                params={"timestamp": timestamp, "signature": signature},
                headers=self._headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                positions = response.json()
                return [p for p in positions if float(p.get('positionAmt', 0)) != 0]
            return []
                
        except Exception as e:
            logger.error(f"Get all positions error: {e}")
            return []
    
    def get_account(self) -> Dict[str, Any]:
        """Get account information."""
        try:
            timestamp = int(time.time() * 1000)
            params = f"timestamp={timestamp}"
            signature = self._sign(params)
            
            response = requests.get(
                f"{FUTURES_API_URL}/fapi/v2/account",
                params={"timestamp": timestamp, "signature": signature},
                headers=self._headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Get account failed: {response.text}")
                return {}
                
        except Exception as e:
            logger.error(f"Get account error: {e}")
            return {}
    
    def get_balance(self, asset: str = "USDT") -> float:
        """Get wallet balance for asset."""
        account = self.get_account()
        
        if not account:
            return 0.0
        
        for balance in account.get('assets', []):
            if balance['asset'] == asset:
                return float(balance['walletBalance'])
        
        return 0.0
    
    def get_wallet_info(self) -> Dict[str, Any]:
        """Get full wallet info."""
        account = self.get_account()
        
        if not account:
            return {}
        
        total_unrealized_pnl = 0.0
        total_wallet_balance = 0.0
        
        for asset in account.get('assets', []):
            total_wallet_balance += float(asset.get('walletBalance', 0))
            total_unrealized_pnl += float(asset.get('unrealizedProfit', 0))
        
        return {
            'total_wallet_balance': total_wallet_balance,
            'total_unrealized_pnl': total_unrealized_pnl,
            'total_assets_value': total_wallet_balance + total_unrealized_pnl,
            'assets': account.get('assets', [])
        }
    
    def get_symbol_price(self, symbol: str) -> float:
        """Get current price for symbol."""
        try:
            response = requests.get(
                f"{FUTURES_API_URL}/fapi/v1/ticker/price",
                params={"symbol": symbol.upper()},
                timeout=10
            )
            
            if response.status_code == 200:
                return float(response.json()['price'])
            return 0.0
            
        except Exception as e:
            logger.error(f"Get price error: {e}")
            return 0.0
    
    def get_mark_price(self, symbol: str) -> float:
        """Get mark price for symbol (used for liquidation)."""
        try:
            response = requests.get(
                f"{FUTURES_API_URL}/fapi/v1/premiumIndex",
                params={"symbol": symbol.upper()},
                timeout=10
            )
            
            if response.status_code == 200:
                return float(response.json()['markPrice'])
            return 0.0
            
        except Exception as e:
            logger.error(f"Get mark price error: {e}")
            return 0.0
    
    def calculate_liquidation_price(self, entry_price: float, position_amt: float,
                                    leverage: int, side: str) -> float:
        """Calculate liquidation price."""
        if leverage <= 0:
            leverage = 1
        
        maintenance_margin_rate = 0.005
        
        if side.upper() == 'LONG':
            liquidation_price = entry_price * (1 - (1 / leverage) - maintenance_margin_rate)
        else:
            liquidation_price = entry_price * (1 + (1 / leverage) + maintenance_margin_rate)
        
        return liquidation_price
    
    def get_liquidation_warning(self, symbol: str) -> Optional[str]:
        """Check if position is near liquidation."""
        position = self.get_position(symbol)
        
        if not position or float(position.get('positionAmt', 0)) == 0:
            return None
        
        entry_price = float(position.get('entryPrice', 0))
        position_amt = float(position.get('positionAmt', 0))
        leverage = int(position.get('leverage', 1))
        mark_price = self.get_mark_price(symbol)
        
        if entry_price == 0 or mark_price == 0:
            return None
        
        side = 'LONG' if position_amt > 0 else 'SHORT'
        liq_price = self.calculate_liquidation_price(entry_price, position_amt, leverage, side)
        
        if side == 'LONG':
            distance_pct = (mark_price - liq_price) / mark_price * 100
        else:
            distance_pct = (liq_price - mark_price) / mark_price * 100
        
        if distance_pct < 1:
            return f"🔴 LIQUIDATION IMMINENT! {distance_pct:.2f}% to liquidation"
        elif distance_pct < 5:
            return f"⚠️ LIQUIDATION WARNING: {distance_pct:.2f}% to liquidation"
        
        return None
    
    def get_leverage_info(self, symbol: str) -> Dict[str, Any]:
        """Get leverage info for symbol."""
        try:
            response = requests.get(
                f"{FUTURES_API_URL}/fapi/v1/leverageBracket",
                params={"symbol": symbol.upper()},
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            return {}
            
        except Exception as e:
            logger.error(f"Get leverage info error: {e}")
            return {}
    
    def get_open_orders(self, symbol: str = None) -> List[Dict[str, Any]]:
        """Get open orders."""
        try:
            timestamp = int(time.time() * 1000)
            params = f"timestamp={timestamp}"
            
            if symbol:
                params = f"symbol={symbol.upper()}&timestamp={timestamp}"
            
            signature = self._sign(params)
            
            url_params = {"timestamp": timestamp, "signature": signature}
            if symbol:
                url_params["symbol"] = symbol.upper()
            
            response = requests.get(
                f"{FUTURES_API_URL}/fapi/v1/openOrders",
                params=url_params,
                headers=self._headers(),
                timeout=10
            )
            
            return response.json() if response.status_code == 200 else []
            
        except Exception as e:
            logger.error(f"Get open orders error: {e}")
            return []
    
    def cancel_order(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """Cancel an order."""
        try:
            timestamp = int(time.time() * 1000)
            params = f"symbol={symbol.upper()}&orderId={order_id}&timestamp={timestamp}"
            signature = self._sign(params)
            
            response = requests.delete(
                f"{FUTURES_API_URL}/fapi/v1/order",
                params={"symbol": symbol.upper(), "orderId": order_id, "timestamp": timestamp, "signature": signature},
                headers=self._headers(),
                timeout=10
            )
            
            return response.json() if response.status_code == 200 else {"error": response.text}
            
        except Exception as e:
            logger.error(f"Cancel order error: {e}")
            return {"error": str(e)}
    
    def get_trade_history(self, symbol: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get trade history."""
        try:
            timestamp = int(time.time() * 1000)
            params = f"timestamp={timestamp}&limit={limit}"
            
            if symbol:
                params = f"symbol={symbol.upper()}&timestamp={timestamp}&limit={limit}"
            
            signature = self._sign(params)
            
            url_params = {"timestamp": timestamp, "limit": limit, "signature": signature}
            if symbol:
                url_params["symbol"] = symbol.upper()
            
            response = requests.get(
                f"{FUTURES_API_URL}/fapi/v1/userTrades",
                params=url_params,
                headers=self._headers(),
                timeout=10
            )
            
            return response.json() if response.status_code == 200 else []
            
        except Exception as e:
            logger.error(f"Get trade history error: {e}")
            return []


class FuturesTradingEngine:
    """Futures trading engine with 75x leverage."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        self.symbol = self.config.get('symbol', 'BTCUSDT')
        self.leverage = self.config.get('leverage', 75)
        self.testnet = self.config.get('testnet', True)
        
        self.client = BinanceFuturesClient(
            api_key=os.getenv('BINANCE_API_KEY'),
            api_secret=os.getenv('BINANCE_SECRET_KEY'),
            testnet=self.testnet
        )
        
        self.running = False
        self.auto_trade = False
        
        logger.info(f"FuturesTradingEngine initialized: {self.symbol} {self.leverage}x (testnet={self.testnet})")
    
    def start(self) -> Dict[str, Any]:
        """Start the futures trading engine."""
        self.running = True
        
        self.client.set_leverage(self.symbol, self.leverage)
        self.client.set_margin_type(self.symbol, 'ISOLATED')
        
        balance = self.client.get_balance()
        price = self.client.get_symbol_price(self.symbol)
        
        logger.info(f"Futures engine started: {self.symbol} {self.leverage}x, balance=${balance}, price=${price}")
        
        return self.get_status()
    
    def stop(self):
        """Stop the futures trading engine."""
        self.running = False
        logger.info("Futures trading stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """Get trading status."""
        balance = self.client.get_balance()
        price = self.client.get_symbol_price(self.symbol)
        position = self.client.get_position(self.symbol)
        wallet = self.client.get_wallet_info()
        
        return {
            "running": self.running,
            "auto_trade": self.auto_trade,
            "symbol": self.symbol,
            "leverage": self.leverage,
            "balance": balance,
            "price": price,
            "position": {
                "amount": float(position.get('positionAmt', 0)) if position else 0,
                "entry_price": float(position.get('entryPrice', 0)) if position else 0,
                "unrealized_pnl": float(position.get('unrealizedProfit', 0)) if position else 0,
                "leverage": int(position.get('leverage', self.leverage)) if position else self.leverage
            } if position else None,
            "wallet": wallet,
            "testnet": self.testnet
        }
    
    def open_long(self, quantity: float) -> Dict[str, Any]:
        """Open LONG position with 75x leverage."""
        if not self.running:
            return {"error": "Engine not running"}
        
        self.client.set_leverage(self.symbol, self.leverage)
        
        result = self.client.long(self.symbol, quantity)
        
        if 'orderId' in result:
            position = self.client.get_position(self.symbol)
            liq_warning = self.client.get_liquidation_warning(self.symbol)
            
            return {
                "success": True,
                "order": result,
                "position": position,
                "liquidation_warning": liq_warning,
                "leverage": self.leverage,
                "side": "LONG"
            }
        
        return result
    
    def open_short(self, quantity: float) -> Dict[str, Any]:
        """Open SHORT position with 75x leverage."""
        if not self.running:
            return {"error": "Engine not running"}
        
        self.client.set_leverage(self.symbol, self.leverage)
        
        result = self.client.short(self.symbol, quantity)
        
        if 'orderId' in result:
            position = self.client.get_position(self.symbol)
            liq_warning = self.client.get_liquidation_warning(self.symbol)
            
            return {
                "success": True,
                "order": result,
                "position": position,
                "liquidation_warning": liq_warning,
                "leverage": self.leverage,
                "side": "SHORT"
            }
        
        return result
    
    def close_all(self) -> Dict[str, Any]:
        """Close all positions."""
        if not self.running:
            return {"error": "Engine not running"}
        
        return self.client.close_position(self.symbol)
    
    def set_leverage(self, leverage: int):
        """Set leverage (1-75)."""
        if leverage < 1:
            leverage = 1
        elif leverage > 75:
            leverage = 75
        
        self.leverage = leverage
        self.client.set_leverage(self.symbol, leverage)
        logger.info(f"Leverage set to {leverage}x")
    
    def toggle_auto_trade(self, enabled: bool = None):
        """Toggle auto-trading."""
        if enabled is None:
            self.auto_trade = not self.auto_trade
        else:
            self.auto_trade = enabled
        
        logger.info(f"Auto-trade: {self.auto_trade}")
        return self.auto_trade
