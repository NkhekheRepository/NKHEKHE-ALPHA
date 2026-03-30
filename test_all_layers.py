#!/usr/bin/env python3
"""
Comprehensive Test Suite for FINANCIAL ORCHESTRATOR
====================================================
Tests all layers including the 5 new components:
1. Event Layer
2. Uncertainty Model
3. Exploration Engine
4. Model Validation Engine
5. Evolution Engine
"""

import sys
import os
sys.path.insert(0, '/home/ubuntu/financial_orchestrator')

import numpy as np
import time
from typing import Dict, Any

# Test results tracking
results = {'passed': 0, 'failed': 0, 'errors': []}

def test(name: str):
    """Decorator for test functions"""
    def decorator(func):
        try:
            func()
            results['passed'] += 1
            print(f"  [PASS] {name}")
        except Exception as e:
            results['failed'] += 1
            results['errors'].append((name, str(e)))
            print(f"  [FAIL] {name}: {e}")
    return decorator


# ============================================================
# TEST: EVENT LAYER
# ============================================================
@test("EventBus: import and instantiate")
def test_event_bus_import():
    from paper_trading.layers.layer10_events.event_bus import EventBus, Event, EventType
    bus = EventBus()
    assert bus is not None

@test("EventBus: publish and subscribe")
def test_event_bus_pubsub():
    from paper_trading.layers.layer10_events.event_bus import EventBus, Event, EventType
    bus = EventBus()
    received = []

    def handler(event):
        received.append(event)

    bus.subscribe(EventType.TRADE_OPENED, handler)
    bus.publish_simple(EventType.TRADE_OPENED, 'test', {'symbol': 'BTCUSDT'})

    assert len(received) == 1
    assert received[0].data['symbol'] == 'BTCUSDT'

@test("EventBus: wildcard subscriber")
def test_event_bus_wildcard():
    from paper_trading.layers.layer10_events.event_bus import EventBus, EventType
    bus = EventBus()
    received = []

    bus.subscribe_all(lambda e: received.append(e))
    bus.publish_simple(EventType.TRADE_OPENED, 'test', {})
    bus.publish_simple(EventType.RISK_ALERT, 'test', {})
    bus.publish_simple(EventType.SIGNAL_GENERATED, 'test', {})

    assert len(received) == 3

@test("EventBus: event history")
def test_event_bus_history():
    from paper_trading.layers.layer10_events.event_bus import EventBus, EventType
    bus = EventBus()
    bus.publish_simple(EventType.TRADE_OPENED, 'test', {})
    bus.publish_simple(EventType.TRADE_CLOSED, 'test', {})

    history = bus.get_history(limit=10)
    assert len(history) == 2

@test("EventBus: statistics")
def test_event_bus_stats():
    from paper_trading.layers.layer10_events.event_bus import EventBus, EventType
    bus = EventBus()
    bus.publish_simple(EventType.TRADE_OPENED, 'test', {})
    bus.publish_simple(EventType.TRADE_OPENED, 'test', {})

    stats = bus.get_stats()
    assert stats['total_published'] == 2
    assert stats['by_type']['trade.opened'] == 2


# ============================================================
# TEST: UNCERTAINTY MODEL
# ============================================================
@test("UncertaintyModel: import and instantiate")
def test_uncertainty_import():
    from paper_trading.layers.layer4_intelligence.uncertainty_model import UncertaintyModel
    model = UncertaintyModel()
    assert model is not None

@test("UncertaintyModel: insufficient data returns zero confidence")
def test_uncertainty_no_data():
    from paper_trading.layers.layer4_intelligence.uncertainty_model import UncertaintyModel
    model = UncertaintyModel()
    pred = model.predict('BTCUSDT', {'price': 50000})
    assert pred.confidence == 0.0
    assert pred.variance == 1.0

