#!/usr/bin/env python3
"""
Autonomous Trading Bot - Enhanced Version
=========================================
Self-learning, self-healing, adaptive trading with 75x leverage.
Integrates: HMM, Self-Learning, Adaptive Strategy, Ensemble, Risk Engine
"""

import sys
import os
import time
import signal
import threading
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

from paper_trading.layers.layer2_risk.risk_engine import RiskEngine
from paper_trading.layers.layer2_risk.circuit_breaker import TradingCircuitBreaker
from paper_trading.layers.layer6_orchestration.health_monitor import HealthMonitor


class AutonomousTrader:
    def __init__(self):
        self.running = False
        self.trading_engine = None
        
        self.price_history = deque(maxlen=200)
        self.trade_history = []
        
        self.check_interval = 30
        self.last_trade_time = 0
        
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
        
        self.current_regime = 'sideways'
        self.current_strategy = 'RlEnhancedCtaStrategy'
        
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
        print("🤖 Initializing Enhanced Autonomous Trader...")
        
        self.trading_engine = TradingBotIntegration()
        self.trading_engine.initialize({'symbol': 'BTCUSDT', 'leverage': 75})
        
        print("  📊 Initializing HMM Regime Detector...")
        self.hmm = HMMRegimeDetector({'n_states': 4, 'lookback_bars': 100})
        
        print("  🧠 Initializing Self-Learning Engine...")
        self.self_learning = SelfLearningEngine({
            'enabled': True,
            'retrain_interval': 1800,
            'min_samples': 50
        })
        
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
        
        print("  🎯 Initializing Signal Aggregator...")
        self.signal_aggregator = SignalAggregator()
        
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
        
        print("  🎭 Initializing Intelligence Ensemble...")
        self.ensemble = IntelligenceEnsemble({
            'hmm': {'enabled': True},
            'decision_tree': {'enabled': True},
            'self_learning': {'enabled': True},
            'adaptive': {'enabled': True}
        })
        
        print("✅ Enhanced Autonomous Trader initialized")
        return True
    
    def start(self):
        self.running = True
        self.trading_engine.start()
        
        print("🚀 Autonomous trading started with full intelligence")
        self._send_alert("🟢 Autonomous Trading Bot Started\n75x Leverage | BTCUSDT")
        
        while self.running:
            try:
                self.trading_loop()
                time.sleep(self.check_interval)
            except Exception as e:
                print(f"❌ Trading loop error: {e}")
                self._handle_error(str(e))
                time.sleep(10)
    
    def trading_loop(self):
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
            self.current_regime = regime
            self.current_strategy = self.adaptive.select_strategy(regime, {})
        
        if position_amt != 0:
            pnl_pct = (price - entry_price) / entry_price if entry_price > 0 else 0
            print(f"[{timestamp}] ${price:,.2f} | PnL: {pnl_pct:.2%} | Regime: {regime} | Strategy: {self.current_strategy}")
            
            self._manage_position(position, price, balance)
        else:
            signal_data = self._generate_signal(price)
            action = signal_data.get('action', 'hold')
            confidence = signal_data.get('confidence', 0)
            
            print(f"[{timestamp}] ${price:,.2f} | Signal: {action} ({confidence:.0%}) | Regime: {regime}")
            
            if self._should_trade(action, confidence, balance):
                self._open_position(action, balance)
    
    def _detect_regime(self, price: float) -> str:
        """Detect market regime using HMM."""
        if len(self.price_history) >= 20:
            self.hmm.update(price)
            return self.hmm.get_current_regime()
        return 'sideways'
    
    def _generate_signal(self, price: float) -> dict:
        """Generate trading signal from multiple sources."""
        signal = {'action': 'hold', 'confidence': 0}
        
        try:
            market_data = {'close': price, 'price_history': list(self.price_history)}
            
            agg_result = self.signal_aggregator.generate(market_data, {})
            if agg_result.get('action'):
                signal['action'] = agg_result['action'].lower()
                signal['confidence'] = 0.6
            
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
    
    def _should_trade(self, action: str, confidence: float, balance: float) -> bool:
        """Check if we should take a trade."""
        if not self.circuit_breaker.check_order_allowed():
            print("  ⏸️ Circuit breaker OPEN - no trades")
            return False
        
        if not self.risk_engine.check_risk({
            'balance': balance,
            'position_value': 0,
            'daily_pnl': self._get_daily_pnl()
        }):
            print("  🛡️ Risk check failed")
            return False
        
        if confidence < 0.6:
            print(f"  ⏳ Confidence too low: {confidence:.0%}")
            return False
        
        time_since_last = time.time() - self.last_trade_time
        if time_since_last < 60:
            print(f"  ⏳ Too soon since last trade: {time_since_last:.0f}s")
            return False
        
        return action in ['buy', 'sell']
    
    def _open_position(self, action: str, balance: float):
        """Open a new position."""
        position_value = balance * 0.05
        price = self.trading_engine.get_price()
        quantity = position_value / price
        
        if action == 'buy':
            result = self.trading_engine.long(quantity)
            side = 'LONG'
        else:
            result = self.trading_engine.short(quantity)
            side = 'SHORT'
        
        if result.get('success') or result.get('orderId'):
            print(f"  ✅ Opened {side}: {quantity} BTC @ ${price:,.2f}")
            self.last_trade_time = time.time()
            
            self._send_alert(f"📈 <b>{side} OPENED</b>\nQty: {quantity} BTC\nPrice: ${price:,.2f}\nRegime: {self.current_regime}")
            
            self.self_learning.add_experience(
                {'price': price, 'regime': self.current_regime},
                action,
                0
            )
    
    def _manage_position(self, position: dict, current_price: float, balance: float):
        """Manage existing position."""
        entry_price = position.get('entry_price', 0)
        amount = position.get('amount', 0)
        
        if entry_price == 0 or amount == 0:
            return
        
        pnl_pct = (current_price - entry_price) / entry_price
        
        if pnl_pct <= -self.stop_loss_pct:
            print(f"  🛑 Stop loss triggered: {pnl_pct:.2%}")
            self.trading_engine.close()
            self._record_trade(pnl_pct, False)
            self._send_alert(f"🛑 <b>STOP LOSS</b>\nPnL: {pnl_pct:.2%}")
            return
        
        if pnl_pct >= self.take_profit_pct:
            print(f"  💰 Take profit triggered: {pnl_pct:.2%}")
            self.trading_engine.close()
            self._record_trade(pnl_pct, True)
            self._send_alert(f"💰 <b>TAKE PROFIT</b>\nPnL: {pnl_pct:.2%}")
            return
        
        if abs(pnl_pct) > 0.015:
            liq_warning = f"⚠️ WARNING: {pnl_pct:.2%} from entry!"
            print(f"  {liq_warning}")
            self._send_alert(liq_warning)
    
    def _record_trade(self, pnl_pct: float, was_winning: bool):
        """Record trade for learning."""
        self.adaptive.record_trade(
            self.current_regime,
            self.current_strategy,
            pnl_pct,
            was_winning
        )
        
        self.self_learning.add_experience(
            {'regime': self.current_regime, 'strategy': self.current_strategy},
            'hold' if was_winning else 'sell',
            pnl_pct
        )
        
        if self.self_learning.should_retrain():
            print("  🔄 Retraining model...")
            self.self_learning.retrain()
    
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
        
        self._send_alert(f"⚠️ <b>ERROR</b>\n{error[:100]}")
    
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
