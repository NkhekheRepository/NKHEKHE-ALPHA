"""
Base Interfaces for Financial Orchestrator
===========================================
Defines the contract that all layers must follow.
Enables modular, plug-and-play architecture.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, List
from datetime import datetime
from enum import Enum


class LayerName(Enum):
    """All available layers in the system"""
    DATA = "data"
    FEATURES = "features"
    STATE = "state"
    STRATEGY = "strategy"
    INTELLIGENCE = "intelligence"
    SCORING = "scoring"
    RISK = "risk"
    EXECUTION = "execution"
    MEMORY = "memory"
    OUTPUT = "output"


@dataclass
class LayerInput:
    """Standard input to any layer"""
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)
    
    def set(self, key: str, value: Any):
        self.data[key] = value


@dataclass
class LayerOutput:
    """Standard output from any layer"""
    result: Any = None
    success: bool = True
    error: Optional[str] = None
    layer_name: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'result': self.result,
            'success': self.success,
            'error': self.error,
            'layer_name': self.layer_name,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata
        }


@dataclass
class MarketData:
    """Standard market data format"""
    symbol: str
    price: float
    volume: float
    timestamp: float
    bid: float = 0.0
    ask: float = 0.0
    high_24h: float = 0.0
    low_24h: float = 0.0
    change_24h: float = 0.0
    change_pct_24h: float = 0.0


@dataclass
class FeatureVector:
    """Standard feature vector format"""
    price: float
    volume: float
    timestamp: float
    returns: float = 0.0
    volatility: float = 0.0
    atr: float = 0.0
    adx: float = 0.0
    rsi: float = 50.0
    macd: Dict[str, float] = field(default_factory=dict)
    bollinger: Dict[str, float] = field(default_factory=dict)
    ema_fast: float = 0.0
    ema_slow: float = 0.0
    volume_ratio: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'price': self.price,
            'volume': self.volume,
            'timestamp': self.timestamp,
            'returns': self.returns,
            'volatility': self.volatility,
            'atr': self.atr,
            'adx': self.adx,
            'rsi': self.rsi,
            'macd': self.macd,
            'bollinger': self.bollinger,
            'ema_fast': self.ema_fast,
            'ema_slow': self.ema_slow,
            'volume_ratio': self.volume_ratio
        }


@dataclass
class TradingSignal:
    """Standard trading signal format"""
    action: str  # buy, sell, hold
    confidence: float  # 0-1
    score: float  # 0-1 (from scoring layer)
    strategy: str
    regime: str
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    position_size: float = 0.0
    explore_exploit: str = "exploit"  # explore or exploit
    reason: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'action': self.action,
            'confidence': self.confidence,
            'score': self.score,
            'strategy': self.strategy,
            'regime': self.regime,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'position_size': self.position_size,
            'explore_exploit': self.explore_exploit,
            'reason': self.reason,
            'metadata': self.metadata
        }


@dataclass
class Trade:
    """Trade execution record"""
    trade_id: str
    symbol: str
    side: str  # LONG, SHORT
    quantity: float
    entry_price: float
    exit_price: Optional[float] = None
    pnl: float = 0.0
    pnl_pct: float = 0.0
    status: str = "open"  # open, closed, cancelled
    strategy: str = ""
    regime: str = ""
    confidence: float = 0.0
    score: float = 0.0
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    explore_exploit: str = "exploit"
    executed_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'trade_id': self.trade_id,
            'symbol': self.symbol,
            'side': self.side,
            'quantity': self.quantity,
            'entry_price': self.entry_price,
            'exit_price': self.exit_price,
            'pnl': self.pnl,
            'pnl_pct': self.pnl_pct,
            'status': self.status,
            'strategy': self.strategy,
            'regime': self.regime,
            'confidence': self.confidence,
            'score': self.score,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'explore_exploit': self.explore_exploit,
            'executed_at': self.executed_at.isoformat() if self.executed_at else None,
            'closed_at': self.closed_at.isoformat() if self.closed_at else None
        }


@dataclass
class Position:
    """Position record"""
    symbol: str
    side: str  # LONG, SHORT
    quantity: float
    entry_price: float
    current_price: float = 0.0
    unrealized_pnl: float = 0.0
    leverage: int = 1
    margin: float = 0.0
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    opened_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'symbol': self.symbol,
            'side': self.side,
            'quantity': self.quantity,
            'entry_price': self.entry_price,
            'current_price': self.current_price,
            'unrealized_pnl': self.unrealized_pnl,
            'leverage': self.leverage,
            'margin': self.margin,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'opened_at': self.opened_at.isoformat() if self.opened_at else None
        }


@dataclass
class DecisionRecord:
    """Decision record for database storage"""
    timestamp: datetime
    symbol: str
    price: float
    regime: str
    strategy: str
    action: str
    confidence: float
    score: float
    risk_passed: bool = True
    rejected_reason: Optional[str] = None
    explore_exploit: str = "exploit"
    layer_outputs: Optional[Dict] = None
    metadata: Optional[Dict] = None


@dataclass
class MetricsRecord:
    """Metrics record for database storage"""
    metric_type: str
    value: float
    period: str = 'daily'
    metadata: Optional[Dict] = None


class BaseLayer(ABC):
    """
    Base class for all layers.
    Every layer must implement this interface.
    """
    
    name: str = "base"
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.enabled = config.get('enabled', True)
        self._healthy = True
        self._last_error: Optional[str] = None
        self._error_count = 0
    
    @abstractmethod
    def process(self, input_data: LayerInput) -> LayerOutput:
        """
        Process input and return output.
        Each layer implements its specific logic here.
        """
        pass
    
    def health_check(self) -> bool:
        """Check if layer is healthy"""
        return self._healthy
    
    def get_status(self) -> Dict[str, Any]:
        """Get detailed status of the layer"""
        return {
            'name': self.name,
            'enabled': self.enabled,
            'healthy': self._healthy,
            'error_count': self._error_count,
            'last_error': self._last_error
        }
    
    def mark_healthy(self):
        """Mark layer as healthy"""
        self._healthy = True
        self._last_error = None
    
    def mark_unhealthy(self, error: str):
        """Mark layer as unhealthy with error"""
        self._healthy = False
        self._last_error = error
        self._error_count += 1
    
    def reset_error_count(self):
        """Reset error count"""
        self._error_count = 0
        self._healthy = True


class LayerWithFallback(BaseLayer):
    """Layer with fallback support - if primary fails, use fallback"""
    
    def __init__(self, config: Dict[str, Any], fallback: Optional[BaseLayer] = None):
        super().__init__(config)
        self.fallback = fallback
    
    def process(self, input_data: LayerInput) -> LayerOutput:
        try:
            return self._process_impl(input_data)
        except Exception as e:
            if self.fallback and self.fallback.enabled:
                return self.fallback.process(input_data)
            return LayerOutput(
                result=None,
                success=False,
                error=str(e),
                layer_name=self.name
            )
    
    @abstractmethod
    def _process_impl(self, input_data: LayerInput) -> LayerOutput:
        """Actual implementation"""
        pass


class LayerRegistry:
    """
    Registry for all layers.
    Enables dynamic layer creation and swapping.
    """
    
    _layers: Dict[str, type] = {}
    _instances: Dict[str, BaseLayer] = {}
    
    @classmethod
    def register(cls, name: str, layer_class: type):
        """Register a layer class"""
        cls._layers[name] = layer_class
    
    @classmethod
    def create(cls, name: str, config: Dict[str, Any]) -> Optional[BaseLayer]:
        """Create a layer instance"""
        if name not in cls._layers:
            return None
        instance = cls._layers[name](config)
        cls._instances[name] = instance
        return instance
    
    @classmethod
    def get(cls, name: str) -> Optional[BaseLayer]:
        """Get a layer instance"""
        return cls._instances.get(name)
    
    @classmethod
    def get_all_instances(cls) -> Dict[str, BaseLayer]:
        """Get all layer instances"""
        return cls._instances.copy()
    
    @classmethod
    def list_registered(cls) -> List[str]:
        """List all registered layer names"""
        return list(cls._layers.keys())


# Import for type hints
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .data_layer import IDataLayer
    from .features_layer import IFeaturesLayer
    from .strategy_layer import IStrategyLayer
    from .intelligence_layer import IIntelligenceLayer
    from .scoring_layer import IScoringLayer
    from .risk_layer import IRiskLayer
    from .execution_layer import IExecutionLayer
    from .memory_layer import IMemoryLayer
