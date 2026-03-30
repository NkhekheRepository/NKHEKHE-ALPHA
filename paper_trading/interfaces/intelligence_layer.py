"""
Intelligence Layer Interface
============================
Contract for ML/AI intelligence layer (HMM, DT, PPO, etc).
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from .base import BaseLayer, LayerInput, LayerOutput, TradingSignal, FeatureVector


class IIntelligenceLayer(ABC):
    """Intelligence layer interface - AI/ML processing"""
    
    @abstractmethod
    def detect_regime(self, features: FeatureVector) -> LayerOutput:
        """Detect market regime (bull, bear, volatile, sideways)"""
        pass
    
    @abstractmethod
    def predict(self, features: FeatureVector, signal: TradingSignal) -> LayerOutput:
        """AI prediction/validation of signal"""
        pass
    
    @abstractmethod
    def learn(self, trade_result: Dict[str, Any]) -> LayerOutput:
        """Learn from trade result"""
        pass
    
    @abstractmethod
    def get_current_regime(self) -> str:
        """Get current detected regime"""
        pass


class IntelligenceLayer(BaseLayer, IIntelligenceLayer):
    """Base implementation of intelligence layer"""
    
    name = "intelligence"
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.hmm_enabled = config.get('hmm', {}).get('enabled', True)
        self.decision_tree_enabled = config.get('decision_tree', {}).get('enabled', True)
        self.self_learning_enabled = config.get('self_learning', {}).get('enabled', True)
        self.adaptive_enabled = config.get('adaptive', {}).get('enabled', True)
        self._current_regime = "sideways"
    
    def process(self, input_data: LayerInput) -> LayerOutput:
        """Process intelligence request"""
        try:
            action = input_data.get('action', 'detect')
            features = input_data.get('features')
            
            if action == 'detect':
                return self.detect_regime(features)
            elif action == 'predict':
                signal = input_data.get('signal')
                return self.predict(features, signal)
            elif action == 'learn':
                trade_result = input_data.get('trade_result')
                return self.learn(trade_result)
            
            return LayerOutput(
                result={'regime': self._current_regime},
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
    
    def detect_regime(self, features: FeatureVector) -> LayerOutput:
        """Detect regime - implemented by HMM"""
        return LayerOutput(
            result={'regime': self._current_regime, 'confidence': 0.7},
            success=True,
            layer_name=self.name
        )
    
    def predict(self, features: FeatureVector, signal: TradingSignal) -> LayerOutput:
        """Predict - implemented by ML models"""
        return LayerOutput(
            result=signal,
            success=True,
            layer_name=self.name
        )
    
    def learn(self, trade_result: Dict[str, Any]) -> LayerOutput:
        """Learn from trade"""
        return LayerOutput(
            result={'learned': True},
            success=True,
            layer_name=self.name
        )
    
    def get_current_regime(self) -> str:
        return self._current_regime
