"""
Layer 4: Hidden Markov Model (HMM) Regime Detection
Detects market regimes: bull, bear, volatile, sideways
"""

from typing import Dict, Any, List, Optional
import numpy as np
from loguru import logger

try:
    from hmmlearn import hmm
    HMM_AVAILABLE = True
except ImportError:
    HMM_AVAILABLE = False


REGIME_NAMES = ['bull', 'bear', 'sideways', 'volatile']


class HMMRegimeDetector:
    """Hidden Markov Model for market regime detection."""
    
    def __init__(self, config: Dict[str, Any]):
        self.n_states = config.get('n_states', 4)
        self.lookback_bars = config.get('lookback_bars', 100)
        
        self.model = None
        self.price_history: List[float] = []
        self.volume_history: List[float] = []
        
        self.current_regime = 'sideways'
        
        if HMM_AVAILABLE:
            self._init_model()
    
    def _init_model(self):
        """Initialize HMM model."""
        try:
            self.model = hmm.GaussianHMM(
                n_components=self.n_states,
                covariance_type="full",
                n_iter=100,
                random_state=42
            )
            logger.info(f"HMM model initialized with {self.n_states} states")
        except Exception as e:
            logger.error(f"Failed to initialize HMM: {e}")
    
    def update(self, price: float, volume: float = 0) -> str:
        """Update with new price/volume and detect regime."""
        self.price_history.append(price)
        if volume > 0:
            self.volume_history.append(volume)
        
        if len(self.price_history) < self.lookback_bars:
            return self._estimate_regime_simple()
        
        return self.detect_regime()
    
    def detect_regime(self) -> str:
        """Detect current market regime."""
        if not HMM_AVAILABLE or self.model is None:
            return self._estimate_regime_simple()
        
        if len(self.price_history) < self.lookback_bars:
            return self._estimate_regime_simple()
        
        try:
            features = self._extract_features()
            
            hidden_states = self.model.predict(features)
            
            current_state = hidden_states[-1]
            
            self.current_regime = self._map_state_to_regime(current_state, features)
            
            return self.current_regime
            
        except Exception as e:
            logger.error(f"HMM detection error: {e}")
            return self._estimate_regime_simple()
    
    def _extract_features(self) -> np.ndarray:
        """Extract features from price history."""
        n = min(len(self.price_history), self.lookback_bars)
        prices = np.array(self.price_history[-n:])
        
        returns = np.diff(prices) / prices[:-1]
        volatility = np.std(returns[-20:]) if len(returns) >= 20 else 0
        
        features = np.column_stack([
            prices[-n:],
            np.arange(n),
            np.full(n, volatility)
        ])
        
        return features
    
    def _estimate_regime_simple(self) -> str:
        """Simple regime estimation without HMM."""
        if len(self.price_history) < 20:
            return 'sideways'
        
        prices = self.price_history[-20:]
        returns = np.diff(prices) / prices[:-1]
        
        trend = (prices[-1] - prices[0]) / prices[0]
        volatility = np.std(returns)
        
        if volatility > 0.03:
            return 'volatile'
        elif trend > 0.02:
            return 'bull'
        elif trend < -0.02:
            return 'bear'
        else:
            return 'sideways'
    
    def _map_state_to_regime(self, state: int, features: np.ndarray) -> str:
        """Map HMM state to regime name."""
        returns = np.diff(features[:, 0]) / features[0, :-1]
        
        if len(returns) < 20:
            return REGIME_NAMES[state % len(REGIME_NAMES)]
        
        recent_return = np.mean(returns[-10:])
        recent_volatility = np.std(returns[-20:])
        
        if recent_volatility > 0.03:
            return 'volatile'
        elif recent_return > 0.002:
            return 'bull'
        elif recent_return < -0.002:
            return 'bear'
        else:
            return 'sideways'
    
    def train(self, prices: List[float], volumes: List[float] = None):
        """Train HMM on historical data."""
        if not HMM_AVAILABLE or self.model is None:
            logger.warning("HMM not available, skipping training")
            return
        
        if len(prices) < 100:
            logger.warning("Not enough data for training")
            return
        
        self.price_history = prices
        if volumes:
            self.volume_history = volumes
        
        try:
            features = self._extract_features()
            self.model.fit(features)
            logger.info("HMM model trained successfully")
        except Exception as e:
            logger.error(f"HMM training failed: {e}")
    
    def get_current_regime(self) -> str:
        """Get current detected regime."""
        return self.current_regime
    
    def get_regime_probabilities(self) -> Dict[str, float]:
        """Get probability distribution over regimes."""
        if not HMM_AVAILABLE or self.model is None or len(self.price_history) < self.lookback_bars:
            return {regime: 0.25 for regime in REGIME_NAMES}
        
        try:
            features = self._extract_features()
            probs = self.model.predict_proba(features)
            
            return {
                regime: float(probs[-1, i]) 
                for i, regime in enumerate(REGIME_NAMES)
            }
        except:
            return {regime: 0.25 for regime in REGIME_NAMES}


def detect_market_regime(price: float, volume: float = 0, 
                         history: List[float] = None) -> str:
    """Convenience function to detect regime."""
    detector = HMMRegimeDetector({'n_states': 4, 'lookback_bars': 100})
    
    if history:
        for p in history:
            detector.update(p)
    
    return detector.update(price, volume)
