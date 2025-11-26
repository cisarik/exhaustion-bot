
import itertools
import pandas as pd
import logging
from backtest_engine import BacktestEngine
from concurrent.futures import ProcessPoolExecutor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("Matrix")

DATA_FILE = "data/binance_ADAUSDT_5m.csv"

def load_5m_data():
    df = pd.read_csv(DATA_FILE)
    return df['close'].tolist()

def run_backtest(params):
    data, l1, l2, l3, sl, tp, use_rsi = params
    
    engine = BacktestEngine(initial_capital=1000.0)
    engine.load_data(data)
    
    engine.detector.level1 = l1
    engine.detector.level2 = l2
    engine.detector.level3 = l3
    # Use fixed lookbacks for grid search simplicity
    engine.detector.lookback1 = 6
    engine.detector.lookback2 = 6
    engine.detector.lookback3 = 6
    
    engine.stop_loss_pct = sl
    engine.take_profit_pct = tp
    
    # OPTIMISTIC SETTINGS (Limit Orders / Low Fee DEX)
    engine.fee_pct = 0.001      # 0.1% Fee
    engine.slippage_pct = 0.001 # 0.1% Slippage
    
    engine.use_rsi_filter = use_rsi
    engine.rsi_period = 14
    engine.rsi_oversold = 30
    engine.rsi_overbought = 70
    
    engine.run()
    metrics = engine.get_metrics()
    
    return {
        "L1": l1, "L2": l2, "L3": l3, "SL": sl, "TP": tp, "RSI": use_rsi,
        "Profit": metrics['total_pnl'],
        "Trades": metrics['total_trades'],
        "WinRate": metrics['win_rate'],
        "DD": metrics['max_drawdown']
    }

def main():
    logger.info("Loading 5m Data...")
    data = load_5m_data()
    logger.info(f"Loaded {len(data)} candles.")
    
    # Parameter Grid for 5m
    # 5m has less noise than 1m, so we can relax levels slightly, but still keep wide stops?
    # Let's test a mix.
    l1_range = [6, 9]
    l2_range = [10, 12]
    l3_range = [14, 18] # Lower than 1m (20) because 14 candles of 5m is a long time (70 mins trend)
    
    sl_range = [0.01, 0.02] # 1%, 2%
    tp_range = [0.02, 0.04] # 2%, 4%
    rsi_range = [True] 
    
    combinations = []
    for l1, l2, l3, sl, tp, rsi in itertools.product(l1_range, l2_range, l3_range, sl_range, tp_range, rsi_range):
        if l1 < l2 < l3:
            combinations.append((data, l1, l2, l3, sl, tp, rsi))
            
    logger.info(f"Testing {len(combinations)} combinations...")
    
    results = []
    with ProcessPoolExecutor() as executor:
        for res in executor.map(run_backtest, combinations):
            results.append(res)
            
    # Sort by Profit
    results.sort(key=lambda x: x['Profit'], reverse=True)
    
    print("\n--- TOP 10 CONFIGURATIONS (5m TIMEFRAME) ---")
    print(f"{'L1':<4} {'L2':<4} {'L3':<4} {'SL':<6} {'TP':<6} {'RSI':<4} | {'PROFIT':<10} {'TRADES':<8} {'WIN%':<6} {'DD%':<6}")
    print("-" * 80)
    
    for r in results[:10]:
        print(f"{r['L1']:<4} {r['L2']:<4} {r['L3']:<4} {r['SL']:<6.3f} {r['TP']:<6.3f} {str(r['RSI']):<4} | ${r['Profit']:<9.2f} {r['Trades']:<8} {r['WinRate']:<6.1f} {r['DD']:<6.1f}")

    if results[0]['Profit'] > 0:
        print("\n✅ FOUND PROFITABLE CONFIGURATION!")
        best = results[0]
        print(f"Recommended: L1={best['L1']}, L2={best['L2']}, L3={best['L3']}, SL={best['SL']}, TP={best['TP']}")
    else:
        print("\n❌ NO PROFITABLE CONFIGURATION FOUND. Strategy may not work on 1m with these fees.")

if __name__ == "__main__":
    main()