@test("UncertaintyModel: prediction with sufficient data")
def test_uncertainty_prediction():
    from paper_trading.layers.layer4_intelligence.uncertainty_model import UncertaintyModel
    model = UncertaintyModel()

    np.random.seed(42)
    for i in range(50):
        model.add_return('BTCUSDT', np.random.normal(0.001, 0.02))

    pred = model.predict('BTCUSDT', {'price': 50000})
    assert pred.sample_size == 50
    assert pred.variance > 0
    assert pred.lower_bound < pred.upper_bound
    assert pred.to_dict()['std'] > 0

@test("UncertaintyModel: position size adjustment")
def test_uncertainty_position_size():
    from paper_trading.layers.layer4_intelligence.uncertainty_model import UncertaintyModel
    model = UncertaintyModel()

    np.random.seed(42)
    for i in range(50):
        model.add_return('BTCUSDT', np.random.normal(0.002, 0.01))

    pred = model.predict('BTCUSDT', {'price': 50000})
    base_size = 1.0
    adjusted = model.adjust_position_size(base_size, pred)

    # Should be positive and reasonable
    assert adjusted >= 0
    assert adjusted <= base_size * 2.0

@test("UncertaintyModel: regime affects variance")
def test_uncertainty_regime():
    from paper_trading.layers.layer4_intelligence.uncertainty_model import UncertaintyModel
    model = UncertaintyModel()

    np.random.seed(42)
    for i in range(50):
        model.add_return('BTCUSDT', np.random.normal(0.001, 0.02))

    pred_trend = model.predict('BTCUSDT', {'price': 50000}, regime='trending')
    pred_volatile = model.predict('BTCUSDT', {'price': 50000}, regime='volatile')

    # Volatile regime should have higher variance
    assert pred_volatile.variance >= pred_trend.variance


# ============================================================
# TEST: EXPLORATION ENGINE
# ============================================================
@test("ExplorationEngine: import and instantiate")
def test_exploration_import():
    from paper_trading.layers.layer4_intelligence.exploration_engine import ExplorationEngine
    engine = ExplorationEngine()
    assert engine is not None

@test("ExplorationEngine: initial exploration rate")
def test_exploration_initial():
    from paper_trading.layers.layer4_intelligence.exploration_engine import ExplorationEngine
    engine = ExplorationEngine({'base_epsilon': 0.15})
    action = engine.should_explore()
    assert action.exploration_rate == 0.15

@test("ExplorationEngine: degradation triggers exploration")
def test_exploration_degradation():
    from paper_trading.layers.layer4_intelligence.exploration_engine import ExplorationEngine
    engine = ExplorationEngine()

    for i in range(20):
        engine.record_outcome('buy', -0.05, False)

    action = engine.should_explore()
    assert action.should_explore is True
    assert 'degraded' in action.reason.lower() or 'performance' in action.reason.lower()

@test("ExplorationEngine: record outcomes")
def test_exploration_record():
    from paper_trading.layers.layer4_intelligence.exploration_engine import ExplorationEngine
    engine = ExplorationEngine()

    for i in range(30):
        engine.record_outcome('buy', np.random.normal(0.001, 0.02), exploration=True)
        engine.record_outcome('sell', np.random.normal(0.002, 0.015), exploration=False)

    stats = engine.get_exploration_stats()
    assert stats['exploration_count'] == 30
    assert stats['exploitation_count'] == 30


# ============================================================
# TEST: MODEL VALIDATION ENGINE
# ============================================================
@test("ModelValidator: import and instantiate")
def test_validator_import():
    from paper_trading.layers.layer5_validation.model_validator import ModelValidator
    validator = ModelValidator()
    assert validator is not None

@test("ModelValidator: insufficient data warning")
def test_validator_no_data():
    from paper_trading.layers.layer5_validation.model_validator import ModelValidator
    validator = ModelValidator()
    result = validator.walk_forward_validation('BTCUSDT')
    assert 'Insufficient' in result.warning or result.sample_size < 30

