from abc import ABC, abstractmethod

class DataClient(ABC):
    @abstractmethod
    def subscribe(self, symbols, callback):
        pass

    @abstractmethod
    def stream(self):
        pass

class CSVDataClient(DataClient):
    def __init__(self, file_path):
        self.file_path = file_path

    def subscribe(self, symbols, callback):
        # Implementation for live data subscription
        pass

    def stream(self):
        # Implementation for backtest data streaming
        pass