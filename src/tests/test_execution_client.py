"""Tests for ExecutionClient and BrokerSim."""

import unittest
from src.execution.execution_client import BrokerSim
from src.types import Order, OrderSide, OrderType


class TestBrokerSim(unittest.TestCase):
    """Test BrokerSim class."""

    def setUp(self):
        """Set up test fixtures."""
        self.broker = BrokerSim()

    def test_initialization(self):
        """Test broker simulator initialization."""
        self.assertEqual(self.broker._order_id_counter, 0)
        self.assertIsNone(self.broker.slippage_model)

    def test_send_order_without_slippage(self):
        """Test sending an order without slippage model."""
        order = Order(
            symbol="AAPL",
            side=OrderSide.BUY,
            quantity=10.0,
            order_type=OrderType.MARKET,
        )

        fill = self.broker.send_order(order)

        self.assertIsNotNone(fill)
        self.assertEqual(fill.symbol, "AAPL")
        self.assertEqual(fill.side, OrderSide.BUY)
        self.assertEqual(fill.quantity, 10.0)
        self.assertEqual(fill.slippage, 0.0)
        self.assertEqual(fill.order_id, "SIM_1")

        # Counter should increment
        fill2 = self.broker.send_order(order)
        self.assertEqual(fill2.order_id, "SIM_2")

    def test_send_order_with_slippage_model(self):
        """Test sending an order with slippage model."""

        def slippage_model(order: Order) -> float:
            return 0.5  # Fixed slippage of 0.5

        broker = BrokerSim(slippage_model=slippage_model)

        order = Order(symbol="AAPL", side=OrderSide.BUY, quantity=10.0)

        fill = broker.send_order(order)

        self.assertEqual(fill.slippage, 0.5)
        # Price should include slippage (100.0 base + 0.5 slippage)
        self.assertEqual(fill.price, 100.5)

    def test_send_sell_order(self):
        """Test sending a sell order."""
        order = Order(symbol="AAPL", side=OrderSide.SELL, quantity=5.0)

        fill = self.broker.send_order(order)

        self.assertEqual(fill.side, OrderSide.SELL)
        self.assertEqual(fill.quantity, 5.0)

    def test_cancel_order(self):
        """Test canceling an order (stub for now)."""
        # Currently a no-op, but should not raise
        self.broker.cancel_order("ORD_123")


if __name__ == "__main__":
    unittest.main()
