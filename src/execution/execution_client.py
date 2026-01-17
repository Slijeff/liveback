from abc import ABC, abstractmethod

class ExecutionClient(ABC):
    @abstractmethod
    def send_order(self, order):
        pass

    @abstractmethod
    def cancel_order(self, order_id):
        pass

class BrokerSim(ExecutionClient):
    def send_order(self, order):
        # Simulate order execution
        pass

    def cancel_order(self, order_id):
        # Simulate order cancellation
        pass