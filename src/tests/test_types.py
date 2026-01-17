"""Tests for core types: Event, Order, Fill."""

import unittest
from datetime import datetime
from src.types import Event, EventType, Order, OrderSide, OrderType, Fill


class TestEvent(unittest.TestCase):
    """Test Event class for bars and ticks."""

    def test_tick_event_creation(self):
        """Test creating a tick event."""
        timestamp = datetime(2024, 1, 1, 12, 0, 0)
        tick = Event(
            timestamp=timestamp,
            symbol="AAPL",
            event_type=EventType.TICK,
            trade_price=150.25,
            volume=100,
        )

        self.assertEqual(tick.symbol, "AAPL")
        self.assertEqual(tick.event_type, EventType.TICK)
        self.assertEqual(tick.trade_price, 150.25)
        self.assertEqual(tick.volume, 100)
        self.assertTrue(tick.is_tick())
        self.assertFalse(tick.is_bar())
        self.assertEqual(tick.close_price, 150.25)

    def test_bar_event_creation(self):
        """Test creating a bar event."""
        timestamp = datetime(2024, 1, 1, 12, 0, 0)
        bar = Event(
            timestamp=timestamp,
            symbol="AAPL",
            event_type=EventType.BAR,
            open=150.0,
            high=150.5,
            low=149.8,
            close=150.25,
            volume=1000,
        )

        self.assertEqual(bar.symbol, "AAPL")
        self.assertEqual(bar.event_type, EventType.BAR)
        self.assertEqual(bar.open, 150.0)
        self.assertEqual(bar.high, 150.5)
        self.assertEqual(bar.low, 149.8)
        self.assertEqual(bar.close, 150.25)
        self.assertTrue(bar.is_bar())
        self.assertFalse(bar.is_tick())
        self.assertEqual(bar.close_price, 150.25)

    def test_bar_event_close_price_fallback(self):
        """Test bar event using trade_price as close fallback."""
        timestamp = datetime(2024, 1, 1, 12, 0, 0)
        bar = Event(
            timestamp=timestamp,
            symbol="AAPL",
            event_type=EventType.BAR,
            trade_price=150.25,
            volume=1000,
        )

        self.assertEqual(bar.close_price, 150.25)


class TestOrder(unittest.TestCase):
    """Test Order class."""

    def test_market_order_creation(self):
        """Test creating a market order."""
        order = Order(
            symbol="AAPL",
            side=OrderSide.BUY,
            quantity=10.0,
            order_type=OrderType.MARKET,
        )

        self.assertEqual(order.symbol, "AAPL")
        self.assertEqual(order.side, OrderSide.BUY)
        self.assertEqual(order.quantity, 10.0)
        self.assertEqual(order.order_type, OrderType.MARKET)
        self.assertIsNone(order.limit_price)
        self.assertIsNone(order.stop_price)

    def test_limit_order_creation(self):
        """Test creating a limit order."""
        order = Order(
            symbol="AAPL",
            side=OrderSide.SELL,
            quantity=5.0,
            order_type=OrderType.LIMIT,
            limit_price=155.0,
        )

        self.assertEqual(order.side, OrderSide.SELL)
        self.assertEqual(order.order_type, OrderType.LIMIT)
        self.assertEqual(order.limit_price, 155.0)


class TestFill(unittest.TestCase):
    """Test Fill class."""

    def test_fill_creation(self):
        """Test creating a fill event."""
        timestamp = datetime(2024, 1, 1, 12, 0, 0)
        fill = Fill(
            order_id="ORD_123",
            timestamp=timestamp,
            symbol="AAPL",
            side=OrderSide.BUY,
            quantity=10.0,
            price=150.25,
            slippage=0.01,
            commission=1.0,
        )

        self.assertEqual(fill.order_id, "ORD_123")
        self.assertEqual(fill.symbol, "AAPL")
        self.assertEqual(fill.side, OrderSide.BUY)
        self.assertEqual(fill.quantity, 10.0)
        self.assertEqual(fill.price, 150.25)
        self.assertEqual(fill.slippage, 0.01)
        self.assertEqual(fill.commission, 1.0)


if __name__ == "__main__":
    unittest.main()
