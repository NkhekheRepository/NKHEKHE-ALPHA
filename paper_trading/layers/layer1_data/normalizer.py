"""
Layer 1: Data Normalizer
Converts exchange data to VNPY BarData format.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from loguru import logger


class DataNormalizer:
    """Normalize market data to VNPY format."""
    
    def __init__(self):
        self.price_precision = 2
        self.volume_precision = 4
    
    def normalize_bar(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize a single bar to standard format."""
        return {
            'symbol': data.get('symbol', 'BTCUSDT').upper(),
            'timestamp': data.get('timestamp', 0),
            'datetime': data.get('datetime', datetime.now()),
            'open': round(float(data.get('open', 0)), self.price_precision),
            'high': round(float(data.get('high', 0)), self.price_precision),
            'low': round(float(data.get('low', 0)), self.price_precision),
            'close': round(float(data.get('close', 0)), self.price_precision),
            'volume': round(float(data.get('volume', 0)), self.volume_precision),
            'turnover': round(float(data.get('turnover', 0)), 2),
            'open_interest': int(data.get('open_interest', 0)),
            'interval': '1m'
        }
    
    def normalize_to_vnpy(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert to VNPY BarData-compatible format."""
        normalized = self.normalize_bar(data)
        
        return {
            'vt_symbol': f"{normalized['symbol']}.BINANCE",
            'symbol': normalized['symbol'],
            'exchange': 'BINANCE',
            'datetime': normalized['datetime'],
            'interval': '1m',
            'open_price': normalized['open'],
            'high_price': normalized['high'],
            'low_price': normalized['low'],
            'close_price': normalized['close'],
            'volume': normalized['volume'],
            'turnover': normalized['turnover'],
            'open_interest': normalized['open_interest']
        }
    
    def normalize_batch(self, data_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize a batch of bars."""
        return [self.normalize_bar(d) for d in data_list]
    
    def calculate_returns(self, bars: List[Dict[str, Any]]) -> List[float]:
        """Calculate returns from price data."""
        if len(bars) < 2:
            return []
        
        returns = []
        for i in range(1, len(bars)):
            prev_close = bars[i-1].get('close', 0)
            curr_close = bars[i].get('close', 0)
            if prev_close > 0:
                ret = (curr_close - prev_close) / prev_close
                returns.append(ret)
        
        return returns
    
    def calculate_volatility(self, bars: List[Dict[str, Any]], window: int = 20) -> float:
        """Calculate rolling volatility."""
        import numpy as np
        
        returns = self.calculate_returns(bars)
        if len(returns) < window:
            return 0.0
        
        return float(np.std(returns[-window:]))
    
    def calculate_indicators(self, bars: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate basic technical indicators."""
        if len(bars) < 2:
            return {}
        
        closes = [b.get('close', 0) for b in bars]
        
        sma_5 = sum(closes[-5:]) / 5 if len(closes) >= 5 else 0
        sma_10 = sum(closes[-10:]) / 10 if len(closes) >= 10 else 0
        sma_20 = sum(closes[-20:]) / 20 if len(closes) >= 20 else 0
        
        returns = self.calculate_returns(bars)
        
        return {
            'price': closes[-1] if closes else 0,
            'sma_5': sma_5,
            'sma_10': sma_10,
            'sma_20': sma_20,
            'volatility': self.calculate_volatility(bars),
            'returns': returns[-1] if returns else 0,
            'volume': bars[-1].get('volume', 0) if bars else 0
        }


normalizer = DataNormalizer()


def normalize_market_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Convenience function to normalize market data."""
    return normalizer.normalize_to_vnpy(data)
