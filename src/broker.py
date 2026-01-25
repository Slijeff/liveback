"""Execution client interfaces for order routing and execution."""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from loguru import logger
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

    def __init__(
        self,
        initial_cash: float,
        slippage: float = 0.0,
        commission: float = 0.0,
    ):
        super().__init__()
        self.cash = initial_cash
        self.slippage = slippage
        self.commission = commission

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
        logger.debug(
            "Order accepted: {} {} {} type={} limit={} stop={}",
            order.symbol,
            order.side.value,
            order.quantity,
            order.order_type.value,
            order.limit_price,
            order.stop_price,
        )

        return order

    def process_orders(self, current_bar: MultiBar) -> None:
        for order in list(self.orders):
            bar = current_bar.get(order.symbol)
            if bar is None:
                logger.debug(
                    "Skipping order (no bar): {} {} {}",
                    order.symbol,
                    order.side.value,
                    order.quantity,
                )
                continue

            open_price = bar.open if bar.open is not None else bar.close
            if open_price is None:
                logger.debug(
                    "Skipping order (no open/close): {} {} {}",
                    order.symbol,
                    order.side.value,
                    order.quantity,
                )
                continue
            high = bar.high if bar.high is not None else open_price
            low = bar.low if bar.low is not None else open_price

            fill_price = None
            if order.order_type == OrderType.MARKET:
                fill_price = open_price
            elif order.order_type == OrderType.LIMIT and order.limit_price is not None:
                if order.side == OrderSide.BUY and low <= order.limit_price:
                    fill_price = min(open_price, order.limit_price)
                elif order.side == OrderSide.SELL and high >= order.limit_price:
                    fill_price = max(open_price, order.limit_price)
            elif order.order_type == OrderType.STOP and order.stop_price is not None:
                if order.side == OrderSide.BUY and high >= order.stop_price:
                    fill_price = max(open_price, order.stop_price)
                elif order.side == OrderSide.SELL and low <= order.stop_price:
                    fill_price = min(open_price, order.stop_price)

            if fill_price is None:
                logger.debug(
                    "Order not filled this bar: {} {} {} type={}",
                    order.symbol,
                    order.side.value,
                    order.quantity,
                    order.order_type.value,
                )
                continue

            quantity = abs(order.quantity)
            position = self.positions.get(order.symbol)
            if position is None:
                position = Position(symbol=order.symbol)
                self.positions[order.symbol] = position

            if self.slippage:
                fill_price = (
                    fill_price + self.slippage
                    if order.side == OrderSide.BUY
                    else fill_price - self.slippage
                )

            trade_pnl = 0.0
            if order.side == OrderSide.BUY:
                if position.quantity < 0:
                    close_quantity = min(abs(position.quantity), quantity)
                    trade_pnl = (position.avg_price - fill_price) * close_quantity
                    position.quantity += close_quantity
                    if position.quantity == 0:
                        position.avg_price = 0.0
                    if quantity > close_quantity:
                        remaining = quantity - close_quantity
                        position.avg_price = fill_price
                        position.quantity = remaining
                else:
                    total_cost = (
                        position.avg_price * position.quantity + fill_price * quantity
                    )
                    position.quantity += quantity
                    position.avg_price = (
                        total_cost / position.quantity if position.quantity else 0.0
                    )
            else:  # SELL
                if position.quantity > 0:
                    close_quantity = min(position.quantity, quantity)
                    trade_pnl = (fill_price - position.avg_price) * close_quantity
                    position.quantity -= close_quantity
                    if position.quantity == 0:
                        position.avg_price = 0.0
                    if quantity > close_quantity:
                        remaining = quantity - close_quantity
                        position.avg_price = fill_price
                        position.quantity = -remaining
                else:
                    total_proceeds = (
                        abs(position.avg_price * position.quantity)
                        + fill_price * quantity
                    )
                    position.quantity -= quantity
                    position.avg_price = (
                        abs(total_proceeds / position.quantity)
                        if position.quantity < 0
                        else 0.0
                    )

            slippage_cost = abs(quantity * self.slippage)
            commission_cost = self.commission
            trade_pnl -= commission_cost

            trade = Trade(
                timestamp=bar.timestamp,
                symbol=order.symbol,
                side=order.side.value,
                quantity=quantity,
                price=fill_price,
                slippage=slippage_cost,
                commission=commission_cost,
                pnl=trade_pnl,
            )
            self.trades.append(trade)
            if trade_pnl != 0.0:
                self.closed_trades.append(trade)
            self.orders.remove(order)
            logger.info(
                "Order filled: {} {} {} @ {} pnl={}",
                order.symbol,
                order.side.value,
                quantity,
                fill_price,
                trade_pnl,
            )
