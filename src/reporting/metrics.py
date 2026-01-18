"""Base and concrete implementations of performance metrics."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List
import numpy as np

from src.types import Trade


@dataclass
class MetricResult:
    """Result of a metric calculation."""

    name: str
    value: float
    unit: str = ""


class Metric(ABC):
    """Base class for all metrics.

    Subclasses should implement the calculate() method to compute
    a specific metric from backtest results.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the metric."""
        pass

    @property
    @abstractmethod
    def unit(self) -> str:
        """The unit of the metric"""
        pass

    @abstractmethod
    def calculate(
        self,
        trades: List[Trade],
        equity_curve: List[float],
        initial_capital: float,
        timestamps: List = None,
    ) -> float:
        """Calculate the metric.

        Args:
            trades: List of Trade objects with entry/exit prices, times, PnL
            equity_curve: List of equity values over time
            initial_capital: Starting capital
            timestamps: List of timestamps corresponding to equity_curve (optional)

        Returns:
            Computed metric value
        """
        pass


class TotalReturnMetric(Metric):
    """Calculate total return percentage."""

    @property
    def name(self) -> str:
        return "Total Return"

    @property
    def unit(self) -> str:
        return "%"

    def calculate(
        self,
        trades: List,
        equity_curve: List[float],
        initial_capital: float,
        timestamps: List = None,
    ) -> float:
        if not equity_curve:
            return 0.0
        final_equity = equity_curve[-1]
        return ((final_equity - initial_capital) / initial_capital) * 100


class AnnualizedReturnMetric(Metric):
    """Calculate annualized return percentage."""

    @property
    def name(self) -> str:
        return "Annualized Return"

    @property
    def unit(self) -> str:
        return "%"

    def calculate(
        self,
        trades: List,
        equity_curve: List[float],
        initial_capital: float,
        timestamps: List = None,
    ) -> float:
        if not equity_curve or len(equity_curve) < 2:
            return 0.0

        # Estimate number of years from timestamps or assume daily bars
        if timestamps and len(timestamps) > 1:
            days = (timestamps[-1] - timestamps[0]).days
            years = days / 365.25
        else:
            # Assume one reading per trading day (252 trading days/year)
            years = len(equity_curve) / 252.0

        if years <= 0:
            return 0.0

        annualized = (((equity_curve[-1] / initial_capital) ** (1 / years)) - 1) * 100
        return annualized


class AnnualizedSharpeRatioMetric(Metric):
    """Calculate Sharpe ratio using daily returns from equity curve.

    Assumes equity_curve represents daily equity values.
    Risk-free rate defaults to 0.
    """

    def __init__(self, risk_free_rate: float = 0.0):
        """Initialize Sharpe ratio metric.

        Args:
            risk_free_rate: Annual risk-free rate (default 0.0)
        """
        self.risk_free_rate = risk_free_rate

    @property
    def name(self) -> str:
        return "Annualized Sharpe Ratio"

    @property
    def unit(self) -> str:
        return ""

    def calculate(
        self,
        trades: List,
        equity_curve: List[float],
        initial_capital: float,
        timestamps: List = None,
    ) -> float:
        if len(equity_curve) < 2:
            return 0.0

        # Calculate daily returns
        equity_array = np.array(equity_curve, dtype=float)
        daily_returns = np.diff(equity_array) / equity_array[:-1]

        if len(daily_returns) == 0:
            return 0.0

        # Calculate Sharpe ratio
        mean_return = np.mean(daily_returns)
        std_return = np.std(daily_returns)

        if std_return == 0:
            return 0.0

        # Annualize (252 trading days per year)
        excess_return = mean_return - (self.risk_free_rate / 252)
        sharpe_ratio = (excess_return / std_return) * np.sqrt(252)

        return float(sharpe_ratio)


class MaxDrawdownMetric(Metric):
    """Calculate maximum drawdown percentage."""

    @property
    def name(self) -> str:
        return "Max Drawdown"

    @property
    def unit(self) -> str:
        return "%"

    def calculate(
        self,
        trades: List,
        equity_curve: List[float],
        initial_capital: float,
        timestamps: List = None,
    ) -> float:
        if not equity_curve:
            return 0.0

        equity_array = np.array(equity_curve, dtype=float)
        running_max = np.maximum.accumulate(equity_array)
        drawdown = (equity_array - running_max) / running_max
        max_drawdown = np.min(drawdown)

        return float(max_drawdown * 100)


class WinRateMetric(Metric):
    """Calculate win rate percentage (trades with positive PnL)."""

    @property
    def name(self) -> str:
        return "Win Rate"

    @property
    def unit(self) -> str:
        return "%"

    def calculate(
        self,
        trades: List[Trade],
        equity_curve: List[float],
        initial_capital: float,
        timestamps: List = None,
    ) -> float:
        if not trades:
            return 0.0

        winners = sum(1 for trade in trades if trade.pnl > 0)
        return (winners / len(trades)) * 100


class AveragePnLPerTradeMetric(Metric):
    """Calculate average PnL per trade."""

    @property
    def name(self) -> str:
        return "Avg PnL Per Trade"

    @property
    def unit(self) -> str:
        return "$"

    def calculate(
        self,
        trades: List,
        equity_curve: List[float],
        initial_capital: float,
        timestamps: List = None,
    ) -> float:
        if not trades:
            return 0.0

        total_pnl = sum(trade.get("pnl", 0) for trade in trades)
        return total_pnl / len(trades)


class NumTradesMetric(Metric):
    """Calculate total number of trades."""

    @property
    def name(self) -> str:
        return "Num Trades"

    @property
    def unit(self) -> str:
        return ""

    def calculate(
        self,
        trades: List,
        equity_curve: List[float],
        initial_capital: float,
        timestamps: List = None,
    ) -> float:
        return float(len(trades))


class ProfitFactorMetric(Metric):
    """Calculate profit factor (gross profit / gross loss).

    Returns infinity if no losing trades. Returns 0 if no trades at all.
    """

    @property
    def name(self) -> str:
        return "Profit Factor"

    @property
    def unit(self) -> str:
        return ""

    def calculate(
        self,
        trades: List[Trade],
        equity_curve: List[float],
        initial_capital: float,
        timestamps: List = None,
    ) -> float:
        if not trades:
            return 0.0

        gross_profit = sum(trade.pnl for trade in trades if trade.pnl > 0)
        gross_loss = abs(sum(trade.pnl for trade in trades if trade.pnl < 0))

        if gross_loss == 0:
            return float("inf") if gross_profit > 0 else 0.0

        return gross_profit / gross_loss


class TotalEquityMetric(Metric):
    @property
    def name(self):
        return "Total Equity"

    @property
    def unit(self):
        return "$"

    def calculate(
        self,
        trades: List,
        equity_curve: List[float],
        initial_capital: float,
        timestamps: List = None,
    ) -> float:
        return equity_curve[-1]


class StartingEquityMetric(Metric):
    @property
    def name(self):
        return "Starting Equity"

    @property
    def unit(self):
        return "$"

    def calculate(
        self,
        trades: List,
        equity_curve: List[float],
        initial_capital: float,
        timestamps: List = None,
    ) -> float:
        return equity_curve[0]


class TotalDurationMetric(Metric):
    @property
    def name(self):
        return "Duration"

    @property
    def unit(self):
        return "days"

    def calculate(
        self,
        trades: List,
        equity_curve: List[float],
        initial_capital: float,
        timestamps: List = None,
    ) -> float:
        return (timestamps[-1] - timestamps[0]).days
