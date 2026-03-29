"""
Main Engine Module
==================
VN.PY MainEngine wrapper with CTA Strategy integration.
"""

import os
import time
import json
import threading
from typing import Dict, Any, Optional, List
from pathlib import Path
from loguru import logger
from datetime import datetime

from .shared_state import shared_state
from .rl_module import get_rl_agent


TRADING_MODE = os.getenv("TRADING_MODE", "paper")
CONFIG_DIR = Path("/vnpy/config")
MEMORY_DIR = Path("/vnpy/memory")


class TradingEngine:
    def __init__(self):
        self.running = False
        self.strategies: Dict[str, Any] = {}
        self.positions: Dict[str, Dict[str, Any]] = {}
        self.orders: Dict[str, Dict[str, Any]] = {}
        self.gateways: Dict[str, Any] = {}
        
        self.rl_agent = None
        self.strategy_config = self._load_strategies()
        
        self._init_gateways()
        
    def _load_strategies(self) -> Dict[str, Any]:
        config_file = CONFIG_DIR / "strategies.json"
        if config_file.exists():
            try:
                with open(config_file) as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load strategies: {e}")
        
        return {
            "strategies": [
                {
                    "name": "RL_Strategy",
                    "symbol": "BTCUSDT",
                    "enabled": True,
                    "mode": TRADING_MODE,
                    "parameters": {
                        "window_size": 50,
                        "risk_threshold": 0.1
                    }
                }
            ]
        }
    
    def _init_gateways(self):
        api_key = os.getenv("BINANCE_API_KEY", "")
        secret_key = os.getenv("BINANCE_SECRET_KEY", "")
        
        if api_key and secret_key:
            logger.info("Binance gateway configured for live trading")
            self.gateways["binance"] = {
                "type": "binance",
                "mode": TRADING_MODE,
                "connected": True
            }
        else:
            logger.info("Running in sandbox/paper mode")
            self.gateways["sandbox"] = {
                "type": "sandbox",
                "mode": "paper",
                "connected": True
            }
    
    def start(self):
        if self.running:
            logger.warning("Engine already running")
            return
        
        self.running = True
        logger.info("Trading Engine started")
        
        self.rl_agent = get_rl_agent()
        
        self._load_positions_from_state()
        self._start_strategies()
        
        shared_state.set_system_status("engine", {
            "status": "running",
            "mode": TRADING_MODE,
            "timestamp": time.time()
        })
    
    def stop(self):
        self.running = False
        logger.info("Trading Engine stopped")
        
        self._save_positions_to_state()
        
        if self.rl_agent:
            self.rl_agent.save_checkpoint()
        
        shared_state.set_system_status("engine", {
            "status": "stopped",
            "timestamp": time.time()
        })
    
    def _load_positions_from_state(self):
        saved_positions = shared_state.get_all_positions()
        self.positions = saved_positions
        logger.info(f"Loaded {len(self.positions)} positions from state")
    
    def _save_positions_to_state(self):
        for symbol, position in self.positions.items():
            shared_state.set_position(symbol, position)
        logger.info(f"Saved {len(self.positions)} positions to state")
    
    def _start_strategies(self):
        for strategy_cfg in self.strategy_config.get("strategies", []):
            if strategy_cfg.get("enabled", False):
                self.strategies[strategy_cfg["name"]] = {
                    "config": strategy_cfg,
                    "running": True,
                    "pnl": 0.0,
                    "trades": 0
                }
                logger.info(f"Started strategy: {strategy_cfg['name']}")
    
    def process_market_data(self, symbol: str, data: Dict[str, Any]):
        if not self.running:
            return
        
        market_state = {
            symbol: {
                "price": data.get("price", 0),
                "volume": data.get("volume", 0),
                "position": self.positions.get(symbol, {}).get("size", 0),
                "pnl": self.positions.get(symbol, {}).get("pnl", 0),
                "volatility": data.get("volatility", 0.5),
                "trend": data.get("trend", 0)
            }
        }
        
        if self.rl_agent and "RL_Strategy" in self.strategies:
            decision = self.rl_agent.get_action_with_risk(market_state)
            
            shared_state.log_rl_decision({
                "symbol": symbol,
                "action": decision["action"],
                "expected_pnl": decision["evaluation"].get("expected_pnl", 0),
                "risk_metrics": decision["evaluation"].get("risk_metrics", {}),
                "timestamp": time.time()
            })
            
            if decision["action"] != "hold":
                self._execute_action(symbol, decision["action"], data.get("price", 0))
    
    def _execute_action(self, symbol: str, action: str, price: float):
        order_id = f"ord_{int(time.time() * 1000)}"
        
        order = {
            "order_id": order_id,
            "symbol": symbol,
            "action": action,
            "price": price,
            "status": "filled",
            "timestamp": time.time(),
            "mode": TRADING_MODE
        }
        
        self.orders[order_id] = order
        
        if symbol not in self.positions:
            self.positions[symbol] = {"size": 0, "pnl": 0, "avg_price": price}
        
        pos = self.positions[symbol]
        
        if action == "buy":
            pos["size"] = pos.get("size", 0) + 1
        elif action == "sell":
            pos["size"] = pos.get("size", 0) - 1
        elif action == "close":
            pos["size"] = 0
        
        pos["avg_price"] = price
        self.positions[symbol] = pos
        
        shared_state.set_order(order_id, order)
        shared_state.set_position(symbol, pos)
        
        logger.info(f"Order executed: {action} {symbol} @ {price}")
    
    def get_status(self) -> Dict[str, Any]:
        return {
            "running": self.running,
            "mode": TRADING_MODE,
            "positions": self.positions,
            "orders": len(self.orders),
            "strategies": {name: {"running": s["running"], "pnl": s["pnl"]} 
                          for name, s in self.strategies.items()},
            "gateways": list(self.gateways.keys()),
            "timestamp": time.time()
        }
    
    def get_positions(self) -> Dict[str, Dict[str, Any]]:
        return self.positions
    
    def get_pnl(self) -> Dict[str, float]:
        total_pnl = sum(p.get("pnl", 0) for p in self.positions.values())
        return {
            "total": total_pnl,
            "by_symbol": {s: p.get("pnl", 0) for s, p in self.positions.items()}
        }
    
    def set_position_target(self, symbol: str, target_size: int) -> bool:
        current = self.positions.get(symbol, {}).get("size", 0)
        diff = target_size - current
        
        if diff > 0:
            self._execute_action(symbol, "buy", 0)
        elif diff < 0:
            self._execute_action(symbol, "sell", 0)
        
        return True


engine: Optional[TradingEngine] = None


def get_engine() -> TradingEngine:
    global engine
    if engine is None:
        engine = TradingEngine()
    return engine
