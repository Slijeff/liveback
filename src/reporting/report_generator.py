"""Report generator for orchestrating metric calculations."""

from typing import List

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
        self.metrics.sort(key=lambda m: m.name)

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
            TotalEquityMetric,
            StartingEquityMetric,
            ProfitFactorMetric,
            TotalDurationMetric,
        )

        return [
            TotalReturnMetric(),
            AnnualizedReturnMetric(),
            AnnualizedSharpeRatioMetric(),
            MaxDrawdownMetric(),
            WinRateMetric(),
            NumTradesMetric(),
            TotalEquityMetric(),
            StartingEquityMetric(),
            ProfitFactorMetric(),
            TotalDurationMetric(),
        ]

    def add_metric(self, metric: Metric) -> "ReportGenerator":
        """Add a metric to the report generator (fluent API).

        Args:
            metric: Metric instance to add

        Returns:
            Self for chaining
        """
        self.metrics.append(metric)
        self.metrics.sort(key=lambda m: m.name)
        return self

    def remove_metric(self, metric_name: str) -> "ReportGenerator":
        """Remove a metric by name.

        Args:
            metric_name: Name of the metric to remove

        Returns:
            Self for chaining
        """
        self.metrics = [m for m in self.metrics if m.name != metric_name]
        self.metrics.sort(key=lambda m: m.name)
        return self

    def generate(self, portfolio: Portfolio) -> List[MetricResult]:
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
                timestamp, equity_curve = list(zip(*portfolio.equity_curve))
                value = metric.calculate(
                    portfolio.trades, equity_curve, portfolio.initial_cash, timestamp
                )
                results.append(
                    MetricResult(name=metric.name, value=value, unit=metric.unit)
                )
            except Exception as e:
                results.append(
                    MetricResult(name=metric.name, value=None, unit=f"Error: {str(e)}")
                )

        return results

    def format_report(
        self,
        reports: List[MetricResult],
        precision: int = 3,
    ) -> str:
        """Format report as human-readable string.

        Args:
            report: Report dictionary from generate()
            precision: Decimal places for float values

        Returns:
            Formatted report string
        """
        lines = ["=" * 50, "Performance Report", "=" * 50]

        for report in reports:
            if isinstance(report.value, float):
                if report.value == float("inf"):
                    formatted_value = "∞"
                elif report.value == float("-inf"):
                    formatted_value = "-∞"
                else:
                    formatted_value = f"{report.value:.{precision}f}"
            else:
                formatted_value = str(report.value)

            unit_str = f" {report.unit}" if report.unit else ""
            lines.append(f"{report.name:<30} {formatted_value:>12}{unit_str}")

        lines.append("=" * 50)
        return "\n".join(lines)
