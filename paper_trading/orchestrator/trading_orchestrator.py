"""
Trading Orchestrator
====================
Main controller that orchestrates all layers with error isolation.
Enables modular, plug-and-play architecture.
"""

import os
import sys
import time
import yaml
import signal
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
from loguru import logger

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from paper_trading.interfaces import (
    BaseLayer, LayerInput, LayerOutput,
    MarketData, FeatureVector, TradingSignal, Trade, Position,
    DataLayer, FeaturesLayer, StrategyLayer, IntelligenceLayer,
    ScoringLayer, RiskLayer, ExecutionLayer, MemoryLayer
)

from ..layers.layer2_risk.correlation_control import CorrelationControl
from ..layers.layer2_risk.portfolio_optimizer import PortfolioOptimizer
from ..layers.layer10_events.event_bus import EventBus, EventType
from ..layers.layer4_intelligence.uncertainty_model import UncertaintyModel
from ..layers.layer4_intelligence.exploration_engine import ExplorationEngine
from ..layers.layer5_validation.model_validator import ModelValidator
from ..layers.layer4_intelligence.evolution_engine import EvolutionEngine


class TradingOrchestrator:
    """
    Main orchestrator that connects all layers.
    Handles error isolation and flow control.
    """
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path or self._get_default_config_path()
        self.config = self._load_config()
        
        self.layers: Dict[str, BaseLayer] = {}
        self.running = False
        self.autonomous_mode = False
        self.update_interval = self.config.get('trading', {}).get('update_interval', 30)
        
        self.symbol = self.config.get('trading', {}).get('symbol', 'BTCUSDT')
        self.leverage = self.config.get('trading', {}).get('leverage', 75)
        
        self._init_layers()
        self._init_portfolio_components()
        self._init_advanced_components()
        self._setup_signal_handlers()
        
        logger.info("TradingOrchestrator initialized")
    
    def _get_default_config_path(self) -> str:
        """Get default config path"""
        return str(Path(__file__).parent.parent / "config" / "unified.yaml")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML"""
        if not Path(self.config_path).exists():
            logger.warning(f"Config file not found: {self.config_path}, using defaults")
            return self._get_default_config()
        
        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        logger.info(f"Loaded config from {self.config_path}")
        return config
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            'trading': {
                'symbol': 'BTCUSDT',
                'leverage': 75,
                'update_interval': 30,
                'initial_capital': 10000
            },
            'layers': {
                'data': {'enabled': True, 'type': 'binance'},
                'features': {'enabled': True, 'type': 'technical'},
                'strategy': {'enabled': True, 'default': 'momentum'},
                'intelligence': {'enabled': True},
                'scoring': {'enabled': True, 'threshold': 0.72},
                'risk': {'enabled': True, 'max_daily_trades': 5},
                'execution': {'enabled': True, 'mode': 'paper'},
                'memory': {'enabled': True},
                'output': {'enabled': True}
            }
        }
    
    def _init_layers(self):
        """Initialize all layers from config"""
        layer_config = self.config.get('layers', {})
        
        if layer_config.get('data', {}).get('enabled', True):
            self.layers['data'] = self._create_layer('data', layer_config.get('data', {}))
        
        if layer_config.get('features', {}).get('enabled', True):
            self.layers['features'] = self._create_layer('features', layer_config.get('features', {}))
        
        if layer_config.get('strategy', {}).get('enabled', True):
            self.layers['strategy'] = self._create_layer('strategy', layer_config.get('strategy', {}))
        
        if layer_config.get('intelligence', {}).get('enabled', True):
            self.layers['intelligence'] = self._create_layer('intelligence', layer_config.get('intelligence', {}))
        
        if layer_config.get('scoring', {}).get('enabled', True):
            self.layers['scoring'] = self._create_layer('scoring', layer_config.get('scoring', {}))
        
        if layer_config.get('risk', {}).get('enabled', True):
            self.layers['risk'] = self._create_layer('risk', layer_config.get('risk', {}))
        
        if layer_config.get('execution', {}).get('enabled', True):
            self.layers['execution'] = self._create_layer('execution', layer_config.get('execution', {}))
        
        if layer_config.get('memory', {}).get('enabled', True):
            self.layers['memory'] = self._create_layer('memory', layer_config.get('memory', {}))
            if 'memory' in self.layers:
                self.layers['memory'].initialize()
        
        logger.info(f"Initialized {len(self.layers)} layers: {list(self.layers.keys())}")
    
    def _init_portfolio_components(self):
        """Initialize correlation control and portfolio optimizer"""
        risk_config = self.config.get('layers', {}).get('risk', {})
        
        self.correlation_control = CorrelationControl(risk_config)
        self.portfolio_optimizer = PortfolioOptimizer(risk_config)
        
        logger.info("Initialized portfolio components: CorrelationControl, PortfolioOptimizer")
    
    def _init_advanced_components(self):
        """Initialize exploration, uncertainty, validation, evolution, and event bus"""
        risk_config = self.config.get('layers', {}).get('risk', {})
        
        self.event_bus = EventBus()
        self.uncertainty_model = UncertaintyModel(risk_config)
        self.exploration_engine = ExplorationEngine(risk_config)
        self.model_validator = ModelValidator(risk_config)
        self.evolution_engine = EvolutionEngine(risk_config)
        
        self._trade_count = 0
        self._last_regime = 'sideways'
        
        logger.info("Initialized advanced components: EventBus, UncertaintyModel, ExplorationEngine, ModelValidator, EvolutionEngine")
    
    def _create_layer(self, name: str, config: Dict[str, Any]) -> Optional[BaseLayer]:
        """Create a layer instance based on type"""
        try:
            if name == 'data':
                from ..layers.layer1_data.binance_client import BinanceDataClient
                return BinanceDataClient(config)
            
            elif name == 'features':
                from ..layers.layer2_features.feature_pipeline import FeaturePipeline
                return FeaturePipeline(config)
            
            elif name == 'strategy':
                from ..layers.layer3_strategies.strategy_aggregator import StrategyAggregator
                return StrategyAggregator(config)
            
            elif name == 'intelligence':
                from ..layers.layer4_intelligence.ensemble import IntelligenceEnsemble
                return IntelligenceEnsemble(config)
            
            elif name == 'scoring':
                from ..layers.layer5_scoring.trade_scorer import TradeScorer
                return TradeScorer(config)
            
            elif name == 'risk':
                from ..layers.layer2_risk.risk_engine import RiskEngine
                return RiskEngine(config)
            
            elif name == 'execution':
                from ..layers.layer5_execution.order_manager import OrderManager
                return OrderManager(config)
            
            elif name == 'memory':
                return MemoryLayer(config)
            
            else:
                logger.warning(f"Unknown layer: {name}")
                return None
        
        except Exception as e:
            logger.error(f"Error creating layer {name}: {e}")
            return None
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info("Received shutdown signal")
        self.stop()
        sys.exit(0)
    
    def start(self, autonomous: bool = False):
        """Start the trading orchestrator"""
        self.running = True
        self.autonomous_mode = autonomous
        
        self.event_bus.publish_simple(
            EventType.SYSTEM_START, 'orchestrator',
            {'autonomous': autonomous, 'symbol': self.symbol, 'leverage': self.leverage}
        )
        
        logger.info(f"TradingOrchestrator started (autonomous: {autonomous})")
        
        if autonomous:
            self._autonomous_loop()
        else:
            self._manual_mode()
    
    def _autonomous_loop(self):
        """Main autonomous trading loop"""
        while self.running:
            try:
                result = self.execute(self.symbol)
                
                if result.success and result.result.get('action') != 'hold':
                    logger.info(f"Executed: {result.result.get('action')} - {result.result.get('reason', '')}")
                
                time.sleep(self.update_interval)
            
            except Exception as e:
                logger.error(f"Autonomous loop error: {e}")
                self._log_error('autonomous_loop', str(e))
                time.sleep(10)
    
    def _manual_mode(self):
        """Manual mode - just keep running"""
        while self.running:
            time.sleep(1)
    
    def execute(self, symbol: str) -> LayerOutput:
        """
        Main execution flow with error isolation.
        Each layer wrapped in try-catch.
        """
        result = LayerOutput(
            result={'action': 'hold', 'reason': 'No decision'},
            success=True,
            layer_name='orchestrator'
        )
        
        layer_outputs = {}
        
        # Step 1: Get data
        result = self._safe_execute('data', symbol=symbol)
        if not result.success:
            return result
        market_data = result.result
        layer_outputs['data'] = result.to_dict()
        
        # Step 2: Calculate features
        result = self._safe_execute('features', 
                                    price=market_data.get('price', 0),
                                    volume=market_data.get('volume', 0))
        if not result.success:
            return result
        features = result.result
        layer_outputs['features'] = result.to_dict()
        
        # Step 3: Generate strategy signal
        result = self._safe_execute('strategy', features=features)
        if not result.success:
            return result
        signal_data = result.result
        layer_outputs['strategy'] = result.to_dict()
        
        # Step 3.5: Exploration check
        try:
            exploration_result = self.exploration_engine.should_explore()
            layer_outputs['exploration'] = exploration_result.to_dict()
            
            if exploration_result.should_explore:
                logger.info(f"Exploration mode: {exploration_result.reason}")
                signal_data['explore_exploit'] = 'explore'
                signal_data['position_size'] = signal_data.get('position_size', 0) * exploration_result.test_size_multiplier
            else:
                signal_data['explore_exploit'] = 'exploit'
        except Exception as e:
            logger.error(f"Exploration check error: {e}")
            exploration_result = None
        
        # Step 4: Intelligence (regime detection)
        result = self._safe_execute('intelligence', features=features)
        regime = 'sideways'
        if result.success and result.result:
            regime = result.result.get('regime', 'sideways')
        layer_outputs['intelligence'] = result.to_dict()
        
        # Emit regime change event
        if regime != self._last_regime:
            self.event_bus.publish_simple(
                EventType.REGIME_CHANGED, 'orchestrator',
                {'old_regime': self._last_regime, 'new_regime': regime, 'symbol': symbol}
            )
            logger.info(f"Regime changed: {self._last_regime} -> {regime}")
            self._last_regime = regime
        
        # Step 4.5: Uncertainty prediction
        try:
            self.uncertainty_model.add_return(symbol, market_data.get('change_pct_24h', 0) / 100)
            uncertain_pred = self.uncertainty_model.predict(symbol, features, regime)
            layer_outputs['uncertainty'] = uncertain_pred.to_dict()
            
            if uncertain_pred.confidence > 0:
                logger.debug(f"Uncertainty: mean={uncertain_pred.mean:.4f}, std={uncertain_pred.std:.4f}, conf={uncertain_pred.confidence:.2f}")
        except Exception as e:
            logger.error(f"Uncertainty prediction error: {e}")
            uncertain_pred = None
        
        # Step 5: Scoring
        result = self._safe_execute('scoring', 
                                    signal=signal_data,
                                    features=features,
                                    regime=regime)
        if not result.success:
            return result
        scored_signal = result.result
        layer_outputs['scoring'] = result.to_dict()
        
        # Step 6: Risk check
        balance = self.layers.get('execution').get_balance() if 'execution' in self.layers else 10000
        positions = {}
        if 'execution' in self.layers:
            positions = {p.symbol: p for p in self.layers['execution'].get_positions()}
        
        result = self._safe_execute('risk',
                                    signal=scored_signal,
                                    balance=balance,
                                    positions=positions)
        if not result.success:
            return result
        
        risk_result = result.result
        layer_outputs['risk'] = result.to_dict()
        
        if not risk_result.get('allowed', False):
            return LayerOutput(
                result={
                    'action': 'hold',
                    'reason': f"Risk rejected: {risk_result.get('reasons', [])}",
                    'score': scored_signal.get('score', 0) if scored_signal else 0
                },
                success=True,
                layer_name='orchestrator',
                metadata={'layer_outputs': layer_outputs}
            )
        
        # Step 6b: Correlation risk check
        try:
            price = market_data.get('price', 0)
            if price > 0:
                self.correlation_control.add_price(symbol, price, time.time())
                self.correlation_control.compute_correlation_matrix()
            
            corr_risk = self.correlation_control.check_correlation_risk(symbol, positions)
            layer_outputs['correlation'] = corr_risk
            
            if corr_risk.get('max_correlation', 0) > self.correlation_control.max_correlation:
                logger.warning(f"Correlation risk detected: {corr_risk}")
                self.event_bus.publish_simple(
                    EventType.RISK_ALERT, 'correlation_control',
                    {'symbol': symbol, 'corr_risk': corr_risk}
                )
        except Exception as e:
            logger.error(f"Correlation check error: {e}")
        
        # Step 6c: Portfolio optimization
        try:
            return_pct = (price - risk_result.get('entry_price', price)) / price * 100 if price > 0 else 0
            self.portfolio_optimizer.add_return(symbol, return_pct)
            
            assets = list(positions.keys()) + [symbol]
            signals = {symbol: scored_signal}
            
            allocations = self.portfolio_optimizer.optimize(assets, balance, signals)
            
            if symbol in allocations:
                optimal_size = allocations[symbol] / price if price > 0 else 0
                scored_signal['position_size'] = min(
                    scored_signal.get('position_size', 0),
                    optimal_size
                )
            
            layer_outputs['portfolio'] = {'allocations': allocations}
        except Exception as e:
            logger.error(f"Portfolio optimization error: {e}")
        
        # Step 6c2: Uncertainty-based position size adjustment
        if uncertain_pred and uncertain_pred.confidence > 0:
            try:
                base_size = scored_signal.get('position_size', 0)
                adjusted_size = self.uncertainty_model.adjust_position_size(base_size, uncertain_pred)
                if adjusted_size != base_size:
                    logger.info(f"Uncertainty adjustment: {base_size:.6f} -> {adjusted_size:.6f} (conf={uncertain_pred.confidence:.2f})")
                scored_signal['position_size'] = adjusted_size
                layer_outputs['uncertainty_adjustment'] = {
                    'original_size': base_size,
                    'adjusted_size': adjusted_size,
                    'confidence': uncertain_pred.confidence
                }
            except Exception as e:
                logger.error(f"Uncertainty size adjustment error: {e}")
        
        # Step 6d: Model validation (every 50 trades)
        if self._trade_count % 50 == 0:
            try:
                validation_result = self.model_validator.comprehensive_validation(symbol)
                layer_outputs['validation'] = validation_result
                
                if not validation_result['valid']:
                    logger.warning(f"Model validation FAILED: {validation_result['recommendation']}")
                    self.event_bus.publish_simple(
                        EventType.RISK_ALERT, 'model_validator',
                        {'symbol': symbol, 'result': validation_result}
                    )
                else:
                    logger.info(f"Model validation passed (trade #{self._trade_count})")
            except Exception as e:
                logger.error(f"Model validation error: {e}")
        
        # Step 6e: Evolution engine (every 100 trades)
        if self._trade_count % 100 == 0:
            try:
                evolved_population = self.evolution_engine.evolve()
                best_genomes = self.evolution_engine.get_best_genomes(3)
                layer_outputs['evolution'] = {
                    'generation': self.evolution_engine.generation,
                    'best_genomes': best_genomes
                }
                logger.info(f"Evolution: gen {self.evolution_engine.generation}, best fitness: {best_genomes[0]['fitness']:.4f}" if best_genomes else "Evolution: no genomes yet")
            except Exception as e:
                logger.error(f"Evolution engine error: {e}")
        
        # Step 7: Execute
        scored_signal['position_size'] = risk_result.get('position_size', 0)
        scored_signal['stop_loss'] = risk_result.get('stop_loss')
        scored_signal['take_profit'] = risk_result.get('take_profit')
        
        result = self._safe_execute('execution',
                                    action='open',
                                    signal=scored_signal)
        layer_outputs['execution'] = result.to_dict()
        
        # Emit trade events
        if result.success:
            self.event_bus.publish_simple(
                EventType.TRADE_OPENED, 'orchestrator',
                {'symbol': symbol, 'action': scored_signal.get('action', 'hold'),
                 'position_size': scored_signal.get('position_size', 0),
                 'regime': regime, 'explore_exploit': signal_data.get('explore_exploit', 'exploit')}
            )
            self._trade_count += 1
            
            # Record trade result for exploration and evolution engines
            try:
                return_pct = 0  # Will be updated on close
                self.exploration_engine.record_outcome(
                    scored_signal.get('action', 'hold'), return_pct,
                    signal_data.get('explore_exploit', 'exploit') == 'explore'
                )
                self.model_validator.add_trade(symbol, return_pct)
                self.evolution_engine.record_result('default', return_pct)
            except Exception as e:
                logger.error(f"Trade recording error: {e}")
        else:
            self.event_bus.publish_simple(
                EventType.TRADE_FAILED, 'orchestrator',
                {'symbol': symbol, 'error': result.error}
            )
        
        # Step 8: Save to memory
        self._safe_execute('memory',
                          action='save_decision',
                          decision={
                              'symbol': symbol,
                              'regime': regime,
                              'signal': scored_signal,
                              'risk_passed': risk_result.get('allowed', False)
                          })
        
        return LayerOutput(
            result={
                'action': scored_signal.get('action', 'hold'),
                'reason': 'Trade executed' if result.success else 'Trade failed',
                'score': scored_signal.get('score', 0),
                'confidence': scored_signal.get('confidence', 0),
                'regime': regime
            },
            success=result.success,
            layer_name='orchestrator',
            metadata={'layer_outputs': layer_outputs}
        )
    
    def _safe_execute(self, layer_name: str, **kwargs) -> LayerOutput:
        """Execute layer with error isolation"""
        layer = self.layers.get(layer_name)
        
        if not layer:
            return LayerOutput(
                result={},
                success=False,
                error=f"Layer {layer_name} not found",
                layer_name=layer_name
            )
        
        if not layer.enabled:
            return LayerOutput(
                result={},
                success=True,
                error=f"Layer {layer_name} disabled",
                layer_name=layer_name
            )
        
        if not layer.health_check():
            self._log_error(layer_name, f"Layer unhealthy: {layer.get_status()}")
            layer.mark_unhealthy(f"Health check failed")
            return LayerOutput(
                result={},
                success=False,
                error=f"Layer {layer_name} unhealthy",
                layer_name=layer_name
            )
        
        try:
            input_data = LayerInput(data=kwargs, metadata={'layer': layer_name})
            result = layer.process(input_data)
            
            if not result.success:
                self._log_error(layer_name, result.error)
                layer.mark_unhealthy(result.error)
            else:
                layer.mark_healthy()
            
            # Update layer health in memory
            if 'memory' in self.layers:
                self.layers['memory'].update_layer_health(
                    layer_name,
                    'healthy' if result.success else 'unhealthy',
                    layer._error_count,
                    layer._last_error
                )
            
            return result
        
        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            logger.error(f"Layer {layer_name} error: {error_msg}")
            layer.mark_unhealthy(error_msg)
            
            return LayerOutput(
                result=None,
                success=False,
                error=error_msg,
                layer_name=layer_name
            )
    
    def _log_error(self, layer_name: str, error: str):
        """Log error to memory layer"""
        if 'memory' in self.layers:
            try:
                self.layers['memory'].log_event(
                    'layer_error',
                    'error',
                    f"Layer {layer_name}: {error}",
                    layer_name=layer_name
                )
            except:
                pass
    
    def stop(self):
        """Stop the trading orchestrator"""
        self.running = False
        
        try:
            self.event_bus.publish_simple(
                EventType.SYSTEM_STOP, 'orchestrator',
                {'trade_count': self._trade_count}
            )
        except:
            pass
        
        logger.info("TradingOrchestrator stopped")
        
        if 'memory' in self.layers:
            try:
                self.layers['memory'].log_event(
                    'orchestrator_stop',
                    'info',
                    'TradingOrchestrator stopped'
                )
            except:
                pass
    
    def get_full_status(self) -> Dict[str, Any]:
        """Get status of all layers - for troubleshooting"""
        return {
            'orchestrator': {
                'running': self.running,
                'autonomous_mode': self.autonomous_mode,
                'symbol': self.symbol,
                'leverage': self.leverage,
                'update_interval': self.update_interval,
                'trade_count': getattr(self, '_trade_count', 0)
            },
            'layers': {
                name: layer.get_status()
                for name, layer in self.layers.items()
            },
            'advanced_components': {
                'event_bus': self.event_bus.get_stats() if hasattr(self, 'event_bus') else None,
                'uncertainty_model': self.uncertainty_model.get_status() if hasattr(self, 'uncertainty_model') else None,
                'exploration_engine': self.exploration_engine.get_status() if hasattr(self, 'exploration_engine') else None,
                'model_validator': self.model_validator.get_status() if hasattr(self, 'model_validator') else None,
                'evolution_engine': self.evolution_engine.get_status() if hasattr(self, 'evolution_engine') else None
            }
        }
    
    def disable_layer(self, layer_name: str):
        """Disable a layer without code changes"""
        if layer_name in self.layers:
            self.layers[layer_name].enabled = False
            logger.info(f"Disabled layer: {layer_name}")
    
    def enable_layer(self, layer_name: str):
        """Enable a layer"""
        if layer_name in self.layers:
            self.layers[layer_name].enabled = True
            logger.info(f"Enabled layer: {layer_name}")
    
    def swap_layer(self, layer_name: str, new_type: str):
        """Swap layer implementation"""
        logger.info(f"Swapping layer {layer_name} to {new_type}")
        new_config = self.config.get('layers', {}).get(layer_name, {})
        new_config['type'] = new_type
        
        new_layer = self._create_layer(layer_name, new_config)
        if new_layer:
            self.layers[layer_name] = new_layer
    
    def get_layer(self, name: str) -> Optional[BaseLayer]:
        """Get a specific layer"""
        return self.layers.get(name)
    
    def execute_command(self, command: str, **kwargs) -> Dict[str, Any]:
        """Execute a manual command"""
        if command == 'status':
            return self.get_full_status()
        
        elif command == 'positions':
            if 'execution' in self.layers:
                positions = self.layers['execution'].get_positions()
                return {'positions': [p.to_dict() for p in positions]}
            return {'positions': []}
        
        elif command == 'balance':
            if 'execution' in self.layers:
                return {'balance': self.layers['execution'].get_balance()}
            return {'balance': 0}
        
        elif command == 'long':
            return self._execute_manual_trade('buy', kwargs.get('quantity', 0.001))
        
        elif command == 'short':
            return self._execute_manual_trade('sell', kwargs.get('quantity', 0.001))
        
        elif command == 'close':
            return self._execute_close(kwargs.get('symbol', self.symbol))
        
        else:
            return {'error': f'Unknown command: {command}'}
    
    def _execute_manual_trade(self, side: str, quantity: float) -> Dict[str, Any]:
        """Execute manual trade"""
        if 'execution' not in self.layers:
            return {'error': 'Execution layer not available'}
        
        signal = TradingSignal(
            action=side,
            confidence=1.0,
            score=1.0,
            strategy='manual',
            regime='unknown',
            position_size=quantity,
            metadata={'symbol': self.symbol}
        )
        
        result = self.layers['execution'].process(LayerInput(
            data={'action': 'open', 'signal': signal}
        ))
        
        return result.to_dict()
    
    def _execute_close(self, symbol: str) -> Dict[str, Any]:
        """Close position"""
        if 'execution' not in self.layers:
            return {'error': 'Execution layer not available'}
        
        result = self.layers['execution'].process(LayerInput(
            data={'action': 'close', 'symbol': symbol}
        ))
        
        return result.to_dict()


def create_orchestrator(config_path: str = None) -> TradingOrchestrator:
    """Create and return orchestrator instance"""
    return TradingOrchestrator(config_path)


if __name__ == '__main__':
    logger.add("logs/orchestrator.log", rotation="10 MB", retention="7 days")
    
    orchestrator = create_orchestrator()
    orchestrator.start(autonomous=True)
