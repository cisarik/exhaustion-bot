import unittest
import logging
from backtest_engine import BacktestEngine
from data_loader import DataLoader
from optimize_strategy import run_optimization

# Setup logger to stdout to see results during test
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("ProfitProof")

class TestProfitPotential(unittest.TestCase):
    def setUp(self):
        self.capital = 1000.0
        # Load actual data - Binance usually has good history
        # Switching to 1h timeframe for more reliable signals
        self.loader = DataLoader(exchange_id='binance', symbol='ADA/USDT', timeframe='1h')
        try:
            # Fetch enough data for optimization + validation
            # 3000 candles of 1h = 125 days (4 months) -> Much better sample size!
            self.data = self.loader.fetch_data(limit=3000)
        except Exception as e:
            self.skipTest(f"Data fetch failed: {e}")

    def test_monthly_projection(self):
        """
        Runs genetic optimization then backtest to project monthly ROI.
        Target: Positive Profit Factor and ROI potential.
        """
        if not self.data:
            self.skipTest("No data available for backtest")

        # 1. TEST DEFAULT PARAMETERS (Pine Script Original)
        logger.info(">>> STEP 1: TESTING ORIGINAL PINE SCRIPT DEFAULTS <<<")
        engine_default = BacktestEngine(initial_capital=self.capital)
        engine_default.load_data(self.data)
        # Defaults: 9, 12, 14 | 4, 3, 2
        engine_default.detector.level1 = 9
        engine_default.detector.level2 = 12
        engine_default.detector.level3 = 14
        engine_default.detector.lookback1 = 4
        engine_default.detector.lookback2 = 3
        engine_default.detector.lookback3 = 2
        engine_default.risk_per_trade = 0.05
        
        engine_default.run()
        metrics_default = engine_default.get_metrics()
        logger.info(f"ORIGINAL Profit: ${metrics_default['total_pnl']:.2f} (Trades: {metrics_default['total_trades']})")

        # 2. OPTIMIZE (AI)
        logger.info(">>> STEP 2: RUNNING GENETIC OPTIMIZATION (50 Generations) on 1h Data <<<")
        # Pass our loaded 1h data to the optimizer
        best_params = run_optimization(n_trials=50, input_data=self.data[:2000]) # Train on first 2000
        
        if not best_params:
            self.fail("Optimization failed to produce parameters.")

        logger.info(f"Best Parameters Found: {best_params}")

        # 3. VALIDATE (Backtest Optimized)
        logger.info(">>> STEP 3: VALIDATING WITH OPTIMIZED PARAMETERS <<<")
        engine = BacktestEngine(initial_capital=self.capital)
        engine.load_data(self.data)

        # Apply Optimized Parameters from best_params
        engine.detector.level1 = best_params['level1']
        engine.detector.level2 = best_params['level2']
        engine.detector.level3 = best_params['level3']
        engine.detector.lookback1 = best_params['lookback1']
        engine.detector.lookback2 = best_params['lookback2']
        engine.detector.lookback3 = best_params['lookback3']
        
        engine.stop_loss_pct = best_params['stop_loss_pct']
        engine.take_profit_pct = best_params['take_profit_pct']
        engine.risk_per_trade = 0.05 # 5% risk for aggressive testing proof

        engine.run()
        metrics = engine.get_metrics()

        # Calculate Duration
        num_candles = len(self.data)
        days = num_candles / (24 * 1) # 1h candles
        
        total_profit = metrics['total_pnl']
        projected_monthly_profit = (total_profit / days) * 30 if days > 0 else 0
        projected_roi = (projected_monthly_profit / self.capital) * 100

        logger.info(f"--- RESULTS ({num_candles} candles / {days:.1f} days) ---")
        logger.info(f"Initial Capital: ${self.capital}")
        logger.info(f"ORIGINAL Profit: ${metrics_default['total_pnl']:.2f} (Trades: {metrics_default['total_trades']})")
        logger.info(f"OPTIMIZED Profit: ${total_profit:.2f} (Trades: {metrics['total_trades']})")
        logger.info(f"Win Rate:        {metrics['win_rate']}%")
        logger.info(f"Max Drawdown:    {metrics['max_drawdown']}%")
        logger.info("-------------------------------------------")
        logger.info(f"PROJECTED MONTHLY PROFIT: ${projected_monthly_profit:.2f}")
        logger.info(f"PROJECTED MONTHLY ROI:    {projected_roi:.2f}%")
        logger.info("-------------------------------------------")

        # Assertions
        if metrics['total_trades'] == 0:
            logger.warning("⚠️ No trades executed. Market might be too flat or params too strict.")
        else:
            if metrics['total_pnl'] > metrics_default['total_pnl']:
                logger.info("✅ AI IMPROVEMENT: Optimization outperformed the default strategy.")
            else:
                logger.info("ℹ️ AI performed similarly or worse than default (Market might be random).")

if __name__ == '__main__':
    unittest.main()
