"""
Layer 9: Memory Layer - PostgreSQL Manager
==========================================
Handles persistent storage for trading system using PostgreSQL.
Provides ACID-compliant storage for trades, decisions, metrics, and events.
"""

import os
import json
import threading
from datetime import datetime, date
from typing import Dict, Any, Optional, List
from decimal import Decimal
from contextlib import contextmanager
from dataclasses import dataclass, asdict

from loguru import logger

try:
    import psycopg2
    from psycopg2 import pool
    from psycopg2.extras import RealDictCursor, Json
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False
    logger.warning("psycopg2 not available, PostgreSQL disabled")

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("redis not available")


@dataclass
class TradeRecord:
    """Trade record for database storage"""
    trade_id: str
    symbol: str
    side: str
    quantity: float
    entry_price: Optional[float] = None
    exit_price: Optional[float] = None
    pnl: float = 0.0
    pnl_pct: float = 0.0
    status: str = 'open'
    strategy: Optional[str] = None
    regime: Optional[str] = None
    confidence: Optional[float] = None
    score: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    explore_exploit: str = 'exploit'
    executed_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None


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
    explore_exploit: str = 'exploit'
    layer_outputs: Optional[Dict] = None
    metadata: Optional[Dict] = None


@dataclass
class MetricsRecord:
    """Metrics record for database storage"""
    metric_type: str
    value: float
    period: str = 'daily'
    metadata: Optional[Dict] = None


