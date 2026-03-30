"""
Layer 3: Signal Aggregator
Combines multiple signals into unified trading decision.
"""

from typing import Dict, Any, List, Optional
from loguru import logger

from .ma_crossover import MACrossoverStrategy, EMACrossoverStrategy
from .rsi import RSIStrategy


class SignalAggregator:
    """Aggregates signals from multiple strategies."""
    
    def __init__(self):
        self.strategies = {
            'ma_crossover': MACrossoverStrategy(fast_window=10, slow_window=30),
            'ema_crossover': EMACrossoverStrategy(fast_window=10, slow_window=30),
            'rsi': RSIStrategy(period=14)
        }
        
        self.weights = {
            'ma_crossover': 0.4,
            'ema_crossover': 0.3,
            'rsi': 0.3
        }
        
        self.enabled_strategies = ['ma_crossover', 'rsi']
    
    def generate(self, market_data: Dict[str, Any], 
                 strategy_config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate aggregated signal from market data."""
        price = market_data.get('close', market_data.get('price', 0))
        
        if price == 0:
            return {'action': None, 'reason': 'No price data'}
        
        signals = {}
        
        for name in self.enabled_strategies:
            if name in self.strategies:
                result = self.strategies[name].update(price)
                if result:
                    signals[name] = result
        
        if not signals:
            return {'action': None, 'reason': 'No signals generated'}
        
        return self._combine_signals(signals)
    
    def _combine_signals(self, signals: Dict[str, Any]) -> Dict[str, Any]:
        """Combine individual signals into final decision."""
        buy_score = 0.0
        sell_score = 0.0
        total_weight = 0.0
        
        for name, signal_data in signals.items():
            weight = self.weights.get(name, 0.0)
            signal = signal_data.get('signal')
            
            if signal == 'buy':
                buy_score += weight
                total_weight += weight
            elif signal == 'sell':
                sell_score += weight
                total_weight += weight
        
        if total_weight == 0:
            return {'action': None, 'reason': 'No consensus', 'signals': signals}
        
        buy_ratio = buy_score / total_weight if total_weight > 0 else 0
        sell_ratio = sell_score / total_weight if total_weight > 0 else 0
        
        threshold = 0.6
        
        if buy_ratio >= threshold:
            return {
                'action': 'buy',
                'confidence': buy_ratio,
                'signals': signals,
                'reason': f'Buy consensus: {buy_ratio:.1%}'
            }
        elif sell_ratio >= threshold:
            return {
                'action': 'sell',
                'confidence': sell_ratio,
                'signals': signals,
                'reason': f'Sell consensus: {sell_ratio:.1%}'
            }
        
        return {
            'action': None,
            'confidence': max(buy_ratio, sell_ratio),
            'signals': signals,
            'reason': 'No consensus'
        }
    
    def enable_strategy(self, name: str):
        """Enable a strategy."""
        if name in self.strategies and name not in self.enabled_strategies:
            self.enabled_strategies.append(name)
    
    def disable_strategy(self, name: str):
        """Disable a strategy."""
        if name in self.enabled_strategies:
            self.enabled_strategies.remove(name)
    
    def set_weight(self, name: str, weight: float):
        """Set weight for a strategy."""
        if name in self.weights:
            self.weights[name] = weight
    
    def reset_all(self):
        """Reset all strategies."""
        for strategy in self.strategies.values():
            strategy.reset()
    
    def get_signal_status(self) -> Dict[str, Any]:
        """Get status of all strategies."""
        status = {
            'enabled': self.enabled_strategies.copy(),
            'weights': self.weights.copy()
        }
        
        for name, strategy in self.strategies.items():
            if hasattr(strategy, 'rsi'):
                status[name] = {'rsi': strategy.get_current_rsi()}
            elif hasattr(strategy, 'fast_ma'):
                status[name] = {
                    'fast_ma': strategy.fast_ma,
                    'slow_ma': strategy.slow_ma
                }
        
        return status


aggregator = SignalAggregator()


def generate_signal(market_data: Dict[str, Any], 
                    strategy_config: Dict[str, Any] = None) -> Dict[str, Any]:
    """Convenience function to generate signal."""
    return aggregator.generate(market_data, strategy_config or {})
