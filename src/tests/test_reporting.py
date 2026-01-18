"""Tests for the reporting module metrics."""

import unittest
from datetime import datetime
from src.reporting import (
    AnnualizedSharpeRatioMetric,
    MaxDrawdownMetric,
    WinRateMetric,
    TotalReturnMetric,
    AveragePnLPerTradeMetric,
    NumTradesMetric,
    ProfitFactorMetric,
    ReportGenerator,
)
from src.portfolio import Portfolio
from src.types import Fill, OrderSide, Trade


class TestMetrics(unittest.TestCase):
    """Test individual metric calculations."""

    def test_total_return_metric(self):
        """Test total return calculation."""
        metric = TotalReturnMetric()
        equity_curve = [100000.0, 105000.0, 103000.0, 110000.0]

        result = metric.calculate([], equity_curve, 100000.0)
        self.assertEqual(result, 10.0)  # 10% return

    def test_total_return_metric_loss(self):
        """Test total return with loss."""
        metric = TotalReturnMetric()
        equity_curve = [100000.0, 95000.0, 90000.0]

        result = metric.calculate([], equity_curve, 100000.0)
        self.assertEqual(result, -10.0)  # -10% return

    def test_total_return_empty_equity_curve(self):
        """Test total return with empty equity curve."""
        metric = TotalReturnMetric()
        result = metric.calculate([], [], 100000.0)
        self.assertEqual(result, 0.0)

    def test_sharpe_ratio_metric(self):
        """Test Sharpe ratio calculation."""
        metric = AnnualizedSharpeRatioMetric(risk_free_rate=0.0)
        # Create equity curve with consistent growth (low volatility)
        equity_curve = [100000.0 + i * 100 for i in range(252)]

        result = metric.calculate([], equity_curve, 100000.0)
        # Should be positive with consistent growth
        self.assertIsInstance(result, float)
        self.assertGreater(result, 0)

    def test_max_drawdown_metric(self):
        """Test maximum drawdown calculation."""
        metric = MaxDrawdownMetric()
        equity_curve = [100000.0, 110000.0, 95000.0, 105000.0]

        result = metric.calculate([], equity_curve, 100000.0)
        # Max drawdown from 110k to 95k = -13.636%
        self.assertTrue(-15 < result < -13)

    def test_max_drawdown_no_drawdown(self):
        """Test max drawdown with only gains."""
        metric = MaxDrawdownMetric()
        equity_curve = [100000.0, 105000.0, 110000.0, 115000.0]

        result = metric.calculate([], equity_curve, 100000.0)
        # No drawdown
        self.assertEqual(result, 0.0)

    def test_win_rate_metric(self):
        """Test win rate calculation."""
        metric = WinRateMetric()
        trades = [
            Trade(
                timestamp=datetime.now(),
                symbol="AAPL",
                side="BUY",
                quantity=10.0,
                price=150.0,
                slippage=0.0,
                commission=1.0,
                pnl=100.0,
            ),
            Trade(
                timestamp=datetime.now(),
                symbol="AAPL",
                side="SELL",
                quantity=10.0,
                price=155.0,
                slippage=0.0,
                commission=1.0,
                pnl=-50.0,
            ),
            Trade(
                timestamp=datetime.now(),
                symbol="AAPL",
                side="BUY",
                quantity=10.0,
                price=155.0,
                slippage=0.0,
                commission=1.0,
                pnl=200.0,
            ),
            Trade(
                timestamp=datetime.now(),
                symbol="AAPL",
                side="SELL",
                quantity=10.0,
                price=160.0,
                slippage=0.0,
                commission=1.0,
                pnl=-30.0,
            ),
        ]

        result = metric.calculate(trades, [], 100000.0, [])
        self.assertEqual(result, 50.0)  # 2 winning / 4 total

    def test_win_rate_all_winners(self):
        """Test win rate with all winning trades."""
        metric = WinRateMetric()
        trades = [
            Trade(
                timestamp=datetime.now(),
                symbol="AAPL",
                side="BUY",
                quantity=10.0,
                price=150.0,
                slippage=0.0,
                commission=1.0,
                pnl=100.0,
            ),
            Trade(
                timestamp=datetime.now(),
                symbol="AAPL",
                side="SELL",
                quantity=10.0,
                price=155.0,
                slippage=0.0,
                commission=1.0,
                pnl=200.0,
            ),
        ]

        result = metric.calculate(trades, [], 100000.0, [])
        self.assertEqual(result, 100.0)

    def test_win_rate_no_trades(self):
        """Test win rate with no trades."""
        metric = WinRateMetric()
        result = metric.calculate([], [], 100000.0)
        self.assertEqual(result, 0.0)

    def test_average_pnl_per_trade(self):
        """Test average PnL calculation."""
        metric = AveragePnLPerTradeMetric()
        trades = [
            {"pnl": 100.0},
            {"pnl": 200.0},
            {"pnl": -50.0},
        ]

        result = metric.calculate(trades, [], 100000.0, [])
        self.assertAlmostEqual(result, 83.333333, places=5)

    def test_num_trades_metric(self):
        """Test number of trades metric."""
        metric = NumTradesMetric()
        trades = [
            Trade(
                timestamp=datetime.now(),
                symbol="AAPL",
                side="BUY",
                quantity=10.0,
                price=150.0,
                slippage=0.0,
                commission=1.0,
                pnl=100.0,
            ),
            Trade(
                timestamp=datetime.now(),
                symbol="AAPL",
                side="SELL",
                quantity=10.0,
                price=155.0,
                slippage=0.0,
                commission=1.0,
                pnl=-50.0,
            ),
            Trade(
                timestamp=datetime.now(),
                symbol="AAPL",
                side="BUY",
                quantity=10.0,
                price=155.0,
                slippage=0.0,
                commission=1.0,
                pnl=75.0,
            ),
        ]

        result = metric.calculate(trades, [], 100000.0, [])
        self.assertEqual(result, 3.0)

    def test_profit_factor_metric(self):
        """Test profit factor calculation."""
        metric = ProfitFactorMetric()
        trades = [
            Trade(
                timestamp=datetime.now(),
                symbol="AAPL",
                side="BUY",
                quantity=10.0,
                price=150.0,
                slippage=0.0,
                commission=1.0,
                pnl=100.0,
            ),
            Trade(
                timestamp=datetime.now(),
                symbol="AAPL",
                side="SELL",
                quantity=10.0,
                price=155.0,
                slippage=0.0,
                commission=1.0,
                pnl=200.0,
            ),
            Trade(
                timestamp=datetime.now(),
                symbol="AAPL",
                side="BUY",
                quantity=10.0,
                price=155.0,
                slippage=0.0,
                commission=1.0,
                pnl=-50.0,
            ),
        ]

        result = metric.calculate(trades, [], 100000.0, [])
        # (100 + 200) / 50 = 6.0
        self.assertEqual(result, 6.0)

    def test_profit_factor_no_losses(self):
        """Test profit factor with no losses."""
        metric = ProfitFactorMetric()
        trades = [
            Trade(
                timestamp=datetime.now(),
                symbol="AAPL",
                side="BUY",
                quantity=10.0,
                price=150.0,
                slippage=0.0,
                commission=1.0,
                pnl=100.0,
            ),
            Trade(
                timestamp=datetime.now(),
                symbol="AAPL",
                side="SELL",
                quantity=10.0,
                price=155.0,
                slippage=0.0,
                commission=1.0,
                pnl=200.0,
            ),
        ]

        result = metric.calculate(trades, [], 100000.0, [])
        self.assertEqual(result, float("inf"))

    def test_profit_factor_no_trades(self):
        """Test profit factor with no trades."""
        metric = ProfitFactorMetric()
        result = metric.calculate([], [], 100000.0)
        self.assertEqual(result, 0.0)


