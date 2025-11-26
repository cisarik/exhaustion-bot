import logging
from typing import List, Dict, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ExhaustionDetector:
    """
    Implements Pine Script Exhaustion Signal logic.
    Levels: 9 (L1), 12 (L2), 14 (L3).
    """
    
    def __init__(self, level1=9, level2=12, level3=14, lookback1=4, lookback2=3, lookback3=2):
        self.level1 = level1
        self.level2 = level2
        self.level3 = level3
        
        self.lookback1 = lookback1
        self.lookback2 = lookback2
        self.lookback3 = lookback3
        
        # State variables
        self.cycle = 0
        self.bullish_signals = 0
        self.bearish_signals = 0

    def reset_state(self):
        self.cycle = 0
        self.bullish_signals = 0
        self.bearish_signals = 0

    def _reset_and_recheck(self, close: float, close_ref: float) -> Tuple[int, int, int]:
        new_bullish = 0
        new_bearish = 0
        new_cycle = 0

        if close < close_ref:
            new_bullish = 1
            new_cycle = new_bullish
        elif close > close_ref:
            new_bearish = 1
            new_cycle = new_bearish

        return new_bullish, new_bearish, new_cycle

    def update(self, close: float, history: List[float]) -> Dict[str, any]:
        """
        Updates state with a new candle close.
        Args:
            close: Current candle close.
            history: List of PREVIOUS closes (excluding current).
        """
        # We need max lookback history
        max_lookback = max(self.lookback1, self.lookback2, self.lookback3)
        if len(history) < max_lookback:
            return self._empty_signal(close)

        close_l1 = history[-self.lookback1]
        close_l2 = history[-self.lookback2]
        close_l3 = history[-self.lookback3]
        
        # Reference for reset is usually lookback1 (close[4] in default script)
        close_reset = close_l1 

        # Capture current state before update
        current_bullish = self.bullish_signals
        current_bearish = self.bearish_signals
        current_cycle = self.cycle

        # --- Logic Start ---
        if current_cycle < self.level1:
            if close < close_l1:
                self.bullish_signals = current_bullish + 1
                self.bearish_signals = 0
                self.cycle = self.bullish_signals
            elif close > close_l1:
                self.bearish_signals = current_bearish + 1
                self.bullish_signals = 0
                self.cycle = self.bearish_signals
            else:
                self.bullish_signals, self.bearish_signals, self.cycle = self._reset_and_recheck(close, close_reset)
        else:
            # Cycle >= Level 1
            if current_bullish > 0:
                if current_bullish < self.level2:
                    # Level 1 -> Level 2 transition
                    if close < close_l2:
                        self.bullish_signals = current_bullish + 1
                        self.cycle = self.bullish_signals
                    else:
                        self.bullish_signals, self.bearish_signals, self.cycle = self._reset_and_recheck(close, close_reset)
                elif current_bullish < self.level3 - 1:
                    # Level 2 -> Level 3 transition
                    if close < close_l3:
                        self.bullish_signals = current_bullish + 1
                        self.cycle = self.bullish_signals
                    else:
                        self.bullish_signals, self.bearish_signals, self.cycle = self._reset_and_recheck(close, close_reset)
                elif current_bullish == self.level3 - 1:
                    # Level 3 Trigger
                    if close < close_l3:
                        self.bullish_signals = self.level3
                        self.cycle = self.bullish_signals
                    else:
                        self.bullish_signals, self.bearish_signals, self.cycle = self._reset_and_recheck(close, close_reset)
            
            elif current_bearish > 0:
                if current_bearish < self.level2:
                    if close > close_l2:
                        self.bearish_signals = current_bearish + 1
                        self.cycle = self.bearish_signals
                    else:
                        self.bullish_signals, self.bearish_signals, self.cycle = self._reset_and_recheck(close, close_reset)
                elif current_bearish < self.level3 - 1:
                    if close > close_l3:
                        self.bearish_signals = current_bearish + 1
                        self.cycle = self.bearish_signals
                    else:
                        self.bullish_signals, self.bearish_signals, self.cycle = self._reset_and_recheck(close, close_reset)
                elif current_bearish == self.level3 - 1:
                    if close > close_l3:
                        self.bearish_signals = self.level3
                        self.cycle = self.bearish_signals
                    else:
                        self.bullish_signals, self.bearish_signals, self.cycle = self._reset_and_recheck(close, close_reset)
            else:
                self.bullish_signals, self.bearish_signals, self.cycle = self._reset_and_recheck(close, close_reset)

        # --- Signal Flags ---
        bull_l1 = self.bullish_signals == self.level1
        bear_l1 = self.bearish_signals == self.level1
        bull_l2 = self.bullish_signals == self.level2
        bear_l2 = self.bearish_signals == self.level2
        bull_l3 = self.bullish_signals == self.level3
        bear_l3 = self.bearish_signals == self.level3

        signal = {
            'bull_l1': bull_l1,
            'bear_l1': bear_l1,
            'bull_l2': bull_l2,
            'bear_l2': bear_l2,
            'bull_l3': bull_l3,
            'bear_l3': bear_l3,
            'bull_count': self.bullish_signals,
            'bear_count': self.bearish_signals,
            'current_price': close
        }
        
        # Reset after Level 3 (as per Pine Script)
        if bull_l3 or bear_l3:
            self.bullish_signals = 0
            self.bearish_signals = 0
            self.cycle = 0
            
        return signal

    def detect_signal(self, closes: List[float]) -> Dict[str, any]:
        """
        Replays the entire history to find the signal at the last candle.
        This ensures stateless behavior for the caller (BacktestEngine/PaperTrader).
        """
        self.reset_state()
        last_signal = self._empty_signal(closes[-1] if closes else 0)
        
        if len(closes) < 5:
            return last_signal
            
        # Replay history
        # We start from index 4 (5th candle) because we need 4 previous candles
        # But wait, the logic needs to build up counts. We should start from the beginning.
        # But we can't check close[4] until index 4.
        
        # We iterate through all candles. For the first 4, we can't really do much logic 
        # that requires close[4], so we just skip or treat as init.
        
        for i in range(len(closes)):
            if i < 4:
                continue
            
            close = closes[i]
            history = closes[:i] # History up to this point
            
            last_signal = self.update(close, history)
            
        return last_signal

    def _empty_signal(self, price):
        return {
            'bull_l1': False, 'bear_l1': False,
            'bull_l2': False, 'bear_l2': False,
            'bull_l3': False, 'bear_l3': False,
            'bull_count': 0, 'bear_count': 0,
            'current_price': price
        }

if __name__ == "__main__":
    # Quick Test
    d = ExhaustionDetector()
    print("ExhaustionDetector initialized.")
