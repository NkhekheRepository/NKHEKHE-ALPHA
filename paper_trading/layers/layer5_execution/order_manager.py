"""
Layer 5: Order Manager
Handles order placement, tracking, and execution.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
from loguru import logger


class OrderStatus(Enum):
    PENDING = "pending"
    FILLED = "filled"
    PARTIAL = "partial"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class Order:
    """Order representation."""
    
    def __init__(self, order_id: str, symbol: str, side: str, order_type: OrderType,
                 size: float, price: float = None, leverage: int = 1):
        self.order_id = order_id
        self.symbol = symbol
        self.side = side
        self.order_type = order_type
        self.size = size
        self.price = price
        self.leverage = leverage
        
        self.status = OrderStatus.PENDING
        self.filled_size = 0
        self.avg_fill_price = 0
        
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        
        self.pnl = 0.0
    
    def fill(self, fill_price: float, fill_size: float):
        """Fill order."""
        self.filled_size += fill_size
        
        if self.avg_fill_price == 0:
            self.avg_fill_price = fill_price
        else:
            self.avg_fill_price = (self.avg_fill_price * (self.filled_size - fill_size) + 
                                   fill_price * fill_size) / self.filled_size
        
        self.updated_at = datetime.now()
        
        if self.filled_size >= self.size:
            self.status = OrderStatus.FILLED
        else:
            self.status = OrderStatus.PARTIAL
    
    def cancel(self):
        """Cancel order."""
        self.status = OrderStatus.CANCELLED
        self.updated_at = datetime.now()
    
    def reject(self, reason: str = ""):
        """Reject order."""
        self.status = OrderStatus.REJECTED
        self.updated_at = datetime.now()
        logger.warning(f"Order {self.order_id} rejected: {reason}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'order_id': self.order_id,
            'symbol': self.symbol,
            'side': self.side,
            'order_type': self.order_type.value,
            'size': self.size,
            'price': self.price,
            'leverage': self.leverage,
            'status': self.status.value,
            'filled_size': self.filled_size,
            'avg_fill_price': self.avg_fill_price,
            'created_at': self.created_at.isoformat(),
            'pnl': self.pnl
        }


class OrderManager:
    """Manages orders and positions."""
    
    def __init__(self, config: Dict[str, Any]):
        self.leverage = config.get('leverage', 75)
        self.mode = config.get('mode', 'paper')
        
        self.orders: Dict[str, Order] = {}
        self.positions: Dict[str, Dict[str, Any]] = {}
        
        self.order_counter = 0
        
        self.order_callbacks: List[callable] = []
    
    def execute(self, signal: str, symbol: str, price: float, 
                size: float, leverage: int = None) -> Optional[Order]:
        """Execute an order."""
        leverage = leverage or self.leverage
        
        if signal == 'buy':
            return self._open_long(symbol, price, size, leverage)
        elif signal == 'sell':
            return self._open_short(symbol, price, size, leverage)
        elif signal == 'close':
            return self._close_position(symbol, price, size)
        
        return None
    
    def _open_long(self, symbol: str, price: float, size: float, 
                   leverage: int) -> Order:
        """Open long position."""
        order_id = self._generate_order_id()
        
        order = Order(order_id, symbol, 'buy', OrderType.MARKET, size, price, leverage)
        
        self.orders[order_id] = order
        
        order.fill(price, size)
        
        self._update_position(symbol, 'long', size, price, leverage)
        
        self._notify_order_callback(order)
        
        logger.info(f"Opened long: {symbol} {size} @ {price} (leverage: {leverage}x)")
        
        return order
    
    def _open_short(self, symbol: str, price: float, size: float,
                    leverage: int) -> Order:
        """Open short position."""
        order_id = self._generate_order_id()
        
        order = Order(order_id, symbol, 'sell', OrderType.MARKET, size, price, leverage)
        
        self.orders[order_id] = order
        
        order.fill(price, size)
        
        self._update_position(symbol, 'short', size, price, leverage)
        
        self._notify_order_callback(order)
        
        logger.info(f"Opened short: {symbol} {size} @ {price} (leverage: {leverage}x)")
        
        return order
    
    def _close_position(self, symbol: str, price: float, size: float = None) -> Optional[Order]:
        """Close position."""
        position = self.positions.get(symbol)
        
        if not position or position.get('size', 0) == 0:
            logger.warning(f"No position to close: {symbol}")
            return None
        
        close_size = size or abs(position['size'])
        
        side = 'sell' if position['size'] > 0 else 'buy'
        
        order_id = self._generate_order_id()
        
        order = Order(order_id, symbol, side, OrderType.MARKET, close_size, price, position.get('leverage', 1))
        
        self.orders[order_id] = order
        
        order.fill(price, close_size)
        
        pnl = self._calculate_pnl(position, close_size, price)
        order.pnl = pnl
        
        self._reduce_position(symbol, close_size)
        
        self._notify_order_callback(order)
        
        logger.info(f"Closed position: {symbol} {close_size} @ {price} PnL: {pnl:.2f}")
        
        return order
    
    def _update_position(self, symbol: str, side: str, size: float, 
                        price: float, leverage: int):
        """Update position."""
        if symbol not in self.positions:
            self.positions[symbol] = {
                'size': 0,
                'entry_price': 0,
                'leverage': leverage,
                'side': None,
                'pnl': 0,
                'unrealized_pnl': 0
            }
        
        position = self.positions[symbol]
        
        if position['size'] == 0:
            position['size'] = size if side == 'long' else -size
            position['entry_price'] = price
            position['side'] = side
        else:
            existing_side = 'long' if position['size'] > 0 else 'short'
            
            if side == existing_side:
                position['size'] += size if side == 'long' else -size
                position['entry_price'] = (position['entry_price'] * (abs(position['size']) - size) + 
                                            price * size) / abs(position['size'])
            else:
                if abs(position['size']) >= size:
                    position['size'] += size if side == 'long' else -size
                    if position['size'] == 0:
                        position['entry_price'] = 0
                        position['side'] = None
                else:
                    remaining = size - abs(position['size'])
                    position['size'] = size if side == 'long' else -size
                    position['entry_price'] = price
                    position['side'] = side
        
        position['leverage'] = leverage
    
    def _reduce_position(self, symbol: str, size: float):
        """Reduce position."""
        position = self.positions.get(symbol)
        
        if position:
            position['size'] = position['size'] - size
            
            if position['size'] == 0:
                position['entry_price'] = 0
                position['side'] = None
    
    def _calculate_pnl(self, position: Dict[str, Any], size: float, 
                       close_price: float) -> float:
        """Calculate realized PnL."""
        if position.get('size', 0) == 0:
            return 0
        
        entry_price = position.get('entry_price', 0)
        
        if position['size'] > 0:
            return (close_price - entry_price) * size
        else:
            return (entry_price - close_price) * size
    
    def update_unrealized_pnl(self, symbol: str, current_price: float):
        """Update unrealized PnL."""
        position = self.positions.get(symbol)
        
        if position and position.get('size', 0) != 0:
            entry_price = position['entry_price']
            
            if position['size'] > 0:
                position['unrealized_pnl'] = (current_price - entry_price) * abs(position['size'])
            else:
                position['unrealized_pnl'] = (entry_price - current_price) * abs(position['size'])
    
    def get_position(self, symbol: str) -> Dict[str, Any]:
        """Get position for symbol."""
        return self.positions.get(symbol, {
            'size': 0, 'entry_price': 0, 'leverage': 1,
            'side': None, 'pnl': 0, 'unrealized_pnl': 0
        })
    
    def get_all_positions(self) -> Dict[str, Dict[str, Any]]:
        """Get all positions."""
        return self.positions
    
    def get_order(self, order_id: str) -> Optional[Order]:
        """Get order by ID."""
        return self.orders.get(order_id)
    
    def get_open_orders(self) -> List[Order]:
        """Get open orders."""
        return [o for o in self.orders.values() 
                if o.status in [OrderStatus.PENDING, OrderStatus.PARTIAL]]
    
    def _generate_order_id(self) -> str:
        """Generate unique order ID."""
        self.order_counter += 1
        return f"ORD_{datetime.now().strftime('%Y%m%d%H%M%S')}_{self.order_counter}"
    
    def add_order_callback(self, callback: callable):
        """Add order callback."""
        self.order_callbacks.append(callback)
    
    def _notify_order_callback(self, order: Order):
        """Notify order callbacks."""
        for callback in self.order_callbacks:
            try:
                callback(order)
            except Exception as e:
                logger.error(f"Order callback error: {e}")