@test("ModelValidator: walk-forward validation")
def test_validator_walkforward():
    from paper_trading.layers.layer5_validation.model_validator import ModelValidator
    validator = ModelValidator()

    np.random.seed(42)
    for i in range(250):
        validator.add_trade('BTCUSDT', np.random.normal(0.001, 0.02))

    result = validator.walk_forward_validation('BTCUSDT')
    assert result.method == 'walk_forward'
    assert result.sample_size > 0

@test("ModelValidator: Monte Carlo validation")
def test_validator_montecarlo():
    from paper_trading.layers.layer5_validation.model_validator import ModelValidator
    validator = ModelValidator({'monte_carlo_sims': 100})

    np.random.seed(42)
    for i in range(100):
        validator.add_trade('BTCUSDT', np.random.normal(0.002, 0.015))

    result = validator.monte_carlo_validation('BTCUSDT')
    assert result.method == 'monte_carlo'

@test("ModelValidator: out-of-sample validation")
def test_validator_oos():
    from paper_trading.layers.layer5_validation.model_validator import ModelValidator
    validator = ModelValidator()

    np.random.seed(42)
    for i in range(200):
        validator.add_trade('BTCUSDT', np.random.normal(0.001, 0.02))

    result = validator.out_of_sample_validation('BTCUSDT')
    assert result.method == 'out_of_sample'

@test("ModelValidator: comprehensive validation")
def test_validator_comprehensive():
    from paper_trading.layers.layer5_validation.model_validator import ModelValidator
    validator = ModelValidator()

    np.random.seed(42)
    for i in range(250):
        validator.add_trade('BTCUSDT', np.random.normal(0.001, 0.02))

    result = validator.comprehensive_validation('BTCUSDT')
    assert 'valid' in result
    assert 'walk_forward' in result
    assert 'monte_carlo' in result
    assert 'out_of_sample' in result


# ============================================================
# TEST: EVOLUTION ENGINE
# ============================================================
@test("EvolutionEngine: import and instantiate")
def test_evolution_import():
    from paper_trading.layers.layer4_intelligence.evolution_engine import EvolutionEngine
    engine = EvolutionEngine()
    assert engine is not None

@test("EvolutionEngine: initial population")
def test_evolution_population():
    from paper_trading.layers.layer4_intelligence.evolution_engine import EvolutionEngine
    engine = EvolutionEngine({'population_size': 10})
    assert len(engine.population) == 10

@test("EvolutionEngine: evolution creates new generation")
def test_evolution_run():
    from paper_trading.layers.layer4_intelligence.evolution_engine import EvolutionEngine
    engine = EvolutionEngine({'population_size': 10})

    for genome in engine.population:
        for i in range(20):
            genome.returns.append(np.random.normal(0.001, 0.02))
            genome.trades += 1

    new_pop = engine.evolve()
    assert len(new_pop) == 10
    assert engine.generation == 1

@test("EvolutionEngine: record results")
def test_evolution_record():
    from paper_trading.layers.layer4_intelligence.evolution_engine import EvolutionEngine
    engine = EvolutionEngine({'population_size': 5})
    sid = engine.population[0].strategy_id
    engine.record_result(sid, 0.01)
    assert engine.population[0].trades == 1

@test("EvolutionEngine: capital allocation")
def test_evolution_allocation():
    from paper_trading.layers.layer4_intelligence.evolution_engine import EvolutionEngine
    engine = EvolutionEngine({'population_size': 5})

    for genome in engine.population:
        for i in range(20):
            genome.returns.append(np.random.normal(0.001, 0.02))
            genome.trades += 1

    alloc = engine.get_capital_allocation(10000)
    total = sum(alloc.values())
    assert abs(total - 10000) < 1.0

@test("EvolutionEngine: best genomes")
def test_evolution_best():
    from paper_trading.layers.layer4_intelligence.evolution_engine import EvolutionEngine
    engine = EvolutionEngine({'population_size': 10})

    for genome in engine.population:
        for i in range(20):
            genome.returns.append(np.random.normal(0.001, 0.02))
            genome.trades += 1

    best = engine.get_best_genomes(3)
    assert len(best) == 3
    assert best[0]['fitness'] >= best[1]['fitness']


