"""
Layer 5: Leverage Handler
Manages 75x leverage and margin calculations.
"""

from typing import Dict, Any, Optional
from loguru import logger


class LeverageHandler:
    """Handles leverage and margin calculations."""
    
    def __init__(self, max_leverage: int = 75):
        self.max_leverage = max_leverage
        
        self.liquidation_buffer = 0.05
    
    def calculate_margin(self, position_size: float, entry_price: float, 
                        leverage: int) -> float:
        """Calculate required margin for position."""
        if leverage <= 0:
            leverage = 1
        
        position_value = position_size * entry_price
        
        margin = position_value / leverage
        
        return margin
    
    def calculate_liquidation_price(self, entry_price: float, leverage: int, 
                                   side: str) -> float:
        """Calculate liquidation price."""
        if leverage <= 0:
            return 0
        
        buffer = self.liquidation_buffer
        
        if side == 'long':
            liquidation = entry_price * (1 - (1 / leverage) - buffer)
        elif side == 'short':
            liquidation = entry_price * (1 + (1 / leverage) + buffer)
        else:
            liquidation = 0
        
        return liquidation
    
    def calculate_position_size(self, capital: float, price: float, 
                               leverage: int, risk_pct: float = 0.1) -> float:
        """Calculate position size based on capital and risk."""
        if leverage > self.max_leverage:
            logger.warning(f"Leverage {leverage} exceeds max {self.max_leverage}, capping")
            leverage = self.max_leverage
        
        risk_amount = capital * risk_pct
        
        position_value = risk_amount * leverage
        
        size = position_value / price
        
        return size
    
    def check_margin_requirement(self, capital: float, position: Dict[str, Any]) -> Dict[str, Any]:
        """Check if position meets margin requirements."""
        size = position.get('size', 0)
        entry_price = position.get('entry_price', 0)
        leverage = position.get('leverage', 1)
        
        if size == 0 or entry_price == 0:
            return {'valid': True, 'reason': 'No position'}
        
        required_margin = self.calculate_margin(abs(size), entry_price, leverage)
        
        if required_margin > capital:
            return {
                'valid': False,
                'reason': 'Insufficient margin',
                'required': required_margin,
                'available': capital
            }
        
        return {
            'valid': True,
            'required': required_margin,
            'available': capital,
            'utilization': (required_margin / capital * 100) if capital > 0 else 0
        }
    
    def calculate_max_leverage_for_position(self, capital: float, position_size: float,
                                          entry_price: float) -> int:
        """Calculate maximum safe leverage for position."""
        position_value = position_size * entry_price
        
        if position_value <= 0:
            return 1
        
        available_margin = capital
        
        leverage = int(available_margin / (position_value / self.max_leverage))
        
        leverage = min(leverage, self.max_leverage)
        leverage = max(leverage, 1)
        
        return leverage
    
    def get_leverage_warning(self, leverage: int) -> Optional[str]:
        """Get warning message for high leverage."""
        if leverage >= 75:
            return "EXTREME: 75x leverage - liquidation extremely likely"
        elif leverage >= 50:
            return "HIGH: 50x+ leverage - liquidation very likely"
        elif leverage >= 30:
            return "MEDIUM: 30x+ leverage - significant liquidation risk"
        elif leverage >= 20:
            return "MODERATE: 20x+ leverage - monitor closely"
        else:
            return None
    
    def simulate_liquidation(self, entry_price: float, leverage: int, 
                           side: str, current_price: float) -> Dict[str, Any]:
        """Simulate liquidation scenario."""
        liquidation_price = self.calculate_liquidation_price(entry_price, leverage, side)
        
        distance_to_liquidation = abs(current_price - liquidation_price)
        distance_pct = (distance_to_liquidation / current_price * 100) if current_price > 0 else 0
        
        return {
            'entry_price': entry_price,
            'current_price': current_price,
            'liquidation_price': liquidation_price,
            'distance_to_liquidation': distance_to_liquidation,
            'distance_pct': distance_pct,
            'leverage': leverage,
            'side': side,
            'will_liquidate': (side == 'long' and current_price <= liquidation_price) or
                             (side == 'short' and current_price >= liquidation_price)
        }


class LeverageManager:
    """Manages leverage across all positions."""
    
    def __init__(self, max_leverage: int = 75):
        self.max_leverage = max_leverage
        self.handler = LeverageHandler(max_leverage)
        
        self.total_exposure = 0
        self.total_margin = 0
    
    def update_exposure(self, positions: Dict[str, Dict[str, Any]]):
        """Update total exposure and margin."""
        total_value = 0
        total_margin = 0
        
        for symbol, position in positions.items():
            size = abs(position.get('size', 0))
            entry_price = position.get('entry_price', 0)
            leverage = position.get('leverage', 1)
            
            if size > 0 and entry_price > 0:
                position_value = size * entry_price
                margin = self.handler.calculate_margin(size, entry_price, leverage)
                
                total_value += position_value
                total_margin += margin
        
        self.total_exposure = total_value
        self.total_margin = total_margin
    
    def get_leverage_ratio(self) -> float:
        """Get current leverage ratio."""
        if self.total_margin <= 0:
            return 0
        return self.total_exposure / self.total_margin
    
    def can_increase_position(self, additional_margin: float, capital: float) -> bool:
        """Check if additional position can be opened."""
        new_total_margin = self.total_margin + additional_margin
        
        if new_total_margin > capital:
            return False
        
        return True


leverage_handler = LeverageHandler(75)
