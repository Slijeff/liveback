"""Execution client interfaces for order routing and execution."""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from src.types import Order, MultiBar, Trade, Position, OrderSide, OrderType


class Broker(ABC):
    """Abstract interface for execution clients (backtest simulation and live brokers)."""

    def __init__(self):
        self.orders: List[Order] = []
        self.trades: List[Trade] = []
        self.closed_trades: List[Trade] = []
        self.positions: Dict[str, Position] = {}  # symbol -> Position

    def next(self, current_bar: MultiBar) -> None:
        self.process_orders(current_bar)

    @abstractmethod
    def new_order(
        self,
        symbol: str,
        quantity: float,
        limit: Optional[float],
        stop: Optional[float],
    ) -> Order:
        pass

    @abstractmethod
    def process_orders(self, current_bar: MultiBar) -> None:
        pass


class BacktestSimulationBroker(Broker):
    """Simulated broker for backtesting."""

    def __init__(self, initial_cash: float):
        super().__init__()
        self.cash = initial_cash

        # Additional initialization for backtest simulation
        self.equity_curve: List[float] = []

    def new_order(
        self,
        symbol: str,
        quantity: float,
        limit: Optional[float],
        stop: Optional[float],
    ) -> Order:
        assert quantity != 0, "Order quantity cannot be zero"

        side = OrderSide.BUY if quantity > 0 else OrderSide.SELL

        if limit is not None:
            order_type = OrderType.LIMIT
        elif stop is not None:
            order_type = OrderType.STOP
        else:
            order_type = OrderType.MARKET

        order = Order(symbol, side, quantity, order_type, limit, stop)
        self.orders.append(order)

        return order

    def process_orders(self, current_bar: MultiBar) -> None:
        pass
