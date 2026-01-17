"""Strategy interface for implementing trading strategies."""

from abc import ABC, abstractmethod
from typing import List, Optional
from src.types import StrategyContext, Event, Fill, Order, OrderId


class Strategy(ABC):
    """Base class for trading strategies. Must be mode-agnostic (no if live/backtest)."""
    
    @abstractmethod
    def initialize(self, context: StrategyContext) -> None:
        """Initialize the strategy with context.
        
        Args:
            context: Strategy context containing portfolio, clients, and config
        """
        pass

    @abstractmethod
    def on_event(self, event: Event) -> None:
        """Handle a market data event.
        
        Args:
            event: Market data event (bar/tick)
        """
        pass

    @abstractmethod
    def on_fill(self, fill: Fill) -> None:
        """Handle a fill event from order execution.
        
        Args:
            fill: Fill event representing an executed order
        """
        pass

    @abstractmethod
    def create_order(self, order: Order) -> OrderId:
        """Create an order (validates and returns order ID or raises).
        
        Args:
            order: Order to create
            
        Returns:
            OrderId: Unique identifier for the created order
            
        Raises:
            Exception: If order is invalid or cannot be created
        """
        pass

    @abstractmethod
    def get_orders(self) -> List[Order]:
        """Get pending orders to be executed (used by engine).
        
        Returns:
            List of orders that should be sent to execution client
        """
        pass