"""
Scoring Layer Interface
======================
Contract for trade scoring and ranking layer.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from .base import BaseLayer, LayerInput, LayerOutput, TradingSignal, FeatureVector


class IScoringLayer(ABC):
    """Scoring layer interface - scores and ranks trading signals"""
    
    @abstractmethod
    def score_signal(self, signal: TradingSignal, features: FeatureVector, 
                    regime: str) -> LayerOutput:
        """Score a trading signal"""
        pass
    
    @abstractmethod
    def rank_signals(self, signals: List[TradingSignal]) -> List[TradingSignal]:
        """Rank multiple trading signals"""
        pass


class ScoringLayer(BaseLayer, IScoringLayer):
    """
    Trade scoring layer.
    Score formula: score = 0.28 * momentum + 0.25 * breakout + 0.17 * volatility + 0.20 * confidence + 0.10 * volume
    """
    
    name = "scoring"
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.threshold = config.get('threshold', 0.72)
        self.high_conviction = config.get('high_conviction', 0.85)
        
        self.weights = {
            'momentum': config.get('momentum_weight', 0.28),
            'breakout': config.get('breakout_weight', 0.25),
            'volatility': config.get('volatility_weight', 0.17),
            'confidence': config.get('confidence_weight', 0.20),
            'volume': config.get('volume_weight', 0.10)
        }
    
    def process(self, input_data: LayerInput) -> LayerOutput:
        """Process scoring request"""
        try:
            signal = input_data.get('signal')
            features = input_data.get('features')
            regime = input_data.get('regime', 'sideways')
            
            if not signal:
                return LayerOutput(
                    result={'action': 'hold', 'score': 0},
                    success=True,
                    layer_name=self.name
                )
            
            result = self.score_signal(signal, features, regime)
            return result
        except Exception as e:
            return LayerOutput(
                result=None,
                success=False,
                error=str(e),
                layer_name=self.name
            )
    
    def score_signal(self, signal: TradingSignal, features: FeatureVector, 
                    regime: str) -> LayerOutput:
        """Score a trading signal"""
        momentum = self._calculate_momentum(features)
        breakout = self._calculate_breakout(features)
        volatility = self._calculate_volatility(features)
        volume = features.volume_ratio if features.volume_ratio else 1.0
        
        score = (
            self.weights['momentum'] * momentum +
            self.weights['breakout'] * breakout +
            self.weights['volatility'] * volatility +
            self.weights['confidence'] * signal.confidence +
            self.weights['volume'] * volume
        )
        
        signal.score = score
        
        if score < self.threshold:
            signal.action = 'hold'
            signal.reason = f'Score {score:.2f} below threshold {self.threshold}'
        
        return LayerOutput(
            result=signal.to_dict(),
            success=True,
            layer_name=self.name,
            metadata={'score': score, 'threshold': self.threshold}
        )
    
    def rank_signals(self, signals: List[TradingSignal]) -> List[TradingSignal]:
        """Rank signals by score"""
        return sorted(signals, key=lambda s: s.score, reverse=True)
    
    def _calculate_momentum(self, features: FeatureVector) -> float:
        """Calculate momentum score"""
        if features.returns > 0.01:
            return 1.0
        elif features.returns < -0.01:
            return 0.0
        return 0.5
    
    def _calculate_breakout(self, features: FeatureVector) -> float:
        """Calculate breakout score"""
        if features.price > features.bollinger.get('upper', 0):
            return 1.0
        elif features.price < features.bollinger.get('lower', 0):
            return 0.0
        return 0.5
    
    def _calculate_volatility(self, features: FeatureVector) -> float:
        """Calculate volatility score (lower is better for scoring)"""
        if features.volatility < 0.01:
            return 1.0
        elif features.volatility > 0.05:
            return 0.0
        return 1.0 - (features.volatility / 0.05)
