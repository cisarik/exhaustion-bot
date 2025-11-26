import asyncio
import logging
import random
import os
import json
from datetime import datetime
from typing import List, Dict
from exhaustion_detector import ExhaustionDetector
from wallet_manager import WalletManager
from profit_manager import ProfitManager
from safety_monitor import SafetyMonitor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot_trade_log.txt", mode='w'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("PaperTrader")
print("Paper Trader Module Loaded.")

class PaperTrader:
    def __init__(self, config_path: str = "config.json"):
        self.load_config(config_path)
        
        # Initialize Components
        self.detector = ExhaustionDetector(
            level1=self.config['strategy']['level1'],
            level2=self.config['strategy']['level2'],
            level3=self.config['strategy']['level3'],
            lookback1=self.config['strategy'].get('lookback1', 4),
            lookback2=self.config['strategy'].get('lookback2', 3),
            lookback3=self.config['strategy'].get('lookback3', 2)
        )
        
        self.capital_usdc = 1000.0 # Default
        self.balance_ada = 0.0
        self.balance_usdc = self.capital_usdc
        
        self.safety = SafetyMonitor(max_trade_size_usdc=self.config['risk'].get('max_trade_size_usdc', 500.0))
        self.wallet_manager = WalletManager() # Loads existing or new
        
        # Initialize Profit Manager (for logic, even if simulated)
        # Assuming we want to withdraw if profit > 100 ADA (example)
        # In paper mode, we won't actually withdraw but we'll log it.
        self.profit_manager = ProfitManager(
            wallet_manager=self.wallet_manager,
            profit_target_ada=100.0, # Configurable?
            reserve_ada=10.0, # Reserve for fees
            user_address="addr_test1..." # Should come from user input/config
        )
        
        self.closes: List[float] = []
        self.positions: List[Dict] = [] 
        
        # Risk Settings
        self.risk_per_trade = self.config['risk']['risk_per_trade']
        self.stop_loss_pct = self.config['risk']['stop_loss_pct']
        self.take_profit_pct = self.config['risk']['take_profit_pct']
        self.fee_pct = 0.003 
        self.slippage_pct = 0.005
        self.paper_mode = self.config['system']['paper_mode']

    def load_config(self, path: str):
        try:
            with open(path, 'r') as f:
                self.config = json.load(f)
            logger.info(f"Config loaded from {path}")
        except Exception as e:
            logger.error(f"Failed to load config: {e}. Using defaults.")
            self.config = {
                "strategy": {"level1": 9, "level2": 12, "level3": 14},
                "risk": {"stop_loss_pct": 0.012, "take_profit_pct": 0.03, "risk_per_trade": 0.02},
                "system": {"paper_mode": True}
            }
            
        # Re-apply settings if components exist
        if hasattr(self, 'detector'):
            strategy = self.config.get('strategy', {})
            self.detector.level1 = strategy.get('level1', 9)
            self.detector.level2 = strategy.get('level2', 12)
            self.detector.level3 = strategy.get('level3', 14)
            self.detector.lookback1 = strategy.get('lookback1', 4)
            self.detector.lookback2 = strategy.get('lookback2', 3)
            self.detector.lookback3 = strategy.get('lookback3', 2)
            
        if hasattr(self, 'safety'):
            self.risk_per_trade = self.config.get('risk', {}).get('risk_per_trade', 0.02)
            self.stop_loss_pct = self.config.get('risk', {}).get('stop_loss_pct', 0.012)
            self.take_profit_pct = self.config.get('risk', {}).get('take_profit_pct', 0.03)
            self.paper_mode = self.config.get('system', {}).get('paper_mode', True)

    async def start(self):
        logger.info(f"Starting Paper Trader. Mode: {'PAPER' if self.paper_mode else 'LIVE'}")
        logger.info(f"Capital: ${self.capital_usdc:.2f}")
        
        if self.paper_mode:
             await self.simulate_websocket_loop()
        else:
             # Real websocket connection would go here
             pass

    async def simulate_websocket_loop(self):
        """Simulates receiving price updates and forming candles."""
        logger.info("Connecting to (Simulated) DeltaDefi Websocket...")
        
        current_price = 1.0 # Start at 1.0 for simplicity
        
        while True:
            # Check Circuit Breaker
            if not self.safety.can_trade():
                logger.critical("TRADING HALTED BY SAFETY MONITOR.")
                break
                
            # Simulate Candle (Random Walk)
            change = random.uniform(-0.01, 0.01) # Smaller volatility
            current_price *= (1 + change)
            
            self.process_candle(current_price)
            self.check_positions(current_price)
            
            # Check Profit Target (Simulated)
            # Convert total value to ADA to check against profit target in ADA
            total_equity_usdc = self.balance_usdc + (self.balance_ada * current_price)
            # implied profit in ADA = (Equity - Initial) / Price? 
            # Or just check accumulated profit?
            # Let's just log equity for now.
            
            if len(self.positions) > 0 or abs(change) > 0.005:
                 # Log status periodically or on activity
                 pass

            await asyncio.sleep(1) 

    def process_candle(self, close_price: float):
        self.closes.append(close_price)
        # Max lookback needed is around 20-30 for detector state? 
        # No, detector is stateful but detect_signal re-runs history.
        # Keep enough history for re-run.
        if len(self.closes) > 100:
            self.closes.pop(0)
            
        # Run Detection
        signal = self.detector.detect_signal(self.closes)
        
        if signal['bull_l3']:
            self.execute_trade('BUY', close_price, signal)
        elif signal['bear_l3']:
            # Logic for Bear L3: Close Longs or Open Short?
            # Original prompt: "Level 3 exhaustion signals" -> reversal.
            # Bull L3 -> Buy. Bear L3 -> Sell.
            self.execute_trade('SELL', close_price, signal)

    def execute_trade(self, side: str, price: float, signal_data: Dict):
        # Check existing positions
        # For simplicity, max 1 position at a time for now?
        # Or multiple?
        if side == 'BUY':
            if any(p['status'] == 'OPEN' for p in self.positions):
                return # Already open
                
            trade_amount_usdc = self.balance_usdc * self.risk_per_trade
            
            if not self.safety.check_trade_size(trade_amount_usdc):
                return
            
            if trade_amount_usdc < 10:
                return

            effective_price = price * (1 + self.slippage_pct)
            fee = trade_amount_usdc * self.fee_pct
            cost = trade_amount_usdc
            
            ada_amount = (cost - fee) / effective_price
            
            self.balance_usdc -= cost
            self.balance_ada += ada_amount # Virtual
            
            position = {
                'id': len(self.positions) + 1,
                'entry_price': effective_price,
                'amount_ada': ada_amount,
                'sl_price': effective_price * (1 - self.stop_loss_pct),
                'tp_price': effective_price * (1 + self.take_profit_pct),
                'status': 'OPEN',
                'entry_time': datetime.now().isoformat()
            }
            self.positions.append(position)
            logger.info(f">>> OPEN LONG | Price: {effective_price:.4f} | Amt: {ada_amount:.2f} ADA | SL: {position['sl_price']:.4f} | TP: {position['tp_price']:.4f}")
            
        elif side == 'SELL':
            # Close all OPEN positions
            for pos in self.positions:
                if pos['status'] == 'OPEN':
                    self.close_position(pos, price, 'SIGNAL_BEAR_L3')

    def check_positions(self, current_price: float):
        for pos in self.positions:
            if pos['status'] != 'OPEN':
                continue
                
            if current_price <= pos['sl_price']:
                self.close_position(pos, current_price, 'SL')
            elif current_price >= pos['tp_price']:
                self.close_position(pos, current_price, 'TP')

    def close_position(self, pos: Dict, current_price: float, reason: str):
        effective_price = current_price * (1 - self.slippage_pct)
        gross_value = pos['amount_ada'] * effective_price
        fee = gross_value * self.fee_pct
        net_return = gross_value - fee
        
        self.balance_usdc += net_return
        self.balance_ada -= pos['amount_ada'] # Should be 0
        
        pos['status'] = 'CLOSED'
        pos['exit_price'] = effective_price
        pos['exit_reason'] = reason
        
        entry_val = pos['amount_ada'] * pos['entry_price'] # Approx cost basis
        pnl = net_return - entry_val
        pos['pnl'] = pnl
        
        self.safety.record_trade_pnl(pnl)
        
        logger.info(f"<<< CLOSE {reason} | Price: {effective_price:.4f} | PnL: ${pnl:.2f} | Bal: ${self.balance_usdc:.2f}")

if __name__ == "__main__":
    import sentry_sdk
    from sentry_sdk.integrations.logging import LoggingIntegration
    from sentry_sdk.integrations.asyncio import AsyncioIntegration
    
    dsn = os.getenv("SENTRY_DSN")
    if dsn:
        sentry_logging = LoggingIntegration(
            level=logging.INFO,
            event_level=logging.ERROR
        )
        sentry_sdk.init(
            dsn=dsn,
            integrations=[sentry_logging, AsyncioIntegration()],
            traces_sample_rate=1.0,
            environment="development",
        )
        logger.info("Sentry SDK Initialized.")

    try:
        trader = PaperTrader()
        asyncio.run(trader.start())
    except KeyboardInterrupt:
        print("Stopping Bot...")
    except Exception as e:
        logger.exception("Fatal Error in Main Loop")
        if dsn:
            sentry_sdk.capture_exception(e)
        raise
