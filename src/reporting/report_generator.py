"""Report generator for orchestrating metric calculations."""

from typing import Dict, List, Any

from src.portfolio import Portfolio
from .metrics import Metric, MetricResult


class ReportGenerator:
    """Generates performance reports by computing selected metrics.

    Accepts a list of Metric plugins and orchestrates their calculation
    from backtest results.
    """

    def __init__(self, metrics: List[Metric] = None):
        """Initialize report generator with metrics.

        Args:
            metrics: List of Metric instances to compute. If None, uses defaults.
        """
        self.metrics = metrics or self._default_metrics()

    @staticmethod
    def _default_metrics() -> List[Metric]:
        """Return default set of metrics."""
        from .metrics import (
            TotalReturnMetric,
            AnnualizedReturnMetric,
            AnnualizedSharpeRatioMetric,
            MaxDrawdownMetric,
            WinRateMetric,
            NumTradesMetric,
        )

        return [
            TotalReturnMetric(),
            AnnualizedReturnMetric(),
            AnnualizedSharpeRatioMetric(),
            MaxDrawdownMetric(),
            WinRateMetric(),
            NumTradesMetric(),
        ]

    def add_metric(self, metric: Metric) -> "ReportGenerator":
        """Add a metric to the report generator (fluent API).

        Args:
            metric: Metric instance to add

        Returns:
            Self for chaining
        """
        self.metrics.append(metric)
        return self

    def remove_metric(self, metric_name: str) -> "ReportGenerator":
        """Remove a metric by name.

        Args:
            metric_name: Name of the metric to remove

        Returns:
            Self for chaining
        """
        self.metrics = [m for m in self.metrics if m.name != metric_name]
        return self

    def generate(self, portfolio: Portfolio) -> Dict[str, Any]:
        """Generate performance report by computing all metrics.

        Args:
            trades: List of Trade objects from backtest
            equity_curve: List of equity values over time
            initial_capital: Starting capital
            timestamps: List of timestamps for equity_curve (optional)

        Returns:
            Dictionary mapping metric names to computed values
        """
        report = {}

        for metric in self.metrics:
            try:
                timestamp, equity_curve = list(zip(*portfolio.equity_curve))
                value = metric.calculate(
                    portfolio.trades, equity_curve, portfolio.initial_cash, timestamp
                )
                report[metric.name] = value
            except Exception as e:
                report[metric.name] = f"Error: {str(e)}"

        return report

    def generate_with_details(
        self,
        trades: List,
        equity_curve: List[float],
        initial_capital: float,
        timestamps: List = None,
    ) -> List[MetricResult]:
        """Generate report with detailed MetricResult objects.

        Args:
            trades: List of Trade objects from backtest
            equity_curve: List of equity values over time
            initial_capital: Starting capital
            timestamps: List of timestamps for equity_curve (optional)

        Returns:
            List of MetricResult objects with name, value, and unit
        """
        results = []

        for metric in self.metrics:
            try:
                value = metric.calculate(
                    trades, equity_curve, initial_capital, timestamps
                )
                unit = self._get_unit_for_metric(metric.name)
                results.append(MetricResult(name=metric.name, value=value, unit=unit))
            except Exception as e:
                results.append(
                    MetricResult(name=metric.name, value=None, unit=f"Error: {str(e)}")
                )

        return results

    @staticmethod
    def _get_unit_for_metric(metric_name: str) -> str:
        """Return unit for a given metric name."""
        units = {
            "Total Return": "%",
            "Annualized Return": "%",
            "Sharpe Ratio": "",
            "Max Drawdown": "%",
            "Win Rate": "%",
            "Num Trades": "",
            "Avg PnL Per Trade": "$",
            "Profit Factor": "x",
        }
        return units.get(metric_name, "")

    def format_report(
        self,
        report: Dict[str, Any],
        precision: int = 4,
    ) -> str:
        """Format report as human-readable string.

        Args:
            report: Report dictionary from generate()
            precision: Decimal places for float values

        Returns:
            Formatted report string
        """
        lines = ["=" * 50, "Performance Report", "=" * 50]

        for metric_name, value in report.items():
            unit = self._get_unit_for_metric(metric_name)
            if isinstance(value, float):
                if value == float("inf"):
                    formatted_value = "∞"
                elif value == float("-inf"):
                    formatted_value = "-∞"
                else:
                    formatted_value = f"{value:.{precision}f}"
            else:
                formatted_value = str(value)

            unit_str = f" {unit}" if unit else ""
            lines.append(f"{metric_name:<30} {formatted_value:>12}{unit_str}")

        lines.append("=" * 50)
        return "\n".join(lines)