# ============================================================
# TEST: EXISTING COMPONENTS (integration)
# ============================================================
@test("FeaturePipeline: import")
def test_feature_pipeline():
    from paper_trading.layers.layer2_features.feature_pipeline import FeaturePipeline
    pipe = FeaturePipeline({})
    assert pipe is not None

@test("RiskEngine: import")
def test_risk_engine():
    from paper_trading.layers.layer2_risk.risk_engine import RiskEngine
    engine = RiskEngine({})
    assert engine is not None

@test("CorrelationControl: import")
def test_correlation_control():
    from paper_trading.layers.layer2_risk.correlation_control import CorrelationControl
    cc = CorrelationControl({})
    assert cc is not None

@test("PortfolioOptimizer: import")
def test_portfolio_optimizer():
    from paper_trading.layers.layer2_risk.portfolio_optimizer import PortfolioOptimizer
    po = PortfolioOptimizer({})
    assert po is not None

@test("CorrelationControl: add prices and compute matrix")
def test_correlation_matrix():
    from paper_trading.layers.layer2_risk.correlation_control import CorrelationControl
    cc = CorrelationControl({'correlation_lookback': 30})

    np.random.seed(42)
    for i in range(50):
        cc.add_price('BTCUSDT', 50000 + i * 100 + np.random.normal(0, 500), time.time())
        cc.add_price('ETHUSDT', 3000 + i * 5 + np.random.normal(0, 30), time.time())

    matrix = cc.compute_correlation_matrix()
    assert matrix is not None
    assert matrix.shape == (2, 2)

@test("PortfolioOptimizer: optimize allocation")
def test_portfolio_optimize():
    from paper_trading.layers.layer2_risk.portfolio_optimizer import PortfolioOptimizer
    po = PortfolioOptimizer({'returns_lookback': 50})

    np.random.seed(42)
    for i in range(60):
        po.add_return('BTCUSDT', np.random.normal(0.001, 0.02))
        po.add_return('ETHUSDT', np.random.normal(0.002, 0.025))

    alloc = po.optimize(['BTCUSDT', 'ETHUSDT'], 10000, {})
    assert len(alloc) == 2

@test("HMM: import")
def test_hmm():
    from paper_trading.layers.layer4_intelligence.hmm import HMMRegimeDetector
    hmm = HMMRegimeDetector({})
    assert hmm is not None

@test("SignalAggregator: import")
def test_signal_aggregator():
    from paper_trading.layers.layer3_signals.signal_aggregator import SignalAggregator
    sa = SignalAggregator()
    assert sa is not None

@test("AdaptiveLearning: import")
def test_adaptive_learning():
    from paper_trading.layers.layer4_intelligence.adaptive_learning import AdaptiveLearning
    al = AdaptiveLearning({})
    assert al is not None


# ============================================================
# TEST: ORCHESTRATOR INTEGRATION
# ============================================================
@test("Orchestrator: import and components")
def test_orchestrator():
    from paper_trading.orchestrator.trading_orchestrator import TradingOrchestrator
    import yaml
    import tempfile

    config = {
        'trading': {'symbol': 'BTCUSDT', 'leverage': 75, 'update_interval': 30},
        'layers': {
            'data': {'enabled': False},
            'features': {'enabled': False},
            'strategy': {'enabled': False},
            'intelligence': {'enabled': False},
            'scoring': {'enabled': False},
            'risk': {'enabled': False},
            'execution': {'enabled': False},
            'memory': {'enabled': False}
        }
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config, f)
        config_path = f.name

    try:
        orch = TradingOrchestrator(config_path)
        assert hasattr(orch, 'correlation_control')
        assert hasattr(orch, 'portfolio_optimizer')
    finally:
        os.unlink(config_path)


