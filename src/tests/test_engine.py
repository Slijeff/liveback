import unittest
from src.engine import BacktestEngine, LiveEngine

class TestEngine(unittest.TestCase):
    def test_backtest_engine_initialization(self):
        # Test initialization of BacktestEngine
        self.assertIsNotNone(BacktestEngine(None, None, None, None, None, None))

    def test_live_engine_initialization(self):
        # Test initialization of LiveEngine
        self.assertIsNotNone(LiveEngine(None, None, None, None, None, None))

if __name__ == '__main__':
    unittest.main()