"""
Layer 4: Uncertainty Model
==========================
Probabilistic predictions with mean ± variance.
All predictions must include uncertainty estimates.
"""

from typing import Dict, Any, Optional, List, Tuple
import numpy as np
from collections import deque
from dataclasses import dataclass
from loguru import logger


@dataclass
class UncertainPrediction:
    """Prediction with uncertainty bounds"""
    mean: float
    variance: float
    confidence: float  # 0-1
    lower_bound: float
    upper_bound: float
    sample_size: int

    @property
    def std(self) -> float:
        return np.sqrt(self.variance)

    @property
    def sharpe(self) -> float:
        if self.std == 0:
            return 0.0
        return self.mean / self.std

    def to_dict(self) -> Dict[str, Any]:
        return {
            'mean': self.mean,
            'variance': self.variance,
            'std': self.std,
            'confidence': self.confidence,
            'lower_bound': self.lower_bound,
            'upper_bound': self.upper_bound,
            'sharpe': self.sharpe,
            'sample_size': self.sample_size
        }


class UncertaintyModel:
    """
    Computes uncertainty-aware predictions for all signals.
    Rules:
    - High uncertainty -> reduce size
    - Low uncertainty + high expectancy -> increase size
    """

    def __init__(self, config: Dict[str, Any] = None):
        config = config or {}
        self.confidence_window = config.get('confidence_window', 50)
        self.min_samples = config.get('min_samples', 10)
        self.confidence_level = config.get('confidence_level', 0.95)
        self.uncertainty_discount = config.get('uncertainty_discount', 0.5)

        self._return_history: Dict[str, deque] = {}
        self._prediction_history: Dict[str, deque] = {}
        self._calibration_data: deque = deque(maxlen=1000)

        logger.info("UncertaintyModel initialized")

    def _get_history(self, asset: str) -> deque:
        if asset not in self._return_history:
            self._return_history[asset] = deque(maxlen=self.confidence_window)
        return self._return_history[asset]

    def _get_pred_history(self, asset: str) -> deque:
        if asset not in self._prediction_history:
            self._prediction_history[asset] = deque(maxlen=self.confidence_window)
        return self._prediction_history[asset]

    def add_return(self, asset: str, return_pct: float):
        """Add observed return for uncertainty calibration"""
        self._get_history(asset).append(return_pct)

    def predict(self, asset: str, features: Dict[str, Any],
                regime: str = 'sideways') -> UncertainPrediction:
        """
        Generate prediction with uncertainty bounds.
        Uses historical returns + Bayesian updating.
        """
        history = self._get_history(asset)

        if len(history) < self.min_samples:
            return UncertainPrediction(
                mean=0.0,
                variance=1.0,
                confidence=0.0,
                lower_bound=-1.0,
                upper_bound=1.0,
                sample_size=len(history)
            )

        returns = np.array(history)

        mean = float(np.mean(returns))
        variance = float(np.var(returns))
        std = float(np.std(returns))

        regime_multiplier = {
            'trending': 0.8,
            'volatile': 1.5,
            'sideways': 1.0,
            'bull': 0.9,
            'bear': 1.2
        }.get(regime, 1.0)

        adjusted_variance = variance * regime_multiplier

        n = len(returns)
        data_confidence = min(1.0, n / (n + 20))
        sharpe_confidence = max(0.0, 1.0 / (1.0 + abs(std / (abs(mean) + 1e-8))))
        confidence = data_confidence * sharpe_confidence

        z_score = 1.96 if self.confidence_level == 0.95 else 2.576
        margin = z_score * np.sqrt(adjusted_variance / n)

        lower = mean - margin
        upper = mean + margin

        prediction = UncertainPrediction(
            mean=mean,
            variance=adjusted_variance,
            confidence=max(0.0, min(1.0, confidence)),
            lower_bound=lower,
            upper_bound=upper,
            sample_size=n
        )

        self._get_pred_history(asset).append(prediction.mean)

        return prediction

    def adjust_position_size(self, base_size: float,
                              prediction: UncertainPrediction) -> float:
        """
        Adjust position size based on uncertainty.
        High uncertainty -> reduce size
        Low uncertainty + high expectancy -> increase size
        """
        if prediction.sample_size < self.min_samples:
            return base_size * 0.2

        uncertainty_factor = 1.0 - (prediction.std * self.uncertainty_discount)
        uncertainty_factor = max(0.1, min(1.5, uncertainty_factor))

        expectancy_factor = 1.0 + prediction.sharpe * 0.1
        expectancy_factor = max(0.5, min(2.0, expectancy_factor))

        adjusted_size = base_size * uncertainty_factor * expectancy_factor * prediction.confidence

        return max(0.0, adjusted_size)

    def get_calibration(self, asset: str) -> Dict[str, Any]:
        """Check if predictions are well-calibrated"""
        preds = self._get_pred_history(asset)
        history = self._get_history(asset)

        if len(preds) < self.min_samples or len(history) < self.min_samples:
            return {'calibrated': False, 'reason': 'Insufficient data'}

        pred_array = np.array(list(preds))
        actual_array = np.array(list(history))[-len(pred_array):]

        if len(actual_array) < len(pred_array):
            actual_array = np.pad(actual_array, (0, len(pred_array) - len(actual_array)))

        pred_array = pred_array[:len(actual_array)]

        mae = float(np.mean(np.abs(pred_array - actual_array)))
        mape = float(np.mean(np.abs((actual_array - pred_array) / (actual_array + 1e-8))))

        return {
            'calibrated': mae < 0.05,
            'mae': mae,
            'mape': mape,
            'sample_size': len(actual_array)
        }

    def get_status(self) -> Dict[str, Any]:
        return {
            'assets_tracked': len(self._return_history),
            'confidence_window': self.confidence_window,
            'min_samples': self.min_samples,
            'confidence_level': self.confidence_level
        }
