"""Execution client interfaces for order routing and execution."""

from abc import ABC, abstractmethod
from typing import List, Dict
from src.types import Order, MultiBar, Trade, Position


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
    def process_orders(self, current_bar: MultiBar) -> None:
        pass
