from typing import List, Dict
from exhaustion_detector import ExhaustionDetector

class BacktestEngine:
    def __init__(self, initial_capital: float = 1000.0):
        self.capital = initial_capital
        self.balance_usdc = initial_capital
        self.balance_ada = 0.0  # Only used for LONG tracking; shorts are margin-style
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
        
        # Filters
        self.use_rsi_filter = False
        self.rsi_period = 14
        self.rsi_oversold = 30
        self.rsi_overbought = 70
        
        self.use_trend_filter = False # EMA 200 Trend Filter
        self.ema_period = 200
        
        # Exit Strategy
        self.use_fib_exit = False # Default to False
        self.fib_level = 0.5 # Target Fib Level

    def load_data(self, data: List[float]):
        """Load historical close prices."""
        self.data = data
        
    def get_fib_levels(self, window: List[float]):
        """Calculate Fib levels for the given window (High/Low)."""
        if not window: return None
        
        # Simple approximation using window max/min
        # For rigorous HFT, we'd need High/Low arrays, but we only have Close.
        # We'll approximate High/Low from the Close history window.
        swing_high = max(window)
        swing_low = min(window)
        diff = swing_high - swing_low
        
        return {
            '0.382': swing_high - (diff * 0.382),
            '0.5': swing_high - (diff * 0.5),
            '0.618': swing_high - (diff * 0.618),
            'low': swing_low,
            'high': swing_high
        }
        
    def calculate_rsi(self, period=14):
        import pandas as pd
        if not self.data:
            return []
        series = pd.Series(self.data)
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return (100 - (100 / (1 + rs))).fillna(50).tolist()
        
    def calculate_ema(self, period=200):
        import pandas as pd
        if not self.data: return []
        return pd.Series(self.data).ewm(span=period, adjust=False).mean().tolist()

    def run(self):
        """Run the backtest simulation with SL/TP and Equity Tracking."""
        self.detector.reset_state()
        self.trades = []
        self.balance_usdc = self.capital
        self.balance_ada = 0.0
        self.equity_curve = []
        
        # Pre-calculate Indicators
        rsi_data = []
        if self.use_rsi_filter:
            rsi_data = self.calculate_rsi(self.rsi_period)
            
        ema_data = []
        if self.use_trend_filter:
            ema_data = self.calculate_ema(self.ema_period)
        
        active_position = None # {entry_price, amount_ada, sl, tp}

        if len(self.data) < 5:
            return

        for i in range(len(self.data)):
            current_price = self.data[i]
            
            # 1. Update Equity Curve
            current_equity = self.balance_usdc
            if active_position:
                if active_position['type'] == 'LONG':
                    current_equity += active_position['amount_ada'] * current_price
                else:
                    # For shorts, equity = free balance + margin + unrealized PnL
                    current_equity += active_position['capital_used']
                    current_equity += (active_position['entry_price'] - current_price) * active_position['amount_ada']
            self.equity_curve.append(current_equity)
            
            # 2. Manage Active Position (SL/TP/Fib)
            if active_position:
                # Check SL
                if current_price <= active_position['sl']:
                    self._close_position(active_position, current_price, 'SL', i)
                    active_position = None
                # Check TP (Standard)
                elif current_price >= active_position['tp']:
                    self._close_position(active_position, current_price, 'TP', i)
                    active_position = None
                # Check Fib Exit (Dynamic TP)
                elif self.use_fib_exit and active_position.get('fib_target') and current_price >= active_position['fib_target']:
                     self._close_position(active_position, current_price, 'FIB_TP', i)
                     active_position = None
            
            # 3. Update Detector
            if i < 4:
                continue
            
            # Pass approx history for detector
            history_slice = self.data[i-10:i] if i >= 10 else self.data[:i]
            signal = self.detector.update(current_price, history_slice)
            
            # 4. Execute Signals
            # Apply Filters
            can_long = True
            can_short = True
            
            if self.use_rsi_filter and i < len(rsi_data):
                current_rsi = rsi_data[i]
                if current_rsi > self.rsi_oversold:
                    can_long = False
                if current_rsi < self.rsi_overbought:
                    can_short = False
                    
            # Apply Trend Filter (EMA)
            # Logic: Long only if Price > EMA. Short only if Price < EMA.
            if self.use_trend_filter and i < len(ema_data):
                current_ema = ema_data[i]
                if current_price < current_ema:
                    can_long = False # Don't buy dips in downtrend
                if current_price > current_ema:
                    can_short = False # Don't short pumps in uptrend
            
            if signal['bull_l3'] and can_long:
                # Entry Signal (Long)
                if not active_position:
                    # Position Sizing (risk from available cash)
                    trade_amt = self.balance_usdc * self.risk_per_trade
                    if trade_amt > 5 and trade_amt <= self.balance_usdc:
                         opened = self._open_position('LONG', current_price, trade_amt, i)
                         if opened:
                             active_position = opened
                         
                         # Calculate Fib Target if enabled
                         if self.use_fib_exit:
                             # Look back X bars to find swing high (e.g. last 50 bars)
                             lookback = 50
                             start_idx = max(0, i - lookback)
                             window = self.data[start_idx:i]
                             fibs = self.get_fib_levels(window)
                             
                             if fibs:
                                 # For LONG, we target retracement from Low up to High? 
                                 # No, we are buying the dip. Price is at Low. 
                                 # We expect bounce to Fib level of the previous DROP.
                                 # Previous Drop: High -> Low. 
                                 # Target: Low + (High - Low) * FibLevel
                                 
                                 # If we use 0.5 level, it means 50% retracement of the drop.
                                 # Fibs calculated as: swing_high - (diff * level) is retracement from top.
                                 # Correct logic:
                                 # Price dropped from High to Low.
                                 # We enter at Low.
                                 # We exit at High - (High-Low)*(1-Fib)? 
                                 # Or simpler: Low + (High-Low)*Fib
                                 
                                 # My get_fib_levels returns levels from High down.
                                 # '0.618' = High - 0.618 * Range. This is DEEP retracement (price is low).
                                 # '0.382' = High - 0.382 * Range. This is SHALLOW retracement (price is high).
                                 
                                 # If we want to catch a bounce to 50%:
                                 # Target = High - 0.5 * Range.
                                 
                                 # Wait, standard Fib Retracement tools measure from Low to High for Uptrend, High to Low for Downtrend.
                                 # Here we assume we are in a Downtrend that is reversing.
                                 # We measure the Drop (High to Low).
                                 # We expect price to retrace UP.
                                 # 38.2% Retracement means price goes up 38.2% of the drop.
                                 # Price = Low + 0.382 * Range.
                                 # Which equals: High - (1 - 0.382) * Range = High - 0.618 * Range.
                                 
                                 # So if I select Fib 0.5, target is High - 0.5 * Range.
                                 # If I select Fib 0.618 (Golden Pocket bounce), target is Low + 0.618*Range.
                                 
                                 # Let's simplify: self.fib_level is the % bounce we want.
                                 # 0.5 means 50% bounce.
                                 range_val = fibs['high'] - fibs['low']
                                 target_price = fibs['low'] + (range_val * self.fib_level)
                                 
                                 # Sanity check: Target must be > Entry
                                 if target_price > current_price:
                                     active_position['fib_target'] = target_price
                                     # Disable fixed TP if Fib is valid? Or keep both?
                                     # Let's keep both, take whichever comes first (min).
                                     # But Fib is usually dynamic TP.
                                     # If Fib target is extremely high, fixed TP might hit first.
                                     # If Fib is small, we take small profit.
                                     pass

                elif active_position['type'] == 'SHORT':
                    # Close Short (Reversal?)
                    # Optional: For now just close. Could flip to long.
                    self._close_position(active_position, current_price, 'SIGNAL_BULL_L3', i)
                    active_position = None
            
            elif signal['bear_l3'] and can_short:
                # Entry Signal (Short) OR Exit Long
                if active_position:
                    if active_position['type'] == 'LONG':
                        self._close_position(active_position, current_price, 'SIGNAL_BEAR_L3', i)
                        active_position = None
                else:
                    # Open Short
                    trade_amt = self.balance_usdc * self.risk_per_trade
                    if trade_amt > 5 and trade_amt <= self.balance_usdc:
                        opened = self._open_position('SHORT', current_price, trade_amt, i)
                        if opened:
                            active_position = opened

    def _open_position(self, side: str, price: float, usdc_amount: float, index=-1):
        # Fee is paid on notional value
        fee = usdc_amount * self.fee_pct

        # Capital check (simple: ensure we have the cash to deploy)
        if usdc_amount > self.balance_usdc:
            return None
        
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

        # Deduct deployed capital from cash balance (margin for shorts too)
        self.balance_usdc -= usdc_amount

        return {
            'type': side,
            'entry_price': entry_price,
            'amount_ada': amount_ada,
            'sl': sl,
            'tp': tp,
            'entry_index': index,
            'capital_used': usdc_amount
        }

    def _close_position(self, pos, price, reason, index=-1):
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

        # Update Balance: return deployed capital + profit/loss
        self.balance_usdc += pos.get('capital_used', 0)
        self.balance_usdc += pnl_net # profit or loss on top of capital
        
        self.trades.append({
            'type': f"{pos['type']}_CLOSE",
            'reason': reason,
            'entry_price': pos['entry_price'],
            'exit_price': exit_price,
            'pnl': pnl_net,
            'pnl_pct': (pnl_net / (pos['entry_price'] * pos['amount_ada'])) * 100,
            'entry_index': pos.get('entry_index', -1),
            'exit_index': index
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
            if eq > peak:
                peak = eq
            dd = (peak - eq) / peak * 100
            if dd > max_dd:
                max_dd = dd
            
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
