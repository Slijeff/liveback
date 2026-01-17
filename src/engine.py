from abc import ABC, abstractmethod

class Engine(ABC):
    @abstractmethod
    def run(self):
        pass

class BacktestEngine(Engine):
    def __init__(self, data_client, execution_client, strategy, portfolio, risk_manager, event_bus):
        self.data_client = data_client
        self.execution_client = execution_client
        self.strategy = strategy
        self.portfolio = portfolio
        self.risk_manager = risk_manager
        self.event_bus = event_bus

    def run(self):
        # Event-driven backtesting loop
        for event in self.data_client.stream():
            self.event_bus.publish(event)
            self.strategy.on_event(event)
            orders = self.strategy.get_orders()
            for order in orders:
                fill = self.execution_client.send_order(order)
                self.portfolio.apply_fill(fill)
                self.strategy.on_fill(fill)

class LiveEngine(Engine):
    def __init__(self, data_client, execution_client, strategy, portfolio, risk_manager, event_bus):
        self.data_client = data_client
        self.execution_client = execution_client
        self.strategy = strategy
        self.portfolio = portfolio
        self.risk_manager = risk_manager
        self.event_bus = event_bus

    def run(self):
        # Real-time trading loop
        self.data_client.subscribe(self.strategy.on_event)
        while True:
            event = self.event_bus.get_next_event()
            self.strategy.on_event(event)
            orders = self.strategy.get_orders()
            for order in orders:
                self.execution_client.send_order(order)