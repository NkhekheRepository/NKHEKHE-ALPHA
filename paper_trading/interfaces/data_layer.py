"""
Data Layer Interface
====================
Contract for data ingestion layer.
"""

from abc import ABC, abstractmethod
from typing import List, Callable, Optional, Dict, Any
from .base import BaseLayer, LayerInput, LayerOutput, MarketData


class IDataLayer(ABC):
    """Data layer interface - handles market data ingestion"""
    
    @abstractmethod
    def fetch(self, symbol: str) -> LayerOutput:
        """Fetch current market data for symbol"""
        pass
    
    @abstractmethod
    def subscribe(self, symbols: List[str], callback: Callable):
        """Subscribe to real-time data updates"""
        pass
    
    @abstractmethod
    def unsubscribe(self, symbols: List[str]):
        """Unsubscribe from real-time data"""
        pass
    
    @abstractmethod
    def get_latest(self, symbol: str) -> Optional[MarketData]:
        """Get latest market data for symbol"""
        pass
    
    @abstractmethod
    def get_price_history(self, symbol: str, interval: str = "1m", 
                          limit: int = 100) -> List[Dict]:
        """Get historical price data"""
        pass
    
    @abstractmethod
    def connect(self) -> bool:
        """Connect to data source"""
        pass
    
    @abstractmethod
    def disconnect(self):
        """Disconnect from data source"""
        pass


class DataLayer(BaseLayer, IDataLayer):
    """Base implementation of data layer"""
    
    name = "data"
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.symbols: List[str] = config.get('symbols', ['BTCUSDT'])
        self.interval = config.get('interval', '1m')
        self._latest_data: Dict[str, MarketData] = {}
        self._callbacks: List[Callable] = []
    
    def process(self, input_data: LayerInput) -> LayerOutput:
        """Process data request"""
        symbol = input_data.get('symbol', self.symbols[0] if self.symbols else 'BTCUSDT')
        
        try:
            market_data = self.fetch(symbol)
            return LayerOutput(
                result=market_data.result,
                success=market_data.success,
                layer_name=self.name
            )
        except Exception as e:
            return LayerOutput(
                result=None,
                success=False,
                error=str(e),
                layer_name=self.name
            )
    
    def add_callback(self, callback: Callable):
        """Add data update callback"""
        self._callbacks.append(callback)
    
    def remove_callback(self, callback: Callable):
        """Remove data update callback"""
        if callback in self._callbacks:
            self._callbacks.remove(callback)
    
    def _notify_callbacks(self, data: MarketData):
        """Notify all callbacks of new data"""
        for callback in self._callbacks:
            try:
                callback(data)
            except Exception:
                pass
