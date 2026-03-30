"""
Pytest fixtures for VNPY CTA Strategy testing.
"""

import sys
import site
from pathlib import Path
from datetime import datetime, timedelta
from typing import List
import numpy as np

vnpy_site_packages = site.getsitepackages()[0]
sys.path.insert(0, vnpy_site_packages)

proj_root = str(Path(__file__).parent.parent)
sys.path.insert(0, proj_root)

from vnpy.trader.object import BarData
from vnpy.trader.constant import Interval, Exchange, Direction, Status, Offset


class SyntheticDataGenerator:
    """
    Generate synthetic OHLCV bar data for testing.
    Supports different market patterns: trending, ranging, volatile.
    """
    
    def __init__(self, symbol: str = "BTCUSDT", initial_price: float = 50000.0):
        self.symbol = symbol
        self.price = initial_price
        self.vt_symbol = f"{symbol}.BINANCE"
    
    def generate_trending_bars(self, n: int = 100, trend: str = "up") -> List[BarData]:
        """Generate bars with clear trend."""
        bars = []
        dt = datetime.now()
        
        for i in range(n):
            if trend == "up":
                change = np.random.normal(0.002, 0.005)
            elif trend == "down":
                change = np.random.normal(-0.002, 0.005)
            else:
                change = np.random.normal(0, 0.003)
            
            self.price *= (1 + change)
            
            bar = BarData(
                gateway_name="mock",
                symbol=self.symbol,
                exchange=Exchange.SMART,
                datetime=dt,
                interval=Interval.MINUTE,
                open_price=self.price * (1 + np.random.uniform(-0.001, 0.001)),
                high_price=self.price * (1 + abs(np.random.uniform(0, 0.005))),
                low_price=self.price * (1 - abs(np.random.uniform(0, 0.005))),
                close_price=self.price,
                volume=100 + np.random.uniform(0, 500),
                turnover=0.0,
                open_interest=0
            )
            bars.append(bar)
            dt += timedelta(minutes=1)
        
        return bars
    
    def generate_ranging_bars(self, n: int = 100, 
                             center: float = None, 
                             width: float = 0.02) -> List[BarData]:
        """Generate bars oscillating around a center price."""
        if center is None:
            center = self.price
        
        bars = []
        dt = datetime.now()
        phase = 0
        
        for i in range(n):
            phase += 2 * np.pi / 20
            oscillation = width * np.sin(phase)
            noise = np.random.normal(0, 0.002)
            self.price = center * (1 + oscillation + noise)
            
            bar = BarData(
                gateway_name="mock",
                symbol=self.symbol,
                exchange=Exchange.SMART,
                datetime=dt,
                interval=Interval.MINUTE,
                open_price=self.price * (1 + np.random.uniform(-0.001, 0.001)),
                high_price=self.price * (1 + abs(np.random.uniform(0, 0.005))),
                low_price=self.price * (1 - abs(np.random.uniform(0, 0.005))),
                close_price=self.price,
                volume=100 + np.random.uniform(0, 500),
                turnover=0.0,
                open_interest=0
            )
            bars.append(bar)
            dt += timedelta(minutes=1)
        
        return bars
    
    def generate_volatile_bars(self, n: int = 100, 
                               volatility: float = 0.02) -> List[BarData]:
        """Generate bars with high volatility."""
        bars = []
        dt = datetime.now()
        
        for i in range(n):
            change = np.random.normal(0, volatility)
            self.price *= (1 + change)
            
            bar = BarData(
                gateway_name="mock",
                symbol=self.symbol,
                exchange=Exchange.SMART,
                datetime=dt,
                interval=Interval.MINUTE,
                open_price=self.price * (1 + np.random.uniform(-0.001, 0.001)),
                high_price=self.price * (1 + abs(np.random.uniform(0, 0.005))),
                low_price=self.price * (1 - abs(np.random.uniform(0, 0.005))),
                close_price=self.price,
                volume=100 + np.random.uniform(0, 500),
                turnover=0.0,
                open_interest=0
            )
            bars.append(bar)
            dt += timedelta(minutes=1)
        
        return bars
    
    def generate_flash_crash(self, n_before: int = 50, 
                            crash_pct: float = 0.10) -> List[BarData]:
        """Generate bars with a flash crash in the middle."""
        bars = []
        dt = datetime.now()
        
        for i in range(n_before):
            change = np.random.normal(0, 0.002)
            self.price *= (1 + change)
            
            bar = BarData(
                gateway_name="mock",
                symbol=self.symbol,
                exchange=Exchange.SMART,
                datetime=dt,
                interval=Interval.MINUTE,
                open_price=self.price * (1 + np.random.uniform(-0.001, 0.001)),
                high_price=self.price * (1 + abs(np.random.uniform(0, 0.005))),
                low_price=self.price * (1 - abs(np.random.uniform(0, 0.005))),
                close_price=self.price,
                volume=100 + np.random.uniform(0, 500),
                turnover=0.0,
                open_interest=0
            )
            bars.append(bar)
            dt += timedelta(minutes=1)
        
        self.price *= (1 - crash_pct)
        
        for i in range(50):
            change = np.random.normal(0.001, 0.003)
            self.price *= (1 + change)
            
            bar = BarData(
                gateway_name="mock",
                symbol=self.symbol,
                exchange=Exchange.SMART,
                datetime=dt,
                interval=Interval.MINUTE,
                open_price=self.price * (1 + np.random.uniform(-0.001, 0.001)),
                high_price=self.price * (1 + abs(np.random.uniform(0, 0.005))),
                low_price=self.price * (1 - abs(np.random.uniform(0, 0.005))),
                close_price=self.price,
                volume=100 + np.random.uniform(0, 500),
                turnover=0.0,
                open_interest=0
            )
            bars.append(bar)
            dt += timedelta(minutes=1)
        
        return bars


