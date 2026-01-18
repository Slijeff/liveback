"""Reporting module for calculating performance metrics."""

from .metrics import (
    Metric,
    AnnualizedSharpeRatioMetric,
    MaxDrawdownMetric,
    WinRateMetric,
    TotalReturnMetric,
    AnnualizedReturnMetric,
    AveragePnLPerTradeMetric,
    NumTradesMetric,
    ProfitFactorMetric,
)
from .report_generator import ReportGenerator

__all__ = [
    "Metric",
    "AnnualizedSharpeRatioMetric",
    "MaxDrawdownMetric",
    "WinRateMetric",
    "TotalReturnMetric",
    "AnnualizedReturnMetric",
    "AveragePnLPerTradeMetric",
    "NumTradesMetric",
    "ProfitFactorMetric",
    "ReportGenerator",
]
