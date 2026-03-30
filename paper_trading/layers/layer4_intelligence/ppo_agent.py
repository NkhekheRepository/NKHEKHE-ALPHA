"""
PPO Reinforcement Learning Agent
================================
Integrates PPO trading agent from vnpy_engine into paper_trading system.
"""

import os
import sys
import numpy as np
from typing import Dict, Any, Optional, List
from pathlib import Path
from loguru import logger

proj_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(proj_root))

try:
    from vnpy_engine.vnpy_local.rl_module import RLAgent, TradingMDP, MonteCarloSimulator
    RL_AVAILABLE = True
except ImportError:
    RL_AVAILABLE = False
    logger.warning("RL module not available, using fallback")


class PPOAgent:
    def __init__(self, symbols: List[str], config: Dict[str, Any] = None):
        self.symbols = symbols
        self.config = config or {}
        self.agent: Optional[RLAgent] = None
        self.monte_carlo = MonteCarloSimulator(n_simulations=1000)
        self.is_trained = False
        
        if RL_AVAILABLE:
            try:
                self.agent = RLAgent(
                    symbols=symbols,
                    memory_path="/home/ubuntu/financial_orchestrator/memory/rl"
                )
                logger.info(f"PPO Agent initialized for {symbols}")
                
                if self.agent.total_steps > 0:
                    self.is_trained = True
                    logger.info(f"PPO Agent loaded with {self.agent.total_steps} training steps")
            except Exception as e:
                logger.error(f"Failed to initialize PPO agent: {e}")
                self.agent = None
    
    def predict(self, state: Dict[str, Any]) -> str:
        if not self.agent:
            return "hold"
        
        try:
            obs = self._state_to_observation(state)
            action, _ = self.agent.policy.predict(obs, deterministic=True)
            
            actions = ['hold', 'buy', 'sell', 'close']
            return actions[action] if action < len(actions) else 'hold'
        except Exception as e:
            logger.error(f"PPO prediction error: {e}")
            return "hold"
    
    def train(self, timesteps: int = 10000):
        if not self.agent:
            logger.warning("Cannot train: agent not initialized")
            return
        
        try:
            self.agent.train(total_timesteps=timesteps)
            self.is_trained = True
            logger.info(f"PPO training completed: {timesteps} timesteps")
        except Exception as e:
            logger.error(f"PPO training error: {e}")
    
    def save_checkpoint(self):
        if self.agent:
            self.agent.save_checkpoint()
    
    def _state_to_observation(self, state: Dict[str, Any]) -> np.ndarray:
        obs = []
        for symbol in self.symbols:
            s = state.get(symbol, {})
            obs.extend([
                s.get('price', 50000) / 50000.0,
                s.get('volume', 100) / 100.0,
                s.get('position', 0) / 10.0,
                s.get('pnl', 0) / 1000.0,
                s.get('volatility', 0.5),
                s.get('trend', 0)
            ])
        return np.array(obs, dtype=np.float32)


class MonteCarloRisk:
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.simulator = MonteCarloSimulator(n_simulations=1000)
        
    def evaluate(self, position: Dict[str, Any], market_data: Dict[str, Any]) -> Dict[str, float]:
        try:
            return self.simulator.evaluate_risk(position, market_data)
        except Exception as e:
            logger.error(f"Monte Carlo risk evaluation error: {e}")
            return {
                'var_95': 0.0,
                'cvar_95': 0.0,
                'expected_return': 0.0,
                'max_drawdown': 0.0,
                'sharpe_ratio': 0.0
            }
    
    def simulate_action(self, action: str, current_state: Dict[str, Any], 
                       n_scenarios: int = 100) -> List[Dict[str, float]]:
        try:
            return self.simulator.simulate_scenarios(action, current_state, n_scenarios)
        except Exception as e:
            logger.error(f"Monte Carlo simulation error: {e}")
            return []
    
    def should_trade(self, action: str, current_state: Dict[str, Any],
                    var_threshold: float = -0.05) -> bool:
        scenarios = self.simulate_action(action, current_state, n_scenarios=100)
        
        if not scenarios:
            return True
        
        returns = [s['price_change'] for s in scenarios]
        var = np.percentile(returns, 5)
        
        return var > var_threshold
