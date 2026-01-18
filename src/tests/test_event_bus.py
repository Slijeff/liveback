"""Tests for EventBus."""

import unittest
from datetime import datetime
from src.event_bus import EventBus
from src.types import DomainEvent


class TestEventBus(unittest.TestCase):
    """Test EventBus class (DomainEvent-only API)."""

    def setUp(self):
        """Set up test fixtures."""
        self.event_bus = EventBus()
        self.received_events = []
        self.event_bus.clear_subscribers()

    def callback(self, event: DomainEvent):
        """Test callback to capture events."""
        self.received_events.append(event)

    def test_initialization(self):
        """Test event bus initialization."""
        self.assertEqual(len(self.event_bus.domain_subscribers), 0)

    def test_subscribe_and_publish(self):
        """Test subscribing and publishing DomainEvents."""
        from src.types import PriceUpdateEvent

        self.event_bus.subscribe(PriceUpdateEvent, self.callback)

        event = PriceUpdateEvent(symbol="AAPL", price=150.0, timestamp=datetime.now())

        self.event_bus.publish(event)

        self.assertEqual(len(self.received_events), 1)
        self.assertEqual(self.received_events[0].symbol, "AAPL")

    def test_multiple_subscribers(self):
        """Test multiple subscribers receiving the same DomainEvent."""
        from src.types import PriceUpdateEvent

        received_events_2 = []

        def callback2(event: DomainEvent):
            received_events_2.append(event)

        self.event_bus.subscribe(PriceUpdateEvent, self.callback)
        self.event_bus.subscribe(PriceUpdateEvent, callback2)

        event = PriceUpdateEvent(symbol="AAPL", price=150.0, timestamp=datetime.now())

        self.event_bus.publish(event)

        self.assertEqual(len(self.received_events), 1)
        self.assertEqual(len(received_events_2), 1)


if __name__ == "__main__":
    unittest.main()
