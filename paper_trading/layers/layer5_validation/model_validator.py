"""
Layer 5: Model Validation Engine
=================================
Walk-forward testing, Monte Carlo simulations, out-of-sample validation.
Constantly verifies: "Is my edge still valid?"
"""

from typing import Dict, Any, Optional, List, Tuple
import numpy as np
from dataclasses import dataclass
from collections import deque
from loguru import logger


@dataclass
class ValidationResult:
    """Result of model validation"""
    is_valid: bool
    method: str
    metric_name: str
    metric_value: float
    p_value: float
    confidence_interval: Tuple[float, float]
    sample_size: int
    warning: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            'is_valid': self.is_valid,
            'method': self.method,
            'metric_name': self.metric_name,
            'metric_value': self.metric_value,
            'p_value': self.p_value,
            'confidence_interval': self.confidence_interval,
            'sample_size': self.sample_size,
            'warning': self.warning
        }


class ModelValidator:
    """
    Continuously validates model performance:
    - Walk-forward testing
    - Monte Carlo simulations
    - Out-of-sample validation
    - Statistical significance testing
    - Confidence intervals
    """

    def __init__(self, config: Dict[str, Any] = None):
        config = config or {}
        self.walk_forward_window = config.get('walk_forward_window', 100)
        self.oos_ratio = config.get('oos_ratio', 0.3)
        self.monte_carlo_sims = config.get('monte_carlo_sims', 1000)
        self.significance_level = config.get('significance_level', 0.05)
        self.min_samples = config.get('min_samples', 30)

        self._returns: Dict[str, deque] = {}
        self._trades: Dict[str, deque] = {}

        logger.info("ModelValidator initialized")

    def _get_returns(self, asset: str) -> deque:
        if asset not in self._returns:
            self._returns[asset] = deque(maxlen=2000)
        return self._returns[asset]

    def add_trade(self, asset: str, return_pct: float):
        """Record a trade result"""
        self._get_returns(asset).append(return_pct)

    def walk_forward_validation(self, asset: str) -> ValidationResult:
        """Walk-forward test: train on past, test on recent"""
        returns = list(self._get_returns(asset))

        if len(returns) < self.walk_forward_window * 2:
            return ValidationResult(
                is_valid=True, method='walk_forward', metric_name='sharpe',
                metric_value=0.0, p_value=1.0, confidence_interval=(0.0, 0.0),
                sample_size=len(returns), warning='Insufficient data'
            )

        train = returns[-self.walk_forward_window * 2:-self.walk_forward_window]
        test = returns[-self.walk_forward_window:]

        train_sharpe = np.mean(train) / (np.std(train) + 1e-8)
        test_sharpe = np.mean(test) / (np.std(test) + 1e-8)

        degradation = (train_sharpe - test_sharpe) / (abs(train_sharpe) + 1e-8)

        p_value = self._permutation_test(train, test, n_permutations=500)

        is_valid = p_value > self.significance_level and degradation < 0.5

        ci = self._bootstrap_ci(test, metric='sharpe')

        warning = ""
        if degradation > 0.3:
            warning = f"Performance degrading ({degradation:.1%})"
        elif p_value < self.significance_level:
            warning = f"Statistically significant difference (p={p_value:.3f})"

        return ValidationResult(
            is_valid=is_valid,
            method='walk_forward',
            metric_name='sharpe',
            metric_value=test_sharpe,
            p_value=p_value,
            confidence_interval=ci,
            sample_size=len(test),
            warning=warning
        )

    def monte_carlo_validation(self, asset: str) -> ValidationResult:
        """Monte Carlo simulation to test if returns are non-random"""
        returns = list(self._get_returns(asset))

        if len(returns) < self.min_samples:
            return ValidationResult(
                is_valid=True, method='monte_carlo', metric_name='mean',
                metric_value=0.0, p_value=1.0, confidence_interval=(0.0, 0.0),
                sample_size=len(returns), warning='Insufficient data'
            )

        actual_mean = np.mean(returns)
        actual_sharpe = actual_mean / (np.std(returns) + 1e-8)

        random_sharpes = []
        for _ in range(self.monte_carlo_sims):
            shuffled = np.random.permutation(returns)
            r_sharpe = np.mean(shuffled) / (np.std(shuffled) + 1e-8)
            random_sharpes.append(r_sharpe)

        p_value = np.mean([s >= actual_sharpe for s in random_sharpes])

        is_valid = p_value < self.significance_level

        ci_lower = float(np.percentile(random_sharpes, 2.5))
        ci_upper = float(np.percentile(random_sharpes, 97.5))

        warning = ""
        if not is_valid:
            warning = "Returns not statistically different from random"

        return ValidationResult(
            is_valid=is_valid,
            method='monte_carlo',
            metric_name='sharpe_vs_random',
            metric_value=actual_sharpe,
            p_value=p_value,
            confidence_interval=(ci_lower, ci_upper),
            sample_size=len(returns),
            warning=warning
        )

    def out_of_sample_validation(self, asset: str) -> ValidationResult:
        """Out-of-sample validation"""
        returns = list(self._get_returns(asset))

        if len(returns) < self.min_samples * 2:
            return ValidationResult(
                is_valid=True, method='out_of_sample', metric_name='mean',
                metric_value=0.0, p_value=1.0, confidence_interval=(0.0, 0.0),
                sample_size=len(returns), warning='Insufficient data'
            )

        split = int(len(returns) * (1 - self.oos_ratio))
        in_sample = returns[:split]
        out_sample = returns[split:]

        is_mean = np.mean(in_sample)
        oos_mean = np.mean(out_sample)
        is_sharpe = np.mean(in_sample) / (np.std(in_sample) + 1e-8)
        oos_sharpe = oos_mean / (np.std(out_sample) + 1e-8)

        if is_mean != 0:
            stability = 1 - abs(oos_mean - is_mean) / abs(is_mean)
        else:
            stability = 1.0 if oos_mean >= 0 else 0.0

        p_value = self._t_test(oos_mean, np.std(out_sample), len(out_sample))

        is_valid = stability > 0.3 and oos_mean > 0

        ci = self._bootstrap_ci(out_sample, metric='mean')

        warning = ""
        if stability < 0.5:
            warning = f"Low out-of-sample stability ({stability:.2f})"

        return ValidationResult(
            is_valid=is_valid,
            method='out_of_sample',
            metric_name='stability',
            metric_value=stability,
            p_value=p_value,
            confidence_interval=ci,
            sample_size=len(out_sample),
            warning=warning
        )

    def comprehensive_validation(self, asset: str) -> Dict[str, Any]:
        """Run all validation methods"""
        wf = self.walk_forward_validation(asset)
        mc = self.monte_carlo_validation(asset)
        oos = self.out_of_sample_validation(asset)

        all_valid = wf.is_valid and mc.is_valid and oos.is_valid

        if not all_valid:
            failed = []
            if not wf.is_valid: failed.append(wf.method)
            if not mc.is_valid: failed.append(mc.method)
            if not oos.is_valid: failed.append(oos.method)
            logger.warning(f"Validation failed: {failed}")

        return {
            'valid': all_valid,
            'walk_forward': wf.to_dict(),
            'monte_carlo': mc.to_dict(),
            'out_of_sample': oos.to_dict(),
            'recommendation': 'reduce_risk' if not all_valid else 'normal'
        }

    def _permutation_test(self, sample_a: List[float], sample_b: List[float],
                          n_permutations: int = 500) -> float:
        actual_diff = np.mean(sample_b) - np.mean(sample_a)
        combined = np.concatenate([sample_a, sample_b])
        count = 0
        for _ in range(n_permutations):
            perm = np.random.permutation(combined)
            perm_diff = np.mean(perm[len(sample_a):]) - np.mean(perm[:len(sample_a)])
            if abs(perm_diff) >= abs(actual_diff):
                count += 1
        return count / n_permutations

    def _t_test(self, mean: float, std: float, n: int) -> float:
        if std == 0 or n < 2:
            return 1.0
        t_stat = mean / (std / np.sqrt(n))
        from scipy import stats as scipy_stats
        return 2 * (1 - scipy_stats.t.cdf(abs(t_stat), n - 1))

    def _bootstrap_ci(self, data: List[float], metric: str = 'mean',
                       n_bootstrap: int = 500, alpha: float = 0.05) -> Tuple[float, float]:
        if len(data) < 10:
            return (0.0, 0.0)
        bootstrap_values = []
        for _ in range(n_bootstrap):
            sample = np.random.choice(data, size=len(data), replace=True)
            if metric == 'mean':
                bootstrap_values.append(np.mean(sample))
            elif metric == 'sharpe':
                bootstrap_values.append(np.mean(sample) / (np.std(sample) + 1e-8))
        return (float(np.percentile(bootstrap_values, 100 * alpha / 2)),
                float(np.percentile(bootstrap_values, 100 * (1 - alpha / 2))))

    def get_status(self) -> Dict[str, Any]:
        return {
            'walk_forward_window': self.walk_forward_window,
            'oos_ratio': self.oos_ratio,
            'monte_carlo_sims': self.monte_carlo_sims,
            'assets_tracked': len(self._returns)
        }
