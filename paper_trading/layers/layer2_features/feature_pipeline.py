"""
Layer 2: Feature Pipeline
=========================
Connects data_lab/feature_engine to the trading system.
Provides ATR, ADX, MACD, Bollinger Bands, etc.
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from collections import deque
from loguru import logger

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

try:
    from data_lab.feature_engine import TechnicalIndicators, FeatureVector as LabFeatureVector
    FEATURES_AVAILABLE = True
except ImportError:
    FEATURES_AVAILABLE = False
    logger.warning("Feature engine not available")


class FeaturePipeline:
    """
    Feature pipeline that calculates technical indicators.
    Integrates with existing data_lab/feature_engine.
    """
    
    name = "features"
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.enabled = config.get('enabled', True)
        
        self.indicators = config.get('indicators', ['atr', 'rsi', 'macd', 'bollinger'])
        
        self.price_history = deque(maxlen=500)
        self.volume_history = deque(maxlen=500)
        
        self._current_features: Optional[Dict[str, Any]] = None
        
        self._atr_period = config.get('periods', {}).get('atr', 14)
        self._rsi_period = config.get('periods', {}).get('rsi', 14)
        self._bb_period = config.get('periods', {}).get('bollinger_period', 20)
        
        logger.info("FeaturePipeline initialized")
    
    def process(self, price: float, volume: float = 0) -> Dict[str, Any]:
        """Process price and calculate features"""
        if price <= 0:
            return self._current_features or self._default_features()
        
        self.price_history.append(price)
        if volume > 0:
            self.volume_history.append(volume)
        
        if len(self.price_history) < 20:
            return self._default_features()
        
        features = self._calculate_features(price)
        self._current_features = features
        
        return features
    
    def _calculate_features(self, current_price: float) -> Dict[str, Any]:
        """Calculate all technical indicators"""
        prices = list(self.price_history)
        
        features = {
            'price': current_price,
            'returns': self._calculate_returns(prices),
            'volatility': self._calculate_volatility(prices),
            'atr': self._calculate_atr(prices),
            'adx': self._calculate_adx(prices),
            'rsi': self._calculate_rsi(prices),
            'macd': self._calculate_macd(prices),
            'bollinger': self._calculate_bollinger(prices),
            'ema_fast': self._calculate_ema(prices, 10),
            'ema_slow': self._calculate_ema(prices, 30),
            'volume_ratio': self._calculate_volume_ratio()
        }
        
        return features
    
    def _calculate_returns(self, prices: List[float]) -> float:
        """Calculate returns"""
        if len(prices) < 2:
            return 0.0
        return (prices[-1] - prices[-2]) / prices[-2] if prices[-2] > 0 else 0.0
    
    def _calculate_volatility(self, prices: List[float]) -> float:
        """Calculate volatility (std dev of returns)"""
        if len(prices) < 14:
            return 0.0
        
        returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
        if len(returns) < 14:
            return 0.0
        
        mean = sum(returns) / len(returns)
        variance = sum((r - mean) ** 2 for r in returns) / len(returns)
        
        return variance ** 0.5
    
    def _calculate_atr(self, prices: List[float], period: int = 14) -> float:
        """Calculate Average True Range"""
        if len(prices) < period + 1:
            return 0.0
        
        tr_values = []
        for i in range(1, len(prices)):
            high = max(prices[i], prices[i-1])
            low = min(prices[i], prices[i-1])
            tr = high - low
            tr_values.append(tr)
        
        if len(tr_values) < period:
            return 0.0
        
        return sum(tr_values[-period:]) / period
    
    def _calculate_adx(self, prices: List[float], period: int = 14) -> float:
        """Calculate Average Directional Index (simplified)"""
        if len(prices) < period + 1:
            return 0.0
        
        gains = []
        losses = []
        
        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        if len(gains) < period:
            return 0.0
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 25.0
        
        di_plus = avg_gain / (avg_gain + avg_loss) * 100
        di_minus = avg_loss / (avg_gain + avg_loss) * 100
        
        dx = abs(di_plus - di_minus) / (di_plus + di_minus) * 100 if (di_plus + di_minus) > 0 else 0
        
        return dx
    
    def _calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """Calculate Relative Strength Index"""
        if len(prices) < period + 1:
            return 50.0
        
        gains = []
        losses = []
        
        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        if len(gains) < period:
            return 50.0
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def _calculate_macd(self, prices: List[float]) -> Dict[str, float]:
        """Calculate MACD"""
        if len(prices) < 26:
            return {'macd': 0, 'signal': 0, 'histogram': 0}
        
        ema_fast = self._calculate_ema(prices, 12)
        ema_slow = self._calculate_ema(prices, 26)
        
        macd = ema_fast - ema_slow
        
        macd_values = []
        for i in range(26, len(prices)):
            ef = self._calculate_ema(prices[:i+1], 12)
            es = self._calculate_ema(prices[:i+1], 26)
            macd_values.append(ef - es)
        
        if len(macd_values) < 9:
            return {'macd': macd, 'signal': 0, 'histogram': macd}
        
        signal = self._calculate_ema(macd_values, 9)
        histogram = macd - signal
        
        return {'macd': macd, 'signal': signal, 'histogram': histogram}
    
    def _calculate_bollinger(self, prices: List[float], period: int = 20) -> Dict[str, float]:
        """Calculate Bollinger Bands"""
        if len(prices) < period:
            return {'upper': 0, 'middle': 0, 'lower': 0, 'width': 0}
        
        recent = prices[-period:]
        middle = sum(recent) / period
        
        variance = sum((p - middle) ** 2 for p in recent) / period
        std = variance ** 0.5
        
        upper = middle + (2 * std)
        lower = middle - (2 * std)
        
        return {'upper': upper, 'middle': middle, 'lower': lower, 'width': upper - lower}
    
    def _calculate_ema(self, prices: List[float], period: int) -> float:
        """Calculate Exponential Moving Average"""
        if len(prices) < period:
            return 0.0
        
        multiplier = 2 / (period + 1)
        ema = prices[0]
        
        for price in prices[1:]:
            ema = (price - ema) * multiplier + ema
        
        return ema
    
    def _calculate_volume_ratio(self) -> float:
        """Calculate volume ratio vs average"""
        if len(self.volume_history) < 20:
            return 1.0
        
        avg_volume = sum(list(self.volume_history)[-20:]) / 20
        current_volume = self.volume_history[-1] if self.volume_history else 0
        
        if avg_volume == 0:
            return 1.0
        
        return current_volume / avg_volume
    
    def _default_features(self) -> Dict[str, Any]:
        """Return default features when insufficient data"""
        return {
            'price': 0,
            'returns': 0,
            'volatility': 0,
            'atr': 0,
            'adx': 0,
            'rsi': 50,
            'macd': {'macd': 0, 'signal': 0, 'histogram': 0},
            'bollinger': {'upper': 0, 'middle': 0, 'lower': 0, 'width': 0},
            'ema_fast': 0,
            'ema_slow': 0,
            'volume_ratio': 1.0
        }
    
    def get_current_features(self) -> Dict[str, Any]:
        """Get current feature vector"""
        return self._current_features or self._default_features()
