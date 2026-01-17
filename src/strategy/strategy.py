from abc import ABC, abstractmethod

class Strategy(ABC):
    @abstractmethod
    def initialize(self, context):
        pass

    @abstractmethod
    def on_event(self, event):
        pass

    @abstractmethod
    def on_fill(self, fill):
        pass

    @abstractmethod
    def get_orders(self):
        pass