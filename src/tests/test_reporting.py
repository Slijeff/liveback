"""Tests for the reporting module metrics."""

import unittest
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
            {"pnl": 100.0},
            {"pnl": -50.0},
            {"pnl": 200.0},
            {"pnl": -30.0},
        ]

        result = metric.calculate(trades, [], 100000.0)
        self.assertEqual(result, 50.0)  # 2 winning / 4 total

    def test_win_rate_all_winners(self):
        """Test win rate with all winning trades."""
        metric = WinRateMetric()
        trades = [{"pnl": 100.0}, {"pnl": 200.0}]

        result = metric.calculate(trades, [], 100000.0)
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

        result = metric.calculate(trades, [], 100000.0)
        self.assertAlmostEqual(result, 83.333333, places=5)

    def test_num_trades_metric(self):
        """Test number of trades metric."""
        metric = NumTradesMetric()
        trades = [{"pnl": 100.0}, {"pnl": -50.0}, {"pnl": 75.0}]

        result = metric.calculate(trades, [], 100000.0)
        self.assertEqual(result, 3.0)

    def test_profit_factor_metric(self):
        """Test profit factor calculation."""
        metric = ProfitFactorMetric()
        trades = [
            {"pnl": 100.0},
            {"pnl": 200.0},
            {"pnl": -50.0},
        ]

        result = metric.calculate(trades, [], 100000.0)
        # (100 + 200) / 50 = 6.0
        self.assertEqual(result, 6.0)

    def test_profit_factor_no_losses(self):
        """Test profit factor with no losses."""
        metric = ProfitFactorMetric()
        trades = [{"pnl": 100.0}, {"pnl": 200.0}]

        result = metric.calculate(trades, [], 100000.0)
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
        equity_curve = [100000.0, 105000.0, 110000.0]
        trades = [{"pnl": 100.0}, {"pnl": -50.0}]

        report = gen.generate(trades, equity_curve, 100000.0)

        self.assertIn("Total Return", report)
        self.assertIn("Sharpe Ratio", report)
        self.assertIn("Max Drawdown", report)
        self.assertIsInstance(report, dict)

    def test_generate_with_custom_metrics(self):
        """Test report generation with custom metrics."""
        gen = ReportGenerator(metrics=[TotalReturnMetric(), WinRateMetric()])
        equity_curve = [100000.0, 105000.0]
        trades = [{"pnl": 100.0}]

        report = gen.generate(trades, equity_curve, 100000.0)

        self.assertEqual(len(report), 2)
        self.assertIn("Total Return", report)
        self.assertIn("Win Rate", report)

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

        gen.remove_metric("Sharpe Ratio")

        self.assertEqual(len(gen.metrics), initial_count - 1)
        self.assertFalse(any(m.name == "Sharpe Ratio" for m in gen.metrics))

    def test_format_report(self):
        """Test report formatting."""
        gen = ReportGenerator(metrics=[TotalReturnMetric()])
        equity_curve = [100000.0, 110000.0]

        report = gen.generate([], equity_curve, 100000.0)
        formatted = gen.format_report(report)

        self.assertIn("Total Return", formatted)
        self.assertIn("10", formatted)  # Should contain the return value
        self.assertIn("=" * 50, formatted)  # Should have borders

    def test_generate_with_details(self):
        """Test detailed result generation."""
        gen = ReportGenerator(metrics=[TotalReturnMetric(), MaxDrawdownMetric()])
        equity_curve = [100000.0, 110000.0, 105000.0]

        results = gen.generate_with_details([], equity_curve, 100000.0)

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].name, "Total Return")
        self.assertEqual(results[0].unit, "%")
        self.assertIsInstance(results[0].value, float)


if __name__ == "__main__":
    unittest.main()
