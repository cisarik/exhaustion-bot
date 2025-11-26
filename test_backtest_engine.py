import unittest
from backtest_engine import BacktestEngine

class TestBacktestEngine(unittest.TestCase):
    def setUp(self):
        self.engine = BacktestEngine(initial_capital=1000.0)
        
    def test_initial_state(self):
        """Test that the engine initializes correctly."""
        self.assertEqual(self.engine.capital, 1000.0)
        self.assertEqual(self.engine.balance_usdc, 1000.0)
        self.assertEqual(self.engine.balance_ada, 0.0)
        self.assertEqual(len(self.engine.trades), 0)
        
    def test_load_data_mock(self):
        """Test loading mock data."""
        # Create a dummy list of candles (close prices)
        data = [1.0, 1.1, 1.05, 1.0]
        self.engine.load_data(data)
        self.assertEqual(len(self.engine.data), 4)
        
    def test_execution_logic(self):
        """Test that a trade is executed and PnL is calculated."""
        # Mock a scenario where ExhaustionDetector WOULD trigger
        # We need enough data for the detector.
        prices = [2.0]
        for _ in range(40):
            prices.append(prices[-1] * 0.99) # Drop by 1% each time
            
        self.engine.load_data(prices)
        self.engine.run()
        
        # We expect at least one trade (SL hit probably)
        self.assertGreater(len(self.engine.trades), 0)
        # The trade type in backtest_engine is 'LONG_CLOSE' or 'SHORT_CLOSE'
        trade = self.engine.trades[0]
        self.assertIn('CLOSE', trade['type'])
        # Verify PnL keys exist
        self.assertIn('pnl', trade)
        self.assertIn('pnl_pct', trade)

if __name__ == '__main__':
    unittest.main()
