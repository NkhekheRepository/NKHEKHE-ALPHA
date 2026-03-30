"""
Layer 2: Portfolio Optimization Engine
Mean-variance optimization, risk-parity, and Kelly criterion allocation.
"""

from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from loguru import logger


class PortfolioOptimizer:
    """Portfolio optimization with multiple strategies."""
    
    def __init__(self, config: Dict[str, Any]):
        self.method = config.get('optimization_method', 'risk_parity')
        self.max_position_pct = config.get('max_position_pct', 25)
        self.min_position_pct = config.get('min_position_pct', 2)
        self.max_leverage = config.get('max_leverage', 5)
        self.target_volatility = config.get('target_volatility', 0.15)
        self.kelly_fraction = config.get('kelly_fraction', 0.25)
        
        self.returns_history: Dict[str, List[float]] = {}
        self.lookback = config.get('returns_lookback', 100)
    
    def add_return(self, asset: str, return_pct: float):
        """Add return observation for optimization."""
        if asset not in self.returns_history:
            self.returns_history[asset] = []
        
        self.returns_history[asset].append(return_pct)
        
        if len(self.returns_history[asset]) > self.lookback:
            self.returns_history[asset] = self.returns_history[asset][-self.lookback:]
    
    def calculate_returns_stats(self) -> Dict[str, Dict[str, float]]:
        """Calculate mean and std dev for each asset."""
        stats = {}
        
        for asset, returns in self.returns_history.items():
            if len(returns) >= 20:
                stats[asset] = {
                    'mean': np.mean(returns),
                    'std': np.std(returns),
                    'sharpe': np.mean(returns) / np.std(returns) if np.std(returns) > 0 else 0
                }
        
        return stats
    
    def calculate_covariance_matrix(self) -> Optional[np.ndarray]:
        """Calculate covariance matrix of returns."""
        assets = list(self.returns_history.keys())
        
        if len(assets) < 2:
            return None
        
        min_length = min(len(self.returns_history[a]) for a in assets)
        
        returns_matrix = np.array([
            self.returns_history[a][:min_length] 
            for a in assets
        ])
        
        try:
            cov_matrix = np.cov(returns_matrix)
            return cov_matrix
        except Exception as e:
            logger.error(f"Error calculating covariance: {e}")
            return None
    
    def mean_variance_optimize(self, expected_returns: np.ndarray, 
                                cov_matrix: np.ndarray) -> Optional[np.ndarray]:
        """Mean-variance optimization (Markowitz)."""
        n = len(expected_returns)
        
        try:
            ones = np.ones(n)
            inv_cov = np.linalg.inv(cov_matrix + 1e-8 * np.eye(n))
            
            weights = inv_cov @ expected_returns
            weights = weights / (ones @ weights)
            
            weights = np.clip(weights, 0, 1)
            weights = weights / weights.sum()
            
            return weights
        except Exception as e:
            logger.error(f"Mean-variance optimization failed: {e}")
            return None
    
    def risk_parity_optimize(self, cov_matrix: np.ndarray) -> Optional[np.ndarray]:
        """Risk parity optimization - equal risk contribution."""
        n = cov_matrix.shape[0]
        
        try:
            inv_cov = np.linalg.inv(cov_matrix + 1e-8 * np.eye(n))
            ones = np.ones(n)
            
            marginal_risk = inv_cov @ ones
            risk_contrib = marginal_risk / np.sum(marginal_risk)
            
            weights = risk_contrib / np.sum(risk_contrib)
            
            return weights
        except Exception as e:
            logger.error(f"Risk parity optimization failed: {e}")
            return None
    
    def kelly_criterion(self, stats: Dict[str, Dict[str, float]], 
                        capital: float) -> Dict[str, float]:
        """Calculate Kelly criterion position sizes."""
        allocations = {}
        
        for asset, stat in stats.items():
            win_rate = 0.5
            if stat['mean'] > 0:
                win_rate = min(0.9, 0.5 + stat['sharpe'] * 0.1)
            
            avg_win = stat['mean']
            avg_loss = abs(stat['std'])
            
            if avg_loss > 0:
                win_loss_ratio = avg_win / avg_loss
                kelly = (win_rate * win_loss_ratio - (1 - win_rate)) / win_loss_ratio
                kelly = max(0, kelly * self.kelly_fraction)
            else:
                kelly = 0
            
            allocation_pct = min(kelly * 100, self.max_position_pct)
            allocations[asset] = max(allocation_pct, self.min_position_pct)
        
        total = sum(allocations.values())
        if total > 100:
            allocations = {k: v / total * 100 for k, v in allocations.items()}
        
        return allocations
    
    def optimize(self, assets: List[str], capital: float,
                 signals: Dict[str, Dict[str, Any]]) -> Dict[str, float]:
        """Run portfolio optimization."""
        if len(assets) < 1:
            return {}
        
        for asset in assets:
            if asset not in self.returns_history or len(self.returns_history[asset]) < 20:
                return {a: capital / len(assets) for a in assets}
        
        stats = self.calculate_returns_stats()
        
        if not stats:
            return {a: capital / len(assets) for a in assets}
        
        assets_with_stats = [a for a in assets if a in stats]
        
        if len(assets_with_stats) < 2:
            return {assets_with_stats[0]: capital} if assets_with_stats else {}
        
        if self.method == 'mean_variance':
            expected = np.array([stats[a]['mean'] for a in assets_with_stats])
            cov = self.calculate_covariance_matrix()
            
            if cov is None:
                return {a: capital / len(assets_with_stats) for a in assets_with_stats}
            
            weights = self.mean_variance_optimize(expected, cov)
            
        elif self.method == 'risk_parity':
            cov = self.calculate_covariance_matrix()
            
            if cov is None:
                return {a: capital / len(assets_with_stats) for a in assets_with_stats}
            
            weights = self.risk_parity_optimize(cov)
            
        else:
            allocations = self.kelly_criterion(stats, capital)
            return allocations
        
        if weights is None:
            return {a: capital / len(assets_with_stats) for a in assets_with_stats}
        
        allocations = {}
        for i, asset in enumerate(assets_with_stats):
            weight = weights[i]
            
            if asset in signals:
                confidence = signals[asset].get('confidence', 0.5)
                weight = weight * confidence
            
            weight = max(self.min_position_pct / 100, min(weight, self.max_position_pct / 100))
            allocations[asset] = weight * capital
        
        total = sum(allocations.values())
        if total > capital:
            scale = capital / total
            allocations = {k: v * scale for k, v in allocations.items()}
        
        return allocations
    
    def get_efficient_frontier(self, assets: List[str], 
                                n_points: int = 10) -> List[Tuple[float, float]]:
        """Calculate efficient frontier points."""
        stats = self.calculate_returns_stats()
        
        if not stats:
            return []
        
        cov = self.calculate_covariance_matrix()
        if cov is None:
            return []
        
        points = []
        
        for i in range(n_points):
            target_vol = (i + 1) * self.target_volatility / n_points
            
            expected = np.array([stats[a]['mean'] for a in assets])
            cov_matrix = cov
            
            try:
                inv_cov = np.linalg.inv(cov_matrix + 1e-8 * np.eye(len(assets)))
                weights = inv_cov @ expected
                weights = weights / np.sum(weights)
                
                portfolio_return = np.dot(weights, expected)
                portfolio_vol = np.sqrt(weights @ cov_matrix @ weights)
                
                points.append((portfolio_vol, portfolio_return))
            except:
                continue
        
        return points
    
    def get_status(self) -> Dict[str, Any]:
        """Get optimizer status."""
        return {
            'method': self.method,
            'assets_tracked': len(self.returns_history),
            'max_position_pct': self.max_position_pct,
            'max_leverage': self.max_leverage,
            'kelly_fraction': self.kelly_fraction
        }
