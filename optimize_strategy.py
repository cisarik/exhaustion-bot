import optuna
import logging
from backtest_engine import BacktestEngine
import json
import os
from data_loader import DataLoader

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Optimizer")

CONFIG_FILE = "config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

# Load Historical Data
loader = DataLoader(exchange_id='kraken', symbol='ADA/USDT', timeframe='15m')
try:
    # Fetch enough data for a meaningful backtest (e.g., 2000 candles)
    data = loader.fetch_data(limit=2000)
    logger.info(f"Loaded {len(data)} candles for optimization.")
except Exception as e:
    logger.error(f"Failed to load data: {e}")
    # In a real app this might be handled gracefully, but for now we need data
    data = [] 

def objective(trial):
    if not data:
        return -1000.0

    # 1. Suggest Hyperparameters
    # Lower thresholds for more sensitivity in low volatility
    level1 = trial.suggest_int("level1", 3, 12)
    level2 = trial.suggest_int("level2", 6, 18)
    level3 = trial.suggest_int("level3", 9, 24)
    
    # Ensure L1 < L2 < L3 logic if needed, or detector handles it
    if level1 >= level2 or level2 >= level3:
        return -1000.0 # Penalize invalid config
        
    lookback1 = trial.suggest_int("lookback1", 1, 10)
    lookback2 = trial.suggest_int("lookback2", 1, 10)
    lookback3 = trial.suggest_int("lookback3", 1, 10)
    
    stop_loss_pct = trial.suggest_float("stop_loss_pct", 0.005, 0.05)
    take_profit_pct = trial.suggest_float("take_profit_pct", 0.01, 0.10)
    
    # 2. Setup Engine
    engine = BacktestEngine(initial_capital=1000.0)
    engine.load_data(data)
    
    # Configure Detector
    engine.detector.level1 = level1
    engine.detector.level2 = level2
    engine.detector.level3 = level3
    engine.detector.lookback1 = lookback1
    engine.detector.lookback2 = lookback2
    engine.detector.lookback3 = lookback3
    
    # Configure Risk
    engine.stop_loss_pct = stop_loss_pct
    engine.take_profit_pct = take_profit_pct
    
    # 3. Run Backtest
    engine.run()
    
    # Metrics
    metrics = engine.get_metrics()
    total_trades = metrics['total_trades']
    total_pnl = metrics['total_pnl']
    
    # 4. Return Metric (Total Profit)
    # Penalize inactivity! We want a bot that trades.
    if total_trades < 5:
        return -500.0 # Hard penalty for inactivity
        
    return total_pnl

def run_optimization(n_trials=20, input_data=None):
    global data
    if input_data is not None:
        data = input_data
    
    if not data:
        # Try loading if not provided
        try:
            loader = DataLoader(exchange_id='kraken', symbol='ADA/USDT', timeframe='15m')
            data = loader.fetch_data(limit=2000)
        except Exception as e:
            logger.error(f"No data loaded for optimization: {e}")
            return None

    logger.info("Starting Genetic Optimization...")
    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=n_trials) 
    
    logger.info("Optimization Complete!")
    logger.info(f"Best Profit: ${study.best_value:.2f}")
    logger.info("Best Parameters:")
    for key, value in study.best_params.items():
        logger.info(f"  {key}: {value}")

    # Save best params to config
    current_config = load_config()
    
    # Ensure sections exist
    if "strategy" not in current_config:
        current_config["strategy"] = {}
    if "risk" not in current_config:
        current_config["risk"] = {}
    
    # Update Strategy
    current_config["strategy"]["level1"] = study.best_params["level1"]
    current_config["strategy"]["level2"] = study.best_params["level2"]
    current_config["strategy"]["level3"] = study.best_params["level3"]
    current_config["strategy"]["lookback1"] = study.best_params["lookback1"]
    current_config["strategy"]["lookback2"] = study.best_params["lookback2"]
    current_config["strategy"]["lookback3"] = study.best_params["lookback3"]
    
    # Update Risk
    current_config["risk"]["stop_loss_pct"] = study.best_params["stop_loss_pct"]
    current_config["risk"]["take_profit_pct"] = study.best_params["take_profit_pct"]
    
    save_config(current_config)
    logger.info("Config updated with optimized parameters.")
    return study.best_params

if __name__ == "__main__":
    run_optimization(n_trials=20)
