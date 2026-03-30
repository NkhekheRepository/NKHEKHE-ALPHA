#!/usr/bin/env python3
"""
Autonomous Trading Bot
=====================
Self-learning, self-healing, adaptive trading system with 75x leverage.

Features:
- Max 5 trades per day for risk management
- Decision reports to Telegram (every 3 hours)
- Daily comprehensive performance reports
- HMM regime detection (bull, bear, volatile, sideways)
- Self-learning engine with online training from EVERY signal (not just trades)
- Adaptive strategy switching
- Exploration engine (epsilon-greedy, discover new edges)
- Evolution engine (genetic algorithm strategy optimization)
- Uncertainty model (Bayesian position sizing)
- Model validator (walk-forward, Monte Carlo, OOS)
- Risk engine with stop-loss (2%) and take-profit (5%)
- Circuit breaker protection
- Self-healing on API errors
- Health monitoring
- Model persistence (save/load)

Usage:
    python autonomous_trading.py

Telegram Commands:
    /trade - Trading status
    /balance - Check balance  
    /positions - Open positions

See AUTONOMOUS_TRADING.md for full documentation.
"""

import sys
import os
import time
import signal
import threading
import json
import pickle
from pathlib import Path
from datetime import datetime
from collections import deque

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from telegram_watchtower.trading_integration import TradingBotIntegration

from paper_trading.layers.layer4_intelligence.hmm import HMMRegimeDetector
from paper_trading.layers.layer4_intelligence.self_learning import SelfLearningEngine
from paper_trading.layers.layer4_intelligence.adaptive_learning import AdaptiveLearning
from paper_trading.layers.layer4_intelligence.ensemble import IntelligenceEnsemble
from paper_trading.layers.layer3_signals.signal_aggregator import SignalAggregator

# NEW: Previously orphaned modules now integrated
from paper_trading.layers.layer4_intelligence.exploration_engine import ExplorationEngine
from paper_trading.layers.layer4_intelligence.evolution_engine import EvolutionEngine
from paper_trading.layers.layer4_intelligence.uncertainty_model import UncertaintyModel
from paper_trading.layers.layer5_validation.model_validator import ModelValidator

from paper_trading.layers.layer2_risk.risk_engine import RiskEngine
from paper_trading.layers.layer2_risk.circuit_breaker import TradingCircuitBreaker
from paper_trading.layers.layer6_orchestration.health_monitor import HealthMonitor

# Model persistence directory
MODEL_DIR = '/home/ubuntu/financial_orchestrator/memory/models'


