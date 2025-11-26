
import unittest
import pandas as pd
import os
from backtest_engine import BacktestEngine

class TestProfitableStrategy(unittest.TestCase):
    def setUp(self):
        self.data_file = "data/binance_ADAUSDT_1m.csv"
        if not os.path.exists(self.data_file):
            self.fail("Data file not found. Please run fetch_1m_data.py first.")
            
        df = pd.read_csv(self.data_file)
        self.data = df['close'].tolist()

    def test_dip_hunting_strategy_profitability(self):
        """
        Regression Test: Verifies that the 'Dip Hunting' configuration 
        (Level 3=20, Wide Stops) yields a profit on the 1m dataset.
        
        Strategy Logic:
        - Wait for extreme exhaustion (20 candles trend).
        - Enter LONG only if RSI < 30 (Oversold).
        - Wide Stop Loss (2.5%) to survive volatility.
        - Big Take Profit (5%) to catch the bounce.
        - Low Fees (0.1%) assuming Limit Orders / rebate tiers.
        """
        engine = BacktestEngine(initial_capital=1000.0)
        engine.load_data(self.data)
        
        # --- PROFITABLE PARAMETERS (Found via Matrix Search) ---
        engine.detector.level1 = 9
        engine.detector.level2 = 14
        engine.detector.level3 = 20 # The 'Dip Hunter' trigger
        
        engine.detector.lookback1 = 6
        engine.detector.lookback2 = 6
        engine.detector.lookback3 = 6
        
        # Risk Settings
        engine.stop_loss_pct = 0.025  # 2.5%
        engine.take_profit_pct = 0.05 # 5.0%
        
        # Execution Settings (Limit Orders)
        engine.fee_pct = 0.001      # 0.1% Maker Fee
        engine.slippage_pct = 0.001 # 0.1%
        
        # Filters
        engine.use_rsi_filter = True
        engine.rsi_period = 14
        engine.rsi_oversold = 30
        engine.rsi_overbought = 70
        
        # Run
        engine.run()
        metrics = engine.get_metrics()
        
        print("\n--- DIP HUNTING STRATEGY RESULTS ---")
        print(f"Total Profit: ${metrics['total_pnl']:.2f}")
        print(f"Trade Count:  {metrics['total_trades']}")
        print(f"Win Rate:     {metrics['win_rate']}%")
        print(f"Max Drawdown: {metrics['max_drawdown']}%")
        print("------------------------------------")
        
        # Assertions
        self.assertGreater(metrics['total_pnl'], 0, "Strategy MUST be profitable to pass regression.")
        self.assertGreater(metrics['total_trades'], 0, "Strategy must take at least one trade.")
        self.assertGreater(metrics['win_rate'], 40, "Win rate should be healthy (>40%).")

if __name__ == '__main__':
    unittest.main()
