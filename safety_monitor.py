import logging

logger = logging.getLogger(__name__)

class SafetyMonitor:
    def __init__(self, max_daily_loss_pct: float = 0.05, max_trade_size_usdc: float = 1000.0, max_consecutive_losses: int = 3):
        self.max_daily_loss_pct = max_daily_loss_pct
        self.max_trade_size_usdc = max_trade_size_usdc
        self.max_consecutive_losses = max_consecutive_losses
        
        self.daily_pnl = 0.0
        self.consecutive_losses = 0
        self.is_circuit_broken = False
        self.initial_capital = 1000.0 # Should be updated or passed in
        
    def check_trade_size(self, amount_usdc: float) -> bool:
        if amount_usdc > self.max_trade_size_usdc:
            logger.warning(f"Trade rejected: Size {amount_usdc} > Limit {self.max_trade_size_usdc}")
            return False
        return True

    def record_trade_pnl(self, pnl_amount: float):
        self.daily_pnl += pnl_amount
        
        if pnl_amount < 0:
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0
            
        self._check_triggers()

    def _check_triggers(self):
        # Check Daily Loss
        # Assuming initial capital is static for this check or we track pct
        loss_limit_abs = self.initial_capital * self.max_daily_loss_pct
        if self.daily_pnl <= -loss_limit_abs:
            logger.critical(f"CIRCUIT BREAKER: Max Daily Loss exceeded ({self.daily_pnl})")
            self.is_circuit_broken = True
            
        # Check Consecutive Losses
        if self.consecutive_losses >= self.max_consecutive_losses:
            logger.critical(f"CIRCUIT BREAKER: Max Consecutive Losses exceeded ({self.consecutive_losses})")
            self.is_circuit_broken = True

    def can_trade(self) -> bool:
        return not self.is_circuit_broken

    def reset_daily(self):
        self.daily_pnl = 0.0
        self.is_circuit_broken = False
        logger.info("Safety Monitor: Daily stats reset.")
        
    def reset_consecutive(self):
        self.consecutive_losses = 0
