"""A buy-and-hold strategy that buys once at the start."""

from loguru import logger
from src.strategy.strategy import Strategy
from src.types import Event, Fill, Order, OrderSide, OrderType


class NoOpStrategy(Strategy):
    """A buy-and-hold strategy that buys once at the start."""

    def __init__(self, cash_percentage: float = 0.95):
        super().__init__()
        """Initialize the buy-and-hold strategy.
        
        Args:
            cash_percentage: Percentage of available cash to use for initial buy (default 0.95)
        """
        self.has_placed_initial_order = False
        self.cash_percentage = cash_percentage

    def on_event(self, event: Event) -> None:
        """Handle a market data event - places buy order on first event.

        Args:
            event: Market data event (bar/tick)
        """
        price = event.close_price or event.trade_price

        # Place buy order on first event only
        if not self.has_placed_initial_order and price is not None:
            available_cash = self.context.portfolio.cash
            cash_to_use = available_cash * self.cash_percentage

            # Calculate number of shares (round down to whole shares)
            quantity = int(cash_to_use / price)

            if quantity > 0:
                order = Order(
                    symbol=event.symbol,
                    side=OrderSide.BUY,
                    quantity=float(quantity),
                    order_type=OrderType.MARKET,
                )
                self.create_order(order)
                self.has_placed_initial_order = True
                logger.info(
                    f"Placing initial buy order: {quantity} shares of {event.symbol} @ ~${price:.2f}"
                )
            else:
                logger.info(
                    f"Not enough cash to buy even 1 share (need ${price:.2f}, have ${available_cash:.2f})"
                )

    def on_fill(self, fill: Fill) -> None:
        """Handle a fill event from order execution (does nothing).

        Args:
            fill: Fill event representing an executed order
        """
        logger.debug(
            f"Received fill: {fill.side.value} {fill.quantity} {fill.symbol} @ ${fill.price:.2f}"
        )
