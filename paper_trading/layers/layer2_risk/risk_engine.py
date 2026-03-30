"""
Layer 2: Risk Management Engine
Risk limits, position sizing, and daily loss tracking.
"""

from typing import Dict, Any, Optional
from datetime import datetime, time
from loguru import logger


class RiskEngine:
    """Risk management engine for position and loss limits."""
    
    def __init__(self, config: Dict[str, Any]):
        self.max_daily_loss_pct = config.get('max_daily_loss_pct', 5)
        self.max_drawdown_pct = config.get('max_drawdown_pct', 20)
        self.position_size_pct = config.get('position_size_pct', 10)
        self.stop_loss_pct = config.get('stop_loss_pct', 2)
        self.take_profit_pct = config.get('take_profit_pct', 5)
        
        self.daily_loss_start = 0.0
        self.peak_capital = 0.0
        self.last_reset_date = datetime.now().date()
        
        self.leverage_limit = 75
    
    def check_risk(self, capital: float, daily_pnl: float, 
                   positions: Dict[str, Any], start_capital: float) -> Dict[str, Any]:
        """Check if trading is allowed based on risk limits."""
        self._check_daily_reset()
        
        daily_loss_pct = (daily_pnl / start_capital * 100) if start_capital > 0 else 0
        
        if daily_loss_pct <= -self.max_daily_loss_pct:
            return {
                'allowed': False,
                'reason': f'Daily loss limit hit: {daily_loss_pct:.2f}%',
                'level': 'critical',
                'risk_score': 100,
                'action': 'stop_trading'
            }
        
        current_drawdown = ((self.peak_capital - capital) / self.peak_capital * 100) \
                          if self.peak_capital > 0 else 0
        
        if current_drawdown >= self.max_drawdown_pct:
            return {
                'allowed': False,
                'reason': f'Drawdown limit hit: {current_drawdown:.2f}%',
                'level': 'critical',
                'risk_score': 100,
                'action': 'stop_trading'
            }
        
        total_exposure = sum(
            abs(pos.get('size', 0)) * pos.get('price', 0) 
            for pos in positions.values()
        )
        
        leverage_used = total_exposure / capital if capital > 0 else 0
        
        if leverage_used > self.leverage_limit:
            return {
                'allowed': False,
                'reason': f'Leverage limit exceeded: {leverage_used:.1f}x',
                'level': 'high',
                'risk_score': 80,
                'action': 'reduce_positions'
            }
        
        risk_score = self._calculate_risk_score(daily_loss_pct, current_drawdown, leverage_used)
        
        if risk_score > 70:
            return {
                'allowed': True,
                'reason': 'High risk - reduce position size',
                'level': 'medium',
                'risk_score': risk_score,
                'action': 'reduce_size'
            }
        
        return {
            'allowed': True,
            'reason': 'Risk checks passed',
            'level': 'low',
            'risk_score': risk_score,
            'action': 'normal'
        }
    
    def check_position_risk(self, position: Dict[str, Any], current_price: float) -> Dict[str, Any]:
        """Check risk for a specific position."""
        entry_price = position.get('entry_price', 0)
        size = position.get('size', 0)
        
        if entry_price == 0 or size == 0:
            return {'allowed': True, 'reason': 'No position'}
        
        pnl_pct = ((current_price - entry_price) / entry_price) * 100
        
        if size > 0:
            if pnl_pct <= -self.stop_loss_pct:
                return {
                    'allowed': False,
                    'reason': f'Stop loss triggered: {pnl_pct:.2f}%',
                    'action': 'close_position'
                }
            elif pnl_pct >= self.take_profit_pct:
                return {
                    'allowed': True,
                    'reason': f'Take profit hit: {pnl_pct:.2f}%',
                    'action': 'consider_take_profit'
                }
        
        return {'allowed': True, 'reason': 'Position risk OK'}
    
    def calculate_position_size(self, capital: float, price: float, 
                                 risk_pct: float = None) -> float:
        """Calculate position size based on risk parameters."""
        risk_pct = risk_pct or self.position_size_pct
        
        base_size = capital * (risk_pct / 100)
        
        leveraged_size = base_size * self.leverage_limit
        
        return leveraged_size / price
    
    def _check_daily_reset(self):
        """Reset daily tracking if new day."""
        today = datetime.now().date()
        if today != self.last_reset_date:
            self.daily_loss_start = 0.0
            self.last_reset_date = today
            logger.info("Daily risk tracking reset")
    
    def _calculate_risk_score(self, daily_loss_pct: float, drawdown: float, 
                               leverage: float) -> float:
        """Calculate overall risk score (0-100)."""
        loss_score = min(abs(daily_loss_pct) / self.max_daily_loss_pct * 50, 50)
        drawdown_score = min(drawdown / self.max_drawdown_pct * 30, 30)
        leverage_score = min(leverage / self.leverage_limit * 20, 20)
        
        return loss_score + drawdown_score + leverage_score
    
    def update_peak_capital(self, capital: float):
        """Update peak capital for drawdown tracking."""
        if capital > self.peak_capital:
            self.peak_capital = capital
    
    def get_risk_status(self) -> Dict[str, Any]:
        """Get current risk status."""
        return {
            'max_daily_loss_pct': self.max_daily_loss_pct,
            'max_drawdown_pct': self.max_drawdown_pct,
            'position_size_pct': self.position_size_pct,
            'stop_loss_pct': self.stop_loss_pct,
            'take_profit_pct': self.take_profit_pct,
            'leverage_limit': self.leverage_limit,
            'peak_capital': self.peak_capital,
            'last_reset': self.last_reset_date.isoformat()
        }
