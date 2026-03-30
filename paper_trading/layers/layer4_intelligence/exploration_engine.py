"""
Layer 4: Exploration Engine
===========================
Adaptive epsilon-greedy exploration for discovering new edges.
Increases exploration when performance degrades.
"""

from typing import Dict, Any, Optional, List
import numpy as np
from collections import deque
from dataclasses import dataclass
from loguru import logger


@dataclass
class ExplorationAction:
    """Result of exploration decision"""
    should_explore: bool
    exploration_rate: float
    action: str  # 'exploit', 'explore', 'random'
    reason: str
    test_size_multiplier: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            'should_explore': self.should_explore,
            'exploration_rate': self.exploration_rate,
            'action': self.action,
            'reason': self.reason,
            'test_size_multiplier': self.test_size_multiplier
        }


class ExplorationEngine:
    """
    Adaptive epsilon-greedy exploration.
    - Increases exploration when performance degrades
    - Decreases when stable
    - Exploration uses smaller capital
    - Tracks exploration success rate
    """

    def __init__(self, config: Dict[str, Any] = None):
        config = config or {}
        self.base_epsilon = config.get('base_epsilon', 0.15)
        self.min_epsilon = config.get('min_epsilon', 0.02)
        self.max_epsilon = config.get('max_epsilon', 0.40)
        self.epsilon_decay = config.get('epsilon_decay', 0.995)
        self.performance_window = config.get('performance_window', 50)
        self.exploration_size_factor = config.get('exploration_size_factor', 0.3)
        self.degradation_threshold = config.get('degradation_threshold', -0.02)

        self.epsilon = self.base_epsilon
        self._performance_history: deque = deque(maxlen=self.performance_window)
        self._exploration_history: List[Dict[str, Any]] = []
        self._exploration_returns: deque = deque(maxlen=200)
        self._exploit_returns: deque = deque(maxlen=200)
        self._steps = 0

        logger.info(f"ExplorationEngine initialized (epsilon={self.base_epsilon})")

    def should_explore(self) -> ExplorationAction:
        """Decide whether to explore or exploit"""
        self._steps += 1

        perf = self._get_recent_performance()
        if perf < self.degradation_threshold:
            self.epsilon = min(self.max_epsilon, self.epsilon * 1.3)
            return ExplorationAction(
                should_explore=True,
                exploration_rate=self.epsilon,
                action='explore',
                reason=f'Performance degraded ({perf:.4f})',
                test_size_multiplier=self.exploration_size_factor
            )

        if len(self._exploration_returns) > 30 and len(self._exploit_returns) > 30:
            exp_mean = np.mean(list(self._exploration_returns))
            expl_mean = np.mean(list(self._exploit_returns))
            if exp_mean > expl_mean:
                self.epsilon = min(self.max_epsilon, self.epsilon * 1.1)
                return ExplorationAction(
                    should_explore=True,
                    exploration_rate=self.epsilon,
                    action='explore',
                    reason=f'Exploration outperforming ({exp_mean:.4f} > {expl_mean:.4f})',
                    test_size_multiplier=self.exploration_size_factor * 1.5
                )

        if np.random.random() < self.epsilon:
            return ExplorationAction(
                should_explore=True,
                exploration_rate=self.epsilon,
                action='random',
                reason='Epsilon-greedy random',
                test_size_multiplier=self.exploration_size_factor
            )

        self.epsilon = max(self.min_epsilon, self.epsilon * self.epsilon_decay)
        return ExplorationAction(
            should_explore=False,
            exploration_rate=self.epsilon,
            action='exploit',
            reason='Normal exploitation',
            test_size_multiplier=1.0
        )

    def record_outcome(self, action: str, return_pct: float, exploration: bool):
        """Record the outcome of an exploration vs exploit action"""
        self._performance_history.append(return_pct)

        if exploration:
            self._exploration_returns.append(return_pct)
        else:
            self._exploit_returns.append(return_pct)

        self._exploration_history.append({
            'action': action,
            'return': return_pct,
            'exploration': exploration,
            'step': self._steps,
            'epsilon': self.epsilon
        })

    def get_exploration_stats(self) -> Dict[str, Any]:
        """Get exploration performance statistics"""
        exp_returns = list(self._exploration_returns)
        expl_returns = list(self._exploit_returns)

        stats = {
            'epsilon': self.epsilon,
            'steps': self._steps,
            'exploration_count': len(exp_returns),
            'exploitation_count': len(expl_returns)
        }

        if len(exp_returns) > 5:
            stats['exploration_mean'] = float(np.mean(exp_returns))
            stats['exploration_std'] = float(np.std(exp_returns))
            stats['exploration_sharpe'] = stats['exploration_mean'] / (stats['exploration_std'] + 1e-8)
        else:
            stats['exploration_mean'] = 0.0
            stats['exploration_std'] = 0.0
            stats['exploration_sharpe'] = 0.0

        if len(expl_returns) > 5:
            stats['exploitation_mean'] = float(np.mean(expl_returns))
            stats['exploitation_std'] = float(np.std(expl_returns))
            stats['exploitation_sharpe'] = stats['exploitation_mean'] / (stats['exploitation_std'] + 1e-8)
        else:
            stats['exploitation_mean'] = 0.0
            stats['exploitation_std'] = 0.0
            stats['exploitation_sharpe'] = 0.0

        return stats

    def _get_recent_performance(self) -> float:
        if len(self._performance_history) < 10:
            return 0.0
        recent = list(self._performance_history)[-20:]
        return float(np.mean(recent))

    def get_status(self) -> Dict[str, Any]:
        return {
            'epsilon': self.epsilon,
            'steps': self._steps,
            'exploration_trades': len(self._exploration_returns),
            'exploit_trades': len(self._exploit_returns)
        }
