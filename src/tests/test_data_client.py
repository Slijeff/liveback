"""Tests for DataClient classes, including YFinanceDataClient."""

import unittest
from unittest.mock import Mock, patch
from datetime import datetime
import pandas as pd
from src.data.data_client import YFinanceDataClient, CSVDataClient
from src.types import EventType


class TestYFinanceDataClient(unittest.TestCase):
    """Test YFinanceDataClient class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create mock historical data (matching yfinance structure)
        # yfinance uses 'Date' as the index name for daily data
        self.mock_hist_data = pd.DataFrame(
            {
                "Open": [150.0, 151.0],
                "High": [150.5, 151.5],
                "Low": [149.8, 150.8],
                "Close": [150.25, 151.25],
                "Volume": [1000000, 1100000],
            },
            index=pd.DatetimeIndex(
                [datetime(2024, 1, 1), datetime(2024, 1, 2)], name="Date"
            ),
        )

    @patch("src.data.data_client.yf.Ticker")
    def test_initialization_with_period(self, mock_ticker_class):
        """Test initialization with period parameter."""
        mock_ticker = Mock()
        mock_ticker.history.return_value = self.mock_hist_data
        mock_ticker_class.return_value = mock_ticker

        client = YFinanceDataClient(symbols=["AAPL"], period="1y", interval="1d")

        self.assertEqual(client.symbols, ["AAPL"])
        self.assertEqual(client.period, "1y")
        self.assertEqual(client.interval, "1d")
        self.assertIsNone(client.start_date)

    @patch("src.data.data_client.yf.Ticker")
    def test_initialization_with_date_range(self, mock_ticker_class):
        """Test initialization with start_date and end_date."""
        mock_ticker = Mock()
        mock_ticker.history.return_value = self.mock_hist_data
        mock_ticker_class.return_value = mock_ticker

        start = datetime(2024, 1, 1)
        end = datetime(2024, 1, 31)

        client = YFinanceDataClient(
            symbols=["AAPL"], start_date=start, end_date=end, interval="1d"
        )

        self.assertEqual(client.symbols, ["AAPL"])
        self.assertEqual(client.start_date, start)
        self.assertEqual(client.end_date, end)
        self.assertIsNone(client.period)

    def test_initialization_no_symbols(self):
        """Test initialization fails with empty symbols list."""
        with self.assertRaises(ValueError) as context:
            YFinanceDataClient(symbols=[], period="1y")

        self.assertIn("at least one symbol", str(context.exception).lower())

    def test_initialization_no_period_or_start_date(self):
        """Test initialization fails without period or start_date."""
        with self.assertRaises(ValueError) as context:
            YFinanceDataClient(symbols=["AAPL"])

        self.assertIn("period", str(context.exception).lower())
        self.assertIn("start_date", str(context.exception).lower())

    @patch("src.data.data_client.yf.Ticker")
    def test_stream_single_symbol(self, mock_ticker_class):
        """Test streaming events for a single symbol."""
        mock_ticker = Mock()
        mock_ticker.history.return_value = self.mock_hist_data
        mock_ticker_class.return_value = mock_ticker

        client = YFinanceDataClient(symbols=["AAPL"], period="1y", interval="1d")

        events = list(client.stream())

        # Should have 2 events (one for each row)
        self.assertEqual(len(events), 2)

        # Check first event
        event1 = events[0]
        self.assertEqual(event1.symbol, "AAPL")
        self.assertEqual(event1.event_type, EventType.BAR)
        self.assertEqual(event1.open, 150.0)
        self.assertEqual(event1.high, 150.5)
        self.assertEqual(event1.low, 149.8)
        self.assertEqual(event1.close, 150.25)
        self.assertEqual(event1.volume, 1000000)
        self.assertEqual(event1.trade_price, 150.25)
        self.assertEqual(event1.timestamp, datetime(2024, 1, 1))

        # Check second event
        event2 = events[1]
        self.assertEqual(event2.symbol, "AAPL")
        self.assertEqual(event2.close, 151.25)
        self.assertEqual(event2.timestamp, datetime(2024, 1, 2))

    @patch("src.data.data_client.yf.Ticker")
    def test_stream_multiple_symbols(self, mock_ticker_class):
        """Test streaming events for multiple symbols."""
        # Create different data for each symbol
        aapl_data = pd.DataFrame(
            {
                "Open": [150.0],
                "High": [150.5],
                "Low": [149.8],
                "Close": [150.25],
                "Volume": [1000000],
            },
            index=pd.DatetimeIndex([datetime(2024, 1, 1)], name="Date"),
        )

        msft_data = pd.DataFrame(
            {
                "Open": [300.0],
                "High": [301.0],
                "Low": [299.5],
                "Close": [300.5],
                "Volume": [2000000],
            },
            index=pd.DatetimeIndex([datetime(2024, 1, 1)], name="Date"),
        )

        def ticker_side_effect(symbol):
            mock_ticker = Mock()
            if symbol == "AAPL":
                mock_ticker.history.return_value = aapl_data
            elif symbol == "MSFT":
                mock_ticker.history.return_value = msft_data
            return mock_ticker

        mock_ticker_class.side_effect = ticker_side_effect

        client = YFinanceDataClient(
            symbols=["AAPL", "MSFT"], period="1y", interval="1d"
        )

        events = list(client.stream())

        # Should have 2 events (one for each symbol)
        self.assertEqual(len(events), 2)

        # Events should be sorted by timestamp
        symbols = [e.symbol for e in events]
        self.assertIn("AAPL", symbols)
        self.assertIn("MSFT", symbols)

        # Find AAPL event
        aapl_event = next(e for e in events if e.symbol == "AAPL")
        self.assertEqual(aapl_event.close, 150.25)

        # Find MSFT event
        msft_event = next(e for e in events if e.symbol == "MSFT")
        self.assertEqual(msft_event.close, 300.5)

    @patch("src.data.data_client.yf.Ticker")
    def test_stream_data_caching(self, mock_ticker_class):
        """Test that data is cached and not fetched multiple times."""
        mock_ticker = Mock()
        mock_ticker.history.return_value = self.mock_hist_data
        mock_ticker_class.return_value = mock_ticker

        client = YFinanceDataClient(symbols=["AAPL"], period="1y", interval="1d")

        # Stream twice
        events1 = list(client.stream())
        events2 = list(client.stream())

        # Should have same number of events
        self.assertEqual(len(events1), len(events2))

        # Ticker.history should only be called once (cached on second call)
        self.assertEqual(mock_ticker.history.call_count, 1)

    @patch("src.data.data_client.yf.Ticker")
    def test_stream_chronological_order(self, mock_ticker_class):
        """Test that events are yielded in chronological order."""
        # Create data with different timestamps
        multi_day_data = pd.DataFrame(
            {
                "Open": [150.0, 151.0, 152.0],
                "High": [150.5, 151.5, 152.5],
                "Low": [149.8, 150.8, 151.8],
                "Close": [150.25, 151.25, 152.25],
                "Volume": [1000000, 1100000, 1200000],
            },
            index=pd.DatetimeIndex(
                [
                    datetime(2024, 1, 1),
                    datetime(2024, 1, 3),  # Out of order
                    datetime(2024, 1, 2),
                ],
                name="Date",
            ),
        )

        mock_ticker = Mock()
        mock_ticker.history.return_value = multi_day_data
        mock_ticker_class.return_value = mock_ticker

        client = YFinanceDataClient(symbols=["AAPL"], period="1y", interval="1d")

        events = list(client.stream())

        # Should be sorted chronologically
        timestamps = [e.timestamp for e in events]
        self.assertEqual(timestamps, sorted(timestamps))
        self.assertEqual(timestamps[0], datetime(2024, 1, 1))
        self.assertEqual(timestamps[1], datetime(2024, 1, 2))
        self.assertEqual(timestamps[2], datetime(2024, 1, 3))

    @patch("src.data.data_client.yf.Ticker")
    def test_stream_handles_missing_data(self, mock_ticker_class):
        """Test that client handles symbols with no data gracefully."""
        # First symbol has data, second has empty data
        aapl_data = pd.DataFrame(
            {
                "Open": [150.0],
                "High": [150.5],
                "Low": [149.8],
                "Close": [150.25],
                "Volume": [1000000],
            },
            index=pd.DatetimeIndex([datetime(2024, 1, 1)], name="Date"),
        )

        def ticker_side_effect(symbol):
            mock_ticker = Mock()
            if symbol == "AAPL":
                mock_ticker.history.return_value = aapl_data
            elif symbol == "INVALID":
                mock_ticker.history.return_value = pd.DataFrame()  # Empty
            return mock_ticker

        mock_ticker_class.side_effect = ticker_side_effect

        client = YFinanceDataClient(
            symbols=["AAPL", "INVALID"], period="1y", interval="1d"
        )

        events = list(client.stream())

        # Should only have events for AAPL
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].symbol, "AAPL")

    @patch("src.data.data_client.yf.Ticker")
    def test_stream_handles_exception(self, mock_ticker_class):
        """Test that client handles exceptions for individual symbols."""
        aapl_data = pd.DataFrame(
            {
                "Open": [150.0],
                "High": [150.5],
                "Low": [149.8],
                "Close": [150.25],
                "Volume": [1000000],
            },
            index=pd.DatetimeIndex([datetime(2024, 1, 1)]),
        )

        def ticker_side_effect(symbol):
            if symbol == "AAPL":
                mock_ticker = Mock()
                mock_ticker.history.return_value = aapl_data
                return mock_ticker
            elif symbol == "ERROR":
                raise Exception("Network error")

        mock_ticker_class.side_effect = ticker_side_effect

        client = YFinanceDataClient(
            symbols=["AAPL", "ERROR"], period="1y", interval="1d"
        )

        # Should not raise, but only return AAPL data
        events = list(client.stream())
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].symbol, "AAPL")

    @patch("src.data.data_client.yf.Ticker")
    def test_stream_all_symbols_fail(self, mock_ticker_class):
        """Test that ValueError is raised when all symbols fail."""
        mock_ticker = Mock()
        mock_ticker.history.return_value = pd.DataFrame()  # Empty
        mock_ticker_class.return_value = mock_ticker

        client = YFinanceDataClient(
            symbols=["INVALID1", "INVALID2"], period="1y", interval="1d"
        )

        with self.assertRaises(ValueError) as context:
            list(client.stream())

        self.assertIn("No data fetched", str(context.exception))

    def test_subscribe_raises_not_implemented(self):
        """Test that subscribe raises NotImplementedError."""
        client = YFinanceDataClient(symbols=["AAPL"], period="1y")

        callback = Mock()

        with self.assertRaises(NotImplementedError) as context:
            client.subscribe(["AAPL"], callback)

        self.assertIn("real-time", str(context.exception).lower())

    @patch("src.data.data_client.yf.Ticker")
    def test_period_takes_precedence_over_dates(self, mock_ticker_class):
        """Test that period parameter takes precedence over start_date/end_date."""
        mock_ticker = Mock()
        mock_ticker.history.return_value = self.mock_hist_data
        mock_ticker_class.return_value = mock_ticker

        client = YFinanceDataClient(
            symbols=["AAPL"],
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 12, 31),
            period="1y",  # Should use this instead
            interval="1d",
        )

        # Trigger data fetch
        list(client.stream())

        # Verify history was called with period, not dates
        mock_ticker.history.assert_called_once_with(period="1y", interval="1d")
        self.assertNotIn("start", str(mock_ticker.history.call_args))
        self.assertNotIn("end", str(mock_ticker.history.call_args))


class TestCSVDataClient(unittest.TestCase):
    """Test CSVDataClient class."""

    def test_initialization(self):
        """Test CSVDataClient initialization."""
        client = CSVDataClient(file_path="test.csv")
        self.assertEqual(client.file_path, "test.csv")

    def test_subscribe_not_implemented(self):
        """Test that CSVDataClient subscribe raises NotImplementedError."""
        client = CSVDataClient(file_path="test.csv")

        with self.assertRaises(NotImplementedError):
            client.subscribe(["AAPL"], lambda e: None)

    def test_stream_returns_empty(self):
        """Test that CSVDataClient stream returns empty (not yet implemented)."""
        client = CSVDataClient(file_path="test.csv")
        events = list(client.stream())
        self.assertEqual(len(events), 0)


if __name__ == "__main__":
    unittest.main()
