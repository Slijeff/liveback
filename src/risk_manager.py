"""Risk management for position sizing and validation."""

from typing import Optional
from src.types import Order, OrderSide, EquityUpdateEvent
from src.portfolio import Portfolio


class RiskManager:
    """Validates orders for risk constraints (position limits, margin, etc.)."""

    def __init__(
        self,
        max_position_size: Optional[float] = None,
        max_portfolio_exposure: Optional[float] = None,
        max_drawdown: Optional[float] = None,
    ):
        """Initialize risk manager.

        Args:
            max_position_size: Maximum position size per symbol (absolute value)
            max_portfolio_exposure: Maximum total portfolio exposure
            max_drawdown: Maximum allowed drawdown from peak equity
        """
        self.max_position_size = max_position_size
        self.max_portfolio_exposure = max_portfolio_exposure
        self.max_drawdown = max_drawdown
        self.peak_equity: Optional[float] = None

    def on_equity_update(self, event: EquityUpdateEvent) -> None:
        """Handle an EquityUpdateEvent by updating peak equity.

        This method is designed to be subscribed to the event bus.

        Args:
            event: EquityUpdateEvent containing equity value
        """
        self.update_peak_equity(event.equity)

    def validate_order(self, order: Order, portfolio: Portfolio) -> bool:
        """Validate an order against risk constraints.

        Args:
            order: Order to validate
            portfolio: Current portfolio state

        Returns:
            True if order passes risk checks, False otherwise
        """
        # Check position size limit
        if self.max_position_size is not None:
            current_position = portfolio.get_position(order.symbol)
            new_quantity = current_position.quantity
            if order.side == OrderSide.BUY:
                new_quantity += order.quantity
            else:
                new_quantity -= order.quantity

            if abs(new_quantity) > self.max_position_size:
                return False

        # Check portfolio exposure limit
        if self.max_portfolio_exposure is not None:
            # Simple check: would this order exceed exposure?
            # More sophisticated checks could consider market value of positions
            current_exposure = sum(
                abs(pos.quantity) * pos.avg_price if pos.quantity != 0 else 0
                for pos in portfolio.positions.values()
            )
            # Approximate new exposure (using order quantity)
            if (
                current_exposure + order.quantity * (order.limit_price or 0)
                > self.max_portfolio_exposure
            ):
                return False

        # Check drawdown limit
        if self.max_drawdown is not None:
            current_equity = portfolio.get_total_equity()
            if self.peak_equity is None or current_equity > self.peak_equity:
                self.peak_equity = current_equity

            if self.peak_equity is not None:
                drawdown = (self.peak_equity - current_equity) / self.peak_equity
                if drawdown > self.max_drawdown:
                    return False

        return True

    def update_peak_equity(self, equity: float) -> None:
        """Update peak equity for drawdown tracking.

        Args:
            equity: Current equity value
        """
        if self.peak_equity is None or equity > self.peak_equity:
            self.peak_equity = equity
