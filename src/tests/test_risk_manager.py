"""Tests for RiskManager."""

import unittest
from datetime import datetime
from src.risk_manager import RiskManager
from src.portfolio import Portfolio
from src.types import Order, OrderSide, Fill


class TestRiskManager(unittest.TestCase):
    """Test RiskManager class."""

    def setUp(self):
        """Set up test fixtures."""
        self.portfolio = Portfolio(initial_cash=100000.0)

    def test_initialization(self):
        """Test risk manager initialization."""
        rm = RiskManager()
        self.assertIsNone(rm.max_position_size)
        self.assertIsNone(rm.max_portfolio_exposure)
        self.assertIsNone(rm.max_drawdown)

        rm = RiskManager(
            max_position_size=100.0, max_portfolio_exposure=50000.0, max_drawdown=0.2
        )
        self.assertEqual(rm.max_position_size, 100.0)
        self.assertEqual(rm.max_portfolio_exposure, 50000.0)
        self.assertEqual(rm.max_drawdown, 0.2)

    def test_position_size_limit(self):
        """Test position size limit validation."""
        rm = RiskManager(max_position_size=100.0)

        # Valid order (would result in position of 50)
        order = Order(symbol="AAPL", side=OrderSide.BUY, quantity=50.0)
        self.assertTrue(rm.validate_order(order, self.portfolio))

        # Invalid order (would result in position of 150)
        order = Order(symbol="AAPL", side=OrderSide.BUY, quantity=150.0)
        self.assertFalse(rm.validate_order(order, self.portfolio))

    def test_position_size_limit_with_existing_position(self):
        """Test position size limit with existing position."""
        rm = RiskManager(max_position_size=100.0)

        # Create existing long position of 60
        fill = Fill(
            order_id="ORD_1",
            timestamp=datetime.now(),
            symbol="AAPL",
            side=OrderSide.BUY,
            quantity=60.0,
            price=150.0,
        )
        self.portfolio.apply_fill(fill)

        # Adding 50 more would exceed limit (110 total)
        order = Order(symbol="AAPL", side=OrderSide.BUY, quantity=50.0)
        self.assertFalse(rm.validate_order(order, self.portfolio))

        # Adding 40 more is within limit (100 total)
        order = Order(symbol="AAPL", side=OrderSide.BUY, quantity=40.0)
        self.assertTrue(rm.validate_order(order, self.portfolio))

    def test_portfolio_exposure_limit(self):
        """Test portfolio exposure limit validation."""
        rm = RiskManager(max_portfolio_exposure=50000.0)

        # Simple check - this is approximate
        # In real implementation, would need market prices
        order = Order(
            symbol="AAPL",
            side=OrderSide.BUY,
            quantity=100.0,
            limit_price=100.0,  # 10000 exposure
        )
        self.assertTrue(rm.validate_order(order, self.portfolio))

    def test_drawdown_limit(self):
        """Test drawdown limit validation."""
        rm = RiskManager(max_drawdown=0.2)  # 20% max drawdown

        # Set peak equity at 100000
        rm.update_peak_equity(100000.0)

        # Current equity at 85000 (15% drawdown) - should pass
        rm.peak_equity = 100000.0
        self.portfolio.cash = 85000.0
        order = Order(symbol="AAPL", side=OrderSide.BUY, quantity=10.0)
        self.assertTrue(rm.validate_order(order, self.portfolio))

        # Current equity at 75000 (25% drawdown) - should fail
        self.portfolio.cash = 75000.0
        self.assertFalse(rm.validate_order(order, self.portfolio))

    def test_no_limits_allows_all_orders(self):
        """Test that risk manager with no limits allows all orders."""
        rm = RiskManager()  # No limits

        order = Order(symbol="AAPL", side=OrderSide.BUY, quantity=1000.0)
        self.assertTrue(rm.validate_order(order, self.portfolio))

    def test_update_peak_equity(self):
        """Test peak equity tracking."""
        rm = RiskManager()

        rm.update_peak_equity(100000.0)
        self.assertEqual(rm.peak_equity, 100000.0)

        # Higher equity updates peak
        rm.update_peak_equity(110000.0)
        self.assertEqual(rm.peak_equity, 110000.0)

        # Lower equity doesn't update peak
        rm.update_peak_equity(90000.0)
        self.assertEqual(rm.peak_equity, 110000.0)


if __name__ == "__main__":
    unittest.main()