class MockCtaEngine:
    """
    Mock CtaEngine for strategy testing.
    Tracks position, orders, trades, and strategy state.
    """
    
    def __init__(self):
        self.strategies = {}
        self.orders = []
        self.trades = []
        self.order_id = 0
        self.positions = {}
        self.logs = []
    
    def write_log(self, msg, strategy=None):
        self.logs.append(msg)
    
    def register_strategy(self, strategy):
        self.strategies[strategy.strategy_name] = strategy
    
    def load_bar(self, strategy, days, interval, callback, use_database=False):
        """Mock load_bar - returns empty list"""
        return []
    
    def send_order(self, strategy, direction, offset, price, volume, stop=False, lock=False, net=False):
        """Mock send_order - creates a trade record
        Note: In the mock, we allow orders even when trading=False to support testing
        """
        self.order_id += 1
        order_id = f"ORDER_{self.order_id}"
        
        from vnpy.trader.object import OrderData
        order = OrderData(
            gateway_name="mock",
            symbol="BTCUSDT",
            exchange=Exchange.SMART,
            orderid=order_id,
            direction=direction,
            offset=offset,
            price=price,
            volume=volume,
            traded=volume,
            status=Status.ALLTRADED,
            datetime=datetime.now()
        )
        
        # Update strategy position
        if direction == Direction.LONG and offset == Offset.OPEN:
            strategy.pos += volume
        elif direction == Direction.SHORT and offset == Offset.OPEN:
            strategy.pos -= volume
        elif direction == Direction.SHORT and offset == Offset.CLOSE:
            strategy.pos -= volume
        elif direction == Direction.LONG and offset == Offset.CLOSE:
            strategy.pos += volume
        
        self.trades.append(order)
        return [order_id]
    
    def sync_strategy_data(self, strategy):
        """Mock sync_strategy_data"""
        pass
    
    def put_strategy_event(self, strategy):
        """Mock put_strategy_event"""
        pass
    
    def start_all(self):
        """Mock start_all"""
        for strategy in self.strategies.values():
            strategy.trading = True
    
    def start_strategy(self, strategy):
        """Start a single strategy and set trading to True"""
        if strategy not in self.strategies.values():
            self.register_strategy(strategy)
        strategy.trading = True
    
    def add_order(self, order):
        self.orders.append(order)
        return order.vt_orderid
    
    def cancel_order(self, vt_orderid):
        pass
    
    def convert_order_request(self, vt_symbol, direction, offset, price, volume):
        from vnpy.trader.object import OrderRequest, OrderData
        
        self.order_id += 1
        order_id = f"ORDER_{self.order_id}"
        
        order = OrderData(
            gateway_name="mock",
            symbol=vt_symbol.split(".")[0],
            exchange=Exchange.SMART,
            orderid=order_id,
            direction=direction,
            offset=offset,
            price=price,
            volume=volume,
            traded=volume,
            status=Status.ALLTRADED,
            datetime=datetime.now()
        )
        
        self.trades.append(order)
        return order
    
    def get_position(self, vt_symbol, direction=Direction.NET):
        key = f"{vt_symbol}_{direction}"
        return self.positions.get(key, 0)


