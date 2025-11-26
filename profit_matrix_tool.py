
import itertools
import pandas as pd
import logging
from backtest_engine import BacktestEngine
from concurrent.futures import ProcessPoolExecutor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("Matrix")

DATA_FILE = "data/binance_ADAUSDT_1m.csv"

def load_data():
    df = pd.read_csv(DATA_FILE)
    return df['close'].tolist()

def run_backtest(params):
    data, l1, l2, l3, sl, tp, use_rsi, use_fib, fib_level, use_trend = params
    
    engine = BacktestEngine(initial_capital=1000.0)
    engine.load_data(data)
    
    engine.detector.level1 = l1
    engine.detector.level2 = l2
    engine.detector.level3 = l3
    engine.detector.lookback1 = 6
    engine.detector.lookback2 = 6
    engine.detector.lookback3 = 6
    
    engine.stop_loss_pct = sl
    engine.take_profit_pct = tp
    
    # OPTIMISTIC SETTINGS (Low Fee for Scalping)
    engine.fee_pct = 0.001      
    engine.slippage_pct = 0.001 
    
    engine.use_rsi_filter = use_rsi
    engine.rsi_period = 14
    engine.rsi_oversold = 30
    engine.rsi_overbought = 70
    
    engine.use_fib_exit = use_fib
    engine.fib_level = fib_level
    
    # TREND FILTER
    engine.use_trend_filter = use_trend
    engine.ema_period = 200
    
    engine.run()
    metrics = engine.get_metrics()
    
    return {
        "L1": l1, "L2": l2, "L3": l3, "SL": sl, "TP": tp, "RSI": use_rsi, "FIB": fib_level if use_fib else 0, "TREND": use_trend,
        "Profit": metrics['total_pnl'],
        "Trades": metrics['total_trades'],
        "WinRate": metrics['win_rate'],
        "DD": metrics['max_drawdown']
    }

def main():
    logger.info("Loading 1m Data...")
    data = load_data()
    logger.info(f"Loaded {len(data)} candles.")
    
    # Parameter Grid V6 (Trend + Pullback)
    # Hypothesis: In Uptrend (EMA200), we can buy weaker dips (L2) safely.
    l1_range = [9]
    l2_range = [14]
    l3_range = [18, 20] # Test stricter vs looser L3
    
    # Strategy Variants:
    # 1. Strict: L3 + Trend Filter (Safest?)
    # 2. Loose: L2 + Trend Filter (More trades?) - Wait, engine triggers on L3 mostly. 
    # Actually, my engine triggers LONG on 'bull_l3'. I need to update engine if I want to trigger on L2.
    # For now, let's stick to L3 but vary the threshold (18 vs 20).
    
    sl_range = [0.015, 0.025]
    tp_range = [0.10] 
    rsi_range = [True] 
    fib_range = [0.5] # Proven best
    trend_range = [True] # Must enable
    
    combinations = []
    for l1, l2, l3, sl, tp, rsi, fib, trend in itertools.product(l1_range, l2_range, l3_range, sl_range, tp_range, rsi_range, fib_range, trend_range):
        if l1 < l2 < l3:
            combinations.append((data, l1, l2, l3, sl, tp, rsi, True, fib, trend))
            
    logger.info(f"Testing {len(combinations)} combinations...")
    
    results = []
    with ProcessPoolExecutor() as executor:
        for res in executor.map(run_backtest, combinations):
            results.append(res)
            
    # Sort by Profit
    results.sort(key=lambda x: x['Profit'], reverse=True)
    
    print("\n--- TOP CONFIGURATIONS (TREND + PULLBACK) ---")
    print(f"{'L3':<4} {'SL':<6} {'FIB':<6} {'TREND':<5} | {'PROFIT':<10} {'TRADES':<8} {'WIN%':<6} {'DD%':<6}")
    print("-" * 80)
    
    for r in results:
        print(f"{r['L3']:<4} {r['SL']:<6.3f} {r['FIB']:<6.3f} {str(r['TREND']):<5} | ${r['Profit']:<9.2f} {r['Trades']:<8} {r['WinRate']:<6.1f} {r['DD']:<6.1f}")
