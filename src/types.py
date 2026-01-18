"""Core types and models for the liveback trading system."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from src.portfolio import Portfolio
    from src.data.data_client import DataClient
    from src.execution.execution_client import ExecutionClient


class OrderSide(Enum):
    """Order side enumeration."""

    BUY = "BUY"
    SELL = "SELL"


class OrderType(Enum):
    """Order type enumeration."""

    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"


class EventType(Enum):
    """Event type enumeration for distinguishing bars vs ticks."""

    TICK = "TICK"  # Single trade or quote update
    BAR = "BAR"  # Aggregated OHLCV bar


@dataclass
class Event:
    """Base event type representing market data (bars or ticks).

    Usage:
    - For TICK events: use trade_price (and optionally bid/ask for quotes)
    - For BAR events: use open, high, low, close (close can also use trade_price)

    Examples:
        # Tick event (single trade)
        Event(timestamp=ts, symbol="AAPL", event_type=EventType.TICK, trade_price=150.25, volume=100)

        # Bar event (OHLCV)
        Event(timestamp=ts, symbol="AAPL", event_type=EventType.BAR,
              open=150.0, high=150.5, low=149.8, close=150.25, volume=1000)
    """

    timestamp: datetime
    symbol: str
    event_type: EventType = EventType.TICK

    # For ticks: trade_price represents the trade price
    # For bars: close price (can use trade_price or close field)
    trade_price: Optional[float] = None
    volume: Optional[float] = None

    # Quote data (bid/ask) - useful for ticks or bar context
    bid: Optional[float] = None
    ask: Optional[float] = None

    # OHLC fields for bars (only populated when event_type == EventType.BAR)
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None

    @property
    def close_price(self) -> Optional[float]:
        """Get close price (for bars) or trade price (for ticks)."""
        if self.event_type == EventType.BAR:
            return self.close if self.close is not None else self.trade_price
        return self.trade_price

    def is_bar(self) -> bool:
        """Check if this is a bar event."""
        return self.event_type == EventType.BAR

    def is_tick(self) -> bool:
        """Check if this is a tick event."""
        return self.event_type == EventType.TICK


@dataclass
class Order:
    """Order representation."""

    symbol: str
    side: OrderSide
    quantity: float
    order_type: OrderType = OrderType.MARKET
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None


@dataclass
class Fill:
    """Fill event representing an executed order."""

    order_id: str
    timestamp: datetime
    symbol: str
    side: OrderSide
    quantity: float
    price: float
    slippage: float = 0.0
    commission: float = 0.0


# Type alias for Order ID
OrderId = str


@dataclass
class StrategyContext:
    """Context passed to strategy during initialization."""

    portfolio: Portfolio
    data_client: DataClient
    execution_client: ExecutionClient
    config: dict = None


@dataclass
class Position:
    """Represents a position in a single symbol."""

    symbol: str
    quantity: float = 0.0
    avg_price: float = 0.0
    unrealized_pnl: float = 0.0


@dataclass
class Trade:
    """Represents a completed trade."""

    timestamp: datetime
    symbol: str
    side: str
    quantity: float
    price: float
    slippage: float
    commission: float
    pnl: float
