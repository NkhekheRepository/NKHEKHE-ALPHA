"""
Paper Trading Engine
====================
Main trading engine for autonomous quant trading system.
Integrates VNPY with self-healing, self-learning, and adaptive learning.
"""

import os
import sys
import time
import threading
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from loguru import logger

CONFIG_PATH = Path(__file__).parent / "config.yaml"


class PaperTradingEngine:
    """
    Main paper trading engine that orchestrates all layers.
    
    Architecture:
    - Layer 1: Data & Connectivity
    - Layer 2: Risk Management
    - Layer 3: Signal Generation
    - Layer 4: Intelligence (ML Ensemble)
    - Layer 5: Execution (VNPY)
    - Layer 6: Orchestration (Self-Healing)
    - Layer 7: Command & Control
    """
    
    def __init__(self, config_path: str = None):
        self.config_path = Path(config_path) if config_path else CONFIG_PATH
        self.config = self._load_config()
        
        self.running = False
        self.update_thread: Optional[threading.Thread] = None
        
        self.capital = self.config['trading']['initial_capital']
        self.leverage = self.config['trading']['leverage']
        self.update_interval = self.config['trading']['update_interval']
        
        self.positions: Dict[str, Dict[str, Any]] = {}
        self.daily_pnl = 0.0
        self.daily_start_capital = self.capital
        
        self.strategies: Dict[str, Any] = {}
        self.active_strategy: Optional[str] = None
        self.current_regime = "sideways"
        
        self._init_layers()
        self._init_strategies()
        
        logger.info(f"PaperTradingEngine initialized: capital=${self.capital}, leverage={self.leverage}x")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        logger.info(f"Loaded config from {self.config_path}")
        return config
    
    def _init_layers(self):
        """Initialize all layers."""
        from .layers.layer1_data.binance_client import BinanceDataClient
        from .layers.layer2_risk.risk_engine import RiskEngine
        from .layers.layer3_signals.signal_aggregator import SignalAggregator
        from .layers.layer4_intelligence.ensemble import IntelligenceEnsemble
        from .layers.layer5_execution.order_manager import OrderManager
        from .layers.layer6_orchestration.health_monitor import HealthMonitor
        
        self.data_client = BinanceDataClient(self.config.get('data', {}))
        self.risk_engine = RiskEngine(self.config.get('risk', {}))
        self.signal_aggregator = SignalAggregator()
        self.intelligence = IntelligenceEnsemble(self.config.get('intelligence', {}))
        self.order_manager = OrderManager(self.config.get('trading', {}))
        self.health_monitor = HealthMonitor(self.config.get('orchestration', {}))
        
        logger.info("All layers initialized")
    
    def _init_strategies(self):
        """Initialize trading strategies from config."""
        for strategy_config in self.config.get('strategies', []):
            if strategy_config.get('enabled', False):
                self.strategies[strategy_config['name']] = {
                    'class': strategy_config['class'],
                    'vt_symbol': strategy_config['vt_symbol'],
                    'parameters': strategy_config.get('parameters', {}),
                    'enabled': True
                }
                
                if self.active_strategy is None:
                    self.active_strategy = strategy_config['name']
        
        logger.info(f"Initialized strategies: {list(self.strategies.keys())}")
    
    def start(self):
        """Start the trading engine."""
        if self.running:
            logger.warning("Engine already running")
            return
        
        self.running = True
        
        self.data_client.connect()
        
        self.health_monitor.start()
        
        self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self.update_thread.start()
        
        logger.info("PaperTradingEngine started")
    
    def stop(self):
        """Stop the trading engine."""
        if not self.running:
            logger.warning("Engine not running")
            return
        
        self.running = False
        
        if self.update_thread:
            self.update_thread.join(timeout=5)
        
        self.data_client.disconnect()
        self.health_monitor.stop()
        
        self._close_all_positions()
        
        logger.info("PaperTradingEngine stopped")
    
    def _update_loop(self):
        """Main update loop running at configured interval."""
        while self.running:
            try:
                self._process_update()
            except Exception as e:
                logger.error(f"Update loop error: {e}")
            
            time.sleep(self.update_interval)
    
    def _process_update(self):
        """Process one update cycle."""
        market_data = self.data_client.get_latest_data()
        
        if not market_data:
            logger.warning("No market data available")
            return
        
        self._detect_regime(market_data)
        
        signals = self._generate_signals(market_data)
        
        validated_signals = self._intelligence_validate(signals, market_data)
        
        risk_check = self.risk_engine.check_risk(
            self.capital,
            self.daily_pnl,
            self.positions,
            self.daily_start_capital
        )
        
        if not risk_check['allowed']:
            logger.warning(f"Risk check failed: {risk_check['reason']}")
            self._handle_risk_breach(risk_check)
            return
        
        self._execute_signals(validated_signals, market_data)
        
        self._update_positions(market_data)
    
    def _detect_regime(self, market_data: Dict[str, Any]):
        """Detect market regime using HMM."""
        try:
            regime = self.intelligence.detect_regime(market_data)
            if regime != self.current_regime:
                logger.info(f"Regime change: {self.current_regime} -> {regime}")
                self.current_regime = regime
                self._switch_strategy(regime)
        except Exception as e:
            logger.error(f"Regime detection error: {e}")
    
    def _switch_strategy(self, regime: str):
        """Switch strategy based on regime."""
        regime_map = self.config.get('intelligence', {}).get('adaptive', {}).get('regime_strategy_map', {})
        strategy_name = regime_map.get(regime)
        
        if strategy_name and strategy_name in self.strategies:
            self.active_strategy = strategy_name
            logger.info(f"Switched to strategy: {strategy_name} for regime: {regime}")
    
    def _generate_signals(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate trading signals from multiple strategies."""
        return self.signal_aggregator.generate(
            market_data,
            self.strategies.get(self.active_strategy, {})
        )
    
    def _intelligence_validate(self, signals: Dict[str, Any], market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate signals using ML ensemble."""
        try:
            return self.intelligence.validate(signals, market_data)
        except Exception as e:
            logger.error(f"Intelligence validation error: {e}")
            return signals
    
    def _execute_signals(self, signals: Dict[str, Any], market_data: Dict[str, Any]):
        """Execute validated signals."""
        if not signals.get('action'):
            return
        
        self.order_manager.execute(
            signal=signals['action'],
            symbol=signals.get('symbol', 'BTCUSDT'),
            price=market_data.get('price', 0),
            size=self._calculate_position_size(),
            leverage=self.leverage
        )
    
    def _calculate_position_size(self) -> float:
        """Calculate position size based on risk parameters."""
        position_pct = self.config.get('risk', {}).get('position_size_pct', 10) / 100
        return self.capital * position_pct * self.leverage
    
    def _update_positions(self, market_data: Dict[str, Any]):
        """Update position tracking and P&L."""
        for symbol, position in self.positions.items():
            current_price = market_data.get('price', position.get('entry_price', 0))
            position['pnl'] = (current_price - position.get('entry_price', 0)) * position.get('size', 0)
    
    def _close_all_positions(self):
        """Close all open positions."""
        for symbol, position in list(self.positions.items()):
            if position.get('size', 0) != 0:
                self.order_manager.close_position(symbol)
        logger.info("All positions closed")
    
    def _handle_risk_breach(self, risk_check: Dict[str, Any]):
        """Handle risk limit breach."""
        reason = risk_check.get('reason', 'Unknown')
        logger.warning(f"Risk breach: {reason}")
        
        self._close_all_positions()
        
        if self.config.get('telegram', {}).get('enabled'):
            try:
                from telegram_notify import send_risk_alert
                send_risk_alert(
                    risk_score=risk_check.get('risk_score', 100),
                    risk_level=risk_check.get('level', 'critical'),
                    message=reason
                )
            except Exception as e:
                logger.error(f"Failed to send risk alert: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current system status."""
        return {
            'running': self.running,
            'capital': self.capital,
            'leverage': self.leverage,
            'daily_pnl': self.daily_pnl,
            'positions': self.positions,
            'active_strategy': self.active_strategy,
            'current_regime': self.current_regime,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_positions(self) -> Dict[str, Dict[str, Any]]:
        """Get current positions."""
        return self.positions
    
    def get_pnl(self) -> float:
        """Get current P&L."""
        return self.daily_pnl
    
    def switch_strategy(self, strategy_name: str) -> bool:
        """Switch to a different strategy."""
        if strategy_name not in self.strategies:
            logger.error(f"Strategy not found: {strategy_name}")
            return False
        
        self.active_strategy = strategy_name
        logger.info(f"Switched to strategy: {strategy_name}")
        return True
    
    def emergency_stop(self):
        """Emergency stop - close all positions and stop engine."""
        logger.critical("EMERGENCY STOP triggered")
        self._close_all_positions()
        self.stop()


_engine: Optional[PaperTradingEngine] = None


def get_engine(config_path: str = None) -> PaperTradingEngine:
    """Get singleton engine instance."""
    global _engine
    if _engine is None:
        _engine = PaperTradingEngine(config_path)
    return _engine


def start_engine(config_path: str = None):
    """Start the paper trading engine."""
    engine = get_engine(config_path)
    engine.start()
    return engine


def stop_engine():
    """Stop the paper trading engine."""
    global _engine
    if _engine:
        _engine.stop()
        _engine = None


if __name__ == "__main__":
    logger.info("Starting Paper Trading Engine...")
    
    engine = PaperTradingEngine()
    engine.start()
    
    try:
        while True:
            time.sleep(10)
            status = engine.get_status()
            logger.info(f"Status: {status}")
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        engine.stop()
