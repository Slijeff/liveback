"""Event bus for decoupled event communication."""

from typing import Callable, List, Dict, Type
from src.types import DomainEvent


class EventBus:
    """Event bus for domain events only (type-based routing).

    This class intentionally only supports `DomainEvent` subclasses. Legacy
    string-based market-data subscribers and the internal queue have been
    removed in favor of explicit domain events (e.g. `PriceUpdateEvent`).
    """

    # Only keep type-based domain event subscribers
    domain_subscribers: Dict[Type, List[Callable[[DomainEvent], None]]] = {}

    def subscribe(
        self, event_type: Type[DomainEvent], callback: Callable[[DomainEvent], None]
    ) -> None:
        """Subscribe to a DomainEvent subclass.

        Args:
            event_type: A subclass of `DomainEvent` to subscribe to.
            callback: Function to call when the event is published.
        """
        if not (isinstance(event_type, type) and issubclass(event_type, DomainEvent)):
            raise TypeError("event_type must be a DomainEvent subclass")
        if event_type not in self.domain_subscribers:
            self.domain_subscribers[event_type] = []
        self.domain_subscribers[event_type].append(callback)

    def publish(self, event: DomainEvent) -> None:
        """Publish a domain event to all subscribers.

        Args:
            event: Instance of a `DomainEvent` subclass.
        """
        if not isinstance(event, DomainEvent):
            raise TypeError("EventBus only accepts DomainEvent instances")
        event_type = type(event)
        for callback in self.domain_subscribers.get(event_type, []):
            callback(event)

    def clear_subscribers(self) -> None:
        self.domain_subscribers = {}
