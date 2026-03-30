"""
Layer 1: Fallback Data Source
REST API fallback when WebSocket fails.
"""

import time
from typing import Dict, Any, Optional, List
from datetime import datetime
from loguru import logger

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


class FallbackDataSource:
    """REST API fallback for market data."""
    
    def __init__(self, config: Dict[str, Any]):
        self.rest_endpoint = config.get('rest_endpoint', 'https://api.binance.com/api/v3')
        self.reconnect_interval = config.get('reconnect_interval', 5)
        
        self.cache: Dict[str, Any] = {}
        self.cache_timeout = 60
    
    def fetch_klines(self, symbol: str = 'BTCUSDT', interval: str = '1m', 
                     limit: int = 100) -> Optional[List[Dict[str, Any]]]:
        """Fetch klines (candlestick) data from REST API."""
        if not REQUESTS_AVAILABLE:
            logger.warning("requests not available, using cached data")
            return self._get_cached_data(symbol)
        
        url = f"{self.rest_endpoint}/klines"
        params = {
            'symbol': symbol.upper(),
            'interval': interval,
            'limit': limit
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            klines = self._parse_klines(data)
            self._cache_data(symbol, klines)
            
            return klines
            
        except Exception as e:
            logger.error(f"Failed to fetch klines: {e}")
            return self._get_cached_data(symbol)
    
    def fetch_ticker(self, symbol: str = 'BTCUSDT') -> Optional[Dict[str, Any]]:
        """Fetch 24hr ticker data."""
        if not REQUESTS_AVAILABLE:
            return self._get_cached_data(symbol)
        
        url = f"{self.rest_endpoint}/ticker/24hr"
        params = {'symbol': symbol.upper()}
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            return {
                'symbol': data.get('symbol', '').lower(),
                'price': float(data.get('lastPrice', 0)),
                'high': float(data.get('highPrice', 0)),
                'low': float(data.get('lowPrice', 0)),
                'volume': float(data.get('volume', 0)),
                'change': float(data.get('priceChange', 0)),
                'change_pct': float(data.get('priceChangePercent', 0)),
                'timestamp': int(time.time() * 1000)
            }
            
        except Exception as e:
            logger.error(f"Failed to fetch ticker: {e}")
            return self._get_cached_data(symbol)
    
    def _parse_klines(self, data: List) -> List[Dict[str, Any]]:
        """Parse Binance kline response to standard format."""
        klines = []
        for k in data:
            klines.append({
                'symbol': k[0].lower() if isinstance(k[0], str) else 'btcusdt',
                'timestamp': k[0],
                'datetime': datetime.fromtimestamp(k[0] / 1000),
                'open': float(k[1]),
                'high': float(k[2]),
                'low': float(k[3]),
                'close': float(k[4]),
                'volume': float(k[5]),
                'closed': k[8],
                'interval': k[7]
            })
        return klines
    
    def _cache_data(self, symbol: str, data: Any):
        """Cache data with timestamp."""
        self.cache[symbol] = {
            'data': data,
            'timestamp': time.time()
        }
    
    def _get_cached_data(self, symbol: str) -> Optional[Any]:
        """Get cached data if not expired."""
        if symbol in self.cache:
            cached = self.cache[symbol]
            if time.time() - cached['timestamp'] < self.cache_timeout:
                logger.info(f"Using cached data for {symbol}")
                return cached['data']
        return None
    
    def is_available(self) -> bool:
        """Check if REST API is available."""
        if not REQUESTS_AVAILABLE:
            return False
        
        try:
            url = f"{self.rest_endpoint}/ping"
            response = requests.get(url, timeout=5)
            return response.status_code == 200
        except:
            return False


fallback_source = FallbackDataSource({})


def fetch_fallback_data(symbol: str = 'BTCUSDT') -> Optional[Dict[str, Any]]:
    """Convenience function to fetch fallback data."""
    return fallback_source.fetch_ticker(symbol)