class MockCtaStrategyParent:
    """Base mock for CTA strategy testing."""
    
    def __init__(self):
        self.inited = False
        self.trading = False
        self.pos = 0.0
        self.orders = []
        self.logs = []
    
    def write_log(self, msg: str):
        self.logs.append(msg)
    
    def put_event(self):
        pass
    
    def sync_data(self):
        pass
    
    def cancel_all(self):
        self.orders = []
    
    def buy(self, price: float, volume: float):
        from vnpy.trader.object import OrderData
        order = OrderData(
            gateway_name="mock",
            symbol="BTCUSDT",
            exchange=Exchange.SMART,
            orderid=f"ORDER_{len(self.orders)}",
            direction=Direction.LONG,
            offset=Offset.OPEN,
            price=price,
            volume=volume,
            traded=volume,
            status=Status.ALLTRADED,
            datetime=datetime.now()
        )
        self.orders.append(order)
        self.pos += volume
        return order.vt_orderid
    
    def sell(self, price: float, volume: float):
        from vnpy.trader.object import OrderData
        order = OrderData(
            gateway_name="mock",
            symbol="BTCUSDT",
            exchange=Exchange.SMART,
            orderid=f"ORDER_{len(self.orders)}",
            direction=Direction.SHORT,
            offset=Offset.CLOSE,
            price=price,
            volume=volume,
            traded=volume,
            status=Status.ALLTRADED,
            datetime=datetime.now()
        )
        self.orders.append(order)
        self.pos -= volume
        return order.vt_orderid
    
    def short(self, price: float, volume: float):
        from vnpy.trader.object import OrderData
        order = OrderData(
            gateway_name="mock",
            symbol="BTCUSDT",
            exchange=Exchange.SMART,
            orderid=f"ORDER_{len(self.orders)}",
            direction=Direction.SHORT,
            offset=Offset.OPEN,
            price=price,
            volume=volume,
            traded=volume,
            status=Status.ALLTRADED,
            datetime=datetime.now()
        )
        self.orders.append(order)
        self.pos -= volume
        return order.vt_orderid
    
    def cover(self, price: float, volume: float):
        from vnpy.trader.object import OrderData
        order = OrderData(
            gateway_name="mock",
            symbol="BTCUSDT",
            exchange=Exchange.SMART,
            orderid=f"ORDER_{len(self.orders)}",
            direction=Direction.LONG,
            offset=Offset.CLOSE,
            price=price,
            volume=volume,
            traded=volume,
            status=Status.ALLTRADED,
            datetime=datetime.now()
        )
        self.orders.append(order)
        self.pos += volume
        return order.vt_orderid
