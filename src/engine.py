"""Trading engines for backtest and live modes."""

from abc import ABC, abstractmethod
import sys
from typing import List
from src.data_client import DataClient
from src.broker import Broker
from src.metrics import Metric
from src.report_generator import ReportGenerator
from src.strategy import Strategy
from src.portfolio import Portfolio
from src.types import (
    Order,
    OrderSide,
    FillEvent,
    PriceUpdateEvent,
)
from loguru import logger


class Engine(ABC):
    """Base engine interface."""

    def set_logging_level(self, level: str):
        logger.configure(handlers=[{"sink": sys.stdout, "level": level}])

    def __init__(
        self,
        data_client: DataClient,
        broker: Broker,
        strategy: Strategy,
        portfolio: Portfolio,
        metrics: List[Metric] = [],
        logging_level: str = "INFO",
    ):
        self.data_client = data_client
        self.execution_client = broker
        self.strategy = strategy
        self.portfolio = portfolio

        self.report_generator = ReportGenerator()
        for metric in metrics:
            self.report_generator.add_metric(metric)
        self.set_logging_level(logging_level)

    @abstractmethod
    def run(self) -> None:
        """Run the engine (blocking)."""
        pass


class BacktestEngine(Engine):
    """Event-driven backtest engine."""

    def __init__(
        self,
        data_client: DataClient,
        broker: Broker,
        strategy: Strategy,
        portfolio: Portfolio,
        metrics: List[Metric] = [],
        logging_level: str = "INFO",
    ):
        super().__init__(
            data_client, broker, strategy, portfolio, metrics, logging_level
        )

    def run(self, show_report: bool = True, finalize_trades: bool = False) -> None:
        """Run event-driven backtesting loop.

        Args:
            show_report: Whether to display the backtest report
            finalize_trades: If True, close all open positions at the end
        """
        # Event-driven backtesting loop
        for event in self.data_client.stream():
            # Publish price update event (portfolio and risk manager will react)
            self.event_bus.publish(
                PriceUpdateEvent(
                    symbol=event.symbol,
                    price=event.close_price,
                    timestamp=event.timestamp,
                )
            )

            # Handle event in strategy
            self.strategy.on_event(event)

            # Get orders from strategy
            orders = self.strategy.get_orders()

            # Process each order
            for order in orders:
                # Send order to execution client (use current event price)
                current_price = (
                    event.close_price if order.symbol == event.symbol else None
                )
                fill = self.execution_client.process_orders(
                    order, current_bar=current_price
                )

                # Publish fill event (portfolio and strategy will react)
                self.event_bus.publish(FillEvent(fill=fill, timestamp=fill.timestamp))

            # Finalize trades by closing all open positions
        if finalize_trades:
            self._close_all_positions()

        if show_report:
            report = self.report_generator.generate(self.portfolio)
            print(self.report_generator.format_report(report))

    def _close_all_positions(self) -> None:
        """Close all open positions by creating and executing closing orders."""
        for symbol, position in list(self.portfolio.positions.items()):
            if position.quantity != 0:
                quantity = position.quantity
                # Create closing order
                closing_side = (
                    OrderSide.SELL if position.quantity > 0 else OrderSide.BUY
                )
                closing_order = Order(
                    symbol=symbol,
                    side=closing_side,
                    quantity=abs(position.quantity),
                )

                # Execute closing order
                fill = self.execution_client.process_orders(
                    closing_order, current_bar=None
                )

                # Publish fill event (portfolio and strategy will react)
                self.event_bus.publish(FillEvent(fill=fill, timestamp=fill.timestamp))

                logger.info(f"Closed position: {symbol} {quantity} @ {fill.price}")
