"""Tests for Portfolio and Position management."""

import unittest
from datetime import datetime
from src.portfolio import Portfolio
from src.types import Fill, OrderSide


class TestPortfolio(unittest.TestCase):
    """Test Portfolio class."""

    def setUp(self):
        """Set up test fixtures."""
        self.portfolio = Portfolio(initial_cash=100000.0)

    def test_initialization(self):
        """Test portfolio initialization."""
        self.assertEqual(self.portfolio.initial_cash, 100000.0)
        self.assertEqual(self.portfolio.cash, 100000.0)
        self.assertEqual(len(self.portfolio.positions), 0)
        self.assertEqual(len(self.portfolio.trades), 0)
        self.assertEqual(len(self.portfolio.equity_curve), 0)

    def test_buy_order_long_position(self):
        """Test applying a buy fill to open a long position."""
        fill = Fill(
            order_id="ORD_1",
            timestamp=datetime.now(),
            symbol="AAPL",
            side=OrderSide.BUY,
            quantity=10.0,
            price=150.0,
            commission=1.0,
        )

        self.portfolio.apply_fill(fill)

        position = self.portfolio.get_position("AAPL")
        self.assertEqual(position.quantity, 10.0)
        # Average price includes commission: (150.0 * 10 + 1.0) / 10 = 150.1
        self.assertAlmostEqual(position.avg_price, 150.1, places=2)
        self.assertEqual(self.portfolio.cash, 100000.0 - (10.0 * 150.0) - 1.0)
        self.assertEqual(len(self.portfolio.trades), 0)

    def test_sell_order_short_position(self):
        """Test applying a sell fill to open a short position."""
        fill = Fill(
            order_id="ORD_1",
            timestamp=datetime.now(),
            symbol="AAPL",
            side=OrderSide.SELL,
            quantity=10.0,
            price=150.0,
            commission=1.0,
        )

        self.portfolio.apply_fill(fill)

        position = self.portfolio.get_position("AAPL")
        self.assertEqual(position.quantity, -10.0)
        self.assertEqual(position.avg_price, 150.0)
        # Selling increases cash (short position)
        self.assertEqual(self.portfolio.cash, 100000.0 + (10.0 * 150.0) - 1.0)

    def test_closing_long_position(self):
        """Test closing a long position with a sell."""
        # First buy to open long
        buy_fill = Fill(
            order_id="ORD_1",
            timestamp=datetime.now(),
            symbol="AAPL",
            side=OrderSide.BUY,
            quantity=10.0,
            price=150.0,
            commission=1.0,
        )
        self.portfolio.apply_fill(buy_fill)

        # Then sell to close
        sell_fill = Fill(
            order_id="ORD_2",
            timestamp=datetime.now(),
            symbol="AAPL",
            side=OrderSide.SELL,
            quantity=10.0,
            price=155.0,
            commission=1.0,
        )
        self.portfolio.apply_fill(sell_fill)

        position = self.portfolio.get_position("AAPL")
        self.assertEqual(position.quantity, 0.0)
        # Check the closed trade has the right PnL
        self.assertEqual(len(self.portfolio.trades), 1)
        self.assertAlmostEqual(self.portfolio.trades[0].pnl, 48.0, places=2)

    def test_closing_short_position(self):
        """Test closing a short position with a buy."""
        # First sell to open short
        sell_fill = Fill(
            order_id="ORD_1",
            timestamp=datetime.now(),
            symbol="AAPL",
            side=OrderSide.SELL,
            quantity=10.0,
            price=150.0,
            commission=1.0,
        )
        self.portfolio.apply_fill(sell_fill)

        # Then buy to close
        buy_fill = Fill(
            order_id="ORD_2",
            timestamp=datetime.now(),
            symbol="AAPL",
            side=OrderSide.BUY,
            quantity=10.0,
            price=145.0,
            commission=1.0,
        )
        self.portfolio.apply_fill(buy_fill)

        position = self.portfolio.get_position("AAPL")
        self.assertEqual(position.quantity, 0.0)
        # Check the closed trade has the right PnL
        self.assertEqual(len(self.portfolio.trades), 1)
        self.assertAlmostEqual(self.portfolio.trades[0].pnl, 49.0, places=2)

    def test_unrealized_pnl(self):
        """Test unrealized PnL calculation."""
        # Open a long position
        fill = Fill(
            order_id="ORD_1",
            timestamp=datetime.now(),
            symbol="AAPL",
            side=OrderSide.BUY,
            quantity=10.0,
            price=150.0,
        )
        self.portfolio.apply_fill(fill)

        # Update unrealized PnL with current price
        current_prices = {"AAPL": 155.0}
        self.portfolio.update_unrealized_pnl(current_prices)

        position = self.portfolio.get_position("AAPL")
        # Unrealized PnL: (155 - 150) * 10 = 50
        self.assertEqual(position.unrealized_pnl, 50.0)

    def test_total_equity(self):
        """Test total equity calculation."""
        # Open a long position
        fill = Fill(
            order_id="ORD_1",
            timestamp=datetime.now(),
            symbol="AAPL",
            side=OrderSide.BUY,
            quantity=10.0,
            price=150.0,
        )
        self.portfolio.apply_fill(fill)

        # Update unrealized PnL
        current_prices = {"AAPL": 155.0}
        self.portfolio.update_unrealized_pnl(current_prices)

        total_equity = self.portfolio.get_total_equity()
        self.assertAlmostEqual(total_equity, 100050.0, places=2)

    def test_record_equity(self):
        """Test recording equity to equity curve."""
        self.portfolio.record_equity(datetime.now())
        self.assertEqual(len(self.portfolio.equity_curve), 1)
        self.assertEqual(self.portfolio.equity_curve[0][1], 100000.0)


if __name__ == "__main__":
    unittest.main()
