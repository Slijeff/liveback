"""Data client interfaces for historical and live market data."""

from abc import ABC, abstractmethod
from typing import List, Iterator, Optional, Dict
from datetime import datetime
import yfinance as yf
import pandas as pd
from src.types import Bar, MultiBar
from loguru import logger


class DataClient(ABC):
    """Abstract interface for data clients (backtest and live modes)."""

    @abstractmethod
    def stream(self) -> Iterator[Dict[str, Bar]]:
        """Stream historical events in chronological order (backtest mode).

        Yields:
            Dict[str, Bar]: Symbol to bar data in time order
        """
        pass


class YFinanceDataClient(DataClient):
    """Data client that fetches historical data from Yahoo Finance using yfinance."""

    def __init__(
        self,
        symbols: List[str],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        period: Optional[str] = None,
        interval: str = "1d",
    ):
        """Initialize YFinance data client.

        Args:
            symbols: List of stock symbols to fetch data for
            start_date: Start date for historical data (optional if period is provided)
            end_date: End date for historical data (optional, defaults to today)
            period: Period string (e.g., "1y", "6mo", "3mo", "1mo", "5d", "1d")
                    If provided, start_date and end_date are ignored
            interval: Data interval ("1m", "2m", "5m", "15m", "30m", "60m", "90m",
                     "1h", "1d", "5d", "1wk", "1mo", "3mo"). Defaults to "1d"

        Note:
            Either (start_date, end_date) or period must be provided.
        """
        if not symbols:
            raise ValueError("At least one symbol must be provided")

        self.symbols = symbols
        self.start_date = start_date
        self.end_date = end_date or datetime.now()
        self.period = period
        self.interval = interval

        self.n_bars: int = None
        self.current_bar: int = None

        # Validate that either period or start_date is provided
        if not period and not start_date:
            raise ValueError("Either 'period' or 'start_date' must be provided")

        # Store fetched data
        self._data: Dict[pd.DataFrame] = None

    def _fetch_data(self) -> Dict[pd.DataFrame]:
        """Fetch historical data from Yahoo Finance.

        Returns:
            DataFrame with Datetime, Symbol, and OHLCV columns
        """
        if self._data is not None:
            return self._data

        all_data = {}
        for symbol in self.symbols:
            logger.debug(f"Fetching data for {symbol}")
            try:
                ticker = yf.Ticker(symbol)

                if self.period:
                    hist = ticker.history(period=self.period, interval=self.interval)
                else:
                    hist = ticker.history(
                        start=self.start_date, end=self.end_date, interval=self.interval
                    )

                if hist.empty:
                    continue

                # Reset index to make Datetime a column
                hist = hist.reset_index()

                # Rename the datetime column to 'Datetime' for consistency
                # yfinance uses 'Date' for daily data, but we want 'Datetime'
                # Check common datetime column names and rename if needed
                datetime_cols = ["Date", "Datetime"]
                for col in datetime_cols:
                    if col in hist.columns and col != "Datetime":
                        hist = hist.rename(columns={col: "Datetime"})
                        break
                # If no named datetime column found, assume first column is datetime
                if "Datetime" not in hist.columns:
                    hist = hist.rename(columns={hist.columns[0]: "Datetime"})

                # Add symbol column
                all_data[symbol] = hist
                if not self.n_bars:
                    self.n_bars = len(hist)
                    logger.debug(f"Fetched {self.n_bars} bars for {symbol}")
                else:
                    assert self.n_bars == hist.size, (
                        "Inconsistent number of bars fetched"
                    )
            except Exception as e:
                # Log warning but continue with other symbols
                print(f"Warning: Failed to fetch data for {symbol}: {e}")
                continue

        if not all_data:
            raise ValueError("No data fetched for any symbols")

        self._data = all_data
        return self._data

    def stream(self) -> Iterator[MultiBar]:
        data = self._fetch_data()
        for i in range(self.n_bars):
            self.current_bar = i
            bars = {}
            for symbol, df in data.items():
                row = df.iloc[i]
                # Convert pandas Timestamp to datetime
                timestamp = row["Datetime"]
                if isinstance(timestamp, pd.Timestamp):
                    timestamp = timestamp.to_pydatetime()

                # Create BAR event with OHLCV data
                event = Bar(
                    timestamp=timestamp,
                    symbol=symbol,
                    open=float(row["Open"]) if pd.notna(row["Open"]) else None,
                    high=float(row["High"]) if pd.notna(row["High"]) else None,
                    low=float(row["Low"]) if pd.notna(row["Low"]) else None,
                    close=float(row["Close"]) if pd.notna(row["Close"]) else None,
                    volume=float(row["Volume"]) if pd.notna(row["Volume"]) else None,
                )
                bars[symbol] = event
            yield bars