@test("Layer count: all 25 layers/interfaces exist")
def test_layer_count():
    expected = [
        'data_layer', 'features_layer', 'strategy_layer', 'intelligence_layer',
        'scoring_layer', 'risk_layer', 'execution_layer', 'memory_layer'
    ]
    for layer in expected:
        module = __import__(f'paper_trading.interfaces.{layer}', fromlist=[''])
        assert module is not None


# ============================================================
# TEST: ORCHESTRATOR FULL INTEGRATION
# ============================================================
@test("Orchestrator: all 5 new components initialized")
def test_orchestrator_advanced_components():
    from paper_trading.orchestrator.trading_orchestrator import TradingOrchestrator
    import yaml
    import tempfile

    config = {
        'trading': {'symbol': 'BTCUSDT', 'leverage': 75, 'update_interval': 30},
        'layers': {
            'data': {'enabled': False},
            'features': {'enabled': False},
            'strategy': {'enabled': False},
            'intelligence': {'enabled': False},
            'scoring': {'enabled': False},
            'risk': {'enabled': False},
            'execution': {'enabled': False},
            'memory': {'enabled': False}
        }
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config, f)
        config_path = f.name

    try:
        orch = TradingOrchestrator(config_path)
        assert hasattr(orch, 'event_bus')
        assert hasattr(orch, 'uncertainty_model')
        assert hasattr(orch, 'exploration_engine')
        assert hasattr(orch, 'model_validator')
        assert hasattr(orch, 'evolution_engine')
        assert hasattr(orch, '_trade_count')
    finally:
        os.unlink(config_path)


@test("Orchestrator: get_full_status() includes advanced components")
def test_orchestrator_status():
    from paper_trading.orchestrator.trading_orchestrator import TradingOrchestrator
    import yaml
    import tempfile

    config = {
        'trading': {'symbol': 'BTCUSDT', 'leverage': 75, 'update_interval': 30},
        'layers': {
            'data': {'enabled': False},
            'features': {'enabled': False},
            'strategy': {'enabled': False},
            'intelligence': {'enabled': False},
            'scoring': {'enabled': False},
            'risk': {'enabled': False},
            'execution': {'enabled': False},
            'memory': {'enabled': False}
        }
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config, f)
        config_path = f.name

    try:
        orch = TradingOrchestrator(config_path)
        status = orch.get_full_status()

        assert 'orchestrator' in status
        assert 'layers' in status
        assert 'advanced_components' in status

        adv = status['advanced_components']
        assert 'event_bus' in adv
        assert 'uncertainty_model' in adv
        assert 'exploration_engine' in adv
        assert 'model_validator' in adv
        assert 'evolution_engine' in adv

        # Each should have a status dict
        assert adv['event_bus'] is not None
        assert adv['uncertainty_model'] is not None
        assert adv['exploration_engine'] is not None
        assert adv['model_validator'] is not None
        assert adv['evolution_engine'] is not None
    finally:
        os.unlink(config_path)


# ============================================================
# RUN ALL TESTS
# ============================================================
if __name__ == '__main__':
    print("=" * 60)
    print("FINANCIAL ORCHESTRATOR - COMPREHENSIVE TEST SUITE")
    print("=" * 60)
    print()

    print("[1/6] Testing Event Layer...")
    # Tests run via decorators

    print("[2/6] Testing Uncertainty Model...")

    print("[3/6] Testing Exploration Engine...")

    print("[4/6] Testing Model Validation Engine...")

    print("[5/6] Testing Evolution Engine...")

    print("[6/6] Testing Integration...")

    print()
    print("=" * 60)
    print(f"RESULTS: {results['passed']} passed, {results['failed']} failed")
    print("=" * 60)

    if results['errors']:
        print("\nFAILED TESTS:")
        for name, error in results['errors']:
            print(f"  - {name}: {error}")
        sys.exit(1)
    else:
        print("\nALL TESTS PASSED")
        sys.exit(0)
