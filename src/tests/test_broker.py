"""Unit tests for broker order processing."""

import unittest
from datetime import datetime

from src.broker import BacktestSimulationBroker
from src.types import Bar, OrderType


def make_bar(
    symbol: str, open_price: float, high: float, low: float, close: float
) -> Bar:
    return Bar(
        timestamp=datetime(2026, 1, 1),
        symbol=symbol,
        open=open_price,
        high=high,
        low=low,
        close=close,
        volume=None,
    )


class TestBacktestSimulationBroker(unittest.TestCase):
    def test_market_order_fills_on_open(self) -> None:
        broker = BacktestSimulationBroker(initial_cash=100000.0)
        order = broker.new_order("AAPL", 10, limit=None, stop=None)
        self.assertEqual(order.order_type, OrderType.MARKET)

        bar = make_bar("AAPL", open_price=100.0, high=105.0, low=95.0, close=102.0)
        broker.process_orders({"AAPL": bar})

        self.assertEqual(len(broker.orders), 0)
        self.assertEqual(len(broker.trades), 1)
        self.assertEqual(broker.trades[0].price, 100.0)
        self.assertEqual(broker.positions["AAPL"].quantity, 10)
        self.assertEqual(broker.positions["AAPL"].avg_price, 100.0)

    def test_limit_buy_fills_at_limit_or_open(self) -> None:
        broker = BacktestSimulationBroker(initial_cash=100000.0)
        order = broker.new_order("AAPL", 10, limit=100.0, stop=None)
        self.assertEqual(order.order_type, OrderType.LIMIT)

        bar = make_bar("AAPL", open_price=105.0, high=106.0, low=99.0, close=104.0)
        broker.process_orders({"AAPL": bar})

        self.assertEqual(len(broker.orders), 0)
        self.assertEqual(len(broker.trades), 1)
        self.assertEqual(broker.trades[0].price, 100.0)
        self.assertEqual(broker.positions["AAPL"].quantity, 10)
        self.assertEqual(broker.positions["AAPL"].avg_price, 100.0)

    def test_stop_sell_triggers_at_stop_or_open(self) -> None:
        broker = BacktestSimulationBroker(initial_cash=100000.0)
        order = broker.new_order("AAPL", -5, limit=None, stop=98.0)
        self.assertEqual(order.order_type, OrderType.STOP)

        bar = make_bar("AAPL", open_price=100.0, high=101.0, low=95.0, close=97.0)
        broker.process_orders({"AAPL": bar})

        self.assertEqual(len(broker.orders), 0)
        self.assertEqual(len(broker.trades), 1)
        self.assertEqual(broker.trades[0].price, 98.0)
        self.assertEqual(broker.positions["AAPL"].quantity, -5)
        self.assertEqual(broker.positions["AAPL"].avg_price, 98.0)

    def test_limit_order_not_filled_keeps_order(self) -> None:
        broker = BacktestSimulationBroker(initial_cash=100000.0)
        broker.new_order("AAPL", -5, limit=105.0, stop=None)

        bar = make_bar("AAPL", open_price=100.0, high=101.0, low=99.0, close=100.0)
        broker.process_orders({"AAPL": bar})

        self.assertEqual(len(broker.orders), 1)
        self.assertEqual(len(broker.trades), 0)

    def test_close_position_realizes_pnl(self) -> None:
        broker = BacktestSimulationBroker(initial_cash=100000.0)
        broker.new_order("AAPL", 10, limit=None, stop=None)
        first_bar = make_bar(
            "AAPL", open_price=100.0, high=101.0, low=99.0, close=100.0
        )
        broker.process_orders({"AAPL": first_bar})

        broker.new_order("AAPL", -5, limit=None, stop=None)
        second_bar = make_bar(
            "AAPL", open_price=110.0, high=111.0, low=109.0, close=110.0
        )
        broker.process_orders({"AAPL": second_bar})

        self.assertEqual(broker.positions["AAPL"].quantity, 5)
        self.assertEqual(broker.positions["AAPL"].avg_price, 100.0)
        self.assertEqual(len(broker.closed_trades), 1)
        self.assertEqual(broker.closed_trades[0].pnl, 50.0)

    def test_slippage_adjusts_fill_price_and_records_cost(self) -> None:
        broker = BacktestSimulationBroker(initial_cash=100000.0, slippage=0.5)
        broker.new_order("AAPL", 10, limit=None, stop=None)
        bar = make_bar("AAPL", open_price=100.0, high=101.0, low=99.0, close=100.0)
        broker.process_orders({"AAPL": bar})

        self.assertEqual(len(broker.trades), 1)
        self.assertEqual(broker.trades[0].price, 100.5)
        self.assertEqual(broker.trades[0].slippage, 5.0)

        broker.new_order("AAPL", -5, limit=None, stop=None)
        bar = make_bar("AAPL", open_price=100.0, high=101.0, low=99.0, close=100.0)
        broker.process_orders({"AAPL": bar})

        self.assertEqual(len(broker.trades), 2)
        self.assertEqual(broker.trades[1].price, 99.5)
        self.assertEqual(broker.trades[1].slippage, 2.5)

    def test_commission_reduces_pnl_and_records_cost(self) -> None:
        broker = BacktestSimulationBroker(initial_cash=100000.0, commission=2.5)
        broker.new_order("AAPL", 10, limit=None, stop=None)
        first_bar = make_bar(
            "AAPL", open_price=100.0, high=101.0, low=99.0, close=100.0
        )
        broker.process_orders({"AAPL": first_bar})

        broker.new_order("AAPL", -10, limit=None, stop=None)
        second_bar = make_bar(
            "AAPL", open_price=110.0, high=111.0, low=109.0, close=110.0
        )
        broker.process_orders({"AAPL": second_bar})

        self.assertEqual(len(broker.closed_trades), 2)
        self.assertEqual(broker.closed_trades[-1].pnl, 97.5)
        self.assertEqual(broker.closed_trades[-1].commission, 2.5)


if __name__ == "__main__":
    unittest.main()
