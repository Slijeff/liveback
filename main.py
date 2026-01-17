from src.data.data_client import YFinanceDataClient
from src.execution.execution_client import BrokerSim
from src.strategy.noop_strategy import NoOpStrategy
from src.portfolio import Portfolio
from src.engine import BacktestEngine
import pandas as pd


def main():
    """Run a backtest with a do-nothing strategy to demonstrate the engine."""

    # Set up data client for historical data
    symbols = ["NVDA"]
    start_date = pd.to_datetime("2025-12-01")
    end_date = pd.to_datetime("2026-01-01")
    data_client = YFinanceDataClient(symbols, start_date, end_date)

    # Set up execution client (simulated broker for backtesting)
    execution_client = BrokerSim()

    # Set up portfolio with initial capital
    portfolio = Portfolio(initial_cash=100000.0)

    # Set up strategy (does nothing, just observes)
    strategy = NoOpStrategy()

    # Set up backtest engine (no risk manager for this example)
    engine = BacktestEngine(
        data_client=data_client,
        execution_client=execution_client,
        strategy=strategy,
        portfolio=portfolio,
    )

    print("=" * 60)
    print("Starting backtest with NoOpStrategy")
    print(f"Symbols: {symbols}")
    print(f"Period: {start_date.date()} to {end_date.date()}")
    print(f"Initial capital: ${portfolio.initial_cash:,.2f}")
    print("=" * 60)
    print()

    # Run the backtest
    engine.run()

    # Print results
    print()
    print("=" * 60)
    print("Backtest complete!")
    print("=" * 60)
    print(f"Final equity: ${portfolio.get_total_equity():,.2f}")
    print(f"Cash: ${portfolio.cash:,.2f}")
    print(f"Total trades: {len(portfolio.trades)}")
    print()
    print("Positions:")
    for symbol, position in portfolio.positions.items():
        if position.quantity != 0:
            print(
                f"  {symbol}: {position.quantity:.2f} shares @ ${position.avg_price:.2f}"
            )
            print(f"    Realized PnL: ${position.realized_pnl:.2f}")
            print(f"    Unrealized PnL: ${position.unrealized_pnl:.2f}")
    print()
    print(f"Equity curve points recorded: {len(portfolio.equity_curve)}")


if __name__ == "__main__":
    main()
