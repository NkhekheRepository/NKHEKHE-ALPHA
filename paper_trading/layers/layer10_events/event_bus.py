"""
Layer 10: Event Bus
==================
Event-driven communication layer for decoupled layer-to-layer messaging.
Supports typed events, async handlers, and event replay.
"""

from typing import Dict, Any, Optional, Callable, List
from enum import Enum
from dataclasses import dataclass, field
from collections import defaultdict
from datetime import datetime
import threading
import time
import json
from loguru import logger


class EventType(Enum):
    """Standard event types"""
    TRADE_OPENED = "trade.opened"
    TRADE_CLOSED = "trade.closed"
    TRADE_FAILED = "trade.failed"
    SIGNAL_GENERATED = "signal.generated"
    SIGNAL_REJECTED = "signal.rejected"
    RISK_ALERT = "risk.alert"
    RISK_BREACH = "risk.breach"
    REGIME_CHANGED = "regime.changed"
    PORTFOLIO_UPDATE = "portfolio.update"
    POSITION_UPDATE = "position.update"
    DATA_RECEIVED = "data.received"
    DATA_ERROR = "data.error"
    LAYER_ERROR = "layer.error"
    LAYER_HEALTH = "layer.health"
    CONFIG_CHANGE = "config.change"
    STRATEGY_SWITCH = "strategy.switch"
    EXPLORATION_ACTION = "exploration.action"
    MODEL_UPDATE = "model.update"
    SYSTEM_START = "system.start"
    SYSTEM_STOP = "system.stop"


@dataclass
class Event:
    """Event data structure"""
    event_type: EventType
    source: str
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    event_id: str = ""
    priority: int = 0  # Higher = more important

    def __post_init__(self):
        if not self.event_id:
            self.event_id = f"{self.event_type.value}_{int(self.timestamp * 1000)}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_id': self.event_id,
            'event_type': self.event_type.value,
            'source': self.source,
            'data': self.data,
            'timestamp': self.timestamp,
            'priority': self.priority
        }


class EventBus:
    """
    Central event bus for inter-layer communication.
    Supports subscribe/publish, event replay, and filtering.
    """

    def __init__(self, config: Dict[str, Any] = None):
        config = config or {}
        self.max_history = config.get('max_event_history', 10000)
        self.replay_enabled = config.get('replay_enabled', True)

        self._subscribers: Dict[EventType, List[Callable]] = defaultdict(list)
        self._wildcard_subscribers: List[Callable] = []
        self._filters: Dict[EventType, List[Callable]] = defaultdict(list)

        self._history: List[Event] = []
        self._lock = threading.Lock()

        self._stats = {
            'total_published': 0,
            'total_delivered': 0,
            'errors': 0,
            'by_type': defaultdict(int)
        }

        logger.info("EventBus initialized")

    def subscribe(self, event_type: EventType, handler: Callable[[Event], None],
                  filter_func: Optional[Callable[[Event], bool]] = None):
        """Subscribe a handler to an event type"""
        with self._lock:
            if filter_func:
                self._filters[event_type].append(filter_func)
            self._subscribers[event_type].append(handler)
        logger.debug(f"Subscribed {handler.__name__} to {event_type.value}")

    def subscribe_all(self, handler: Callable[[Event], None]):
        """Subscribe to all events"""
        with self._lock:
            self._wildcard_subscribers.append(handler)
        logger.debug(f"Subscribed {handler.__name__} to all events")

    def unsubscribe(self, event_type: EventType, handler: Callable[[Event], None]):
        """Unsubscribe a handler"""
        with self._lock:
            if handler in self._subscribers[event_type]:
                self._subscribers[event_type].remove(handler)

    def publish(self, event: Event) -> int:
        """Publish an event to all subscribers. Returns number of deliveries."""
        with self._lock:
            self._history.append(event)
            if len(self._history) > self.max_history:
                self._history = self._history[-self.max_history:]

            self._stats['total_published'] += 1
            self._stats['by_type'][event.event_type.value] += 1

        delivered = 0

        try:
            with self._lock:
                handlers = list(self._subscribers.get(event.event_type, []))
                handlers.extend(self._wildcard_subscribers)

            for handler in handlers:
                try:
                    filters = self._filters.get(event.event_type, [])
                    if filters and not all(f(event) for f in filters):
                        continue

                    handler(event)
                    delivered += 1
                except Exception as e:
                    logger.error(f"Error in event handler {handler.__name__}: {e}")
                    self._stats['errors'] += 1

            self._stats['total_delivered'] += delivered

        except Exception as e:
            logger.error(f"Error publishing event {event.event_type.value}: {e}")
            self._stats['errors'] += 1

        return delivered

    def publish_simple(self, event_type: EventType, source: str,
                       data: Dict[str, Any] = None, priority: int = 0) -> int:
        """Convenience method to publish an event"""
        event = Event(
            event_type=event_type,
            source=source,
            data=data or {},
            priority=priority
        )
        return self.publish(event)

    def get_history(self, event_type: Optional[EventType] = None,
                    source: Optional[str] = None,
                    since: Optional[float] = None,
                    limit: int = 100) -> List[Dict[str, Any]]:
        """Get filtered event history"""
        with self._lock:
            events = list(self._history)

        if event_type:
            events = [e for e in events if e.event_type == event_type]
        if source:
            events = [e for e in events if e.source == source]
        if since:
            events = [e for e in events if e.timestamp >= since]

        events = events[-limit:]
        return [e.to_dict() for e in events]

    def get_stats(self) -> Dict[str, Any]:
        """Get event bus statistics"""
        with self._lock:
            return dict(self._stats)

    def clear(self):
        """Clear all subscribers and history"""
        with self._lock:
            self._subscribers.clear()
            self._wildcard_subscribers.clear()
            self._filters.clear()
            self._history.clear()
        logger.info("EventBus cleared")


# Singleton instance
_event_bus_instance: Optional[EventBus] = None


def get_event_bus(config: Dict[str, Any] = None) -> EventBus:
    """Get or create the singleton EventBus instance"""
    global _event_bus_instance
    if _event_bus_instance is None:
        _event_bus_instance = EventBus(config)
    return _event_bus_instance
