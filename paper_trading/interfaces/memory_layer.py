"""
Memory Layer Interface
======================
Contract for persistent storage layer (PostgreSQL + Redis).
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
from .base import BaseLayer, LayerInput, LayerOutput, Trade, DecisionRecord, MetricsRecord


class IMemoryLayer(ABC):
    """Memory layer interface - handles persistence"""
    
    @abstractmethod
    def save_trade(self, trade: Trade) -> LayerOutput:
        """Save trade to database"""
        pass
    
    @abstractmethod
    def update_trade(self, trade: Trade) -> LayerOutput:
        """Update trade in database"""
        pass
    
    @abstractmethod
    def get_trades(self, filters: Dict[str, Any]) -> List[Dict]:
        """Get trades with filters"""
        pass
    
    @abstractmethod
    def save_decision(self, decision: DecisionRecord) -> LayerOutput:
        """Save decision to database"""
        pass
    
    @abstractmethod
    def get_decisions(self, limit: int = 100) -> List[Dict]:
        """Get recent decisions"""
        pass
    
    @abstractmethod
    def save_metric(self, metric: MetricsRecord) -> LayerOutput:
        """Save metric to database"""
        pass
    
    @abstractmethod
    def get_metrics(self, metric_type: str = None, days: int = 30) -> List[Dict]:
        """Get metrics"""
        pass
    
    @abstractmethod
    def log_event(self, event_type: str, severity: str, message: str,
                  details: Dict = None, layer_name: str = None) -> LayerOutput:
        """Log system event"""
        pass
    
    @abstractmethod
    def update_layer_health(self, layer_name: str, status: str,
                           error_count: int = 0, error: str = None) -> LayerOutput:
        """Update layer health status"""
        pass
    
    @abstractmethod
    def get_layer_health(self) -> List[Dict]:
        """Get health of all layers"""
        pass
    
    @abstractmethod
    def cache_set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Set cache value in Redis"""
        pass
    
    @abstractmethod
    def cache_get(self, key: str) -> Optional[Any]:
        """Get cache value from Redis"""
        pass


