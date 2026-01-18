"""Portfolio and position management."""

from datetime import datetime
from typing import Dict, List, Tuple

from src.types import (
    Fill,
    OrderSide,
    Trade,
    Position,
    FillEvent,
    PriceUpdateEvent,
    EquityUpdateEvent,
)

from src.event_bus import EventBus


class Portfolio:
    """Tracks positions, PnL, and cash across all symbols."""

    def __init__(self, initial_cash: float = 100000.0):
        """Initialize portfolio.

        Args:
            event_bus: Event bus for publishing equity update events
            initial_cash: Starting cash balance
        """
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.positions: Dict[str, Position] = {}
        self.equity_curve: List[Tuple[datetime, float]] = []
        self.trades: List[Trade] = []
        self.event_bus = EventBus()

    def on_fill(self, event: FillEvent) -> None:
        """Handle a FillEvent by applying the fill to the portfolio.

        This method is designed to be subscribed to the event bus.

        Args:
            event: FillEvent containing the fill data
        """
        self.apply_fill(event.fill)

    def on_price_update(self, event: PriceUpdateEvent) -> None:
        """Handle a PriceUpdateEvent by updating unrealized PnL and recording equity.

        This method is designed to be subscribed to the event bus.

        Args:
            event: PriceUpdateEvent containing price and timestamp
        """
        current_prices = {event.symbol: event.price}
        self.update_unrealized_pnl(current_prices)
        self.record_equity(event.timestamp)
        # Publish equity update event
        self.event_bus.publish(
            EquityUpdateEvent(
                equity=self.get_total_equity(),
                timestamp=event.timestamp,
            )
        )

    def apply_fill(self, fill: Fill) -> None:
        """Apply a fill to update positions and cash.

        Args:
            fill: Fill event to apply
        """
        symbol = fill.symbol
        if symbol not in self.positions:
            self.positions[symbol] = Position(symbol=symbol)

        position = self.positions[symbol]
        cost = fill.quantity * fill.price + fill.commission
        trade_pnl = 0.0

        if fill.side == OrderSide.BUY:
            if position.quantity < 0:
                # Closing short position
                close_quantity = min(abs(position.quantity), fill.quantity)
                pnl = (
                    position.avg_price - fill.price
                ) * close_quantity - fill.commission
                trade_pnl = pnl
                position.quantity += close_quantity
                self.cash += fill.quantity * fill.price - cost

                self.trades.append(
                    Trade(
                        timestamp=fill.timestamp,
                        symbol=fill.symbol,
                        side=fill.side.value,
                        quantity=close_quantity,
                        price=fill.price,
                        slippage=fill.slippage,
                        commission=fill.commission,
                        pnl=trade_pnl,
                    )
                )

                if fill.quantity > close_quantity:
                    # Opening long position with remainder
                    remaining = fill.quantity - close_quantity
                    total_cost = remaining * fill.price
                    position.avg_price = fill.price
                    position.quantity = remaining
                    self.cash -= total_cost
            else:
                # Adding to long position
                total_cost = position.avg_price * position.quantity + cost
                position.quantity += fill.quantity
                position.avg_price = (
                    total_cost / position.quantity if position.quantity > 0 else 0
                )
                self.cash -= cost
        else:  # SELL
            if position.quantity > 0:
                # Closing long position
                close_quantity = min(position.quantity, fill.quantity)
                pnl = (
                    fill.price - position.avg_price
                ) * close_quantity - fill.commission
                trade_pnl = pnl
                position.quantity -= close_quantity
                self.cash += close_quantity * fill.price - fill.commission

                self.trades.append(
                    Trade(
                        timestamp=fill.timestamp,
                        symbol=fill.symbol,
                        side=fill.side.value,
                        quantity=close_quantity,
                        price=fill.price,
                        slippage=fill.slippage,
                        commission=fill.commission,
                        pnl=trade_pnl,
                    )
                )

                if fill.quantity > close_quantity:
                    # Opening short position with remainder
                    remaining = fill.quantity - close_quantity
                    position.avg_price = fill.price
                    position.quantity = -remaining
                    self.cash += remaining * fill.price - fill.commission
            else:
                # Adding to short position
                total_proceeds = (
                    abs(position.avg_price * position.quantity)
                    + fill.quantity * fill.price
                )
                position.quantity -= fill.quantity
                position.avg_price = (
                    abs(total_proceeds / position.quantity)
                    if position.quantity < 0
                    else 0
                )
                self.cash += fill.quantity * fill.price - fill.commission
        # Publish equity update event
        self.event_bus.publish(
            EquityUpdateEvent(
                equity=self.get_total_equity(),
                timestamp=fill.timestamp,
            )
        )

    def update_unrealized_pnl(self, current_prices: Dict[str, float]) -> None:
        """Update unrealized PnL based on current market prices.

        Args:
            current_prices: Dictionary mapping symbols to current prices
        """
        for symbol, position in self.positions.items():
            if position.quantity != 0 and symbol in current_prices:
                current_price = current_prices[symbol]
                if position.quantity > 0:
                    position.unrealized_pnl = (
                        current_price - position.avg_price
                    ) * position.quantity
                else:
                    position.unrealized_pnl = (
                        position.avg_price - current_price
                    ) * abs(position.quantity)

    def get_total_equity(self) -> float:
        """Get total equity (cash + market value of all positions).

        Returns:
            Total equity value
        """
        position_market_value = sum(
            pos.quantity * pos.avg_price + pos.unrealized_pnl
            for pos in self.positions.values()
        )
        return self.cash + position_market_value

    def record_equity(self, timestamp: datetime) -> None:
        """Record current equity to equity curve."""
        self.equity_curve.append((timestamp, self.get_total_equity()))

    def get_position(self, symbol: str) -> Position:
        """Return existing position or create a new zero position for the symbol.

        This prevents callers from needing to check for existence and aligns with
        risk manager logic which expects a Position object even when none exists
        yet for a given symbol.
        """
        if symbol not in self.positions:
            self.positions[symbol] = Position(symbol=symbol)
        return self.positions[symbol]
