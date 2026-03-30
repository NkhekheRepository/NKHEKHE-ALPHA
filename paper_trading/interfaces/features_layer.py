"""
Features Layer Interface
========================
Contract for technical indicators and feature calculation.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from .base import BaseLayer, LayerInput, LayerOutput, FeatureVector


class IFeaturesLayer(ABC):
    """Features layer interface - calculates technical indicators"""
    
    @abstractmethod
    def calculate(self, price: float, volume: float, 
                 price_history: List[float]) -> LayerOutput:
        """Calculate all features from price data"""
        pass
    
    @abstractmethod
    def get_features(self) -> Optional[FeatureVector]:
        """Get current feature vector"""
        pass
    
    @abstractmethod
    def get_atr(self) -> Optional[float]:
        """Get Average True Range"""
        pass
    
    @abstractmethod
    def get_adx(self) -> Optional[float]:
        """Get Average Directional Index"""
        pass
    
    @abstractmethod
    def get_rsi(self) -> Optional[float]:
        """Get Relative Strength Index"""
        pass
    
    @abstractmethod
    def get_macd(self) -> Optional[Dict[str, float]]:
        """Get MACD values"""
        pass
    
    @abstractmethod
    def get_bollinger_bands(self) -> Optional[Dict[str, float]]:
        """Get Bollinger Bands values"""
        pass


class FeaturesLayer(BaseLayer, IFeaturesLayer):
    """Base implementation of features layer"""
    
    name = "features"
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.indicators = config.get('indicators', ['atr', 'adx', 'rsi', 'macd', 'bollinger'])
        self.price_history: List[float] = []
        self.volume_history: List[float] = []
        self._current_features: Optional[FeatureVector] = None
    
    def process(self, input_data: LayerInput) -> LayerOutput:
        """Process features calculation request"""
        try:
            price = input_data.get('price', 0)
            volume = input_data.get('volume', 0)
            price_history = input_data.get('price_history', self.price_history)
            
            if price > 0:
                self.price_history.append(price)
                if len(self.price_history) > 500:
                    self.price_history.pop(0)
            
            if volume > 0:
                self.volume_history.append(volume)
                if len(self.volume_history) > 500:
                    self.volume_history.pop(0)
            
            result = self.calculate(price, volume, price_history)
            return result
        except Exception as e:
            return LayerOutput(
                result=None,
                success=False,
                error=str(e),
                layer_name=self.name
            )
    
    def calculate(self, price: float, volume: float, 
                  price_history: List[float]) -> LayerOutput:
        """Calculate features - implemented by subclasses"""
        return LayerOutput(
            result=self._current_features,
            success=True,
            layer_name=self.name
        )
