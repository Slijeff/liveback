"""Data client interfaces for historical and live market data."""

from abc import ABC, abstractmethod
from typing import List, Callable, Iterator, Optional
from datetime import datetime
import yfinance as yf
import pandas as pd
from src.types import Event, EventType


class DataClient(ABC):
    """Abstract interface for data clients (backtest and live modes)."""

    @abstractmethod
    def subscribe(self, symbols: List[str], callback: Callable[[Event], None]) -> None:
        """Subscribe to real-time data for given symbols (live mode).

        Args:
            symbols: List of symbols to subscribe to
            callback: Function to call when new events arrive
        """
        pass

    @abstractmethod
    def stream(self) -> Iterator[Event]:
        """Stream historical events in chronological order (backtest mode).

        Yields:
            Event: Market data events in time order
        """
        pass


class CSVDataClient(DataClient):
    """Data client that reads historical data from CSV files."""

    def __init__(self, file_path: str):
        """Initialize CSV data client.

        Args:
            file_path: Path to CSV file containing historical data
        """
        self.file_path = file_path

    def subscribe(self, symbols: List[str], callback: Callable[[Event], None]) -> None:
        """Subscribe to live data (not supported for CSV client)."""
        raise NotImplementedError("CSV client does not support live subscription")

    def stream(self) -> Iterator[Event]:
        """Stream historical events from CSV file.

        Yields:
            Event: Market data events from the CSV file
        """
        # TODO: Implement CSV parsing and event generation
        # Should parse CSV and yield Event objects with proper timestamps
        yield from []


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

        # Validate that either period or start_date is provided
        if not period and not start_date:
            raise ValueError("Either 'period' or 'start_date' must be provided")

        # Store fetched data
        self._data: Optional[pd.DataFrame] = None

    def _fetch_data(self) -> pd.DataFrame:
        """Fetch historical data from Yahoo Finance.

        Returns:
            DataFrame with Datetime, Symbol, and OHLCV columns
        """
        if self._data is not None:
            return self._data

        all_data = []
        for symbol in self.symbols:
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
                hist["Symbol"] = symbol
                all_data.append(hist)
            except Exception as e:
                # Log warning but continue with other symbols
                print(f"Warning: Failed to fetch data for {symbol}: {e}")
                continue

        if not all_data:
            raise ValueError("No data fetched for any symbols")

        # Combine all dataframes
        combined = pd.concat(all_data, ignore_index=True)

        # Sort by timestamp and symbol for chronological order
        combined = combined.sort_values(["Datetime", "Symbol"]).reset_index(drop=True)

        self._data = combined
        return self._data

    def stream(self) -> Iterator[Event]:
        """Stream historical events in chronological order (backtest mode).

        Yields:
            Event: Market data events (BAR type) in chronological order
        """
        data = self._fetch_data()

        for _, row in data.iterrows():
            # Convert pandas Timestamp to datetime
            timestamp = row["Datetime"]
            if isinstance(timestamp, pd.Timestamp):
                timestamp = timestamp.to_pydatetime()

            # Create BAR event with OHLCV data
            event = Event(
                timestamp=timestamp,
                symbol=row["Symbol"],
                event_type=EventType.BAR,
                open=float(row["Open"]) if pd.notna(row["Open"]) else None,
                high=float(row["High"]) if pd.notna(row["High"]) else None,
                low=float(row["Low"]) if pd.notna(row["Low"]) else None,
                close=float(row["Close"]) if pd.notna(row["Close"]) else None,
                volume=float(row["Volume"]) if pd.notna(row["Volume"]) else None,
                trade_price=float(row["Close"]) if pd.notna(row["Close"]) else None,
            )

            yield event

    def subscribe(self, symbols: List[str], callback: Callable[[Event], None]) -> None:
        """Subscribe to real-time data (not fully supported by yfinance).

        Note:
            yfinance does not provide real-time streaming data. This method
            will raise NotImplementedError. For live trading, consider using
            a different data provider that supports WebSocket streaming.

        Args:
            symbols: List of symbols to subscribe to
            callback: Function to call when new events arrive

        Raises:
            NotImplementedError: yfinance does not support real-time streaming
        """
        raise NotImplementedError(
            "yfinance does not support real-time data streaming. "
            "Use stream() for historical backtesting, or use a different "
            "data provider for live trading."
        )
