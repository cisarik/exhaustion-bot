
import pandas as pd
import logging
from backtest_engine import BacktestEngine

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("Validator")

DATA_FILE = "data/kraken_ADAUSDT_15m.csv"

def load_15m_data():
    df = pd.read_csv(DATA_FILE)
    return df['close'].tolist()

def run_validation():
    logger.info("Loading 15m Data...")
    data = load_15m_data()
    logger.info(f"Loaded {len(data)} candles.")
    
    engine = BacktestEngine(initial_capital=1000.0)
    engine.load_data(data)
    
    # Configured "Dip Hunting" Parameters
    engine.detector.level1 = 9
    engine.detector.level2 = 14
    engine.detector.level3 = 20
    engine.detector.lookback1 = 6
    engine.detector.lookback2 = 6
    engine.detector.lookback3 = 6
    
    engine.stop_loss_pct = 0.025
    engine.take_profit_pct = 0.05
    engine.fee_pct = 0.001 # Optimistic fee
    
    # Enable RSI Filter? Based on previous findings, it helped.
    engine.use_rsi_filter = True
    engine.rsi_period = 14
    engine.rsi_oversold = 30
    engine.rsi_overbought = 70
    
    engine.run()
    metrics = engine.get_metrics()
    
    print("\n--- 15m TIMEFRAME VALIDATION (Dip Hunting) ---")
    print(f"Profit:      ${metrics['total_pnl']:.2f}")
    print(f"Trades:      {metrics['total_trades']}")
    print(f"Win Rate:    {metrics['win_rate']}%")
    print(f"Max DD:      {metrics['max_drawdown']}%")
    print(f"Final Equity:${metrics['final_equity']:.2f}")
    print("-" * 50)
    
    if metrics['total_trades'] == 0:
        print("⚠️  WARNING: No trades triggered. L3=20 might be too extreme for 15m.")
    elif metrics['total_pnl'] > 0:
        print("✅ Strategy is PROFITABLE on 15m as well.")
    else:
        print("❌ Strategy is LOSING on 15m.")

if __name__ == "__main__":
    run_validation()