class TestReportGenerator(unittest.TestCase):
    """Test the ReportGenerator orchestration."""

    def test_generate_with_default_metrics(self):
        """Test report generation with default metrics."""
        gen = ReportGenerator()
        portfolio = Portfolio(initial_cash=100000.0)
        equity_curve_values = [100000.0, 105000.0, 110000.0]

        # Build equity curve with timestamps
        for i, eq in enumerate(equity_curve_values):
            ts = datetime.now()
            portfolio.equity_curve.append((ts, eq))

        # Add some trades
        fill1 = Fill(
            order_id="ORD_1",
            timestamp=datetime.now(),
            symbol="AAPL",
            side=OrderSide.BUY,
            quantity=10.0,
            price=150.0,
        )
        fill2 = Fill(
            order_id="ORD_2",
            timestamp=datetime.now(),
            symbol="AAPL",
            side=OrderSide.SELL,
            quantity=10.0,
            price=151.0,
        )
        portfolio.apply_fill(fill1)
        portfolio.apply_fill(fill2)

        report = gen.generate(portfolio)

        # Result should be a list of MetricResult objects
        self.assertIsNotNone(report)
        self.assertTrue(len(report) > 0)
        # Check that some expected metrics exist
        metric_names = [r.name for r in report]
        self.assertIn("Total Return", metric_names)

    def test_generate_with_custom_metrics(self):
        """Test report generation with custom metrics."""
        gen = ReportGenerator(metrics=[TotalReturnMetric(), WinRateMetric()])
        portfolio = Portfolio(initial_cash=100000.0)

        # Build equity curve with timestamps
        for eq in [100000.0, 105000.0]:
            ts = datetime.now()
            portfolio.equity_curve.append((ts, eq))

        # Add a trade
        fill = Fill(
            order_id="ORD_1",
            timestamp=datetime.now(),
            symbol="AAPL",
            side=OrderSide.BUY,
            quantity=10.0,
            price=150.0,
        )
        portfolio.apply_fill(fill)

        report = gen.generate(portfolio)

        self.assertEqual(len(report), 2)
        metric_names = [r.name for r in report]
        self.assertIn("Total Return", metric_names)
        self.assertIn("Win Rate", metric_names)

    def test_add_metric_fluent_api(self):
        """Test fluent API for adding metrics."""
        gen = ReportGenerator()
        initial_count = len(gen.metrics)
        gen.add_metric(TotalReturnMetric()).add_metric(WinRateMetric())

        self.assertEqual(len(gen.metrics), initial_count + 2)

    def test_remove_metric(self):
        """Test removing a metric."""
        gen = ReportGenerator()
        initial_count = len(gen.metrics)

        gen.remove_metric("Annualized Sharpe Ratio")

        self.assertEqual(len(gen.metrics), initial_count - 1)
        self.assertFalse(any(m.name == "Sharpe Ratio" for m in gen.metrics))

    def test_format_report(self):
        """Test report formatting."""
        gen = ReportGenerator(metrics=[TotalReturnMetric()])
        portfolio = Portfolio(initial_cash=100000.0)

        # Build equity curve with timestamps
        for eq in [100000.0, 110000.0]:
            ts = datetime.now()
            portfolio.equity_curve.append((ts, eq))

        report = gen.generate(portfolio)
        formatted = gen.format_report(report)

        self.assertIn("Total Return", formatted)
        self.assertIn("10", formatted)  # Should contain the return value
        self.assertIn("=" * 50, formatted)  # Should have borders


if __name__ == "__main__":
    unittest.main()
