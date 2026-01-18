"""Base and concrete implementations of performance metrics."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List
import numpy as np
from scipy.stats import gmean

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
    """Calculate annualized return percentage using geometric mean of daily returns.

    Implementation based on backtesting.py: assumes returns are compounded.
    See: https://dx.doi.org/10.2139/ssrn.3054517
    """

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

        # Calculate daily returns
        equity_array = np.array(equity_curve, dtype=float)
        daily_returns = np.diff(equity_array) / equity_array[:-1]

        if len(daily_returns) == 0:
            return 0.0

        # Calculate geometric mean of daily returns
        gmean_day_return = gmean(1 + daily_returns) - 1

        # Annualize (252 trading days per year)
        annualized_return = (1 + gmean_day_return) ** 252 - 1

        return float(annualized_return * 100)


class AnnualizedVolatilityMetric(Metric):
    """Calculate annualized volatility using compounded returns formula.

    Implementation based on backtesting.py:
    volatility = sqrt((var(day_returns) + gmean^2)^252 - gmean^(2*252))
    See: https://dx.doi.org/10.2139/ssrn.3054517
    """

    @property
    def name(self) -> str:
        return "Annualized Volatility"

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

        # Calculate daily returns
        equity_array = np.array(equity_curve, dtype=float)
        daily_returns = np.diff(equity_array) / equity_array[:-1]

        if len(daily_returns) == 0:
            return 0.0

        # Calculate geometric mean of daily returns
        gmean_day_return = gmean(1 + daily_returns) - 1

        # Use sample variance (ddof=1 for sample, ddof=0 for population)
        # If only one return value, use population variance
        ddof = int(bool(len(daily_returns)))
        variance = daily_returns.var(ddof=ddof)

        # Annualized volatility formula from backtesting.py
        annualized_volatility = np.sqrt(
            (variance + (1 + gmean_day_return) ** 2) ** 252
            - (1 + gmean_day_return) ** (2 * 252)
        )

        return float(annualized_volatility * 100)


class AnnualizedSharpeRatioMetric(Metric):
    """Calculate Sharpe ratio using annualized return and volatility.

    Implementation based on backtesting.py:
    Sharpe = (annualized_return - risk_free_rate) / annualized_volatility
    See: https://dx.doi.org/10.2139/ssrn.3054517
    """

    def __init__(self, risk_free_rate: float = 0.0):
        """Initialize Sharpe ratio metric.

        Args:
            risk_free_rate: Annual risk-free rate as decimal (e.g., 0.02 for 2%)
        """
        self.risk_free_rate = risk_free_rate
        self._annualized_return_metric = AnnualizedReturnMetric()
        self._volatility_metric = AnnualizedVolatilityMetric()

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
        if not equity_curve or len(equity_curve) < 2:
            return 0.0

        # Get annualized return (in %)
        annualized_return_pct = self._annualized_return_metric.calculate(
            trades, equity_curve, initial_capital, timestamps
        )

        # Get annualized volatility (in %)
        volatility_pct = self._volatility_metric.calculate(
            trades, equity_curve, initial_capital, timestamps
        )

        if volatility_pct == 0 or np.isnan(volatility_pct):
            return 0.0

        # Convert return and volatility from % to decimal for calculation
        annualized_return = annualized_return_pct / 100
        volatility = volatility_pct / 100

        # Sharpe ratio = (return - risk_free_rate) / volatility
        sharpe_ratio = (annualized_return - self.risk_free_rate) / volatility

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
