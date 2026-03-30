"""
Trading Integration for Telegram Bot
===================================
Connects NkhekheAlphaBot to Binance Futures trading.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List

sys.path.insert(0, str(Path(__file__).parent.parent))

from paper_trading.layers.layer1_data.binance_futures import FuturesTradingEngine
from dotenv import load_dotenv

load_dotenv()


class TradingBotIntegration:
    def __init__(self):
        self.futures_engine: Optional[FuturesTradingEngine] = None
        self.alert_callback = None
        
    def initialize(self, config: Dict[str, Any] = None) -> bool:
        """Initialize the futures trading engine."""
        try:
            cfg = config or {}
            
            futures_config = {
                'symbol': cfg.get('symbol', 'BTCUSDT'),
                'leverage': cfg.get('leverage', 75),
                'testnet': os.getenv('BINANCE_TESTNET', 'true').lower() == 'true'
            }
            
            self.futures_engine = FuturesTradingEngine(futures_config)
            return True
            
        except Exception as e:
            print(f"Failed to initialize futures engine: {e}")
            return False
    
    def start(self) -> Dict[str, Any]:
        """Start the futures engine."""
        if not self.futures_engine:
            return {"error": "Engine not initialized"}
        
        return self.futures_engine.start()
    
    def stop(self):
        """Stop the futures engine."""
        if self.futures_engine:
            self.futures_engine.stop()
    
    def get_status(self) -> Dict[str, Any]:
        """Get trading status."""
        if not self.futures_engine:
            return {"error": "Engine not initialized"}
        
        return self.futures_engine.get_status()
    
    def long(self, quantity: float) -> Dict[str, Any]:
        """Open LONG position."""
        if not self.futures_engine:
            return {"error": "Engine not initialized"}
        
        result = self.futures_engine.open_long(quantity)
        
        if self.alert_callback and 'orderId' in result:
            self.alert_callback(self._format_trade_alert("LONG", result))
        
        return result
    
    def short(self, quantity: float) -> Dict[str, Any]:
        """Open SHORT position."""
        if not self.futures_engine:
            return {"error": "Engine not initialized"}
        
        result = self.futures_engine.open_short(quantity)
        
        if self.alert_callback and 'orderId' in result:
            self.alert_callback(self._format_trade_alert("SHORT", result))
        
        return result
    
    def close(self) -> Dict[str, Any]:
        """Close position."""
        if not self.futures_engine:
            return {"error": "Engine not initialized"}
        
        result = self.futures_engine.close_all()
        
        if self.alert_callback and 'orderId' in result:
            self.alert_callback(self._format_close_alert(result))
        
        return result
    
    def set_leverage(self, leverage: int):
        """Set leverage (1-75)."""
        if not self.futures_engine:
            return {"error": "Engine not initialized"}
        
        self.futures_engine.set_leverage(leverage)
        return {"success": True, "leverage": leverage}
    
    def get_balance(self) -> float:
        """Get wallet balance."""
        if not self.futures_engine:
            return 0.0
        
        return self.futures_engine.client.get_balance()
    
    def get_price(self, symbol: str = None) -> float:
        """Get current price."""
        if not self.futures_engine:
            return 0.0
        
        sym = symbol or self.futures_engine.symbol
        return self.futures_engine.client.get_symbol_price(sym)
    
    def get_positions(self) -> List[Dict[str, Any]]:
        """Get all open positions."""
        if not self.futures_engine:
            return []
        
        return self.futures_engine.client.get_all_positions()
    
    def get_trade_history(self, symbol: str = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Get trade history."""
        if not self.futures_engine:
            return []
        
        sym = symbol or self.futures_engine.symbol
        return self.futures_engine.client.get_trade_history(sym, limit)
    
    def get_liquidation_warning(self, symbol: str = None) -> Optional[str]:
        """Get liquidation warning."""
        if not self.futures_engine:
            return None
        
        sym = symbol or self.futures_engine.symbol
        return self.futures_engine.client.get_liquidation_warning(sym)
    
    def set_alert_callback(self, callback):
        """Set callback for trade alerts."""
        self.alert_callback = callback
    
    def _format_trade_alert(self, side: str, result: Dict[str, Any]) -> str:
        """Format trade alert message."""
        order = result.get('order', {})
        position = result.get('position', {})
        
        emoji = "📈" if side == "LONG" else "📉"
        
        return f"""
{emoji} <b>{side} EXECUTED</b>

<b>Symbol:</b> {order.get('symbol', 'BTCUSDT')}
<b>Quantity:</b> {order.get('executedQty', 'N/A')}
<b>Price:</b> ${float(order.get('avgPrice', 0)):,.2f}
<b>Leverage:</b> {result.get('leverage', 75)}x
<b>PnL:</b> ${position.get('unrealized_pnl', 0):.2f}
"""
    
    def _format_close_alert(self, result: Dict[str, Any]) -> str:
        """Format close position alert."""
        return f"""
🛑 <b>POSITION CLOSED</b>

<b>Symbol:</b> {result.get('symbol', 'BTCUSDT')}
<b>Status:</b> {result.get('status', 'FILLED')}
"""


trading_integration = TradingBotIntegration()
