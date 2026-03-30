"""
Financial Orchestrator Interfaces
=================================
Modular layer contracts for plug-and-play architecture.
"""

from .base import (
    BaseLayer,
    LayerInput,
    LayerOutput,
    MarketData,
    FeatureVector,
    TradingSignal,
    Trade,
    Position,
    DecisionRecord,
    MetricsRecord,
    LayerRegistry,
    LayerWithFallback
)

from .data_layer import IDataLayer, DataLayer
from .features_layer import IFeaturesLayer, FeaturesLayer
from .strategy_layer import IStrategyLayer, StrategyLayer, StrategyRegistry
from .intelligence_layer import IIntelligenceLayer, IntelligenceLayer
from .scoring_layer import IScoringLayer, ScoringLayer
from .risk_layer import IRiskLayer, RiskLayer
from .execution_layer import IExecutionLayer, ExecutionLayer
from .memory_layer import IMemoryLayer, MemoryLayer

__all__ = [
    'BaseLayer',
    'LayerInput',
    'LayerOutput',
    'MarketData',
    'FeatureVector',
    'TradingSignal',
    'Trade',
    'Position',
    'DecisionRecord',
    'MetricsRecord',
    'LayerRegistry',
    'LayerWithFallback',
    'IDataLayer',
    'DataLayer',
    'IFeaturesLayer',
    'FeaturesLayer',
    'IStrategyLayer',
    'StrategyLayer',
    'StrategyRegistry',
    'IIntelligenceLayer',
    'IntelligenceLayer',
    'IScoringLayer',
    'ScoringLayer',
    'IRiskLayer',
    'RiskLayer',
    'IExecutionLayer',
    'ExecutionLayer',
    'IMemoryLayer',
    'MemoryLayer'
]
