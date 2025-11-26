
import unittest
from backtest_engine import BacktestEngine
import pandas as pd
import os

class TestHFTStrategy(unittest.TestCase):
    def setUp(self):
        self.data_file = "data/binance_ADAUSDT_1m.csv"
        self.data = []
        if os.path.exists(self.data_file):
            df = pd.read_csv(self.data_file)
            self.data = df['close'].tolist()
        else:
            self.fail("1m Data file not found. Please run data fetcher first.")

    def test_1m_scalping_profitability(self):
        """
        TDD: Verifies that the strategy is profitable on 1m timeframe with specific params.
        If this test fails, the strategy logic or parameters need adjustment.
        """
        engine = BacktestEngine(initial_capital=1000.0)
        engine.load_data(self.data)
        
        # HFT Parameters (Tighter than 15m)
        # We need to find a profitable set.
        # Start with hypothesis: Higher levels (filter noise), smaller lookback.
        engine.detector.level1 = 9
        engine.detector.level2 = 13
        engine.detector.level3 = 18 # Higher threshold for 1m noise
        
        engine.detector.lookback1 = 10
        engine.detector.lookback2 = 10
        engine.detector.lookback3 = 10
        
        # Tight Risk Management for Scalping
        engine.stop_loss_pct = 0.005 # 0.5% SL
        engine.take_profit_pct = 0.01 # 1.0% TP (Risk:Reward 1:2)
        engine.fee_pct = 0.001 # Assume lower fees for HFT/Volume or efficient DEX? 
                               # DeltaDefi might have 0.3%. Let's stick to 0.3% to be realistic.
        engine.fee_pct = 0.003 
        
        engine.run()
        metrics = engine.get_metrics()
        
        print("\n--- 1m HFT Strategy Result ---")
        print(f"Trades: {metrics['total_trades']}")
        print(f"Profit: ${metrics['total_pnl']:.2f}")
        print(f"Win Rate: {metrics['win_rate']}%")
        print(f"Final Equity: ${metrics['final_equity']:.2f}")
        
        # Assertions
        self.assertGreater(metrics['total_trades'], 10, "Strategy is too passive for HFT")
        self.assertGreater(metrics['total_pnl'], 0, "Strategy is losing money on 1m data!")

if __name__ == '__main__':
    unittest.main()
