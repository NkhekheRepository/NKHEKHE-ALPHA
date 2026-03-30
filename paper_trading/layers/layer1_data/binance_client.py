"""
Layer 1: Data & Connectivity
Binance WebSocket Client for real-time market data.
"""

import asyncio
import json
import threading
from typing import Dict, Any, Optional, List
from collections import deque
from datetime import datetime
from loguru import logger

try:
    import websockets
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False


class BinanceDataClient:
    """Binance WebSocket client for market data."""
    
    def __init__(self, config: Dict[str, Any]):
        self.ws_endpoint = config.get('ws_endpoint', 'wss://stream.binance.com:9443/ws')
        self.rest_endpoint = config.get('rest_endpoint', 'https://api.binance.com/api/v3')
        self.reconnect_interval = config.get('reconnect_interval', 5)
        self.max_reconnect_attempts = config.get('max_reconnect_attempts', 10)
        self.buffer_size = config.get('buffer_size', 100)
        
        self.connected = False
        self.ws = None
        self.ws_thread: Optional[threading.Thread] = None
        
        self.data_buffer: deque = deque(maxlen=self.buffer_size)
        self.latest_data: Dict[str, Any] = {}
        
        self.symbols = ['btcusdt']
        self._lock = threading.Lock()
    
    def connect(self):
        """Connect to Binance WebSocket."""
        if not WEBSOCKETS_AVAILABLE:
            logger.warning("websockets not available, using mock data")
            self.connected = True
            self._start_mock_data()
            return
        
        try:
            self.ws_thread = threading.Thread(target=self._run_ws, daemon=True)
            self.ws_thread.start()
            logger.info("Binance WebSocket connection started")
        except Exception as e:
            logger.error(f"Failed to connect to Binance: {e}")
            self._start_mock_data()
    
    def disconnect(self):
        """Disconnect from Binance WebSocket."""
        self.connected = False
        if self.ws:
            try:
                asyncio.run(self.ws.close())
            except:
                pass
        logger.info("Binance WebSocket disconnected")
    
    def _run_ws(self):
        """Run WebSocket connection in thread."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self._connect_ws())
    
    async def _connect_ws(self):
        """Connect to Binance WebSocket stream."""
        streams = '/'.join([f"{s}@kline_1m" for s in self.symbols])
        url = f"{self.ws_endpoint}/{streams}"
        
        reconnect_count = 0
        while self.connected and reconnect_count < self.max_reconnect_attempts:
            try:
                async with websockets.connect(url) as ws:
                    self.ws = ws
                    self.connected = True
                    reconnect_count = 0
                    
                    async for message in ws:
                        if not self.connected:
                            break
                        self._process_message(message)
                        
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                reconnect_count += 1
                await asyncio.sleep(self.reconnect_interval)
        
        if reconnect_count >= self.max_reconnect_attempts:
            logger.error("Max reconnection attempts reached")
            self._start_mock_data()
    
    def _process_message(self, message: str):
        """Process incoming WebSocket message."""
        try:
            data = json.loads(message)
            
            if 'k' in data:
                kline = data['k']
                bar_data = {
                    'symbol': kline['s'].lower(),
                    'timestamp': kline['t'],
                    'open': float(kline['o']),
                    'high': float(kline['h']),
                    'low': float(kline['l']),
                    'close': float(kline['c']),
                    'volume': float(kline['v']),
                    'closed': kline['x'],
                    'datetime': datetime.fromtimestamp(kline['t'] / 1000)
                }
                
                with self._lock:
                    self.data_buffer.append(bar_data)
                    self.latest_data = bar_data
                    
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    def _start_mock_data(self):
        """Start generating mock data for testing."""
        import random
        
        def mock_loop():
            base_price = 50000
            while self.connected:
                try:
                    price = base_price + random.uniform(-500, 500)
                    bar = {
                        'symbol': 'btcusdt',
                        'timestamp': int(datetime.now().timestamp() * 1000),
                        'open': price - random.uniform(-100, 100),
                        'high': price + random.uniform(0, 200),
                        'low': price - random.uniform(0, 200),
                        'close': price,
                        'volume': random.uniform(10, 100),
                        'closed': True,
                        'datetime': datetime.now()
                    }
                    with self._lock:
                        self.data_buffer.append(bar)
                        self.latest_data = bar
                except Exception as e:
                    logger.error(f"Mock data error: {e}")
                
                import time
                time.sleep(1)
        
        thread = threading.Thread(target=mock_loop, daemon=True)
        thread.start()
    
    def get_latest_data(self) -> Dict[str, Any]:
        """Get the latest market data."""
        with self._lock:
            if not self.latest_data:
                return self._get_default_data()
            return self.latest_data.copy()
    
    def get_buffer(self, n: int = 100) -> List[Dict[str, Any]]:
        """Get recent n bars from buffer."""
        with self._lock:
            return list(self.data_buffer)[-n:]
    
    def _get_default_data(self) -> Dict[str, Any]:
        """Return default data when no connection."""
        return {
            'symbol': 'btcusdt',
            'timestamp': int(datetime.now().timestamp() * 1000),
            'open': 50000,
            'high': 50100,
            'low': 49900,
            'close': 50000,
            'volume': 50,
            'closed': True,
            'datetime': datetime.now()
        }
    
    def is_connected(self) -> bool:
        """Check if connected to data source."""
        return self.connected
