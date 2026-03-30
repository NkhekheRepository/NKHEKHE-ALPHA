#!/usr/bin/env python3
"""
Live Trading System Launcher
============================
Starts the autonomous live trading system with real Binance API.
"""

import os
import sys
import signal
from pathlib import Path
from loguru import logger

proj_root = Path(__file__).parent
sys.path.insert(0, str(proj_root))

from dotenv import load_dotenv
load_dotenv()

logger.add("logs/live_trading.log", rotation="10 MB", retention="7 days")


def main():
    from paper_trading.layers.layer1_data.binance_live import LiveTradingEngine
    
    config = {
        'symbol': 'BTCUSDT',
        'testnet': os.getenv('BINANCE_TESTNET', 'true').lower() == 'true',
        'quantity': 0.001
    }
    
    engine = LiveTradingEngine(config)
    
    def signal_handler(sig, frame):
        logger.info("Shutting down...")
        engine.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("=" * 50)
    logger.info("Live Trading System Starting...")
    logger.info("=" * 50)
    
    status = engine.start()
    
    logger.info(f"Symbol: {status['symbol']}")
    logger.info(f"Balance: ${status['balance']}")
    logger.info(f"Price: ${status['price']}")
    logger.info(f"Testnet: {status['testnet']}")
    logger.info("=" * 50)
    
    if not status['testnet']:
        logger.warning("*** LIVE TRADING - REAL MONEY ***")
    else:
        logger.info("Running on TESTNET - No real money")
    
    try:
        import time
        while True:
            time.sleep(10)
            
            status = engine.get_status()
            logger.debug(f"Running: {status['running']}, Price: ${status['price']}")
            
    except KeyboardInterrupt:
        logger.info("Interrupted...")
        engine.stop()


if __name__ == "__main__":
    main()
