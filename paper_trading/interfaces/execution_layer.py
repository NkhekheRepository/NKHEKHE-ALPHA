"""
Execution Layer Interface
=========================
Contract for trade execution layer.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from .base import BaseLayer, LayerInput, LayerOutput, TradingSignal, Trade, Position


class IExecutionLayer(ABC):
    """Execution layer interface - handles order execution"""
    
    @abstractmethod
    def open_position(self, signal: TradingSignal) -> LayerOutput:
        """Open a position"""
        pass
    
    @abstractmethod
    def close_position(self, symbol: str, quantity: float = None) -> LayerOutput:
        """Close a position"""
        pass
    
    @abstractmethod
    def get_positions(self) -> List[Position]:
        """Get all open positions"""
        pass
    
    @abstractmethod
    def get_balance(self) -> float:
        """Get account balance"""
        pass


class ExecutionLayer(BaseLayer, IExecutionLayer):
    """Trade execution layer"""
    
    name = "execution"
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.mode = config.get('mode', 'paper')
        self.slippage = config.get('slippage', 0.001)
        self.leverage = config.get('leverage', 75)
        self._positions: Dict[str, Position] = {}
        self._balance = config.get('initial_balance', 10000)
    
    def process(self, input_data: LayerInput) -> LayerOutput:
        """Process execution request"""
        try:
            action = input_data.get('action')
            
            if action == 'open':
                signal = input_data.get('signal')
                return self.open_position(signal)
            elif action == 'close':
                symbol = input_data.get('symbol')
                quantity = input_data.get('quantity')
                return self.close_position(symbol, quantity)
            elif action == 'get_positions':
                return LayerOutput(
                    result=[p.to_dict() for p in self.get_positions()],
                    success=True,
                    layer_name=self.name
                )
            elif action == 'get_balance':
                return LayerOutput(
                    result={'balance': self.get_balance()},
                    success=True,
                    layer_name=self.name
                )
            
            return LayerOutput(
                result={'error': 'Unknown action'},
                success=False,
                layer_name=self.name
            )
        except Exception as e:
            return LayerOutput(
                result=None,
                success=False,
                error=str(e),
                layer_name=self.name
            )
    
    def open_position(self, signal: TradingSignal) -> LayerOutput:
        """Open a position"""
        if signal.action == 'hold':
            return LayerOutput(
                result={'message': 'No action - hold'},
                success=True,
                layer_name=self.name
            )
        
        symbol = signal.metadata.get('symbol', 'BTCUSDT')
        side = 'LONG' if signal.action == 'buy' else 'SHORT'
        
        entry_price = signal.metadata.get('price', 0)
        if self.slippage > 0:
            if side == 'LONG':
                entry_price *= (1 + self.slippage)
            else:
                entry_price *= (1 - self.slippage)
        
        position = Position(
            symbol=symbol,
            side=side,
            quantity=signal.position_size / entry_price,
            entry_price=entry_price,
            leverage=self.leverage,
            margin=signal.position_size / self.leverage
        )
        
        self._positions[symbol] = position
        
        return LayerOutput(
            result={
                'trade_id': f'{symbol}_{side}_{int(time.time())}',
                'side': side,
                'quantity': position.quantity,
                'entry_price': entry_price,
                'status': 'open'
            },
            success=True,
            layer_name=self.name
        )
    
    def close_position(self, symbol: str, quantity: float = None) -> LayerOutput:
        """Close a position"""
        if symbol not in self._positions:
            return LayerOutput(
                result={'error': 'No position found'},
                success=False,
                layer_name=self.name
            )
        
        position = self._positions[symbol]
        
        if quantity and quantity < position.quantity:
            position.quantity -= quantity
            return LayerOutput(
                result={'partial': True, 'remaining': position.quantity},
                success=True,
                layer_name=self.name
            )
        
        del self._positions[symbol]
        
        return LayerOutput(
            result={'status': 'closed', 'symbol': symbol},
            success=True,
            layer_name=self.name
        )
    
    def get_positions(self) -> List[Position]:
        """Get all open positions"""
        return list(self._positions.values())
    
    def get_balance(self) -> float:
        """Get account balance"""
        return self._balance
    
    def update_position_prices(self, current_prices: Dict[str, float]):
        """Update position prices and calculate PnL"""
        for symbol, position in self._positions.items():
            if symbol in current_prices:
                position.current_price = current_prices[symbol]
                if position.side == 'LONG':
                    position.unrealized_pnl = (
                        (position.current_price - position.entry_price) * position.quantity
                    )
                else:
                    position.unrealized_pnl = (
                        (position.entry_price - position.current_price) * position.quantity
                    )


import time
