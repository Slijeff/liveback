"""Event bus for decoupled event communication."""

from collections import deque
from typing import Callable, List, Optional, Dict, Type, Union
from src.types import Event, DomainEvent


class EventBus:
    """Simple event bus for pub/sub pattern."""

    def __init__(self):
        """Initialize event bus."""
        # Market data events (string-keyed for backward compatibility)
        self.subscribers: Dict[str, List[Callable[[Event], None]]] = {}
        # Domain events (type-keyed)
        self.domain_subscribers: Dict[Type, List[Callable[[DomainEvent], None]]] = {}
        self.event_queue: deque = deque()

    def subscribe(
        self, event_type: Union[Optional[str], Type], callback: Callable
    ) -> None:
        """Subscribe to events of a specific type.

        Args:
            event_type: Event type to subscribe to. Can be:
                - None for all market data events (legacy)
                - string for specific market event type (legacy)
                - DomainEvent subclass for domain events (new)
            callback: Function to call when event is published
        """
        # Handle domain events (type-based)
        if isinstance(event_type, type) and issubclass(event_type, DomainEvent):
            if event_type not in self.domain_subscribers:
                self.domain_subscribers[event_type] = []
            self.domain_subscribers[event_type].append(callback)
        # Handle market data events (string-based, legacy)
        else:
            if event_type not in self.subscribers:
                self.subscribers[event_type] = []
            self.subscribers[event_type].append(callback)

    def publish(self, event: Union[Event, DomainEvent]) -> None:
        """Publish an event to all subscribers.

        Args:
            event: Event to publish (market data or domain event)
        """
        if isinstance(event, DomainEvent):
            # Domain event: use type-based routing
            event_type = type(event)
            if event_type in self.domain_subscribers:
                for callback in self.domain_subscribers[event_type]:
                    callback(event)
        else:
            # Market data event: use legacy string-based routing
            # Add to queue
            self.event_queue.append(event)

            # Notify subscribers (could filter by event type in future)
            for subscribers in self.subscribers.values():
                for callback in subscribers:
                    callback(event)

    def get_next_event(self, timeout: Optional[float] = None) -> Optional[Event]:
        """Get next event from queue (for live mode).

        Args:
            timeout: Optional timeout in seconds

        Returns:
            Next event or None if queue is empty
        """
        if self.event_queue:
            return self.event_queue.popleft()
        return None

    def has_events(self) -> bool:
        """Check if there are pending events.

        Returns:
            True if there are events in the queue
        """
        return len(self.event_queue) > 0