class PostgreSQLManager:
    """
    PostgreSQL connection manager with connection pooling.
    Handles all database operations for the trading system.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        self.config = config or {}
        self.host = self.config.get('host', 'localhost')
        self.port = self.config.get('port', 5432)
        self.database = self.config.get('database', 'trading_system')
        self.user = self.config.get('user', 'trader')
        self.password = self.config.get('password', os.getenv('POSTGRES_PASSWORD', 'nwa45690'))
        
        self.pool = None
        self.redis_client = None
        self._connected = False
        self._initialized = True
        
        logger.info(f"PostgreSQL Manager initialized: {self.user}@{self.host}:{self.port}/{self.database}")
    
    def connect(self) -> bool:
        """Establish connection to PostgreSQL"""
        if not POSTGRES_AVAILABLE:
            logger.error("psycopg2 not available")
            return False
        
        try:
            self.pool = pool.ThreadedConnectionPool(
                minconn=2,
                maxconn=10,
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password
            )
            self._connected = True
            logger.info(f"Connected to PostgreSQL: {self.host}:{self.port}")
            return True
        except psycopg2.OperationalError as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            self._connected = False
            return False
    
    def disconnect(self):
        """Close all connections"""
        if self.pool:
            self.pool.closeall()
            self._connected = False
            logger.info("Disconnected from PostgreSQL")
    
    def connect_redis(self, host: str = 'localhost', port: int = 6379) -> bool:
        """Connect to Redis for caching"""
        if not REDIS_AVAILABLE:
            logger.warning("redis not available")
            return False
        
        try:
            self.redis_client = redis.Redis(
                host=host,
                port=port,
                db=0,
                decode_responses=True
            )
            self.redis_client.ping()
            logger.info(f"Connected to Redis: {host}:{port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            return False
    
    @contextmanager
    def get_connection(self):
        """Get connection from pool"""
        conn = self.pool.getconn()
        try:
            yield conn
        finally:
            self.pool.putconn(conn)
    
    def execute(self, query: str, params: tuple = None) -> bool:
        """Execute a query"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, params)
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"Query execution error: {e}")
            return False
    
    def fetch_one(self, query: str, params: tuple = None) -> Optional[Dict]:
        """Fetch one row"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(query, params)
                    return cursor.fetchone()
        except Exception as e:
            logger.error(f"Query fetch error: {e}")
            return None
    
    def fetch_all(self, query: str, params: tuple = None) -> List[Dict]:
        """Fetch all rows"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(query, params)
                    return cursor.fetchall()
        except Exception as e:
            logger.error(f"Query fetch error: {e}")
            return []
    
    # ==================== TRADE OPERATIONS ====================
    
    def save_trade(self, trade: TradeRecord) -> Optional[int]:
        """Save a trade to database"""
        query = """
            INSERT INTO trades (
                trade_id, symbol, side, quantity, entry_price, exit_price,
                pnl, pnl_pct, status, strategy, regime, confidence, score,
                stop_loss, take_profit, explore_exploit, executed_at, closed_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            ) RETURNING id
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (
                        trade.trade_id, trade.symbol, trade.side, trade.quantity,
                        trade.entry_price, trade.exit_price, trade.pnl, trade.pnl_pct,
                        trade.status, trade.strategy, trade.regime, trade.confidence,
                        trade.score, trade.stop_loss, trade.take_profit,
                        trade.explore_exploit, trade.executed_at, trade.closed_at
                    ))
                    trade_id = cursor.fetchone()[0]
                    conn.commit()
                    
                    # Also cache in Redis for fast access
                    self.cache_set(f"trade:{trade.trade_id}", asdict(trade), ttl=3600)
                    
                    return trade_id
        except psycopg2.IntegrityError:
            logger.warning(f"Trade {trade.trade_id} already exists, updating...")
            return self.update_trade(trade)
        except Exception as e:
            logger.error(f"Error saving trade: {e}")
            return None
    
    def update_trade(self, trade: TradeRecord) -> bool:
        """Update an existing trade"""
        query = """
            UPDATE trades SET
                exit_price = %s, pnl = %s, pnl_pct = %s, status = %s,
                closed_at = %s, updated_at = NOW()
            WHERE trade_id = %s
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (
                        trade.exit_price, trade.pnl, trade.pnl_pct,
                        trade.status, trade.closed_at, trade.trade_id
                    ))
                    conn.commit()
                    
                    # Invalidate cache
                    self.cache_delete(f"trade:{trade.trade_id}")
                    
                    return True
        except Exception as e:
            logger.error(f"Error updating trade: {e}")
            return False
    
    def get_trade(self, trade_id: str) -> Optional[Dict]:
        """Get a trade by ID (from cache or DB)"""
        # Try cache first
        cached = self.cache_get(f"trade:{trade_id}")
        if cached:
            return cached
        
        # Fetch from DB
        query = "SELECT * FROM trades WHERE trade_id = %s"
        result = self.fetch_one(query, (trade_id,))
        if result:
            self.cache_set(f"trade:{trade_id}", dict(result), ttl=3600)
        return result
    
    def get_open_trades(self, symbol: str = None) -> List[Dict]:
        """Get all open trades"""
        if symbol:
            query = "SELECT * FROM trades WHERE status = 'open' AND symbol = %s ORDER BY executed_at DESC"
            return self.fetch_all(query, (symbol,))
        query = "SELECT * FROM trades WHERE status = 'open' ORDER BY executed_at DESC"
        return self.fetch_all(query)
    
    def get_trade_history(self, symbol: str = None, limit: int = 50) -> List[Dict]:
        """Get trade history"""
        if symbol:
            query = "SELECT * FROM trades WHERE symbol = %s ORDER BY executed_at DESC LIMIT %s"
            return self.fetch_all(query, (symbol, limit))
        query = "SELECT * FROM trades ORDER BY executed_at DESC LIMIT %s"
        return self.fetch_all(query, (limit,))
    
    def close_trade(self, trade_id: str, exit_price: float, pnl: float, pnl_pct: float) -> bool:
        """Close a trade"""
        trade = self.get_trade(trade_id)
        if not trade:
            return False
        
        trade_record = TradeRecord(
            trade_id=trade['trade_id'],
            symbol=trade['symbol'],
            side=trade['side'],
            quantity=trade['quantity'],
            entry_price=trade['entry_price'],
            exit_price=exit_price,
            pnl=pnl,
            pnl_pct=pnl_pct,
            status='closed',
            strategy=trade['strategy'],
            regime=trade['regime'],
            confidence=trade['confidence'],
            score=trade['score'],
            stop_loss=trade['stop_loss'],
            take_profit=trade['take_profit'],
            explore_exploit=trade['explore_exploit'],
            executed_at=trade['executed_at'],
            closed_at=datetime.now()
        )
        return self.update_trade(trade_record)
    
    # ==================== DECISION OPERATIONS ====================
    
    def save_decision(self, decision: DecisionRecord) -> Optional[int]:
        """Save a decision to database"""
        query = """
            INSERT INTO decisions (
                timestamp, symbol, price, regime, strategy, action,
                confidence, score, risk_passed, rejected_reason,
                explore_exploit, layer_outputs, metadata
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            ) RETURNING id
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (
                        decision.timestamp, decision.symbol, decision.price,
                        decision.regime, decision.strategy, decision.action,
                        decision.confidence, decision.score, decision.risk_passed,
                        decision.rejected_reason, decision.explore_exploit,
                        Json(decision.layer_outputs) if decision.layer_outputs else None,
                        Json(decision.metadata) if decision.metadata else None
                    ))
                    decision_id = cursor.fetchone()[0]
                    conn.commit()
                    return decision_id
        except Exception as e:
            logger.error(f"Error saving decision: {e}")
            return None
    
    def get_recent_decisions(self, limit: int = 100) -> List[Dict]:
        """Get recent decisions"""
        query = "SELECT * FROM decisions ORDER BY timestamp DESC LIMIT %s"
        return self.fetch_all(query, (limit,))
    
    def get_decisions_by_regime(self, regime: str, limit: int = 100) -> List[Dict]:
        """Get decisions by regime"""
        query = "SELECT * FROM decisions WHERE regime = %s ORDER BY timestamp DESC LIMIT %s"
        return self.fetch_all(query, (regime, limit))
    
    # ==================== METRICS OPERATIONS ====================
    
    def save_metric(self, metric: MetricsRecord) -> Optional[int]:
        """Save a metric"""
        query = """
            INSERT INTO metrics (metric_type, value, period, metadata)
            VALUES (%s, %s, %s, %s) RETURNING id
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (
                        metric.metric_type, metric.value, metric.period,
                        Json(metric.metadata) if metric.metadata else None
                    ))
                    metric_id = cursor.fetchone()[0]
                    conn.commit()
                    return metric_id
        except Exception as e:
            logger.error(f"Error saving metric: {e}")
            return None
    
    def get_metrics(self, metric_type: str = None, period: str = 'daily', 
                    days: int = 30) -> List[Dict]:
        """Get metrics"""
        if metric_type:
            query = """
                SELECT * FROM metrics 
                WHERE metric_type = %s AND period = %s 
                AND timestamp > NOW() - INTERVAL '%s days'
                ORDER BY timestamp DESC
            """
            return self.fetch_all(query, (metric_type, period, days))
        query = """
            SELECT * FROM metrics 
            WHERE period = %s AND timestamp > NOW() - INTERVAL '%s days'
            ORDER BY timestamp DESC
        """
        return self.fetch_all(query, (period, days))
    
    def get_performance_summary(self, days: int = 7) -> Dict[str, Any]:
        """Get performance summary"""
        query = """
            SELECT 
                COUNT(*) as total_trades,
                COUNT(*) FILTER (WHERE pnl > 0) as winning_trades,
                COUNT(*) FILTER (WHERE pnl < 0) as losing_trades,
                COALESCE(SUM(pnl), 0) as total_pnl,
                COALESCE(AVG(pnl), 0) as avg_pnl,
                COALESCE(AVG(pnl_pct), 0) as avg_pnl_pct,
                COALESCE(MAX(pnl), 0) as best_trade,
                COALESCE(MIN(pnl), 0) as worst_trade
            FROM trades
            WHERE status = 'closed' 
            AND executed_at > NOW() - INTERVAL '%s days'
        """
        result = self.fetch_one(query, (days,))
        if result:
            total = result['winning_trades'] + result['losing_trades']
            win_rate = (result['winning_trades'] / total * 100) if total > 0 else 0
            result['win_rate'] = win_rate
        return result or {}
    
    # ==================== REGIME PERFORMANCE ====================
    
    def update_regime_performance(self, regime: str, trade_pnl: float, 
                                  confidence: float, won: bool) -> bool:
        """Update regime performance stats"""
        query = """
            INSERT INTO regime_performance (regime, total_trades, winning_trades, 
                                           total_pnl, avg_confidence)
            VALUES (%s, 1, %s, %s, %s)
            ON CONFLICT (regime) DO UPDATE SET
                total_trades = regime_performance.total_trades + 1,
                winning_trades = regime_performance.winning_trades + %s,
                total_pnl = regime_performance.total_pnl + %s,
                avg_confidence = (regime_performance.avg_confidence * regime_performance.total_trades + %s) 
                                / (regime_performance.total_trades + 1),
                win_rate = (regime_performance.winning_trades + %s)::float / 
                          (regime_performance.total_trades + 1) * 100,
                last_updated = NOW()
        """
        try:
            return self.execute(query, (
                regime, 1 if won else 0, trade_pnl, confidence,
                1 if won else 0, trade_pnl, confidence, 1 if won else 0
            ))
        except Exception as e:
            logger.error(f"Error updating regime performance: {e}")
            return False
    
    def get_regime_performance(self) -> List[Dict]:
        """Get performance by regime"""
        query = "SELECT * FROM regime_performance ORDER BY total_trades DESC"
        return self.fetch_all(query)
    
    # ==================== SYSTEM EVENTS ====================
    
    def log_event(self, event_type: str, severity: str, message: str,
                  details: Dict = None, layer_name: str = None) -> bool:
        """Log a system event"""
        query = """
            INSERT INTO system_events (event_type, severity, message, details, layer_name)
            VALUES (%s, %s, %s, %s, %s)
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (
                        event_type, severity, message,
                        Json(details) if details else None, layer_name
                    ))
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"Error logging event: {e}")
            return False
    
    def get_recent_events(self, severity: str = None, limit: int = 100) -> List[Dict]:
        """Get recent system events"""
        if severity:
            query = """
                SELECT * FROM system_events 
                WHERE severity >= %s ORDER BY timestamp DESC LIMIT %s
            """
            severity_order = {'debug': 0, 'info': 1, 'warning': 2, 'error': 3, 'critical': 4}
            min_severity = severity_order.get(severity, 0)
            return self.fetch_all(query, (min_severity, limit))
        query = "SELECT * FROM system_events ORDER BY timestamp DESC LIMIT %s"
        return self.fetch_all(query, (limit,))
    
    # ==================== LAYER HEALTH ====================
    
    def update_layer_health(self, layer_name: str, status: str, 
                            error_count: int = 0, error: str = None) -> bool:
        """Update layer health status"""
        query = """
            INSERT INTO layer_health (layer_name, status, error_count, last_error, last_check)
            VALUES (%s, %s, %s, %s, NOW())
            ON CONFLICT (layer_name) DO UPDATE SET
                status = %s, error_count = %s, last_error = %s, last_check = NOW()
        """
        try:
            return self.execute(query, (
                layer_name, status, error_count, error,
                status, error_count, error
            ))
        except Exception as e:
            logger.error(f"Error updating layer health: {e}")
            return False
    
    def get_layer_health(self) -> List[Dict]:
        """Get health of all layers"""
        query = """
            SELECT * FROM layer_health 
            WHERE (layer_name, last_check) IN (
                SELECT layer_name, MAX(last_check) FROM layer_health GROUP BY layer_name
            )
        """
        return self.fetch_all(query)
    
    # ==================== REDIS CACHE OPERATIONS ====================
    
    def cache_set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Set a cache value in Redis"""
        if not self.redis_client:
            return False
        try:
            serialized = json.dumps(value, default=str)
            self.redis_client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            logger.error(f"Error setting cache: {e}")
            return False
    
    def cache_get(self, key: str) -> Optional[Any]:
        """Get a cache value from Redis"""
        if not self.redis_client:
            return None
        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Error getting cache: {e}")
            return None
    
    def cache_delete(self, key: str) -> bool:
        """Delete a cache value"""
        if not self.redis_client:
            return False
        try:
            self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Error deleting cache: {e}")
            return False
    
    def cache_clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern"""
        if not self.redis_client:
            return 0
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return 0
    
    # ==================== POSITIONS ====================
    
    def save_position(self, symbol: str, side: str, quantity: float,
                      entry_price: float, leverage: int = 1,
                      margin: float = 0) -> Optional[int]:
        """Save a position"""
        query = """
            INSERT INTO positions (symbol, side, quantity, entry_price, leverage, margin)
            VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (symbol, side, quantity, entry_price, leverage, margin))
                    pos_id = cursor.fetchone()[0]
                    conn.commit()
                    
                    # Also cache in Redis
                    pos_key = f"position:{symbol}"
                    self.cache_set(pos_key, {
                        'id': pos_id, 'symbol': symbol, 'side': side,
                        'quantity': quantity, 'entry_price': entry_price,
                        'leverage': leverage, 'margin': margin
                    }, ttl=60)
                    
                    return pos_id
        except Exception as e:
            logger.error(f"Error saving position: {e}")
            return None
    
    def update_position(self, symbol: str, quantity: float, current_price: float,
                        unrealized_pnl: float) -> bool:
        """Update a position"""
        query = """
            UPDATE positions SET
                quantity = %s, current_price = %s, unrealized_pnl = %s, updated_at = NOW()
            WHERE symbol = %s
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (quantity, current_price, unrealized_pnl, symbol))
                    conn.commit()
                    
                    # Invalidate cache
                    self.cache_delete(f"position:{symbol}")
                    
                    return True
        except Exception as e:
            logger.error(f"Error updating position: {e}")
            return False
    
    def close_position(self, symbol: str) -> bool:
        """Close a position"""
        query = "DELETE FROM positions WHERE symbol = %s"
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (symbol,))
                    conn.commit()
                    self.cache_delete(f"position:{symbol}")
                    return True
        except Exception as e:
            logger.error(f"Error closing position: {e}")
            return False
    
    def get_position(self, symbol: str = None) -> Optional[Dict]:
        """Get position (from cache or DB)"""
        if symbol:
            cached = self.cache_get(f"position:{symbol}")
            if cached:
                return cached
            query = "SELECT * FROM positions WHERE symbol = %s"
            result = self.fetch_one(query, (symbol,))
            if result:
                self.cache_set(f"position:{symbol}", dict(result), ttl=60)
            return result
        return None
    
    def get_all_positions(self) -> List[Dict]:
        """Get all open positions"""
        query = "SELECT * FROM positions ORDER BY opened_at DESC"
        return self.fetch_all(query)
    
    # ==================== UTILITY ====================
    
    def is_connected(self) -> bool:
        """Check if connected to PostgreSQL"""
        return self._connected and self.pool is not None
    
    def health_check(self) -> Dict[str, Any]:
        """Check health of all connections"""
        postgres_ok = self.is_connected()
        redis_ok = False
        
        if self.redis_client:
            try:
                self.redis_client.ping()
                redis_ok = True
            except:
                pass
        
        return {
            'postgres': 'healthy' if postgres_ok else 'unhealthy',
            'redis': 'healthy' if redis_ok else 'unhealthy',
            'timestamp': datetime.now().isoformat()
        }


# Global instance
_postgres_manager: Optional[PostgreSQLManager] = None


def get_postgres_manager(config: Dict[str, Any] = None) -> PostgreSQLManager:
    """Get or create PostgreSQL manager instance"""
    global _postgres_manager
    if _postgres_manager is None:
        _postgres_manager = PostgreSQLManager(config)
    return _postgres_manager


def init_postgres(config: Dict[str, Any] = None) -> bool:
    """Initialize PostgreSQL with config"""
    global _postgres_manager
    manager = get_postgres_manager(config)
    postgres_ok = manager.connect()
    redis_ok = manager.connect_redis()
    return postgres_ok
