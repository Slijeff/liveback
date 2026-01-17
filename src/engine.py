"""Trading engines for backtest and live modes."""

from abc import ABC, abstractmethod
from typing import List, Optional
from src.data.data_client import DataClient
from src.execution.execution_client import ExecutionClient
from src.strategy.strategy import Strategy
from src.portfolio import Portfolio
from src.risk_manager import RiskManager
from src.event_bus import EventBus
from src.types import StrategyContext, Event, Order


class Engine(ABC):
    """Base engine interface."""
    
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
        risk_manager: Optional[RiskManager],
        event_bus: EventBus
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
        self.event_bus = event_bus
        
        # Initialize strategy
        context = StrategyContext(
            portfolio=portfolio,
            data_client=data_client,
            execution_client=execution_client
        )
        self.strategy.initialize(context)

    def run(self) -> None:
        """Run event-driven backtesting loop."""
        # Event-driven backtesting loop
        for event in self.data_client.stream():
            # Publish event to event bus
            self.event_bus.publish(event)
            
            # Update unrealized PnL if we have price data
            price = event.close_price  # Works for both bars (close) and ticks (trade_price)
            if price is not None:
                current_prices = {event.symbol: price}
                self.portfolio.update_unrealized_pnl(current_prices)
                self.portfolio.record_equity()
            
            # Handle event in strategy
            self.strategy.on_event(event)
            
            # Get orders from strategy
            orders = self.strategy.get_orders()
            
            # Process each order
            for order in orders:
                # Validate with risk manager if present
                if self.risk_manager and not self.risk_manager.validate_order(order, self.portfolio):
                    continue  # Skip invalid orders
                
                # Send order to execution client
                fill = self.execution_client.send_order(order)
                
                # Apply fill to portfolio
                self.portfolio.apply_fill(fill)
                
                # Notify strategy of fill
                self.strategy.on_fill(fill)
                
                # Update risk manager peak equity
                if self.risk_manager:
                    self.risk_manager.update_peak_equity(self.portfolio.get_total_equity())


class LiveEngine(Engine):
    """Live trading engine for real-time execution."""
    
    def __init__(
        self,
        data_client: DataClient,
        execution_client: ExecutionClient,
        strategy: Strategy,
        portfolio: Portfolio,
        risk_manager: Optional[RiskManager],
        event_bus: EventBus,
        symbols: List[str]
    ):
        """Initialize live engine.
        
        Args:
            data_client: Data client providing real-time data
            execution_client: Execution client (real broker)
            strategy: Trading strategy instance
            portfolio: Portfolio manager
            risk_manager: Optional risk manager for order validation
            event_bus: Event bus for event routing
            symbols: List of symbols to subscribe to
        """
        self.data_client = data_client
        self.execution_client = execution_client
        self.strategy = strategy
        self.portfolio = portfolio
        self.risk_manager = risk_manager
        self.event_bus = event_bus
        self.symbols = symbols
        
        # Initialize strategy
        context = StrategyContext(
            portfolio=portfolio,
            data_client=data_client,
            execution_client=execution_client
        )
        self.strategy.initialize(context)

    def run(self) -> None:
        """Run real-time trading loop."""
        # Subscribe to real-time data feed
        self.data_client.subscribe(self.symbols, self.event_bus.publish)
        
        # Real-time trading loop
        while True:
            # Get next event from event bus
            event = self.event_bus.get_next_event()
            if event is None:
                continue
            
            # Update unrealized PnL if we have price data
            if event.trade_price:
                current_prices = {event.symbol: event.trade_price}
                self.portfolio.update_unrealized_pnl(current_prices)
            
            # Handle event in strategy
            self.strategy.on_event(event)
            
            # Get orders from strategy
            orders = self.strategy.get_orders()
            
            # Process each order
            for order in orders:
                # Validate with risk manager if present
                if self.risk_manager and not self.risk_manager.validate_order(order, self.portfolio):
                    continue  # Skip invalid orders
                
                # Send order to execution client (live mode: async handling would be better)
                fill = self.execution_client.send_order(order)
                
                # Apply fill to portfolio
                self.portfolio.apply_fill(fill)
                
                # Notify strategy of fill
                self.strategy.on_fill(fill)
                
                # Update risk manager peak equity
                if self.risk_manager:
                    self.risk_manager.update_peak_equity(self.portfolio.get_total_equity())