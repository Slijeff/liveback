"""Execution client interfaces for order routing and execution."""

from abc import ABC, abstractmethod
from typing import Optional, Callable
from src.types import Order, Fill, OrderId
from datetime import datetime


class ExecutionClient(ABC):
    """Abstract interface for execution clients (backtest simulation and live brokers)."""

    @abstractmethod
    def send_order(self, order: Order, current_price: Optional[float] = None) -> Fill:
        """Send an order for execution.

        Args:
            order: Order to execute
            current_price: Optional current market price (useful for backtest simulation)

        Returns:
            Fill: Fill event representing the executed order

        Raises:
            Exception: If order cannot be executed
        """
        pass

    @abstractmethod
    def cancel_order(self, order_id: OrderId) -> None:
        """Cancel a pending order.

        Args:
            order_id: ID of the order to cancel
        """
        pass


class BrokerSim(ExecutionClient):
    """Simulated broker for backtesting (executes orders at simulated prices)."""

    def __init__(self, slippage_model: Optional[Callable[[Order], float]] = None):
        """Initialize broker simulator.

        Args:
            slippage_model: Optional function to compute slippage for fills
        """
        self.slippage_model = slippage_model
        self._order_id_counter = 0
        self._last_prices = {}  # Track last seen price per symbol

    def send_order(self, order: Order, current_price: Optional[float] = None) -> Fill:
        """Simulate order execution at current market price.

        Args:
            order: Order to simulate
            current_price: Optional current market price for the symbol (if not provided, uses last seen price)

        Returns:
            Fill: Simulated fill event
        """

        self._order_id_counter += 1
        order_id = f"SIM_{self._order_id_counter}"

        # Use provided price, last seen price, or default
        if current_price is not None:
            fill_price = current_price
            self._last_prices[order.symbol] = current_price
        elif order.symbol in self._last_prices:
            fill_price = self._last_prices[order.symbol]
        else:
            raise ValueError(
                f"No price available for {order.symbol}. Provide current_price or process market data first."
            )

        slippage = 0.0 if not self.slippage_model else self.slippage_model(order)

        return Fill(
            order_id=order_id,
            timestamp=datetime.now(),
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            price=fill_price + slippage,
            slippage=slippage,
            commission=0.0,
        )

    def cancel_order(self, order_id: OrderId) -> None:
        """Cancel a simulated order (stub for now)."""
        # TODO: Track pending orders and cancel them
        pass
