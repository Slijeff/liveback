"""Core types and models for the liveback trading system."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from src.portfolio import Portfolio
    from src.data_client import DataClient
    from src.execution_client import ExecutionClient


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
class Bar:
    timestamp: datetime
    symbol: str

    volume: Optional[float] = None
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None

    def __repr__(self):
        return (
            f"Bar(symbol={self.symbol}, timestamp={self.timestamp}, "
            f"open={self.open}, high={self.high}, low={self.low}, close={self.close}, volume={self.volume})"
        )


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


# ============================================================================
# Domain Events for event bus
# ============================================================================


@dataclass
class DomainEvent:
    """Base class for domain events."""

    pass


@dataclass
class FillEvent(DomainEvent):
    """Event published when an order is filled.

    Subscribers should include:
    - Portfolio (to apply_fill)
    - Strategy (to on_fill)
    - RiskManager (to update peak equity)
    - ReportGenerator (to record fills)
    """

    fill: Fill
    timestamp: datetime


@dataclass
class PriceUpdateEvent(DomainEvent):
    """Event published when a price update occurs (from market data).

    Subscribers should include:
    - Portfolio (to update_unrealized_pnl and record_equity)
    - Risk tracking components
    """

    symbol: str
    price: float
    timestamp: datetime


@dataclass
class EquityUpdateEvent(DomainEvent):
    """Event published when portfolio equity changes.

    Subscribers should include:
    - RiskManager (to update_peak_equity)
    - Monitoring/alerting systems
    """

    equity: float
    timestamp: datetime
