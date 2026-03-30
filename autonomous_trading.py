#!/usr/bin/env python3
"""
Autonomous Trading Bot
======================
Self-learning, self-healing trading with 75x leverage.
"""

import sys
import os
import time
import signal
import threading
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from telegram_watchtower.trading_integration import TradingBotIntegration
from paper_trading.layers.layer3_signals.signal_aggregator import SignalAggregator

class AutonomousTrader:
    def __init__(self):
        self.running = False
        self.trading_engine = None
        self.signal_aggregator = None
        self.check_interval = 60  # seconds
        self.position_check_interval = 30
        
        self.max_position_pct = 0.1  # 10% of balance
        self.stop_loss_pct = 0.02  # 2%
        self.take_profit_pct = 0.05  # 5%
        
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        print("\n🛑 Autonomous trading stopped")
        self.running = False
        sys.exit(0)
    
    def initialize(self):
        print("🤖 Initializing Autonomous Trader...")
        
        self.trading_engine = TradingBotIntegration()
        self.trading_engine.initialize({'symbol': 'BTCUSDT', 'leverage': 75})
        
        self.signal_aggregator = SignalAggregator()
        
        print("✅ Autonomous Trader initialized")
        return True
    
    def start(self):
        self.running = True
        self.trading_engine.start()
        
        print("🚀 Autonomous trading started")
        
        # Main trading loop
        while self.running:
            try:
                self.trading_loop()
                time.sleep(self.check_interval)
            except Exception as e:
                print(f"❌ Trading loop error: {e}")
                time.sleep(10)
    
    def trading_loop(self):
        status = self.trading_engine.get_status()
        position = status.get('position', {})
        price = status.get('price', 0)
        balance = status.get('balance', 0)
        
        position_amt = position.get('amount', 0) if position else 0
        
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Price: ${price:,.2f} | Position: {position_amt} BTC")
        
        if position_amt == 0:
            # No position - check for entry signal
            signal = self._get_signal()
            if signal in ['BUY', 'STRONG_BUY']:
                self._open_position('long', balance)
        else:
            # Have position - check for exit/tp/sl
            self._manage_position(position, price)
    
    def _get_signal(self):
        """Get trading signal from aggregator."""
        try:
            if self.signal_aggregator:
                price = self.trading_engine.get_price()
                market_data = {'close': price}
                result = self.signal_aggregator.generate(market_data, {})
                return result.get('action', 'HOLD')
        except Exception as e:
            print(f"Signal error: {e}")
        return 'HOLD'
    
    def _open_position(self, side: str, balance: float):
        """Open a new position."""
        # Calculate position size (5% of balance)
        position_value = balance * 0.05
        price = self.trading_engine.get_price()
        quantity = position_value / price
        
        if side == 'long':
            result = self.trading_engine.long(quantity)
            print(f"📈 Opened LONG: {quantity} BTC @ ${price:,.2f}")
        else:
            result = self.trading_engine.short(quantity)
            print(f"📉 Opened SHORT: {quantity} BTC @ ${price:,.2f}")
    
    def _manage_position(self, position: dict, current_price: float):
        """Manage existing position."""
        entry_price = position.get('entry_price', 0)
        amount = position.get('amount', 0)
        
        if entry_price == 0 or amount == 0:
            return
        
        pnl_pct = (current_price - entry_price) / entry_price
        
        # Check stop loss (2%)
        if pnl_pct <= -self.stop_loss_pct:
            print(f"🛑 Stop loss triggered: {pnl_pct:.2%}")
            self.trading_engine.close()
            return
        
        # Check take profit (5%)
        if pnl_pct >= self.take_profit_pct:
            print(f"💰 Take profit triggered: {pnl_pct:.2%}")
            self.trading_engine.close()
            return
        
        # Check liquidation warning
        if abs(pnl_pct) > 0.015:
            print(f"⚠️ WARNING: {pnl_pct:.2%} from entry - close to liquidation!")
    
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