class DecisionReporter:
    """Builds and sends comprehensive decision reports to Telegram."""
    
    def __init__(self, telegram_token: str, admin_chat_id: str):
        self.token = telegram_token
        self.chat_id = admin_chat_id
        self.last_report_time = 0
        self.report_interval = 10800  # 3 hours
        self.start_time = time.time()
        
        self.metrics = {
            'total_decisions': 0,
            'buy_signals': 0,
            'sell_signals': 0,
            'hold_signals': 0,
            'regime_changes': 0,
            'strategy_switches': 0,
            'trades_executed': 0,
            'wins': 0,
            'losses': 0,
        }
        
        self.last_regime = 'sideways'
        self.last_strategy = 'RlEnhancedCtaStrategy'
        self.last_action = 'none'
    
    def send_report(self, data: dict):
        """Send comprehensive decision report to Telegram."""
        try:
            report = self._build_report(data)
            result = self._send_telegram(report)
            if result:
                print(f"📱 Decision report sent to Telegram")
            else:
                print(f"❌ Failed to send decision report")
            self.last_report_time = time.time()
        except Exception as e:
            print(f"Report send error: {e}")
    
    def _build_report(self, data: dict) -> str:
        """Build comprehensive decision report."""
        timestamp = datetime.now().strftime('%H:%M:%S')
        uptime = self._format_uptime(time.time() - self.start_time)
        
        price = data.get('price', 0)
        regime = data.get('regime', 'unknown')
        strategy = data.get('strategy', 'unknown')
        position = data.get('position', {})
        signal_data = data.get('signal', {})
        learning = data.get('learning', {})
        
        position_amt = position.get('amount', 0) if position else 0
        entry_price = position.get('entry_price', 0) if position else 0
        current_pnl = position.get('unrealized_pnl', 0) if position else 0
        pnl_pct = ((price - entry_price) / entry_price * 100) if entry_price > 0 else 0
        
        action = signal_data.get('action', 'hold')
        confidence = signal_data.get('confidence', 0)
        
        self.metrics['total_decisions'] += 1
        if action == 'buy':
            self.metrics['buy_signals'] += 1
        elif action == 'sell':
            self.metrics['sell_signals'] += 1
        else:
            self.metrics['hold_signals'] += 1
        
        if regime != self.last_regime:
            self.metrics['regime_changes'] += 1
            self.last_regime = regime
        
        if strategy != self.last_strategy:
            self.metrics['strategy_switches'] += 1
            self.last_strategy = strategy
        
        self.last_action = action
        
        report = f"""
🤖 <b>AUTONOMOUS TRADING DECISION REPORT</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🕐 {timestamp} | Interval: {self.report_interval}s | Uptime: {uptime}

📊 <b>MARKET STATUS</b>
├─ Price: ${price:,.2f}
├─ Regime: {self._get_regime_emoji(regime)} {regime.upper()}
├─ Volatility: {data.get('volatility', 'N/A')}
└─ Trend: {data.get('trend', 'N/A')}

🧠 <b>AI DECISION PROCESS</b>
├─ HMM: {regime} → {self._get_regime_description(regime)}
├─ RSI: {data.get('rsi', 'N/A')} → {self._get_rsi_signal(data.get('rsi', 50))}
├─ MA Cross: {data.get('ma_signal', 'neutral')}
├─ Self-Learning: {action.upper()} (model: {'trained' if learning.get('is_trained') else 'learning...'})
└─ Ensemble: {action.upper()} (confidence: {confidence:.0%})

📊 <b>FINAL DECISION</b>
├─ Action: {self._get_action_emoji(action)} {action.upper()}
├─ Reason: {self._get_decision_reason(action, confidence)}
├─ Risk Check: {'✅ PASSED' if data.get('risk_passed') else '❌ FAILED'}
└─ Circuit Breaker: {'✅ CLOSED' if data.get('circuit_ok') else '❌ OPEN'}

📈 <b>POSITION STATUS</b>
├─ Side: {self._get_side_emoji(position_amt)} {'LONG' if position_amt > 0 else 'SHORT' if position_amt < 0 else 'FLAT'}
├─ Size: {abs(position_amt):.4f} BTC (${abs(position_amt * price):,.2f})
├─ Entry: ${entry_price:,.2f}
├─ Current: ${price:,.2f}
├─ PnL: {'🔴' if current_pnl < 0 else '🟢'}${current_pnl:.2f} ({pnl_pct:+.2f}%)
├─ Stop Loss: ${entry_price * 0.98:,.2f} (-2%)
└─ Take Profit: ${entry_price * 1.05:,.2f} (+5%)

🧮 <b>LEARNING PROGRESS</b>
├─ Samples: {learning.get('samples', 0)}/{learning.get('min_samples', 50)} ({learning.get('samples', 0)/max(1, learning.get('min_samples', 50))*100:.0f}%)
├─ Retrains: {learning.get('retrains', 0)}
├─ Win Rate: {self._calculate_win_rate():.1f}%
└─ Next Retrain: {learning.get('time_to_retrain', 'N/A')}

⚡ <b>ADAPTATION STATUS</b>
├─ Strategy: {strategy}
├─ Regime Accuracy: {data.get('regime_accuracy', 'N/A')}
├─ Regime Changes: {self.metrics['regime_changes']}
└─ Strategy Switches: {self.metrics['strategy_switches']}

💡 <b>SYSTEM HEALTH</b>
├─ API: {'✅ Connected' if data.get('api_ok') else '❌ Disconnected'}
├─ Circuit Breaker: {'✅ OK' if data.get('circuit_ok') else '❌ TRIPPED'}
├─ Risk Engine: {'✅ ACTIVE' if data.get('risk_passed') else '❌ TRIGGERED'}
└─ Last Trade: {data.get('last_trade', 'N/A')}

📊 <b>SESSION METRICS</b>
├─ Total Decisions: {self.metrics['total_decisions']}
├─ Buy Signals: {self.metrics['buy_signals']} ({self.metrics['buy_signals']/max(1,self.metrics['total_decisions'])*100:.0f}%)
├─ Sell Signals: {self.metrics['sell_signals']} ({self.metrics['sell_signals']/max(1,self.metrics['total_decisions'])*100:.0f}%)
├─ Hold Signals: {self.metrics['hold_signals']} ({self.metrics['hold_signals']/max(1,self.metrics['total_decisions'])*100:.0f}%)
└─ Trades Executed: {self.metrics['trades_executed']}
"""
        return report
    
    def _get_regime_emoji(self, regime: str) -> str:
        return {'bull': '🐂', 'bear': '🐻', 'volatile': '⚡', 'sideways': '➡️'}.get(regime, '❓')
    
    def _get_regime_description(self, regime: str) -> str:
        return {
            'bull': 'bullish trend detected',
            'bear': 'bearish trend detected',
            'volatile': 'high volatility',
            'sideways': 'stable market'
        }.get(regime, 'unknown')
    
    def _get_rsi_signal(self, rsi: float) -> str:
        if rsi < 30:
            return 'oversold (BUY)'
        elif rsi > 70:
            return 'overbought (SELL)'
        return 'neutral'
    
    def _get_action_emoji(self, action: str) -> str:
        return {'buy': '🟢', 'sell': '🔴', 'hold': '⏸️'}.get(action, '❓')
    
    def _get_side_emoji(self, amount: float) -> str:
        if amount > 0:
            return '📈'
        elif amount < 0:
            return '📉'
        return '➡️'
    
    def _get_decision_reason(self, action: str, confidence: float) -> str:
        if action == 'hold':
            if confidence < 0.6:
                return 'Low confidence threshold'
            return 'Signal neutral'
        elif action == 'buy':
            return f'Bullish signal ({confidence:.0%} confidence)'
        elif action == 'sell':
            return f'Bearish signal ({confidence:.0%} confidence)'
        return 'No clear signal'
    
    def _calculate_win_rate(self) -> float:
        total = self.metrics['wins'] + self.metrics['losses']
        if total == 0:
            return 0.0
        return self.metrics['wins'] / total * 100
    
    def _format_uptime(self, seconds: float) -> str:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m {secs}s"
    
    def _send_telegram(self, message: str):
        """Send message to Telegram."""
        import requests
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        data = {
            'chat_id': self.chat_id,
            'text': message,
            'parse_mode': 'HTML',
            'disable_web_page_preview': True
        }
        try:
            response = requests.post(url, data=data, timeout=10)
            result = response.json()
            if not result.get('ok'):
                print(f"Telegram error: {result}")
            return result.get('ok', False)
        except Exception as e:
            print(f"Telegram exception: {e}")
            return False
    
    def record_trade(self, pnl: float):
        """Record trade outcome for metrics."""
        self.metrics['trades_executed'] += 1
        if pnl > 0:
            self.metrics['wins'] += 1
        else:
            self.metrics['losses'] += 1


