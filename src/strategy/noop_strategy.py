"""A buy-and-hold strategy that buys once at the start."""

from typing import List
from src.strategy.strategy import Strategy
from src.types import StrategyContext, Event, Fill, Order, OrderId, OrderSide, OrderType


class NoOpStrategy(Strategy):
    """A buy-and-hold strategy that buys once at the start."""
    
    def __init__(self, cash_percentage: float = 0.95):
        """Initialize the buy-and-hold strategy.
        
        Args:
            cash_percentage: Percentage of available cash to use for initial buy (default 0.95)
        """
        self.context: StrategyContext = None
        self.pending_orders: List[Order] = []
        self._order_id_counter = 0
        self.has_placed_initial_order = False
        self.cash_percentage = cash_percentage
    
    def initialize(self, context: StrategyContext) -> None:
        """Initialize the strategy with context.
        
        Args:
            context: Strategy context containing portfolio, clients, and config
        """
        self.context = context
        print(f"BuyAndHoldStrategy initialized with ${context.portfolio.initial_cash:,.2f} initial cash")
        print(f"Will use {self.cash_percentage*100:.1f}% of cash for initial buy")
    
    def on_event(self, event: Event) -> None:
        """Handle a market data event - places buy order on first event.
        
        Args:
            event: Market data event (bar/tick)
        """
        price = event.close_price or event.trade_price
        print(f"[Strategy] Received {event.event_type.value} for {event.symbol}: ${price:.2f}")
        
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
                    order_type=OrderType.MARKET
                )
                self.pending_orders.append(order)
                self.has_placed_initial_order = True
                print(f"[Strategy] Placing initial buy order: {quantity} shares of {event.symbol} @ ~${price:.2f}")
            else:
                print(f"[Strategy] Not enough cash to buy even 1 share (need ${price:.2f}, have ${available_cash:.2f})")
    
    def on_fill(self, fill: Fill) -> None:
        """Handle a fill event from order execution (does nothing).
        
        Args:
            fill: Fill event representing an executed order
        """
        print(f"[Strategy] Received fill: {fill.side.value} {fill.quantity} {fill.symbol} @ ${fill.price:.2f}")
    
    def create_order(self, order: Order) -> OrderId:
        """Create an order (returns order ID but doesn't actually queue it).
        
        Args:
            order: Order to create
            
        Returns:
            OrderId: Unique identifier for the created order
        """
        self._order_id_counter += 1
        order_id = f"NOOP_{self._order_id_counter}"
        print(f"[Strategy] Order created (but not queued): {order_id}")
        return order_id
    
    def get_orders(self) -> List[Order]:
        """Get pending orders (returns orders once, then clears them).
        
        Returns:
            List of pending orders (only returns initial buy order once)
        """
        # Return pending orders and clear them (so they're only sent once)
        orders = self.pending_orders.copy()
        self.pending_orders.clear()
        return orders
