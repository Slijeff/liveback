"""Tests for Engine classes."""

import unittest
from src.engine import BacktestEngine, LiveEngine
from src.portfolio import Portfolio
from src.event_bus import EventBus
from src.strategy.strategy import Strategy
from src.types import StrategyContext, Event, Order, Fill


class MockDataClient:
    """Mock data client for testing."""

    def stream(self):
        """Yield mock events."""
        from datetime import datetime
        from src.types import EventType

        yield Event(
            timestamp=datetime.now(),
            symbol="AAPL",
            event_type=EventType.TICK,
            trade_price=150.0,
        )

    def subscribe(self, symbols, callback):
        """Mock subscribe (does nothing)."""
        pass


class MockExecutionClient:
    """Mock execution client for testing."""

    def send_order(self, order: Order) -> Fill:
        """Return mock fill."""
        from datetime import datetime
        from src.types import Fill

        return Fill(
            order_id="MOCK_1",
            timestamp=datetime.now(),
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            price=150.0,
        )

    def cancel_order(self, order_id):
        """Mock cancel (does nothing)."""
        pass


class MockStrategy(Strategy):
    """Mock strategy for testing."""

    def __init__(self):
        self.context = None
        self.orders = []
        self.events_received = []
        self.fills_received = []

    def initialize(self, context: StrategyContext):
        self.context = context

    def on_event(self, event: Event):
        self.events_received.append(event)

    def on_fill(self, fill: Fill):
        self.fills_received.append(fill)

    def create_order(self, order: Order) -> str:
        self.orders.append(order)
        return f"ORD_{len(self.orders)}"

    def get_orders(self):
        orders = self.orders.copy()
        self.orders.clear()  # Clear after retrieving
        return orders


class TestEngine(unittest.TestCase):
    """Test Engine classes."""

    def setUp(self):
        """Set up test fixtures."""
        self.data_client = MockDataClient()
        self.execution_client = MockExecutionClient()
        self.strategy = MockStrategy()
        self.portfolio = Portfolio(initial_cash=100000.0)
        self.risk_manager = None
        self.event_bus = EventBus()

    def test_backtest_engine_initialization(self):
        """Test BacktestEngine initialization."""
        engine = BacktestEngine(
            data_client=self.data_client,
            execution_client=self.execution_client,
            strategy=self.strategy,
            portfolio=self.portfolio,
            risk_manager=self.risk_manager,
            event_bus=self.event_bus,
        )

        self.assertIsNotNone(engine)
        self.assertIsNotNone(self.strategy.context)
        self.assertEqual(self.strategy.context.portfolio, self.portfolio)

    def test_live_engine_initialization(self):
        """Test LiveEngine initialization."""
        engine = LiveEngine(
            data_client=self.data_client,
            execution_client=self.execution_client,
            strategy=self.strategy,
            portfolio=self.portfolio,
            risk_manager=self.risk_manager,
            event_bus=self.event_bus,
            symbols=["AAPL", "MSFT"],
        )

        self.assertIsNotNone(engine)
        self.assertIsNotNone(self.strategy.context)


if __name__ == "__main__":
    unittest.main()
