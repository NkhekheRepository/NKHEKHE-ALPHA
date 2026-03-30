"""
Risk Layer Interface
====================
Contract for risk management layer.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from .base import BaseLayer, LayerInput, LayerOutput, TradingSignal, Position


class IRiskLayer(ABC):
    """Risk layer interface - manages position sizing and risk limits"""
    
    @abstractmethod
    def check_risk(self, signal: TradingSignal, balance: float, 
                   positions: Dict[str, Position]) -> LayerOutput:
        """Check if trade passes risk checks"""
        pass
    
    @abstractmethod
    def calculate_size(self, signal: TradingSignal, balance: float, 
                      volatility: float) -> float:
        """Calculate position size based on risk"""
        pass
    
    @abstractmethod
    def check_daily_limits(self, daily_trades: int, daily_pnl: float) -> bool:
        """Check if daily limits are reached"""
        pass


class RiskLayer(BaseLayer, IRiskLayer):
    """Risk management layer implementation"""
    
    name = "risk"
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.max_daily_trades = config.get('max_daily_trades', 5)
        self.max_position_pct = config.get('max_position_pct', 0.10)
        self.max_daily_loss_pct = config.get('max_daily_loss_pct', 0.05)
        self.max_drawdown_pct = config.get('max_drawdown_pct', 0.20)
        self.stop_loss_pct = config.get('stop_loss_pct', 0.02)
        self.take_profit_pct = config.get('take_profit_pct', 0.05)
        
        self._daily_trades = 0
        self._daily_pnl = 0.0
        self._consecutive_losses = 0
    
    def process(self, input_data: LayerInput) -> LayerOutput:
        """Process risk check request"""
        try:
            signal = input_data.get('signal')
            balance = input_data.get('balance', 10000)
            positions = input_data.get('positions', {})
            
            if not signal:
                return LayerOutput(
                    result={'allowed': False, 'reason': 'No signal'},
                    success=True,
                    layer_name=self.name
                )
            
            result = self.check_risk(signal, balance, positions)
            return result
        except Exception as e:
            return LayerOutput(
                result=None,
                success=False,
                error=str(e),
                layer_name=self.name
            )
    
    def check_risk(self, signal: TradingSignal, balance: float, 
                   positions: Dict[str, Position]) -> LayerOutput:
        """Check if trade passes risk checks"""
        allowed = True
        reasons = []
        
        if not self.check_daily_limits(self._daily_trades, self._daily_pnl):
            allowed = False
            reasons.append('Daily limit reached')
        
        total_exposure = sum(p.quantity * p.current_price for p in positions.values())
        if total_exposure > balance * self.max_position_pct * 2:
            allowed = False
            reasons.append('Max exposure reached')
        
        if self._daily_pnl < -balance * self.max_daily_loss_pct:
            allowed = False
            reasons.append('Daily loss limit reached')
        
        if not allowed:
            return LayerOutput(
                result={'allowed': False, 'reasons': reasons},
                success=True,
                layer_name=self.name
            )
        
        position_size = self.calculate_size(signal, balance, signal.confidence)
        signal.position_size = position_size
        
        if signal.stop_loss is None:
            signal.stop_loss = signal.entry_price * (1 - self.stop_loss_pct)
        if signal.take_profit is None:
            signal.take_profit = signal.entry_price * (1 + self.take_profit_pct)
        
        return LayerOutput(
            result={
                'allowed': True,
                'position_size': position_size,
                'stop_loss': signal.stop_loss,
                'take_profit': signal.take_profit,
                'reasons': reasons
            },
            success=True,
            layer_name=self.name
        )
    
    def calculate_size(self, signal: TradingSignal, balance: float, 
                       volatility: float) -> float:
        """Calculate position size based on risk and confidence"""
        base_size = balance * self.max_position_pct
        
        if signal.score > 0.85:
            base_size *= 1.2
        elif signal.score < 0.72:
            base_size *= 0.7
        
        if signal.confidence > 0.8:
            base_size *= 1.1
        
        if volatility > 0.03:
            base_size *= 0.75
        elif volatility > 0.02:
            base_size *= 0.9
        
        return base_size
    
    def check_daily_limits(self, daily_trades: int, daily_pnl: float) -> bool:
        """Check if daily limits are reached"""
        if daily_trades >= self.max_daily_trades:
            return False
        if daily_pnl < -self.max_daily_loss_pct * 10000:
            return False
        return True
    
    def record_trade(self, pnl: float):
        """Record trade result for daily tracking"""
        self._daily_trades += 1
        self._daily_pnl += pnl
        if pnl < 0:
            self._consecutive_losses += 1
        else:
            self._consecutive_losses = 0
    
    def reset_daily(self):
        """Reset daily counters"""
        self._daily_trades = 0
        self._daily_pnl = 0.0
        self._consecutive_losses = 0
