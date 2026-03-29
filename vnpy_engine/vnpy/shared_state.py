"""
Shared State Layer
=================
Redis + Filesystem integration for real-time state sharing
between VN.PY engine and Financial Orchestrator.
"""

import os
import json
import pickle
import redis
from typing import Any, Dict, Optional
from pathlib import Path
from loguru import logger

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

MEMORY_DIR = Path("/vnpy/memory")
LOGS_DIR = Path("/vnpy/logs")
MODELS_DIR = Path("/vnpy/models")

MEMORY_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)


class SharedState:
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self._connect_redis()
        
    def _connect_redis(self):
        try:
            self.redis_client = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                decode_responses=True,
                socket_connect_timeout=5
            )
            self.redis_client.ping()
            logger.info(f"Connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Using memory-only mode.")
            self.redis_client = None
    
    def set_position(self, symbol: str, position: Dict[str, Any]):
        key = f"position:{symbol}"
        self._redis_set(key, position)
        logger.debug(f"Position updated: {symbol} = {position}")
    
    def get_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        key = f"position:{symbol}"
        return self._redis_get(key)
    
    def get_all_positions(self) -> Dict[str, Dict[str, Any]]:
        positions = {}
        if not self.redis_client:
            return positions
        for key in self.redis_client.keys("position:*"):
            symbol = key.replace("position:", "")
            positions[symbol] = self._redis_get(key)
        return positions
    
    def set_order(self, order_id: str, order_data: Dict[str, Any]):
        key = f"order:{order_id}"
        self._redis_set(key, order_data)
    
    def get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        key = f"order:{order_id}"
        return self._redis_get(key)
    
    def set_pnl(self, session_id: str, pnl_data: Dict[str, Any]):
        key = f"pnl:{session_id}"
        self._redis_set(key, pnl_data)
    
    def get_pnl(self, session_id: str) -> Optional[Dict[str, Any]]:
        key = f"pnl:{session_id}"
        return self._redis_get(key)
    
    def set_signal(self, symbol: str, signal: Dict[str, Any]):
        key = f"signal:{symbol}"
        self._redis_set(key, signal)
        logger.info(f"Signal set: {symbol} = {signal}")
    
    def get_signal(self, symbol: str) -> Optional[Dict[str, Any]]:
        key = f"signal:{symbol}"
        return self._redis_get(key)
    
    def set_risk_limits(self, limits: Dict[str, Any]):
        key = "risk:limits"
        self._redis_set(key, limits)
    
    def get_risk_limits(self) -> Dict[str, Any]:
        return self._redis_get("risk:limits") or {}
    
    def log_rl_decision(self, decision: Dict[str, Any]):
        key = f"rl:decision:{decision.get('timestamp', 0)}"
        self._redis_set(key, decision)
        logger.info(f"RL Decision logged: {decision.get('action')}")
    
    def set_system_status(self, component: str, status: Dict[str, Any]):
        key = f"status:{component}"
        self._redis_set(key, status)
    
    def get_system_status(self, component: str) -> Dict[str, Any]:
        return self._redis_get(f"status:{component}") or {"status": "unknown"}
    
    def publish_event(self, channel: str, message: Dict[str, Any]):
        if self.redis_client:
            self.redis_client.publish(channel, json.dumps(message))
    
    def subscribe(self, channel: str):
        if self.redis_client:
            return self.redis_client.pubsub()
        return None
    
    def save_checkpoint(self, name: str, data: Any) -> bool:
        filepath = MEMORY_DIR / f"{name}.pkl"
        try:
            with open(filepath, 'wb') as f:
                pickle.dump(data, f)
            logger.info(f"Checkpoint saved: {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to save checkpoint {name}: {e}")
            return False
    
    def load_checkpoint(self, name: str) -> Optional[Any]:
        filepath = MEMORY_DIR / f"{name}.pkl"
        if not filepath.exists():
            logger.warning(f"Checkpoint not found: {filepath}")
            return None
        try:
            with open(filepath, 'rb') as f:
                data = pickle.load(f)
            logger.info(f"Checkpoint loaded: {filepath}")
            return data
        except Exception as e:
            logger.error(f"Failed to load checkpoint {name}: {e}")
            return None
    
    def append_log(self, filename: str, message: str):
        filepath = LOGS_DIR / filename
        try:
            with open(filepath, 'a') as f:
                f.write(f"{message}\n")
        except Exception as e:
            logger.error(f"Failed to write log: {e}")
    
    def _redis_set(self, key: str, value: Any):
        if self.redis_client:
            try:
                serialized = json.dumps(value) if isinstance(value, (dict, list)) else value
                self.redis_client.set(key, serialized)
            except Exception as e:
                logger.error(f"Redis set failed for {key}: {e}")
    
    def _redis_get(self, key: str) -> Any:
        if not self.redis_client:
            return None
        try:
            value = self.redis_client.get(key)
            if value:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            return None
        except Exception as e:
            logger.error(f"Redis get failed for {key}: {e}")
            return None
    
    def health_check(self) -> bool:
        if self.redis_client:
            try:
                self.redis_client.ping()
                return True
            except:
                return False
        return False


shared_state = SharedState()
