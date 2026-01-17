"""Event bus for decoupled event communication."""

from collections import deque
from typing import Callable, List, Optional, Dict
from src.types import Event


class EventBus:
    """Simple event bus for pub/sub pattern."""

    def __init__(self):
        """Initialize event bus."""
        self.subscribers: Dict[str, List[Callable[[Event], None]]] = {}
        self.event_queue: deque = deque()

    def subscribe(
        self, event_type: Optional[str], callback: Callable[[Event], None]
    ) -> None:
        """Subscribe to events of a specific type.

        Args:
            event_type: Event type to subscribe to (None for all events)
            callback: Function to call when event is published
        """
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)

    def publish(self, event: Event) -> None:
        """Publish an event to all subscribers.

        Args:
            event: Event to publish
        """
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
