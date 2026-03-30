"""
Strategy Layer Interface
========================
Contract for trading strategy layer.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Type
from .base import BaseLayer, LayerInput, LayerOutput, TradingSignal, FeatureVector


class IStrategyLayer(ABC):
    """Strategy layer interface - generates trading signals"""
    
    @abstractmethod
    def generate_signal(self, features: FeatureVector) -> LayerOutput:
        """Generate trading signal from features"""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Get strategy name"""
        pass
    
    @abstractmethod
    def reset(self):
        """Reset strategy state"""
        pass


class StrategyRegistry:
    """
    Registry for strategies - enables plug-and-play strategies.
    Add new strategies without touching core code.
    """
    
    _strategies: Dict[str, Type[IStrategyLayer]] = {}
    
    @classmethod
    def register(cls, name: str, strategy_class: Type[IStrategyLayer]):
        """Register a strategy class"""
        cls._strategies[name] = strategy_class
    
    @classmethod
    def get(cls, name: str) -> Type[IStrategyLayer]:
        """Get strategy class by name"""
        return cls._strategies.get(name)
    
    @classmethod
    def create(cls, name: str, config: Dict[str, Any] = None) -> IStrategyLayer:
        """Create strategy instance"""
        strategy_class = cls.get(name)
        if strategy_class:
            return strategy_class(config or {})
        return None
    
    @classmethod
    def list_all(cls) -> List[str]:
        """List all registered strategy names"""
        return list(cls._strategies.keys())


class StrategyLayer(BaseLayer, IStrategyLayer):
    """Base implementation of strategy layer"""
    
    name = "strategy"
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.active_strategies: Dict[str, IStrategyLayer] = {}
        self.default_strategy = config.get('default', 'momentum')
    
    def process(self, input_data: LayerInput) -> LayerOutput:
        """Process strategy signal generation"""
        try:
            features = input_data.get('features')
            if not features:
                return LayerOutput(
                    result={'action': 'hold', 'reason': 'No features'},
                    success=True,
                    layer_name=self.name
                )
            
            signal = self.generate_signal(features)
            return LayerOutput(
                result=signal.result,
                success=True,
                layer_name=self.name
            )
        except Exception as e:
            return LayerOutput(
                result=None,
                success=False,
                error=str(e),
                layer_name=self.name
            )
    
    def generate_signal(self, features: FeatureVector) -> LayerOutput:
        """Generate signal - implemented by strategies"""
        return LayerOutput(
            result=TradingSignal(action='hold', confidence=0, score=0, 
                               strategy=self.get_name(), regime='unknown'),
            success=True,
            layer_name=self.name
        )
    
    def register_strategy(self, name: str, strategy: IStrategyLayer):
        """Register a strategy"""
        self.active_strategies[name] = strategy
    
    def get_name(self) -> str:
        return self.name
