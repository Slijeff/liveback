"""Trading engines for backtest and live modes."""

from abc import ABC, abstractmethod
import sys
from typing import List, Optional
from src.data.data_client import DataClient
from src.execution.execution_client import ExecutionClient
from src.reporting.metrics import Metric
from src.reporting.report_generator import ReportGenerator
from src.strategy.strategy import Strategy
from src.portfolio import Portfolio
from src.risk_manager import RiskManager
from src.event_bus import EventBus
from src.types import (
    StrategyContext,
    Order,
    OrderSide,
    FillEvent,
    PriceUpdateEvent,
    EquityUpdateEvent,
)
from loguru import logger


class Engine(ABC):
    """Base engine interface."""

    def set_logging_level(self, level: str):
        logger.configure(handlers=[{"sink": sys.stdout, "level": level}])

    @abstractmethod
    def run(self) -> None:
        """Run the engine (blocking)."""
        pass


class BacktestEngine(Engine):
    """Event-driven backtest engine."""

    def __init__(
        self,
        data_client: DataClient,
        execution_client: ExecutionClient,
        strategy: Strategy,
        portfolio: Portfolio,
        metrics: List[Metric] = [],
        logging_level: str = "INFO",
        risk_manager: Optional[RiskManager] = None,
        event_bus: Optional[EventBus] = None,
    ):
        """Initialize backtest engine.

        Args:
            data_client: Data client providing historical data stream
            execution_client: Execution client (simulated broker)
            strategy: Trading strategy instance
            portfolio: Portfolio manager
            risk_manager: Optional risk manager for order validation
            event_bus: Event bus for event routing
        """
        self.data_client = data_client
        self.execution_client = execution_client
        self.strategy = strategy
        self.portfolio = portfolio
        self.risk_manager = risk_manager
        self.event_bus = event_bus if event_bus is not None else EventBus()
        self.report_generator = ReportGenerator()
        for metric in metrics:
            self.report_generator.add_metric(metric)
        self.set_logging_level(logging_level)
        self.current_timestamp = None

        # Initialize strategy
        context = StrategyContext(
            portfolio=portfolio,
            data_client=data_client,
            execution_client=execution_client,
        )
        self.strategy.initialize(context)

        # Register event subscribers
        self._register_event_subscribers()

    def _register_event_subscribers(self) -> None:
        """Register all event subscribers on the event bus."""
        # Portfolio subscribes to fill events
        self.event_bus.subscribe(FillEvent, self.portfolio.on_fill)

        # Portfolio subscribes to price update events
        self.event_bus.subscribe(PriceUpdateEvent, self.portfolio.on_price_update)

        # Strategy subscribes to fill events
        self.event_bus.subscribe(FillEvent, self.strategy.on_fill_event)

        # Risk manager subscribes to equity update events (if present)
        if self.risk_manager:
            self.event_bus.subscribe(
                EquityUpdateEvent, self.risk_manager.on_equity_update
            )

    def run(self, show_report: bool = True, finalize_trades: bool = False) -> None:
        """Run event-driven backtesting loop.

        Args:
            show_report: Whether to display the backtest report
            finalize_trades: If True, close all open positions at the end
        """
        # Event-driven backtesting loop
        for event in self.data_client.stream():
            self.current_timestamp = event.timestamp

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
                # Validate with risk manager if present
                if self.risk_manager and not self.risk_manager.validate_order(
                    order, self.portfolio
                ):
                    continue  # Skip invalid orders

                # Send order to execution client (use current event price)
                current_price = (
                    event.close_price if order.symbol == event.symbol else None
                )
                fill = self.execution_client.send_order(
                    order, current_price=current_price
                )

                # Publish fill event (portfolio and strategy will react)
                self.event_bus.publish(FillEvent(fill=fill, timestamp=fill.timestamp))

                # Publish equity update event (risk manager will react)
                self.event_bus.publish(
                    EquityUpdateEvent(
                        equity=self.portfolio.get_total_equity(),
                        timestamp=fill.timestamp,
                    )
                )

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
                fill = self.execution_client.send_order(
                    closing_order, current_price=None
                )

                # Publish fill event (portfolio and strategy will react)
                self.event_bus.publish(FillEvent(fill=fill, timestamp=fill.timestamp))

                # Publish equity update event
                self.event_bus.publish(
                    EquityUpdateEvent(
                        equity=self.portfolio.get_total_equity(),
                        timestamp=fill.timestamp,
                    )
                )

                logger.info(f"Closed position: {symbol} {quantity} @ {fill.price}")
