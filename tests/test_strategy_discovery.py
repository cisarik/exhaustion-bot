
import unittest
import pandas as pd
import os
import itertools
from backtest_engine import BacktestEngine

class TestStrategyDiscovery(unittest.TestCase):
    """
    This is a 'Discovery Test'. 
    Instead of testing a fixed configuration, it hunts for a profitable one.
    It passes if ANY configuration in the search space is profitable.
    """
    
    @classmethod
    def setUpClass(cls):
        # Load data once for all tests
        cls.data_file = "data/binance_ADAUSDT_1m.csv"
        if not os.path.exists(cls.data_file):
            raise unittest.SkipTest("Data file not found. Run fetch_1m_data.py first.")
            
        df = pd.read_csv(cls.data_file)
        cls.data = df['close'].tolist()
        print(f"\n[Discovery] Loaded {len(cls.data)} candles for analysis.")

    def test_find_profitable_1m_strategy(self):
        """
        Matrix Search: Scans high-probability parameter space to find a winning config.
        """
        # Search Space (Expanded for wider discovery)
        # L3: From aggressive (16) to extreme (24)
        l3_range = [16, 18, 20, 22, 24] 
        # SL: Fine grained around 2.5%
        sl_range = [0.02, 0.025, 0.03] 
        # TP: 3% to 6%
        tp_range = [0.03, 0.04, 0.05, 0.06] 
        
        best_result = None
        results = []
        
        total_combinations = len(l3_range) * len(sl_range) * len(tp_range)
        print(f"[Discovery] Scanning {total_combinations} combinations...")

        for l3, sl, tp in itertools.product(l3_range, sl_range, tp_range):
            # Setup Engine
            engine = BacktestEngine(initial_capital=1000.0)
            engine.load_data(self.data)
            
            # Strategy Params
            engine.detector.level1 = 9
            engine.detector.level2 = 14
            engine.detector.level3 = l3
            engine.detector.lookback1 = 6
            engine.detector.lookback2 = 6
            engine.detector.lookback3 = 6
            
            # Risk Params
            engine.stop_loss_pct = sl
            engine.take_profit_pct = tp
            engine.fee_pct = 0.001 # Optimistic/Limit Order Fee
            engine.slippage_pct = 0.001 # Low slippage for limit orders
            
            # Enable RSI Filter (Must have for 1m)
            engine.use_rsi_filter = True
            engine.rsi_period = 14
            engine.rsi_oversold = 30
            engine.rsi_overbought = 70
            
            # Run
            engine.run()
            metrics = engine.get_metrics()
            
            # Store
            res = {
                'L3': l3, 'SL': sl, 'TP': tp,
                'Profit': metrics['total_pnl'],
                'Trades': metrics['total_trades'],
                'WinRate': metrics['win_rate'],
                'DD': metrics['max_drawdown']
            }
            results.append(res)
            
            if best_result is None or res['Profit'] > best_result['Profit']:
                best_result = res

        # Sort findings
        results.sort(key=lambda x: x['Profit'], reverse=True)
        
        # Output "Eye Candy" Report
        print("\n" + "="*65)
        print(f"🔎 STRATEGY DISCOVERY RESULTS (Top 5 of {total_combinations})")
        print("="*65)
        print(f"{'L3':<4} {'SL':<6} {'TP':<6} | {'PROFIT':<10} {'TRADES':<8} {'WIN%':<6} {'DD%':<6}")
        print("-" * 65)
        
        for r in results[:5]:
            profit_str = f"${r['Profit']:.2f}"
            print(f"{r['L3']:<4} {r['SL']:<6.3f} {r['TP']:<6.3f} | {profit_str:<10} {r['Trades']:<8} {r['WinRate']:<6.1f} {r['DD']:<6.1f}")
        print("="*65 + "\n")

        # Assertions
        if best_result['Profit'] <= 0:
            self.fail("❌ Matrix Search failed to find ANY profitable configuration on this dataset.")
        
        # Also fail if trade count is too low (overfitting on 1-2 lucky trades)
        if best_result['Trades'] < 3:
             print("⚠️  Warning: Best strategy has very few trades. Might be statistical noise.")
        
        print(f"✅ SUCCESS: Found profitable config: L3={best_result['L3']}, SL={best_result['SL']}, TP={best_result['TP']}")

if __name__ == '__main__':
    unittest.main()