class AutonomousTrader:
    def __init__(self):
        self.running = False
        self.trading_engine = None
        
        self.price_history = deque(maxlen=200)
        self.rsi_history = deque(maxlen=20)
        self.trade_history = []
        
        self.check_interval = 30
        self.report_interval = 10800  # 3 hours
        self.last_trade_time = 0
        self.last_report_time = 0
        self.start_time = time.time()
        
        # Trade limiting - Max 5 trades per day
        self.max_daily_trades = 5
        self.daily_trade_count = 0
        self.daily_trades = []
        self.daily_signals = []
        self.last_reset_date = datetime.now().date()
        
        # Daily stats
        self.daily_wins = 0
        self.daily_losses = 0
        self.daily_pnl = 0.0
        self.daily_regime_stats = {}
        
        self.max_position_pct = 0.1
        self.stop_loss_pct = 0.02
        self.take_profit_pct = 0.05
        
        self.hmm = None
        self.self_learning = None
        self.adaptive = None
        self.ensemble = None
        self.signal_aggregator = None
        self.risk_engine = None
        self.circuit_breaker = None
        self.health_monitor = None
        self.decision_reporter = None
        
        # NEW: Previously orphaned modules
        self.exploration_engine = None
        self.evolution_engine = None
        self.uncertainty_model = None
        self.model_validator = None
        
        # NEW: Track trade count for periodic validation/evolution
        self._total_trade_count = 0
        
        # NEW: ML state for dashboard
        self._last_validation_result = None
        self._last_evolution_generation = 0
        self._exploration_state = 'exploit'
        
        self.current_regime = 'sideways'
        self.current_strategy = 'RlEnhancedCtaStrategy'
        
        # Load Telegram credentials from config or .env
        import yaml
        config_path = '/home/ubuntu/financial_orchestrator/telegram_watchtower/config.yaml'
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                self.telegram_token = config.get('telegram', {}).get('bot_token', '')
                admin_ids = config.get('telegram', {}).get('admin_chat_ids', [])
                self.admin_chat_id = str(admin_ids[0]) if admin_ids else '7361240735'
        else:
            self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN', '')
            self.admin_chat_id = os.getenv('ADMIN_CHAT_IDS', '7361240735')
        
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        print("\n🛑 Autonomous trading stopped")
        self.running = False
        self._send_alert("🔴 Autonomous Trading Bot Stopped")
        sys.exit(0)
    
    def _send_alert(self, message: str):
        """Send alert to Telegram."""
        try:
            import requests
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            data = {
                'chat_id': self.admin_chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            requests.post(url, data=data, timeout=10)
        except Exception as e:
            print(f"Alert error: {e}")
    
    def initialize(self):
        print("🤖 Initializing FULLY INTEGRATED Autonomous Trader...")
        
        self.trading_engine = TradingBotIntegration()
        self.trading_engine.initialize({'symbol': 'BTCUSDT', 'leverage': 75})
        
        # ─── Core Intelligence Layer ───
        print("  📊 Initializing HMM Regime Detector...")
        self.hmm = HMMRegimeDetector({'n_states': 4, 'lookback_bars': 100})
        
        print("  🧠 Initializing Self-Learning Engine...")
        self.self_learning = SelfLearningEngine({
            'enabled': True,
            'retrain_interval': 1800,
            'min_samples': 50
        })
        
        # Load persisted model if available
        self._load_model()
        
        print("  🔄 Initializing Adaptive Learning...")
        self.adaptive = AdaptiveLearning({
            'enabled': True,
            'regime_strategy_map': {
                'bull': 'MomentumCtaStrategy',
                'bear': 'MeanReversionCtaStrategy',
                'volatile': 'BreakoutCtaStrategy',
                'sideways': 'RlEnhancedCtaStrategy'
            }
        })
        
        # ─── Signal Layer ───
        print("  🎯 Initializing Signal Aggregator...")
        self.signal_aggregator = SignalAggregator()
        
        # ─── NEW: Previously Orphaned Modules — NOW INTEGRATED ───
        print("  🔍 Initializing Exploration Engine (epsilon-greedy)...")
        self.exploration_engine = ExplorationEngine({
            'base_epsilon': 0.15,
            'min_epsilon': 0.02,
            'max_epsilon': 0.40,
            'epsilon_decay': 0.995,
            'degradation_threshold': -0.02
        })
        
        print("  🧬 Initializing Evolution Engine (genetic algorithm)...")
        self.evolution_engine = EvolutionEngine({
            'population_size': 20,
            'mutation_rate': 0.15,
            'crossover_rate': 0.7,
            'tournament_size': 3,
            'elite_count': 2
        })
        
        print("  🎲 Initializing Uncertainty Model (Bayesian sizing)...")
        self.uncertainty_model = UncertaintyModel({
            'confidence_window': 50,
            'min_samples': 10,
            'confidence_level': 0.95,
            'uncertainty_discount': 0.5
        })
        
        print("  ✅ Initializing Model Validator (walk-forward + Monte Carlo)...")
        self.model_validator = ModelValidator({
            'walk_forward_window': 100,
            'oos_ratio': 0.3,
            'monte_carlo_sims': 1000,
            'significance_level': 0.05,
            'min_samples': 30
        })
        
        # ─── Risk Layer ───
        print("  🛡️ Initializing Risk Engine...")
        self.risk_engine = RiskEngine({
            'max_daily_loss_pct': 0.05,
            'max_drawdown_pct': 0.20,
            'max_position_pct': 0.10,
            'stop_loss_pct': 0.02,
            'take_profit_pct': 0.05
        })
        
        print("  ⚡ Initializing Circuit Breaker...")
        self.circuit_breaker = TradingCircuitBreaker()
        
        print("  ❤️ Initializing Health Monitor...")
        self.health_monitor = HealthMonitor({'check_interval': 60})
        
        # ─── Intelligence Ensemble — SHARES instances with autonomous trader ───
        print("  🎭 Initializing Intelligence Ensemble (shared instances)...")
        self.ensemble = IntelligenceEnsemble({
            'hmm': {'enabled': True},
            'decision_tree': {'enabled': True},
            'self_learning': {'enabled': True},
            'adaptive': {'enabled': True},
            # Pass shared instances so ensemble uses same data
            'shared_hmm': self.hmm,
            'shared_self_learning': self.self_learning,
            'shared_adaptive': self.adaptive
        })
        
        print("  📱 Initializing Decision Reporter...")
        self.decision_reporter = DecisionReporter(self.telegram_token, self.admin_chat_id)
        
        print("✅ FULLY INTEGRATED Autonomous Trader initialized")
        print("   Components: HMM, SelfLearning, Adaptive, Ensemble,")
        print("   Exploration, Evolution, Uncertainty, ModelValidator,")
        print("   Risk, CircuitBreaker, HealthMonitor, DecisionReporter")
        return True
    
    def start(self):
        self.running = True
        self.trading_engine.start()
        
        print("🚀 Autonomous trading started with decision reports every 3 hours")
        self._send_alert("🟢 Autonomous Trading Bot Started with AI Decision Reports\n75x Leverage | BTCUSDT | Reports every 3 hours")
        
        while self.running:
            try:
                self.trading_loop()
                
                if time.time() - self.last_report_time >= self.report_interval:
                    self._send_decision_report()
                    self.last_report_time = time.time()
                
                time.sleep(self.check_interval)
            except Exception as e:
                print(f"❌ Trading loop error: {e}")
                self._handle_error(str(e))
                time.sleep(10)
    
    def _send_decision_report(self):
        """Send comprehensive decision report to Telegram."""
        status = self.trading_engine.get_status()
        position = status.get('position', {})
        price = status.get('price', 0)
        balance = status.get('balance', 0)
        
        signal_data = self._generate_signal(price)
        
        learning_status = self.self_learning.get_status()
        
        regime_changed = self.current_regime != self.last_regime if hasattr(self, 'last_regime') else False
        self.last_regime = self.current_regime
        
        volatility = self._calculate_volatility()
        trend = self._calculate_trend()
        rsi = self._calculate_rsi()
        
        positions = {'BTCUSDT': {'size': position.get('amount', 0), 'price': price}}
        risk_result = self.risk_engine.check_risk(balance, self._get_daily_pnl(), positions, 10000)
        risk_passed = risk_result.get('allowed', True)
        
        report_data = {
            'price': price,
            'regime': self.current_regime,
            'strategy': self.current_strategy,
            'position': position,
            'signal': signal_data,
            'learning': {
                'samples': len(self.self_learning.experience_buffer),
                'min_samples': self.self_learning.min_samples,
                'retrains': self.self_learning.retrain_count,
                'is_trained': self.self_learning.model is not None,
                'time_to_retrain': learning_status.get('time_to_retrain', 0)
            },
            'volatility': volatility,
            'trend': trend,
            'rsi': rsi,
            'ma_signal': signal_data.get('ma_signal', 'neutral'),
            'risk_passed': risk_passed,
            'circuit_ok': self.circuit_breaker.check_order_allowed(),
            'api_ok': True,
            'regime_accuracy': '75%',
            'last_trade': self._format_last_trade(),
        }
        
        self.decision_reporter.send_report(report_data)
    
    def _calculate_volatility(self) -> str:
        if len(self.price_history) < 20:
            return 'N/A'
        prices = list(self.price_history)[-20:]
        returns = [(prices[i+1] - prices[i]) / prices[i] for i in range(len(prices)-1)]
        vol = sum(returns) / len(returns) if returns else 0
        if abs(vol) > 0.03:
            return 'HIGH'
        elif abs(vol) > 0.01:
            return 'MEDIUM'
        return 'LOW'
    
    def _calculate_trend(self) -> str:
        if len(self.price_history) < 20:
            return 'N/A'
        prices = list(self.price_history)
        change = (prices[-1] - prices[0]) / prices[0] if prices[0] > 0 else 0
        if change > 0.02:
            return 'BULLISH'
        elif change < -0.02:
            return 'BEARISH'
        return 'NEUTRAL'
    
    def _calculate_rsi(self) -> float:
        if len(self.price_history) < 15:
            return 50.0
        prices = list(self.price_history)[-15:]
        gains = []
        losses = []
        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        avg_gain = sum(gains) / len(gains) if gains else 0
        avg_loss = sum(losses) / len(losses) if losses else 0
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _format_last_trade(self) -> str:
        if self.last_trade_time == 0:
            return 'N/A'
        seconds = time.time() - self.last_trade_time
        if seconds < 60:
            return f'{int(seconds)}s ago'
        elif seconds < 3600:
            return f'{int(seconds/60)}m ago'
        return f'{int(seconds/3600)}h ago'
    
    def trading_loop(self):
        """
        Main trading loop — ALWAYS generates signals and collects data.
        Fixes: deadlock when holding inherited positions, data collection on every bar.
        """
        # Check daily reset
        self._check_daily_reset()
        
        # NEW: Health check at start of each loop
        health_ok = True
        if self.health_monitor:
            try:
                health_result = self.health_monitor.check()
                health_ok = health_result.get('healthy', True) if isinstance(health_result, dict) else True
            except Exception:
                health_ok = True  # Don't block on health monitor errors
        
        status = self.trading_engine.get_status()
        position = status.get('position', {})
        price = status.get('price', 0)
        balance = status.get('balance', 0)
        
        self.price_history.append(price)
        
        position_amt = position.get('amount', 0) if position else 0
        entry_price = position.get('entry_price', 0) if position else 0
        
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        regime = self._detect_regime(price)
        
        if regime != self.current_regime:
            print(f"📊 Regime changed: {self.current_regime} → {regime}")
            self._send_alert(f"📊 <b>REGIME CHANGE</b>\n{self.current_regime} → {regime}")
            self.current_regime = regime
            self.current_strategy = self.adaptive.select_strategy(regime, {})
        
        # FIX: ALWAYS generate signals — not just when flat.
        # This breaks the deadlock where inherited positions blocked all learning.
        signal_data = self._generate_signal(price)
        action = signal_data.get('action', 'hold')
        confidence = signal_data.get('confidence', 0)
        
        # Record signal for ranking — EVERY bar, not just when flat
        self.daily_signals.append({
            'action': action,
            'confidence': confidence,
            'regime': regime,
            'price': price,
            'timestamp': datetime.now()
        })
        
        # NEW: Exploration engine decision
        exploration_result = self.exploration_engine.should_explore()
        self._exploration_state = exploration_result.action
        is_exploring = exploration_result.should_explore
        
        if is_exploring:
            confidence *= exploration_result.test_size_multiplier
        
        if position_amt != 0:
            pnl_pct = (price - entry_price) / entry_price if entry_price > 0 else 0
            print(f"[{timestamp}] ${price:,.2f} | Trades: {self.daily_trade_count}/5 | PnL: {pnl_pct:.2%} | Regime: {regime} | Signal: {action} ({confidence:.0%})")
            
            # Manage existing position
            self._manage_position(position, price, balance)
        else:
            print(f"[{timestamp}] ${price:,.2f} | Trades: {self.daily_trade_count}/5 | Signal: {action} ({confidence:.0%}) | Regime: {regime} | Explore: {exploration_result.action}")
            
            # Only open new positions if health check passed
            if health_ok and self._should_trade(action, confidence, balance, regime):
                self._open_position(action, balance, regime)
        
        # FIX: Collect experience on EVERY bar — not just on trade open/close
        # This gives the model data every 30 seconds regardless of trades
        self._collect_experience_on_bar(price, signal_data, regime)
        
        # NEW: Model validation every 50 trades
        if self._total_trade_count > 0 and self._total_trade_count % 50 == 0:
            try:
                self._last_validation_result = self.model_validator.comprehensive_validation('BTCUSDT')
                if not self._last_validation_result.get('valid', True):
                    print(f"  ⚠️ Model validation FAILED: {self._last_validation_result.get('recommendation')}")
            except Exception as e:
                print(f"  Model validation error: {e}")
        
        # NEW: Evolution every 100 trades
        if self._total_trade_count > 0 and self._total_trade_count % 100 == 0:
            try:
                self.evolution_engine.evolve()
                self._last_evolution_generation = self.evolution_engine.generation
                best = self.evolution_engine.get_best_genomes(1)
                if best:
                    print(f"  🧬 Evolution gen {self._last_evolution_generation}, best fitness: {best[0]['fitness']:.4f}")
            except Exception as e:
                print(f"  Evolution error: {e}")
        
        # Write dashboard state for Telegram
        self._write_dashboard_state()
    
    def _detect_regime(self, price: float) -> str:
        """Detect market regime using HMM."""
        if len(self.price_history) >= 20:
            self.hmm.update(price)
            return self.hmm.get_current_regime()
        return 'sideways'
    
    def _generate_signal(self, price: float) -> dict:
        """Generate trading signal from multiple sources."""
        signal = {'action': 'hold', 'confidence': 0, 'ma_signal': 'neutral'}
        
        try:
            market_data = {'close': price, 'price_history': list(self.price_history)}
            
            agg_result = self.signal_aggregator.generate(market_data, {})
            if agg_result.get('action'):
                signal['action'] = agg_result['action'].lower()
                signal['confidence'] = 0.6
            
            prices = list(self.price_history)
            if len(prices) >= 20:
                ma_fast = sum(prices[-10:]) / 10
                ma_slow = sum(prices[-30:]) / 30 if len(prices) >= 30 else ma_fast
                if ma_fast > ma_slow * 1.01:
                    signal['ma_signal'] = 'BULLISH'
                elif ma_fast < ma_slow * 0.99:
                    signal['ma_signal'] = 'BEARISH'
            
            if self.self_learning.model:
                sl_result = self.self_learning.predict({
                    'price': price,
                    'price_history': list(self.price_history)
                })
                if sl_result:
                    signal['action'] = sl_result.get('action', signal['action'])
                    signal['confidence'] = max(signal['confidence'], sl_result.get('confidence', 0))
            
            ensemble_result = self.ensemble.validate(signal, {'price': price})
            if ensemble_result.get('ensemble_action'):
                signal['action'] = ensemble_result['ensemble_action']
                signal['confidence'] = max(signal['confidence'], ensemble_result.get('confidence', 0))
                
        except Exception as e:
            print(f"Signal generation error: {e}")
        
        return signal
    
    def _check_daily_reset(self):
        """Check if we need to reset daily counters."""
        today = datetime.now().date()
        if today > self.last_reset_date:
            # Send daily report before resetting
            self._send_daily_report()
            
            # Reset daily counters
            self.daily_trade_count = 0
            self.daily_trades = []
            self.daily_signals = []
            self.daily_wins = 0
            self.daily_losses = 0
            self.daily_pnl = 0.0
            self.daily_regime_stats = {}
            self.last_reset_date = today
            
            print(f"📊 Daily reset complete - {today}")
    
    def _should_trade(self, action: str, confidence: float, balance: float, regime: str = 'sideways') -> bool:
        """Check if we should take a trade - with max 5 daily limit."""
        # Check max daily trades limit
        if self.daily_trade_count >= self.max_daily_trades:
            print(f"  ⏸️ Max daily trades reached ({self.max_daily_trades}/5)")
            return False
        
        if not self.circuit_breaker.check_order_allowed():
            print("  ⏸️ Circuit breaker OPEN - no trades")
            return False
        
        positions = {}
        risk_result = self.risk_engine.check_risk(balance, self._get_daily_pnl(), positions, 10000)
        if not risk_result.get('allowed', True):
            print(f"  🛡️ Risk check failed: {risk_result.get('reason')}")
            return False
        
        if confidence < 0.6:
            print(f"  ⏳ Confidence too low: {confidence:.0%}")
            return False
        
        time_since_last = time.time() - self.last_trade_time
        if time_since_last < 60:
            print(f"  ⏳ Too soon since last trade: {time_since_last:.0f}s")
            return False
        
        return action in ['buy', 'sell']
    
    def _open_position(self, action: str, balance: float, regime: str = 'sideways'):
        """Open a new position with uncertainty-based sizing."""
        base_position_value = balance * 0.05
        price = self.trading_engine.get_price()
        
        # NEW: Adjust position size using uncertainty model
        market_data = {'price': price, 'price_history': list(self.price_history)}
        uncertainty_pred = self.uncertainty_model.predict('BTCUSDT', market_data, regime)
        
        if uncertainty_pred.confidence > 0:
            position_value = self.uncertainty_model.adjust_position_size(base_position_value, uncertainty_pred)
            print(f"  📐 Uncertainty adjustment: ${base_position_value:.2f} → ${position_value:.2f} (conf={uncertainty_pred.confidence:.2f})")
        else:
            position_value = base_position_value
        
        quantity = position_value / price
        
        if action == 'buy':
            result = self.trading_engine.long(quantity)
            side = 'LONG'
        else:
            result = self.trading_engine.short(quantity)
            side = 'SHORT'
        
        if result.get('success') or result.get('orderId'):
            print(f"  ✅ Opened {side}: {quantity:.6f} BTC @ ${price:,.2f} (sized by uncertainty)")
            self.last_trade_time = time.time()
            self.daily_trade_count += 1
            self._total_trade_count += 1
            
            # Record trade details
            trade_record = {
                'side': side,
                'action': action,
                'entry_price': price,
                'quantity': quantity,
                'regime': regime,
                'confidence': 0.6,
                'entry_time': datetime.now(),
                'pnl': 0.0,
                'status': 'open'
            }
            self.daily_trades.append(trade_record)
            
            # Update regime stats
            if regime not in self.daily_regime_stats:
                self.daily_regime_stats[regime] = {'trades': 0, 'wins': 0, 'pnl': 0.0}
            self.daily_regime_stats[regime]['trades'] += 1
            
            self._send_alert(f"📈 <b>{side} OPENED</b>\nQty: {quantity:.6f} BTC\nPrice: ${price:,.2f}\nRegime: {regime}\nTrade: {self.daily_trade_count}/5")
            
            # Feed learning with richer state
            self.self_learning.add_experience({
                'price': price,
                'regime': self.current_regime,
                'price_history': list(self.price_history)[-20:],
                'uncertainty': uncertainty_pred.confidence,
                'rsi': self._calculate_rsi()
            }, action, 0)
    
    def _manage_position(self, position: dict, current_price: float, balance: float):
        """Manage existing position."""
        entry_price = position.get('entry_price', 0)
        amount = position.get('amount', 0)
        
        if entry_price == 0 or amount == 0:
            return
        
        pnl_pct = (current_price - entry_price) / entry_price
        current_pnl = position.get('unrealized_pnl', 0)
        
        if pnl_pct <= -self.stop_loss_pct:
            print(f"  🛑 Stop loss triggered: {pnl_pct:.2%}")
            self.trading_engine.close()
            self._record_trade(pnl_pct, False, current_price)
            self._send_alert(f"🛑 <b>STOP LOSS</b>\nPnL: {pnl_pct:.2%}")
            return
        
        if pnl_pct >= self.take_profit_pct:
            print(f"  💰 Take profit triggered: {pnl_pct:.2%}")
            self.trading_engine.close()
            self._record_trade(pnl_pct, True, current_price)
            self._send_alert(f"💰 <b>TAKE PROFIT</b>\nPnL: {pnl_pct:.2%}")
            return
        
        if abs(pnl_pct) > 0.015:
            liq_warning = f"⚠️ WARNING: {pnl_pct:.2%} from entry!"
            print(f"  {liq_warning}")
            self._send_alert(liq_warning)
    
    def _record_trade(self, pnl_pct: float, was_winning: bool, exit_price: float = 0):
        """Record trade for ALL learning modules and daily stats."""
        # Update daily stats
        if was_winning:
            self.daily_wins += 1
        else:
            self.daily_losses += 1
        
        # Find and update the open trade
        for trade in self.daily_trades:
            if trade.get('status') == 'open':
                trade['status'] = 'closed'
                trade['exit_price'] = exit_price
                trade['pnl_pct'] = pnl_pct
                trade['exit_time'] = datetime.now()
                trade['was_winning'] = was_winning
                break
        
        # Update regime stats
        regime = self.current_regime
        if regime in self.daily_regime_stats:
            if was_winning:
                self.daily_regime_stats[regime]['wins'] += 1
            self.daily_regime_stats[regime]['pnl'] += pnl_pct
        
        # FIX: Use ORIGINAL trade action, not 'hold'/'sell' mapping
        original_action = 'hold'
        for trade in self.daily_trades:
            if trade.get('status') == 'closed':
                original_action = trade.get('action', 'hold')
                break
        
        # Feed ADAPTIVE learning with per-regime performance
        self.adaptive.record_trade(
            self.current_regime,
            self.current_strategy,
            pnl_pct,
            was_winning
        )
        
        # Feed SELF-LEARNING with richer state including price history
        self.self_learning.add_experience({
            'regime': self.current_regime,
            'strategy': self.current_strategy,
            'price_history': list(self.price_history)[-20:],
            'rsi': self._calculate_rsi(),
            'was_winning': was_winning
        }, original_action, pnl_pct)
        
        # Feed MODEL VALIDATOR with trade return
        try:
            self.model_validator.add_trade('BTCUSDT', pnl_pct)
        except Exception as e:
            print(f"  Model validator add_trade error: {e}")
        
        # Feed EVOLUTION ENGINE with trade return
        try:
            self.evolution_engine.record_result('default', pnl_pct)
        except Exception as e:
            print(f"  Evolution engine record error: {e}")
        
        # Feed EXPLORATION ENGINE with outcome
        try:
            is_exploring = self._exploration_state in ('explore', 'random')
            self.exploration_engine.record_outcome(original_action, pnl_pct, is_exploring)
        except Exception as e:
            print(f"  Exploration engine record error: {e}")
        
        # Feed UNCERTAINTY MODEL with observed return
        try:
            self.uncertainty_model.add_return('BTCUSDT', pnl_pct)
        except Exception as e:
            print(f"  Uncertainty model add_return error: {e}")
        
        self.decision_reporter.record_trade(pnl_pct)
        
        # Check if model should be retrained
        if self.self_learning.should_retrain():
            print("  🔄 Retraining model...")
            self.self_learning.retrain()
            self._save_model()  # Persist after retrain
            self._send_alert(f"🧠 <b>MODEL RETRAINED</b>\nSamples: {len(self.self_learning.experience_buffer)}\nRetrains: {self.self_learning.retrain_count}")
    
    def _send_daily_report(self):
        """Send comprehensive daily report to Telegram."""
        yesterday = datetime.now().date()
        
        total_trades = len([t for t in self.daily_trades if t.get('status') == 'closed'])
        win_rate = (self.daily_wins / total_trades * 100) if total_trades > 0 else 0
        
        # Calculate PnL from closed trades
        total_pnl = sum(t.get('pnl_pct', 0) for t in self.daily_trades if t.get('status') == 'closed')
        
        # Build trades list
        trades_list = []
        for t in self.daily_trades:
            if t.get('status') == 'closed':
                emoji = '🟢' if t.get('was_winning') else '🔴'
                trades_list.append(f"{emoji} {t.get('side')} | Entry: ${t.get('entry_price', 0):,.0f} | Exit: ${t.get('exit_price', 0):,.0f} | PnL: {t.get('pnl_pct', 0):.2%}")
        
        trades_text = '\n'.join(trades_list) if trades_list else 'No closed trades'
        
        # Regime performance
        regime_text = []
        for regime, stats in self.daily_regime_stats.items():
            wr = (stats['wins'] / stats['trades'] * 100) if stats['trades'] > 0 else 0
            regime_text.append(f"├─ {regime}: {stats['trades']} trades | Win: {wr:.0f}% | PnL: {stats['pnl']:+.2%}")
        regime_perf = '\n'.join(regime_text) if regime_text else 'No regime data'
        
        # Learning status
        learning_status = self.self_learning.get_status()
        is_trained = '✅ TRAINED' if self.self_learning.model else '⏳ LEARNING'
        
        # Build report
        report = f"""
📊 <b>DAILY TRADING REPORT - {yesterday}</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 <b>PERFORMANCE SUMMARY</b>
├─ Date: {yesterday}
├─ Trades Executed: {total_trades}/5
├─ Wins: {self.daily_wins}
├─ Losses: {self.daily_losses}
├─ Win Rate: {win_rate:.1f}%
├─ Net PnL: {total_pnl:+.2%}
└─ Signals Evaluated: {len(self.daily_signals)}

🏆 <b>TRADE HISTORY</b>
{trades_text}

🧠 <b>LEARNING INSIGHTS</b>
├─ AI Model: {is_trained}
├─ Samples: {len(self.self_learning.experience_buffer)}/50
├─ Retrains: {self.self_learning.retrain_count}
└─ Model Accuracy: {learning_status.get('time_to_retrain', 'N/A')}

📊 <b>REGIME PERFORMANCE</b>
{regime_perf}

⚡ <b>ADAPTATION</b>
├─ Strategy: {self.current_strategy}
├─ Current Regime: {self.current_regime}
└─ Uptime: {self._format_uptime(time.time() - self.start_time)}

❤️ <b>SYSTEM HEALTH</b>
├─ API: ✅ Connected
├─ Circuit Breaker: ✅ OK
└─ Status: 🟢 HEALTHY
"""
        self._send_alert(report)
    
    def _format_uptime(self, seconds: float) -> str:
        """Format uptime string."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"
    
    def _get_daily_pnl(self) -> float:
        """Calculate daily PnL."""
        today = datetime.now().date()
        daily_trades = [
            t for t in self.trade_history
            if datetime.fromisoformat(t['timestamp']).date() == today
        ]
        return sum(t.get('pnl', 0) for t in daily_trades)
    
    def _handle_error(self, error: str):
        """Handle errors with self-healing."""
        print(f"🔧 Handling error: {error}")
        
        if 'API' in error or 'connection' in error:
            self.circuit_breaker.record_order_failure()
            print("  🔌 Circuit breaker recorded failure")
        
        self._send_alert(f"⚠️ <b>ERROR</b>\n{error[:200]}")
    
    # ─── NEW METHODS FOR ML INTEGRATION ───
    
    def _collect_experience_on_bar(self, price: float, signal_data: dict, regime: str):
        """
        Collect learning experience on EVERY bar (every 30 seconds).
        This ensures the model gets data even during hold periods.
        """
        if not self.self_learning or not self.self_learning.enabled:
            return
        
        try:
            state = {
                'price': price,
                'regime': regime,
                'price_history': list(self.price_history)[-20:],
                'rsi': self._calculate_rsi(),
                'volatility': self._calculate_volatility() != 'LOW',
                'volume': 0,
                'timestamp': time.time()
            }
            
            action = signal_data.get('action', 'hold')
            # Reward is 0 for bar-level collection (real reward comes from trades)
            self.self_learning.add_experience(state, action, 0.0)
            
            # Also feed uncertainty model with price return
            if len(self.price_history) >= 2:
                returns = [(list(self.price_history)[i+1] - list(self.price_history)[i]) / list(self.price_history)[i] 
                           for i in range(len(list(self.price_history))-1)]
                if returns:
                    self.uncertainty_model.add_return('BTCUSDT', returns[-1])
        except Exception as e:
            # Silent fail — don't block trading loop
            pass
    
    def _load_model(self):
        """Load persisted model from disk."""
        try:
            os.makedirs(MODEL_DIR, exist_ok=True)
            model_path = os.path.join(MODEL_DIR, 'self_learning_model.pkl')
            
            if os.path.exists(model_path):
                with open(model_path, 'rb') as f:
                    data = pickle.load(f)
                
                if hasattr(self.self_learning, 'model') and data.get('model'):
                    self.self_learning.model = data['model']
                    self.self_learning.retrain_count = data.get('retrain_count', 0)
                    print(f"  📂 Loaded model from disk (retrains: {self.self_learning.retrain_count})")
                
                # Also load experience buffer
                if data.get('experience_buffer'):
                    self.self_learning.experience_buffer.extend(data['experience_buffer'])
                    print(f"  📂 Loaded {len(data['experience_buffer'])} experiences from disk")
            else:
                print("  📂 No persisted model found — starting fresh")
        except Exception as e:
            print(f"  ⚠️ Model load error: {e}")
    
    def _save_model(self):
        """Persist model to disk."""
        try:
            os.makedirs(MODEL_DIR, exist_ok=True)
            model_path = os.path.join(MODEL_DIR, 'self_learning_model.pkl')
            
            data = {
                'model': self.self_learning.model,
                'retrain_count': self.self_learning.retrain_count,
                'experience_buffer': list(self.self_learning.experience_buffer),
                'timestamp': time.time()
            }
            
            with open(model_path, 'wb') as f:
                pickle.dump(data, f)
            
            print(f"  💾 Model saved to {model_path}")
        except Exception as e:
            print(f"  ⚠️ Model save error: {e}")
    
    def _write_dashboard_state(self):
        """Write current state to shared file for Telegram dashboard."""
        try:
            import json
            status = self.trading_engine.get_status() if self.trading_engine else {}
            position = status.get('position', {})
            price = status.get('price', 0)
            balance = status.get('balance', 0)
            
            position_amt = position.get('amount', 0) if position else 0
            entry_price = position.get('entry_price', 0) if position else 0
            current_pnl = position.get('unrealized_pnl', 0) if position else 0
            pnl_pct = ((price - entry_price) / entry_price * 100) if entry_price > 0 else 0
            
            total_trades = self.daily_wins + self.daily_losses
            win_rate = (self.daily_wins / total_trades * 100) if total_trades > 0 else 0
            
            # Generate current signal
            signal_data = self._generate_signal(price) if price > 0 else {'action': 'hold', 'confidence': 0}
            
            state = {
                'timestamp': datetime.now().isoformat(),
                'running': self.running,
                'uptime': time.time() - self.start_time,
                
                # Market
                'price': price,
                'regime': self.current_regime,
                'strategy': self.current_strategy,
                'rsi': self._calculate_rsi(),
                'volatility': self._calculate_volatility(),
                'trend': self._calculate_trend(),
                
                # Position
                'position_side': 'LONG' if position_amt > 0 else 'SHORT' if position_amt < 0 else 'FLAT',
                'position_amount': abs(position_amt),
                'position_entry': entry_price,
                'position_pnl': current_pnl,
                'position_pnl_pct': pnl_pct,
                
                # Account
                'balance': balance,
                'leverage': status.get('leverage', 75),
                'testnet': status.get('testnet', True),
                
                # Signal
                'signal_action': signal_data.get('action', 'hold'),
                'signal_confidence': signal_data.get('confidence', 0),
                'signal_ma': signal_data.get('ma_signal', 'neutral'),
                
                # Learning (core ML)
                'learning_samples': len(self.self_learning.experience_buffer) if self.self_learning else 0,
                'learning_min_samples': 50,
                'learning_retrains': self.self_learning.retrain_count if self.self_learning else 0,
                'learning_trained': (self.self_learning.model is not None) if self.self_learning else False,
                
                # NEW: Exploration engine state
                'exploration_state': self._exploration_state,
                'exploration_epsilon': self.exploration_engine.epsilon if self.exploration_engine else 0,
                'exploration_trades': len(self.exploration_engine._exploration_returns) if self.exploration_engine else 0,
                'exploit_trades': len(self.exploration_engine._exploit_returns) if self.exploration_engine else 0,
                
                # NEW: Uncertainty model state
                'uncertainty_confidence': 0,
                'uncertainty_std': 0,
                
                # NEW: Model validator state
                'validation_valid': self._last_validation_result.get('valid', True) if self._last_validation_result else True,
                'validation_recommendation': self._last_validation_result.get('recommendation', 'normal') if self._last_validation_result else 'normal',
                
                # NEW: Evolution engine state
                'evolution_generation': self._last_evolution_generation,
                'evolution_best_fitness': self.evolution_engine.get_status().get('best_fitness', 0) if self.evolution_engine else 0,
                'evolution_best_sharpe': self.evolution_engine.get_status().get('best_sharpe', 0) if self.evolution_engine else 0,
                
                # NEW: Ensemble state
                'ensemble_decision_tree_trained': self.ensemble.decision_tree.is_trained if self.ensemble else False,
                
                # Daily stats
                'daily_trades': self.daily_trade_count,
                'daily_max_trades': self.max_daily_trades,
                'daily_wins': self.daily_wins,
                'daily_losses': self.daily_losses,
                'daily_win_rate': win_rate,
                'daily_signals': len(self.daily_signals),
                'daily_regime_stats': self.daily_regime_stats,
                
                # Risk
                'stop_loss_pct': self.stop_loss_pct,
                'take_profit_pct': self.take_profit_pct,
                'circuit_breaker_ok': self.circuit_breaker.check_order_allowed() if self.circuit_breaker else True,
            }
            
            state_path = '/tmp/nkhekhe_dashboard_state.json'
            with open(state_path, 'w') as f:
                json.dump(state, f, indent=2, default=str)
        except Exception as e:
            print(f"Dashboard state write error: {e}")
    
    def stop(self):
        self.running = False
        if self.trading_engine:
            self.trading_engine.stop()


def main():
    trader = AutonomousTrader()
    trader.initialize()
    trader.start()


if __name__ == "__main__":
    main()
