"""Tests for EventBus."""

import unittest
from datetime import datetime
from src.event_bus import EventBus
from src.types import Event, EventType


class TestEventBus(unittest.TestCase):
    """Test EventBus class."""

    def setUp(self):
        """Set up test fixtures."""
        self.event_bus = EventBus()
        self.received_events = []

    def callback(self, event: Event):
        """Test callback to capture events."""
        self.received_events.append(event)

    def test_initialization(self):
        """Test event bus initialization."""
        self.assertEqual(len(self.event_bus.subscribers), 0)
        self.assertEqual(len(self.event_bus.event_queue), 0)
        self.assertFalse(self.event_bus.has_events())

    def test_subscribe_and_publish(self):
        """Test subscribing and publishing events."""
        self.event_bus.subscribe(None, self.callback)

        event = Event(
            timestamp=datetime.now(),
            symbol="AAPL",
            event_type=EventType.TICK,
            trade_price=150.0,
        )

        self.event_bus.publish(event)

        self.assertEqual(len(self.received_events), 1)
        self.assertEqual(self.received_events[0].symbol, "AAPL")
        self.assertTrue(self.event_bus.has_events())

    def test_multiple_subscribers(self):
        """Test multiple subscribers receiving the same event."""
        received_events_2 = []

        def callback2(event: Event):
            received_events_2.append(event)

        self.event_bus.subscribe(None, self.callback)
        self.event_bus.subscribe(None, callback2)

        event = Event(
            timestamp=datetime.now(),
            symbol="AAPL",
            event_type=EventType.TICK,
            trade_price=150.0,
        )

        self.event_bus.publish(event)

        self.assertEqual(len(self.received_events), 1)
        self.assertEqual(len(received_events_2), 1)

    def test_get_next_event(self):
        """Test getting events from queue."""
        event1 = Event(
            timestamp=datetime.now(),
            symbol="AAPL",
            event_type=EventType.TICK,
            trade_price=150.0,
        )
        event2 = Event(
            timestamp=datetime.now(),
            symbol="MSFT",
            event_type=EventType.TICK,
            trade_price=200.0,
        )

        self.event_bus.publish(event1)
        self.event_bus.publish(event2)

        retrieved = self.event_bus.get_next_event()
        self.assertEqual(retrieved.symbol, "AAPL")

        retrieved = self.event_bus.get_next_event()
        self.assertEqual(retrieved.symbol, "MSFT")

        # Queue should be empty now
        self.assertFalse(self.event_bus.has_events())
        self.assertIsNone(self.event_bus.get_next_event())

    def test_has_events(self):
        """Test has_events method."""
        self.assertFalse(self.event_bus.has_events())

        event = Event(
            timestamp=datetime.now(),
            symbol="AAPL",
            event_type=EventType.TICK,
            trade_price=150.0,
        )
        self.event_bus.publish(event)

        self.assertTrue(self.event_bus.has_events())

        self.event_bus.get_next_event()
        self.assertFalse(self.event_bus.has_events())


if __name__ == "__main__":
    unittest.main()
