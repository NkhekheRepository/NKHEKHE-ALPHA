#!/usr/bin/env python3
"""
Live Trading System with Automated Trading + Telegram Alerts
============================================================
"""

import os
import sys
import signal
import time
from pathlib import Path
from loguru import logger
from dotenv import load_dotenv

proj_root = Path(__file__).parent
sys.path.insert(0, str(proj_root))

load_dotenv()

logger.add("logs/live_trading.log", rotation="10 MB", retention="7 days")


def main():
    from paper_trading.layers.layer1_data.binance_live import LiveTradingEngine
    from paper_trading.layers.layer3_signals.signal_aggregator import SignalAggregator
    from paper_trading.telegram_alerts import TelegramAlerts
    
    config = {
        'symbol': 'BTCUSDT',
        'testnet': os.getenv('BINANCE_TESTNET', 'true').lower() == 'true',
        'quantity': 0.0001
    }
    
    engine = LiveTradingEngine(config)
    aggregator = SignalAggregator()
    telegram = TelegramAlerts()
    
    last_signal_time = 0
    signal_interval = 60
    
    def signal_handler(sig, frame):
        logger.info("Shutting down...")
        engine.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("=" * 60)
    logger.info("AUTOMATED LIVE TRADING SYSTEM + TELEGRAM ALERTS")
    logger.info("=" * 60)
    
    status = engine.start()
    
    logger.info(f"Symbol: {status['symbol']}")
    logger.info(f"Balance: ${status['balance']}")
    logger.info(f"Price: ${status['price']}")
    logger.info(f"Testnet: {status['testnet']}")
    logger.info(f"Telegram: {'Enabled' if telegram.enabled else 'Disabled'}")
    logger.info("=" * 60)
    
    if telegram.enabled:
        telegram.send_status_alert(status)
    
    if not status['testnet']:
        logger.warning("*** LIVE TRADING - REAL MONEY ***")
    else:
        logger.info("Running on TESTNET - No real money")
    
    price_history = []
    
    try:
        while True:
            current_time = time.time()
            
            price = engine.client.get_symbol_price('BTCUSDT')
            
            if price > 0:
                price_history.append(price)
                if len(price_history) > 100:
                    price_history.pop(0)
                
                if current_time - last_signal_time >= signal_interval and len(price_history) >= 30:
                    market_data = {'price': price}
                    signal_result = aggregator.generate(market_data, {})
                    
                    action = signal_result.get('action')
                    confidence = signal_result.get('confidence', 0)
                    
                    if action in ['buy', 'sell']:
                        logger.info(f"Signal: {action.upper()} | Price: ${price:.2f} | Confidence: {confidence:.1%}")
                        
                        if telegram.enabled:
                            telegram.send_signal_alert(action, 'BTCUSDT', price, confidence)
                        
                        result = engine.execute_signal(action)
                        
                        if 'orderId' in result:
                            logger.info(f"ORDER EXECUTED: {action.upper()} {config['quantity']} BTC @ ${price:.2f}")
                            
                            if telegram.enabled:
                                telegram.send_trade_alert(action, 'BTCUSDT', config['quantity'], price)
                        elif 'error' not in str(result):
                            logger.info(f"Order placed: {result}")
                    
                    last_signal_time = current_time
            
            status = engine.get_status()
            logger.debug(f"Running: {status['running']}, Price: ${price:.2f}")
            
            time.sleep(10)
            
    except KeyboardInterrupt:
        logger.info("Interrupted...")
        engine.stop()


if __name__ == "__main__":
    main()
