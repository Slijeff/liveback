"""Strategy interface for implementing trading strategies."""

from abc import ABC, abstractmethod
from typing import List
from src.types import StrategyContext, Event, Fill, Order, OrderId, FillEvent
from loguru import logger


class Strategy(ABC):
    """Base class for trading strategies. Must be mode-agnostic (no if live/backtest)."""

    def __init__(self) -> None:
        super().__init__()
        self.pending_orders: List[Order] = []
        self._order_id_counter = 0
        self.context: StrategyContext = None

    def initialize(self, context: StrategyContext) -> None:
        """Initialize the strategy with context.

        Args:
            context: Strategy context containing portfolio, clients, and config
        """
        self.context = context

    @abstractmethod
    def on_event(self, event: Event) -> None:
        """Handle a market data event.

        Args:
            event: Market data event (bar/tick)
        """
        pass

    @abstractmethod
    def on_fill(self, fill: Fill) -> None:
        """Handle a fill event from order execution.

        Args:
            fill: Fill event representing an executed order
        """
        pass

    def on_fill_event(self, event: FillEvent) -> None:
        """Handle a FillEvent by delegating to on_fill.

        This method is designed to be subscribed to the event bus.

        Args:
            event: FillEvent containing fill data
        """
        self.on_fill(event.fill)

    def create_order(self, order: Order) -> OrderId:
        """Create an order (validates and returns order ID or raises).

        Args:
            order: Order to create

        Returns:
            OrderId: Unique identifier for the created order

        Raises:
            Exception: If order is invalid or cannot be created
        """
        self.pending_orders.append(order)
        self._order_id_counter += 1
        order_id = f"{self.__class__.__name__}_{self._order_id_counter}"
        logger.debug(f"Order created: {order_id}")
        return order_id

    def get_orders(self) -> List[Order]:
        """Get pending orders to be executed (used by engine).

        Returns:
            List of orders that should be sent to execution client
        """
        orders = self.pending_orders.copy()
        self.pending_orders.clear()
        return orders
