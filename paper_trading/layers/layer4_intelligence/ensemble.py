"""
Layer 4: Intelligence Ensemble
Combines HMM, Decision Tree, PPO, and Adaptive Learning.
"""

from typing import Dict, Any, List, Optional
from loguru import logger

from .hmm import HMMRegimeDetector
from .decision_tree import DecisionTreeAgent
from .self_learning import SelfLearningEngine
from .adaptive_learning import AdaptiveLearning


class IntelligenceEnsemble:
    """Ensemble of ML models for trading intelligence."""
    
    def __init__(self, config: Dict[str, Any]):
        self.hmm_enabled = config.get('hmm', {}).get('enabled', True)
        self.decision_tree_enabled = config.get('decision_tree', {}).get('enabled', True)
        self.self_learning_enabled = config.get('self_learning', {}).get('enabled', True)
        self.adaptive_enabled = config.get('adaptive', {}).get('enabled', True)
        
        self.hmm = HMMRegimeDetector(config.get('hmm', {}))
        self.decision_tree = DecisionTreeAgent(config.get('decision_tree', {}))
        self.self_learning = SelfLearningEngine(config.get('self_learning', {}))
        self.adaptive = AdaptiveLearning(config.get('adaptive', {}))
        
        self.price_history: List[float] = []
        self.volume_history: List[float] = []
        
        self.current_regime = 'sideways'
        
        logger.info("Intelligence Ensemble initialized")
    
    def update(self, price: float, volume: float = 0):
        """Update all models with new data."""
        self.price_history.append(price)
        if volume > 0:
            self.volume_history.append(volume)
        
        if len(self.price_history) >= 20:
            self.hmm.update(price, volume)
            
            self.current_regime = self.hmm.get_current_regime()
    
    def detect_regime(self, market_data: Dict[str, Any]) -> str:
        """Detect current market regime."""
        price = market_data.get('price', market_data.get('close', 0))
        volume = market_data.get('volume', 0)
        
        if price > 0:
            self.update(price, volume)
        
        return self.current_regime
    
    def validate(self, signals: Dict[str, Any], market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate signals using ensemble."""
        regime = self.detect_regime(market_data)
        
        validated_signals = signals.copy()
        validated_signals['regime'] = regime
        
        ensemble_votes = []
        
        if self.decision_tree_enabled:
            dt_result = self.decision_tree.predict(market_data)
            if dt_result:
                ensemble_votes.append(dt_result['action'])
                validated_signals['decision_tree'] = dt_result
        
        if self.self_learning_enabled and self.self_learning.model:
            sl_result = self.self_learning.predict(market_data)
            if sl_result:
                ensemble_votes.append(sl_result['action'])
                validated_signals['self_learning'] = sl_result
        
        if self.adaptive_enabled:
            strategy = self.adaptive.select_strategy(regime, market_data)
            validated_signals['recommended_strategy'] = strategy
        
        final_action = self._combine_votes(ensemble_votes, signals.get('action'))
        
        validated_signals['ensemble_action'] = final_action
        validated_signals['confidence'] = self._calculate_confidence(ensemble_votes, final_action)
        
        if self.self_learning_enabled:
            action = signals.get('action')
            if action and action != 'hold':
                self.self_learning.add_experience(
                    market_data, action, 0
                )
                
                if self.self_learning.should_retrain():
                    self.self_learning.retrain()
        
        return validated_signals
    
    def _combine_votes(self, votes: List[str], base_action: str = None) -> str:
        """Combine votes from different models."""
        if not votes:
            return base_action or 'hold'
        
        vote_counts = {}
        for vote in votes:
            vote_counts[vote] = vote_counts.get(vote, 0) + 1
        
        best_vote = max(vote_counts, key=vote_counts.get)
        
        return best_vote
    
    def _calculate_confidence(self, votes: List[str], action: str) -> float:
        """Calculate confidence of ensemble decision."""
        if not votes:
            return 0.5
        
        action_count = votes.count(action)
        return action_count / len(votes)
    
    def get_status(self) -> Dict[str, Any]:
        """Get ensemble status."""
        return {
            'current_regime': self.current_regime,
            'price_history_len': len(self.price_history),
            'hmm': {
                'enabled': self.hmm_enabled,
                'current_regime': self.hmm.get_current_regime()
            },
            'decision_tree': {
                'enabled': self.decision_tree_enabled,
                'is_trained': self.decision_tree.is_trained
            },
            'self_learning': self.self_learning.get_status(),
            'adaptive': self.adaptive.get_performance_report()
        }


def create_ensemble(config: Dict[str, Any] = None) -> IntelligenceEnsemble:
    """Create intelligence ensemble."""
    return IntelligenceEnsemble(config or {})
