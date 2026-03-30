"""
Market Data Module
=================
Real-time market data from Binance WebSocket API.
"""

import os
import asyncio
import json
import time
import threading
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, field
from loguru import logger
import websockets

BINANCE_WS_URL = os.getenv("BINANCE_WS_URL", "wss://stream.binance.com:9443/ws")
PAPER_MODE = os.getenv("PAPER_MODE", "true").lower() == "true"


@dataclass
class TickerData:
    symbol: str
    price: float
    volume: float
    bid_price: float
    ask_price: float
    high_24h: float
    low_24h: float
    change_24h: float
    change_percent_24h: float
    timestamp: float = field(default_factory=time.time)


@dataclass
class KlineData:
    symbol: str
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: float
    trades: int
    interval: str
    timestamp: float = field(default_factory=time.time)


class BinanceMarketData:
    def __init__(self, symbols: List[str] = None, callbacks: Dict[str, Callable] = None):
        self.symbols = symbols or ["btcusdt", "ethusdt", "bnbusdt"]
        self.callbacks = callbacks or {}
        self.ws = None
        self.running = False
        self.reconnect_delay = 5
        self._loop = None
        self._thread = None
        self._ticker_cache: Dict[str, TickerData] = {}
        self._kline_cache: Dict[str, List[KlineData]] = {}
        
        logger.info(f"BinanceMarketData initialized for {self.symbols} (Paper Mode: {PAPER_MODE})")
    
    def start(self):
        if self.running:
            return
        self.running = True
        self._thread = threading.Thread(target=self._run_async, daemon=True)
        self._thread.start()
        logger.info("Market data feed started")
    
    def stop(self):
        self.running = False
        if self._loop:
            self._loop.call_soon_threadsafe(self._loop.stop)
        logger.info("Market data feed stopped")
    
    def _run_async(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._connect_loop())
    
    async def _connect_loop(self):
        while self.running:
            try:
                streams = "/".join([f"{s}@ticker" for s in self.symbols])
                ws_url = f"{BINANCE_WS_URL}/{streams}"
                
                async with websockets.connect(ws_url) as ws:
                    self.ws = ws
                    logger.info(f"Connected to Binance WebSocket")
                    
                    async for message in ws:
                        if not self.running:
                            break
                        await self._handle_message(message)
                        
            except websockets.exceptions.ConnectionClosed:
                logger.warning(f"WebSocket disconnected, reconnecting in {self.reconnect_delay}s...")
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
            
            if self.running:
                await asyncio.sleep(self.reconnect_delay)
    
    async def _handle_message(self, message: str):
        try:
            data = json.loads(message)
            
            if "e" in data and data["e"] == "24hrTicker":
                ticker = self._parse_ticker(data)
                self._ticker_cache[ticker.symbol] = ticker
                
                if "ticker" in self.callbacks:
                    self.callbacks["ticker"](ticker)
                
                symbol_upper = ticker.symbol.upper()
                shared_data = {
                    "price": ticker.price,
                    "volume": ticker.volume,
                    "bid": ticker.bid_price,
                    "ask": ticker.ask_price,
                    "high": ticker.high_24h,
                    "low": ticker.low_24h,
                    "change": ticker.change_24h,
                    "change_percent": ticker.change_percent_24h,
                    "timestamp": ticker.timestamp
                }
                
                if symbol_upper in self.callbacks:
                    self.callbacks[symbol_upper](shared_data)
                    
        except Exception as e:
            logger.error(f"Failed to handle message: {e}")
    
    def _parse_ticker(self, data: Dict) -> TickerData:
        symbol = data["s"].lower()
        return TickerData(
            symbol=symbol,
            price=float(data["c"]),
            volume=float(data["v"]),
            bid_price=float(data["b"]),
            ask_price=float(data["a"]),
            high_24h=float(data["h"]),
            low_24h=float(data["l"]),
            change_24h=float(data["p"]),
            change_percent_24h=float(data["P"])
        )
    
    def get_ticker(self, symbol: str) -> Optional[TickerData]:
        return self._ticker_cache.get(symbol.lower())
    
    def get_price(self, symbol: str) -> Optional[float]:
        ticker = self.get_ticker(symbol)
        return ticker.price if ticker else None
    
    def subscribe_ticker(self, callback: Callable, symbol: str = None):
        if symbol:
            self.callbacks[symbol.upper()] = callback
        else:
            self.callbacks["ticker"] = callback

    def subscribe(self, callback: Callable, symbol: str):
        self.subscribe_ticker(callback, symbol)
    
    def get_all_prices(self) -> Dict[str, float]:
        return {s: t.price for s, t in self._ticker_cache.items() if t}


class MockMarketData:
    def __init__(self, symbols: List[str] = None):
        self.symbols = symbols or ["BTCUSDT", "ETHUSDT"]
        self._running = False
        self._thread = None
        self._callbacks = {}
        
    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._generate_data, daemon=True)
        self._thread.start()
        
    def stop(self):
        self._running = False
        
    def _generate_data(self):
        import numpy as np
        prices = {s: 50000 if "BTC" in s else 3000 for s in self.symbols}
        
        while self._running:
            for symbol in self.symbols:
                change = np.random.randn() * 0.002
                prices[symbol] *= (1 + change)
                
                data = {
                    "symbol": symbol,
                    "price": prices[symbol],
                    "volume": 100 + np.random.rand() * 500,
                    "bid": prices[symbol] * 0.999,
                    "ask": prices[symbol] * 1.001,
                    "timestamp": time.time()
                }
                
                if symbol in self._callbacks:
                    self._callbacks[symbol](data)
                    
            time.sleep(1)
    
    def subscribe(self, callback: Callable, symbol: str):
        self._callbacks[symbol] = callback
    
    def get_price(self, symbol: str) -> Optional[float]:
        return None


def get_market_data(symbols: List[str] = None, callbacks: Dict[str, Callable] = None):
    if PAPER_MODE:
        logger.info("Using MockMarketData for paper trading")
        return MockMarketData(symbols)
    else:
        logger.info("Using BinanceMarketData for live trading")
        return BinanceMarketData(symbols, callbacks)


market_data_instance: Optional[BinanceMarketData] = None


def get_market_data_instance(symbols: List[str] = None) -> BinanceMarketData:
    global market_data_instance
    if market_data_instance is None:
        market_data_instance = get_market_data(symbols)
    return market_data_instance