class MemoryLayer(BaseLayer, IMemoryLayer):
    """Memory layer implementation using PostgreSQL and Redis"""
    
    name = "memory"
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.postgres_config = config.get('postgres', {})
        self.redis_config = config.get('redis', {})
        self._postgres_manager = None
        self._redis_client = None
    
    def initialize(self):
        """Initialize connections"""
        try:
            from ..layers.layer9_memory.postgres_manager import get_postgres_manager
            self._postgres_manager = get_postgres_manager(self.postgres_config)
            self._postgres_manager.connect()
            self._postgres_manager.connect_redis(
                host=self.redis_config.get('host', 'localhost'),
                port=self.redis_config.get('port', 6379)
            )
            self.mark_healthy()
        except Exception as e:
            self.mark_unhealthy(str(e))
    
    def process(self, input_data: LayerInput) -> LayerOutput:
        """Process memory request"""
        try:
            action = input_data.get('action')
            
            if action == 'save_trade':
                trade = input_data.get('trade')
                return self.save_trade(trade)
            elif action == 'save_decision':
                decision = input_data.get('decision')
                return self.save_decision(decision)
            elif action == 'save_metric':
                metric = input_data.get('metric')
                return self.save_metric(metric)
            elif action == 'log_event':
                return self.log_event(
                    input_data.get('event_type'),
                    input_data.get('severity'),
                    input_data.get('message'),
                    input_data.get('details'),
                    input_data.get('layer_name')
                )
            elif action == 'get_trades':
                return LayerOutput(
                    result=self.get_trades(input_data.get('filters', {})),
                    success=True,
                    layer_name=self.name
                )
            elif action == 'get_layer_health':
                return LayerOutput(
                    result=self.get_layer_health(),
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
    
    def save_trade(self, trade: Trade) -> LayerOutput:
        """Save trade to database"""
        if not self._postgres_manager:
            return LayerOutput(result=None, success=False, 
                             error="PostgreSQL not connected", layer_name=self.name)
        
        try:
            from ..layers.layer9_memory.postgres_manager import TradeRecord
            trade_record = TradeRecord(
                trade_id=trade.trade_id,
                symbol=trade.symbol,
                side=trade.side,
                quantity=trade.quantity,
                entry_price=trade.entry_price,
                exit_price=trade.exit_price,
                pnl=trade.pnl,
                pnl_pct=trade.pnl_pct,
                status=trade.status,
                strategy=trade.strategy,
                regime=trade.regime,
                confidence=trade.confidence,
                score=trade.score,
                stop_loss=trade.stop_loss,
                take_profit=trade.take_profit,
                explore_exploit=trade.explore_exploit,
                executed_at=trade.executed_at,
                closed_at=trade.closed_at
            )
            trade_id = self._postgres_manager.save_trade(trade_record)
            return LayerOutput(
                result={'trade_id': trade_id},
                success=True,
                layer_name=self.name
            )
        except Exception as e:
            return LayerOutput(result=None, success=False, 
                             error=str(e), layer_name=self.name)
    
    def update_trade(self, trade: Trade) -> LayerOutput:
        """Update trade in database"""
        if not self._postgres_manager:
            return LayerOutput(result=None, success=False,
                             error="PostgreSQL not connected", layer_name=self.name)
        
        try:
            from ..layers.layer9_memory.postgres_manager import TradeRecord
            trade_record = TradeRecord(
                trade_id=trade.trade_id,
                symbol=trade.symbol,
                side=trade.side,
                quantity=trade.quantity,
                entry_price=trade.entry_price,
                exit_price=trade.exit_price,
                pnl=trade.pnl,
                pnl_pct=trade.pnl_pct,
                status=trade.status,
                strategy=trade.strategy,
                regime=trade.regime,
                confidence=trade.confidence,
                score=trade.score,
                stop_loss=trade.stop_loss,
                take_profit=trade.take_profit,
                explore_exploit=trade.explore_exploit,
                executed_at=trade.executed_at,
                closed_at=trade.closed_at
            )
            success = self._postgres_manager.update_trade(trade_record)
            return LayerOutput(result={'updated': success}, success=success,
                             layer_name=self.name)
        except Exception as e:
            return LayerOutput(result=None, success=False,
                             error=str(e), layer_name=self.name)
    
    def get_trades(self, filters: Dict[str, Any]) -> List[Dict]:
        """Get trades with filters"""
        if not self._postgres_manager:
            return []
        
        symbol = filters.get('symbol')
        status = filters.get('status')
        
        if status == 'open':
            return self._postgres_manager.get_open_trades(symbol)
        return self._postgres_manager.get_trade_history(symbol, filters.get('limit', 50))
    
    def save_decision(self, decision: DecisionRecord) -> LayerOutput:
        """Save decision to database"""
        if not self._postgres_manager:
            return LayerOutput(result=None, success=False,
                             error="PostgreSQL not connected", layer_name=self.name)
        
        try:
            decision_id = self._postgres_manager.save_decision(decision)
            return LayerOutput(result={'decision_id': decision_id}, success=True,
                             layer_name=self.name)
        except Exception as e:
            return LayerOutput(result=None, success=False,
                             error=str(e), layer_name=self.name)
    
    def get_decisions(self, limit: int = 100) -> List[Dict]:
        """Get recent decisions"""
        if not self._postgres_manager:
            return []
        return self._postgres_manager.get_recent_decisions(limit)
    
    def save_metric(self, metric: MetricsRecord) -> LayerOutput:
        """Save metric to database"""
        if not self._postgres_manager:
            return LayerOutput(result=None, success=False,
                             error="PostgreSQL not connected", layer_name=self.name)
        
        try:
            metric_id = self._postgres_manager.save_metric(metric)
            return LayerOutput(result={'metric_id': metric_id}, success=True,
                             layer_name=self.name)
        except Exception as e:
            return LayerOutput(result=None, success=False,
                             error=str(e), layer_name=self.name)
    
    def get_metrics(self, metric_type: str = None, days: int = 30) -> List[Dict]:
        """Get metrics"""
        if not self._postgres_manager:
            return []
        return self._postgres_manager.get_metrics(metric_type, days=days)
    
    def log_event(self, event_type: str, severity: str, message: str,
                  details: Dict = None, layer_name: str = None) -> LayerOutput:
        """Log system event"""
        if not self._postgres_manager:
            return LayerOutput(result={'logged': False}, success=False,
                             error="PostgreSQL not connected", layer_name=self.name)
        
        try:
            success = self._postgres_manager.log_event(event_type, severity, message, details, layer_name)
            return LayerOutput(result={'logged': success}, success=success, layer_name=self.name)
        except Exception as e:
            return LayerOutput(result=None, success=False, error=str(e), layer_name=self.name)
    
    def update_layer_health(self, layer_name: str, status: str,
                           error_count: int = 0, error: str = None) -> LayerOutput:
        """Update layer health status"""
        if not self._postgres_manager:
            return LayerOutput(result=None, success=False,
                             error="PostgreSQL not connected", layer_name=self.name)
        
        try:
            success = self._postgres_manager.update_layer_health(layer_name, status, error_count, error)
            return LayerOutput(result={'updated': success}, success=success, layer_name=self.name)
        except Exception as e:
            return LayerOutput(result=None, success=False, error=str(e), layer_name=self.name)
    
    def get_layer_health(self) -> List[Dict]:
        """Get health of all layers"""
        if not self._postgres_manager:
            return []
        return self._postgres_manager.get_layer_health()
    
    def cache_set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Set cache value in Redis"""
        if not self._postgres_manager:
            return False
        return self._postgres_manager.cache_set(key, value, ttl)
    
    def cache_get(self, key: str) -> Optional[Any]:
        """Get cache value from Redis"""
        if not self._postgres_manager:
            return None
        return self._postgres_manager.cache_get(key)
