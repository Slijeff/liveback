"""Data client interfaces for historical and live market data."""

from abc import ABC, abstractmethod
from typing import List, Callable, Iterator, Optional
from src.types import Event


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