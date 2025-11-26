import unittest
from backtest_engine import BacktestEngine
from exhaustion_detector import ExhaustionDetector

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
        """Test that a trade is executed when a signal is detected."""
        # Mock a scenario where ExhaustionDetector WOULD trigger
        # We need enough data for the detector.
        # The new logic requires 14 consecutive counts for Level 3.
        # Count starts at index 4. So we need index 4 + 13 = 17 (18th candle) at minimum.
        # Let's generate 30 candles of dropping prices to be safe.
        
        prices = [2.0]
        for _ in range(30):
            prices.append(prices[-1] * 0.99) # Drop by 1% each time
            
        self.engine.load_data(prices)
        self.engine.run()
        
        # We expect at least one BUY trade
        self.assertGreater(len(self.engine.trades), 0)
        self.assertEqual(self.engine.trades[0]['type'], 'BUY')
        
    def test_pnl_calculation(self):
        """Test PnL tracking."""
        # Manually simulate a trade
        self.engine.execute_trade('BUY', price=1.0, amount_usdc=100.0)
        self.assertLess(self.engine.balance_usdc, 901.0) # 1000 - 100 + fee
        self.assertGreater(self.engine.balance_ada, 0.0)
        
        # Sell at profit
        self.engine.execute_trade('SELL', price=1.1, amount_ada=self.engine.balance_ada)
        
        # Balance should be > 1000 (Profit) - Fees
        # Buy 100 @ 1.0 -> Fee 0.3% -> Cost 0.3. Net 99.7 USD worth of ADA.
        # Sell @ 1.1 -> Value ~109.67 -> Fee 0.3% -> Net ~109.34
        # Total ~1009.34
        self.assertGreater(self.engine.balance_usdc, 1000.0)

if __name__ == '__main__':
    unittest.main()
