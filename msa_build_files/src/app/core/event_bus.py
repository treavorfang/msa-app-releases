# src/app/core/event_bus.py
from typing import Type, Callable, Dict, List, Any
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class Event:
    """Base class for all domain events"""
    pass

class EventBus:
    """
    A simple Publish/Subscribe event bus to decouple components.
    Follows Google's 'Excellence' principle by reducing direct coupling.
    """
    _subscribers: Dict[Type[Event], List[Callable[[Event], None]]] = defaultdict(list)

    @classmethod
    def subscribe(cls, event_type: Type[Event], handler: Callable[[Event], None]):
        """Subscribe a handler to a specific event type."""
        cls._subscribers[event_type].append(handler)

    @classmethod
    def unsubscribe(cls, event_type: Type[Event], handler: Callable[[Event], None]):
        """Unsubscribe a handler from a specific event type."""
        if event_type in cls._subscribers:
            if handler in cls._subscribers[event_type]:
                cls._subscribers[event_type].remove(handler)

    @classmethod
    def publish(cls, event: Event):
        """Publish an event to all subscribers."""
        # In a production Google app, this might be async or queued.
        # For this PySide6 app, we keep it synchronous to ensure UI updates happen immediately
        # on the main thread, or we could use QThread if needed.
        for handler in cls._subscribers[type(event)]:
            try:
                handler(event)
            except Exception as e:
                print(f"Error handling event {event}: {e}")

    @classmethod
    def clear(cls):
        """Clear all subscribers (useful for testing)."""
        cls._subscribers.clear()
