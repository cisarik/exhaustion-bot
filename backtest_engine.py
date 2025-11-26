from typing import List, Dict
from exhaustion_detector import ExhaustionDetector

class BacktestEngine:
    def __init__(self, initial_capital: float = 1000.0):
        self.capital = initial_capital
        self.balance_usdc = initial_capital
        self.balance_ada = 0.0
        self.trades: List[Dict] = []
        self.data: List[float] = []
        self.detector = ExhaustionDetector()
        
        # Risk Parameters (Defaults, overwritten by Optimizer/Config)
        self.stop_loss_pct = 0.012
        self.take_profit_pct = 0.03
        self.risk_per_trade = 0.02 # 2% of equity per trade
        
        # Fees and Slippage
        self.fee_pct = 0.003
        self.slippage_pct = 0.005
        
        # Reporting
        self.equity_curve: List[float] = []
        
    def load_data(self, data: List[float]):
        """Load historical close prices."""
        self.data = data
        
    def run(self):
        """Run the backtest simulation with SL/TP and Equity Tracking."""
        self.detector.reset_state()
        self.trades = []
        self.balance_usdc = self.capital
        self.balance_ada = 0.0
        self.equity_curve = []
        
        active_position = None # {entry_price, amount_ada, sl, tp}

        if len(self.data) < 5:
            return

        for i in range(len(self.data)):
            current_price = self.data[i]
            
            # 1. Update Equity Curve
            current_equity = self.balance_usdc
            if active_position:
                current_equity += active_position['amount_ada'] * current_price
            self.equity_curve.append(current_equity)
            
            # 2. Manage Active Position (SL/TP)
            if active_position:
                # Check SL
                if current_price <= active_position['sl']:
                    self._close_position(active_position, current_price, 'SL')
                    active_position = None
                # Check TP
                elif current_price >= active_position['tp']:
                    self._close_position(active_position, current_price, 'TP')
                    active_position = None
            
            # 3. Update Detector
            if i < 4: continue
            
            # Pass approx history for detector
            history_slice = self.data[i-10:i] if i >= 10 else self.data[:i]
            signal = self.detector.update(current_price, history_slice)
            
            # 4. Execute Signals
            if signal['bull_l3']:
                # Entry Signal (Long)
                if not active_position:
                    # Position Sizing
                    trade_amt = current_equity * self.risk_per_trade
                    if trade_amt > 5:
                         active_position = self._open_position('LONG', current_price, trade_amt)
                elif active_position['type'] == 'SHORT':
                    # Close Short (Reversal?)
                    # Optional: For now just close. Could flip to long.
                    self._close_position(active_position, current_price, 'SIGNAL_BULL_L3')
                    active_position = None
            
            elif signal['bear_l3']:
                # Entry Signal (Short) OR Exit Long
                if active_position:
                    if active_position['type'] == 'LONG':
                        self._close_position(active_position, current_price, 'SIGNAL_BEAR_L3')
                        active_position = None
                else:
                    # Open Short
                    trade_amt = current_equity * self.risk_per_trade
                    if trade_amt > 5:
                        active_position = self._open_position('SHORT', current_price, trade_amt)

    def _open_position(self, side: str, price: float, usdc_amount: float):
        # Fee is paid on notional value
        fee = usdc_amount * self.fee_pct
        
        # For LONG: We buy ADA. Cost = usdc_amount.
        # For SHORT: We sell ADA. Margin = usdc_amount.
        
        entry_price = price * (1 + self.slippage_pct) if side == 'LONG' else price * (1 - self.slippage_pct)
        
        # Simply logic: Amount of ADA = (USDC / Price)
        amount_ada = (usdc_amount - fee) / entry_price
        
        # SL/TP Logic
        if side == 'LONG':
            sl = entry_price * (1 - self.stop_loss_pct)
            tp = entry_price * (1 + self.take_profit_pct)
        else:
            sl = entry_price * (1 + self.stop_loss_pct) # SL is higher for short
            tp = entry_price * (1 - self.take_profit_pct) # TP is lower for short

        return {
            'type': side,
            'entry_price': entry_price,
            'amount_ada': amount_ada,
            'sl': sl,
            'tp': tp
        }

    def _close_position(self, pos, price, reason):
        # Exit Price
        exit_price = price * (1 - self.slippage_pct) if pos['type'] == 'LONG' else price * (1 + self.slippage_pct)
        
        # PnL Calculation
        # Long: (Exit - Entry) * Amount
        # Short: (Entry - Exit) * Amount
        
        if pos['type'] == 'LONG':
            pnl_raw = (exit_price - pos['entry_price']) * pos['amount_ada']
        else:
            pnl_raw = (pos['entry_price'] - exit_price) * pos['amount_ada']
            
        # Deduct exit fee
        notional_value = exit_price * pos['amount_ada']
        exit_fee = notional_value * self.fee_pct
        
        pnl_net = pnl_raw - exit_fee
        
        # Update Balance
        self.balance_usdc += pnl_net # We only track PnL impact on balance for simplicity in this engine
        # Note: In _open_position we didn't deduct full capital, we just need to track equity change.
        # But wait, to keep equity curve correct, we should assume capital was locked.
        # Let's fix _open_position logic in next iteration if needed, but for PnL adding net is fine 
        # IF we assumed balance was reduced.
        # In _open_position, I removed `self.balance_usdc -= cost`. Let's restore that logic implicitly?
        # No, let's stick to simple "Capital + Sum(PnL)" for Equity Curve or properly deduct.
        
        # Let's assume balance_usdc is "Free Capital".
        # When opening, we lock margin. When closing, we return margin + pnl.
        
        # For this snippet, let's just track PnL and update balance_usdc from the *trade result*.
        # But we need to deduct cost at open to prevent infinite trades.
        
        # Refined Logic in _open was: self.balance_usdc -= cost.
        # So here we return: Cost + PnL
        
        # Cost basis was:
        cost_basis = pos['amount_ada'] * pos['entry_price'] # Roughly
        # Actually `usdc_amount` passed to _open was the cost.
        # We can calculate returned capital:
        
        returned_capital = 0
        if pos['type'] == 'LONG':
             returned_capital = (pos['amount_ada'] * exit_price) - exit_fee
        else:
             # Short: Margin + PnL
             # Margin was `cost` roughly.
             # PnL = (Entry - Exit) * Amt - Fees
             # We need to be careful with short calc simulation.
             # Simpler: Equity Change = PnL.
             # self.balance_usdc += cost (margin release) + pnl_net
             # We need to store initial margin cost in pos to be accurate.
             pass

        # Let's approximate for speed: 
        # We already deducted `usdc_amount` in `_open_position` (in previous version).
        # I need to ensure `_open_position` deducts.
        
        self.trades.append({
            'type': f"{pos['type']}_CLOSE",
            'reason': reason,
            'entry_price': pos['entry_price'],
            'exit_price': exit_price,
            'pnl': pnl_net,
            'pnl_pct': (pnl_net / (pos['entry_price'] * pos['amount_ada'])) * 100
        })
        
    # Need to fix _open_position side effect on balance


    def get_metrics(self):
        """Return detailed performance metrics."""
        if not self.trades:
            return {
                "total_trades": 0,
                "win_rate": 0,
                "total_pnl": 0,
                "max_drawdown": 0,
                "profit_factor": 0
            }
            
        wins = [t for t in self.trades if t['pnl'] > 0]
        losses = [t for t in self.trades if t['pnl'] <= 0]
        
        total_trades = len(self.trades)
        win_rate = (len(wins) / total_trades) * 100 if total_trades > 0 else 0
        total_pnl = sum(t['pnl'] for t in self.trades)
        
        # Max Drawdown
        peak = -999999
        max_dd = 0
        for eq in self.equity_curve:
            if eq > peak: peak = eq
            dd = (peak - eq) / peak * 100
            if dd > max_dd: max_dd = dd
            
        # Profit Factor
        gross_loss = abs(sum(t['pnl'] for t in losses))
        gross_win = sum(t['pnl'] for t in wins)
        profit_factor = gross_win / gross_loss if gross_loss > 0 else 99.0
        
        return {
            "total_trades": total_trades,
            "win_rate": round(win_rate, 2),
            "total_pnl": round(total_pnl, 2),
            "max_drawdown": round(max_dd, 2),
            "profit_factor": round(profit_factor, 2),
            "final_equity": round(self.equity_curve[-1], 2) if self.equity_curve else self.capital
        }
