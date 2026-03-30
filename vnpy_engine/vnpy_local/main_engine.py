"""
Main Engine Module
=================
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
from dotenv import load_dotenv
load_dotenv()

from vnpy.event import EventEngine
from vnpy.trader.engine import MainEngine as VnpyMainEngine

from vnpy_ctastrategy import CtaStrategyApp

from .shared_state import shared_state
from .rl_module import get_rl_agent
from .market_data import get_market_data_instance
from .strategies import CTA_STRATEGY_REGISTRY


TRADING_MODE = os.getenv("TRADING_MODE", "paper")
CONFIG_DIR = Path("/vnpy/config")
MEMORY_DIR = Path("/vnpy/memory")


class CtaStrategyManager:
    def __init__(self, cta_engine, trading_engine):
        self.cta_engine = cta_engine
        self.trading_engine = trading_engine
        self.cta_strategies: Dict[str, Any] = {}
        self.strategy_vt_symbols: Dict[str, str] = {}

    def add_strategy(self, strategy_name: str, class_name: str, vt_symbol: str, parameters: Dict) -> bool:
        if class_name not in CTA_STRATEGY_REGISTRY:
            logger.error(f"Strategy class {class_name} not found in registry")
            return False

        strategy_class = CTA_STRATEGY_REGISTRY[class_name]

        try:
            self.cta_engine.add_strategy(
                strategy_class,
                strategy_name,
                vt_symbol,
                parameters
            )
            self.cta_strategies[strategy_name] = {
                "class": class_name,
                "vt_symbol": vt_symbol,
                "parameters": parameters
            }
            self.strategy_vt_symbols[strategy_name] = vt_symbol
            logger.info(f"Added CTA strategy: {strategy_name} ({class_name})")
            return True
        except Exception as e:
            logger.error(f"Failed to add strategy {strategy_name}: {e}")
            return False

    def init_strategy(self, strategy_name: str) -> bool:
        try:
            self.cta_engine.init_strategy(strategy_name)
            logger.info(f"Initialized CTA strategy: {strategy_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to init strategy {strategy_name}: {e}")
            return False

    def start_strategy(self, strategy_name: str) -> bool:
        try:
            self.cta_engine.start_strategy(strategy_name)
            logger.info(f"Started CTA strategy: {strategy_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to start strategy {strategy_name}: {e}")
            return False

    def stop_strategy(self, strategy_name: str) -> bool:
        try:
            self.cta_engine.stop_strategy(strategy_name)
            logger.info(f"Stopped CTA strategy: {strategy_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to stop strategy {strategy_name}: {e}")
            return False

    def get_strategy_status(self, strategy_name: str) -> Dict[str, Any]:
        strategy_data = self.cta_engine.get_strategy_data(strategy_name)
        return {
            "inited": strategy_data.get("inited", False),
            "trading": strategy_data.get("trading", False),
            "pos": strategy_data.get("pos", 0)
        }

    def get_all_strategy_status(self) -> Dict[str, Dict[str, Any]]:
        return {
            name: self.get_strategy_status(name)
            for name in self.cta_strategies.keys()
        }

    def remove_strategy(self, strategy_name: str) -> bool:
        try:
            self.cta_engine.remove_strategy(strategy_name)
            if strategy_name in self.cta_strategies:
                del self.cta_strategies[strategy_name]
            if strategy_name in self.strategy_vt_symbols:
                del self.strategy_vt_symbols[strategy_name]
            return True
        except Exception as e:
            logger.error(f"Failed to remove strategy {strategy_name}: {e}")
            return False


class TradingEngine:
    def __init__(self):
        self.running = False
        self.strategies: Dict[str, Any] = {}
        self.cta_strategies: Dict[str, Any] = {}
        self.positions: Dict[str, Dict[str, Any]] = {}
        self.orders: Dict[str, Dict[str, Any]] = {}
        self.gateways: Dict[str, Any] = {}

        self.rl_agent = None
        self.strategy_config = self._load_strategies()
        self.market_data = None

        self._init_vnpy_engine()
        self._init_gateways()
        self._init_market_data()

    def _init_vnpy_engine(self):
        try:
            self.event_engine = EventEngine()
            self.vnpy_main_engine = VnpyMainEngine(self.event_engine)
            self.cta_app = self.vnpy_main_engine.add_app(CtaStrategyApp)
            self.cta_engine = self.vnpy_main_engine.get_engine("CtaStrategyApp")
            self.cta_manager = CtaStrategyManager(self.cta_engine, self)
            logger.info("VN.PY CtaEngine initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize VN.PY CtaEngine: {e}")
            self.cta_engine = None
            self.cta_manager = None

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
            try:
                from vnpy_binance import BinanceGateway
                self.vnpy_main_engine.add_gateway(BinanceGateway)
                self.gateways["binance"] = {
                    "type": "binance",
                    "mode": TRADING_MODE,
                    "connected": True
                }
                # Set gateway setting
                setting = {
                    "key": api_key,
                    "secret": secret_key,
                    "session_number": 3,
                    "proxy_host": "",
                    "proxy_port": 0
                }
                self.vnpy_main_engine.write_gateway_setting(BinanceGateway.__name__, setting)
                logger.info("Binance gateway added successfully")
            except Exception as e:
                logger.error(f"Failed to add Binance gateway: {e}")
                self.gateways["sandbox"] = {
                    "type": "sandbox",
                    "mode": "paper",
                    "connected": True
                }
        else:
            logger.info("Running in sandbox/paper mode")
            self.gateways["sandbox"] = {
                "type": "sandbox",
                "mode": "paper",
                "connected": True
            }

    def _init_market_data(self):
        symbols = []
        for strategy in self.strategy_config.get("strategies", []):
            if strategy.get("enabled"):
                symbol = strategy.get("symbol", "BTCUSDT")
                if symbol not in symbols:
                    symbols.append(symbol)

        if not symbols:
            symbols = ["BTCUSDT"]

        self.market_data = get_market_data_instance(symbols)

        for symbol in symbols:
            if hasattr(self.market_data, 'subscribe_ticker'):
                self.market_data.subscribe_ticker(
                    lambda data, s=symbol: self._on_market_data(s, data),
                    symbol=symbol
                )
            elif hasattr(self.market_data, 'subscribe'):
                self.market_data.subscribe(
                    lambda data, s=symbol: self._on_market_data(s, data),
                    symbol=symbol
                )

        logger.info(f"Market data initialized for symbols: {symbols}")

    def _convert_to_bar(self, market_data: Dict[str, Any]) -> Optional[Any]:
        try:
            from vnpy.trader.object import BarData
            from datetime import datetime

            return BarData(
                symbol=market_data.get("symbol", "UNKNOWN"),
                exchange=None,
                datetime=datetime.fromtimestamp(market_data.get("timestamp", time.time())),
                open_price=market_data.get("open", market_data.get("price", 0)),
                high_price=market_data.get("high", market_data.get("price", 0)),
                low_price=market_data.get("low", market_data.get("price", 0)),
                close_price=market_data.get("price", 0),
                volume=market_data.get("volume", 0),
                turnover=0,
                open_interest=0
            )
        except Exception as e:
            logger.error(f"Failed to convert market data to bar: {e}")
            return None

    def start(self):
        if self.running:
            logger.warning("Engine already running")
            return

        self.running = True
        logger.info("Trading Engine started")

        self.rl_agent = get_rl_agent()

        if self.market_data:
            self.market_data.start()

        self._load_positions_from_state()
        self._start_strategies()
        self._init_cta_strategies()

        shared_state.set_system_status("engine", {
            "status": "running",
            "mode": TRADING_MODE,
            "timestamp": time.time()
        })

    def stop(self):
        self.running = False
        logger.info("Trading Engine stopped")

        self._stop_cta_strategies()

        if self.market_data:
            self.market_data.stop()

        self._save_positions_to_state()

        if self.rl_agent:
            self.rl_agent.save_checkpoint()

        if hasattr(self, 'vnpy_main_engine'):
            try:
                self.vnpy_main_engine.close()
            except Exception as e:
                logger.error(f"Error closing VN.PY main engine: {e}")

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
            strategy_type = strategy_cfg.get("type", "rl")

            if not strategy_cfg.get("enabled", False):
                continue

            if strategy_type in ["cta", "cta_rl"]:
                self.cta_strategies[strategy_cfg["name"]] = {
                    "config": strategy_cfg,
                    "running": False,
                    "pnl": 0.0,
                    "trades": 0
                }
            else:
                self.strategies[strategy_cfg["name"]] = {
                    "config": strategy_cfg,
                    "running": True,
                    "pnl": 0.0,
                    "trades": 0
                }
                logger.info(f"Started strategy: {strategy_cfg['name']}")

    def _init_cta_strategies(self):
        if not self.cta_manager:
            logger.warning("CtaEngine not available, skipping CTA strategy initialization")
            return

        for strategy_cfg in self.strategy_config.get("strategies", []):
            strategy_type = strategy_cfg.get("type", "rl")

            if strategy_type not in ["cta", "cta_rl"]:
                continue

            if not strategy_cfg.get("enabled", False):
                continue

            strategy_name = strategy_cfg.get("name")
            class_name = strategy_cfg.get("class", "MomentumCtaStrategy")
            vt_symbol = strategy_cfg.get("vt_symbol", f"{strategy_cfg.get('symbol', 'BTCUSDT')}.BINANCE")
            parameters = strategy_cfg.get("parameters", {})

            success = self.cta_manager.add_strategy(
                strategy_name,
                class_name,
                vt_symbol,
                parameters
            )

            if success:
                self.cta_manager.init_strategy(strategy_name)
                self.cta_manager.start_strategy(strategy_name)

                if strategy_name in self.cta_strategies:
                    self.cta_strategies[strategy_name]["running"] = True

                logger.info(f"Started CTA strategy: {strategy_name}")

    def _stop_cta_strategies(self):
        if not self.cta_manager:
            return

        for strategy_name in list(self.cta_strategies.keys()):
            self.cta_manager.stop_strategy(strategy_name)
            logger.info(f"Stopped CTA strategy: {strategy_name}")

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

        if self.cta_engine and self.rl_agent:
            self._process_cta_with_rl(symbol, data, market_state)

    def _process_cta_with_rl(self, symbol: str, data: Dict[str, Any], market_state: Dict):
        bar = self._convert_to_bar(data)
        if not bar:
            return

        for strategy_name, strategy_info in self.cta_strategies.items():
            config = strategy_info.get("config", {})
            if config.get("type") == "cta_rl" and config.get("parameters", {}).get("rl_enabled", True):
                try:
                    vt_symbol = config.get("vt_symbol", f"{symbol}.BINANCE")
                    if symbol in vt_symbol or vt_symbol.split(".")[0] in symbol:
                        strategy_data = self.cta_engine.get_strategy_data(strategy_name)
                        pos = strategy_data.get("pos", 0)

                        rl_decision = self.rl_agent.get_action_with_risk(market_state)

                        shared_state.log_rl_decision({
                            "symbol": symbol,
                            "strategy": strategy_name,
                            "cta_action": "signal_generated",
                            "rl_action": rl_decision["action"],
                            "rl_approved": rl_decision["action"] != "hold",
                            "timestamp": time.time()
                        })
                except Exception as e:
                    logger.error(f"Error in CTA+RL hybrid processing: {e}")

    def _on_market_data(self, symbol: str, data: Dict[str, Any]):
        self.process_market_data(symbol, data)

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
        cta_status = {}
        if self.cta_manager:
            cta_status = self.cta_manager.get_all_strategy_status()

        return {
            "running": self.running,
            "mode": TRADING_MODE,
            "positions": self.positions,
            "orders": len(self.orders),
            "rl_strategies": {name: {"running": s["running"], "pnl": s["pnl"]}
                             for name, s in self.strategies.items()},
            "cta_strategies": cta_status,
            "gateways": list(self.gateways.keys()),
            "timestamp": time.time()
        }

    def get_positions(self) -> Dict[str, Dict[str, Any]]:
        return self.positions

    def get_pnl(self) -> Dict[str, Any]:
        total_pnl = sum(p.get("pnl", 0) for p in self.positions.values())
        return {
            "total": float(total_pnl),
            "by_symbol": {s: float(p.get("pnl", 0)) for s, p in self.positions.items()}
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
