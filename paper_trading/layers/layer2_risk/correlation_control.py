"""
Layer 2: Correlation Control Engine
Computes rolling correlation matrix and reduces exposure to highly correlated assets.
"""

from typing import Dict, List, Any, Optional
import numpy as np
from collections import deque
from loguru import logger


class CorrelationControl:
    """Manages correlation risk between assets."""
    
    def __init__(self, config: Dict[str, Any]):
        self.max_correlation = config.get('max_correlation', 0.7)
        self.lookback_period = config.get('correlation_lookback', 50)
        self.min_correlation_assets = config.get('min_correlation_assets', 3)
        self.correlation_window = deque(maxlen=self.lookback_period)
        self.price_history: Dict[str, deque] = {}
        self.correlation_matrix: Optional[np.ndarray] = None
        self.assets: List[str] = []
    
    def add_price(self, asset: str, price: float, timestamp: float):
        """Add price observation for correlation calculation."""
        if asset not in self.price_history:
            self.price_history[asset] = deque(maxlen=self.lookback_period)
            if asset not in self.assets:
                self.assets.append(asset)
        
        self.price_history[asset].append((price, timestamp))
    
    def calculate_returns_matrix(self) -> Optional[np.ndarray]:
        """Calculate returns matrix for correlation computation."""
        if len(self.assets) < 2:
            return None
        
        returns_data = []
        valid_assets = []
        
        for asset in self.assets:
            if asset in self.price_history and len(self.price_history[asset]) >= self.lookback_period:
                prices = [p for p, _ in self.price_history[asset]]
                if len(prices) >= 2:
                    returns = np.diff(prices) / prices[:-1]
                    returns_data.append(returns)
                    valid_assets.append(asset)
        
        if len(returns_data) < 2:
            return None
        
        min_length = min(len(r) for r in returns_data)
        returns_data = [r[:min_length] for r in returns_data]
        
        self.assets = valid_assets
        return np.array(returns_data)
    
    def compute_correlation_matrix(self) -> Optional[np.ndarray]:
        """Compute rolling correlation matrix between assets."""
        returns_matrix = self.calculate_returns_matrix()
        
        if returns_matrix is None or returns_matrix.shape[0] < 2:
            return None
        
        try:
            self.correlation_matrix = np.corrcoef(returns_matrix)
            return self.correlation_matrix
        except Exception as e:
            logger.error(f"Error computing correlation matrix: {e}")
            return None
    
    def get_asset_correlations(self, asset: str) -> Dict[str, float]:
        """Get correlations for a specific asset with all others."""
        if self.correlation_matrix is None or asset not in self.assets:
            return {}
        
        try:
            idx = self.assets.index(asset)
            correlations = {}
            for i, other_asset in enumerate(self.assets):
                if i != idx:
                    correlations[other_asset] = float(self.correlation_matrix[idx, i])
            return correlations
        except Exception as e:
            logger.error(f"Error getting correlations for {asset}: {e}")
            return {}
    
    def check_correlation_risk(self, new_asset: str, current_positions: Dict[str, Any]) -> Dict[str, Any]:
        """Check if adding new asset creates correlation risk."""
        if self.correlation_matrix is None:
            return {'allowed': True, 'reason': 'Insufficient data for correlation'}
        
        high_corr_assets = []
        max_corr = 0.0
        
        for asset, position in current_positions.items():
            if asset == new_asset:
                continue
            
            asset_corrs = self.get_asset_correlations(asset)
            if new_asset in asset_corrs:
                corr = asset_corrs[new_asset]
                if abs(corr) > self.max_correlation:
                    high_corr_assets.append((asset, corr))
                max_corr = max(max_corr, abs(corr))
        
        if len(high_corr_assets) > 0:
            return {
                'allowed': True,
                'reason': f'High correlation with: {high_corr_assets}',
                'level': 'medium',
                'max_correlation': max_corr,
                'action': 'reduce_exposure'
            }
        
        return {
            'allowed': True,
            'reason': 'Correlation risk acceptable',
            'level': 'low',
            'max_correlation': max_corr,
            'action': 'normal'
        }
    
    def get_portfolio_correlation_risk(self, positions: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall portfolio correlation risk."""
        if self.correlation_matrix is None or len(self.assets) < 2:
            return {
                'risk_level': 'unknown',
                'average_correlation': 0.0,
                'max_correlation': 0.0,
                'highly_correlated_pairs': []
            }
        
        position_assets = [a for a in positions.keys() if a in self.assets]
        
        if len(position_assets) < 2:
            return {
                'risk_level': 'low',
                'average_correlation': 0.0,
                'max_correlation': 0.0,
                'highly_correlated_pairs': []
            }
        
        idx_map = {a: i for i, a in enumerate(self.assets)}
        
        correlations = []
        high_corr_pairs = []
        
        for i, asset1 in enumerate(position_assets):
            for j, asset2 in enumerate(position_assets):
                if i < j:
                    idx1, idx2 = idx_map[asset1], idx_map[asset2]
                    corr = float(self.correlation_matrix[idx1, idx2])
                    correlations.append(abs(corr))
                    
                    if abs(corr) > self.max_correlation:
                        high_corr_pairs.append((asset1, asset2, corr))
        
        avg_corr = np.mean(correlations) if correlations else 0.0
        max_corr = max(correlations) if correlations else 0.0
        
        risk_level = 'low'
        if len(high_corr_pairs) > 2:
            risk_level = 'high'
        elif len(high_corr_pairs) > 0:
            risk_level = 'medium'
        
        return {
            'risk_level': risk_level,
            'average_correlation': float(avg_corr),
            'max_correlation': float(max_corr),
            'highly_correlated_pairs': high_corr_pairs,
            'action': 'reduce' if risk_level == 'high' else 'monitor'
        }
    
    def get_diversification_benefit(self, positions: Dict[str, Any]) -> float:
        """Calculate portfolio diversification benefit (0-1)."""
        risk = self.get_portfolio_correlation_risk(positions)
        
        if risk['risk_level'] == 'unknown' or risk['risk_level'] == 'low':
            return 1.0
        elif risk['risk_level'] == 'medium':
            return 0.5
        else:
            return 0.2
    
    def get_status(self) -> Dict[str, Any]:
        """Get current correlation status."""
        return {
            'assets_tracked': len(self.assets),
            'lookback_period': self.lookback_period,
            'max_correlation_threshold': self.max_correlation,
            'correlation_matrix_available': self.correlation_matrix is not None
        }
