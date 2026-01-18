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
        logging_level="DEBUG",
    )
    engine.run(finalize_trades=True)


if __name__ == "__main__":
    main()
