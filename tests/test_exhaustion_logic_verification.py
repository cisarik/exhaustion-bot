import unittest
from exhaustion_detector import ExhaustionDetector

class TestExhaustionLogicStrict(unittest.TestCase):
    def test_bullish_sequence(self):
        """
        Verifies the logic against a manually constructed sequence that should trigger L1, L2, L3.
        Pine Script Defaults: L1=9, L2=12, L3=14. Lookbacks: 4, 3, 2.
        """
        detector = ExhaustionDetector(level1=9, level2=12, level3=14, lookback1=4, lookback2=3, lookback3=2)
        
        # Construct a sequence
        # We need enough history to start. 4 candles.
        # [100, 100, 100, 100]
        
        # We need 9 candles where close < close[4].
        # Candle 1 (Index 4): close < history[0] (100). Let's use 90.
        # Candle 2 (Index 5): close < history[1] (100). Let's use 90.
        # ...
        # To make it simple, let's just make price drop continuously.
        # 100, 100, 100, 100, 90, 89, 88, 87, 86, 85, 84, 83, 82
        # Indices:
        # 0,1,2,3 = Init
        # 4: 90 < 100 (close[4]). Bull=1.
        # 5: 89 < 100. Bull=2.
        # ...
        
        prices = [100.0] * 4
        # Generate 9 candles that are strictly lower than close[4]
        # To ensure close < close[4], a simple descending sequence works.
        current_price = 99.0
        for _ in range(9):
            prices.append(current_price)
            current_price -= 1.0
            
        # At this point, we have 4 + 9 = 13 candles.
        # The last candle (index 12) should trigger Level 1 (Bullish=9).
        
        # Replay
        signal = detector.detect_signal(prices)
        self.assertTrue(signal['bull_l1'], "Level 1 Bullish should be True after 9 counts")
        self.assertEqual(signal['bull_count'], 9)
        
        # Now we need 3 more candles for Level 2 (Total 12).
        # Condition for 10, 11, 12 is: close < close[3].
        # Current prices end at 91 (index 12).
        # Next candle (index 13). Ref is index 10.
        # prices[10] is ... let's compute.
        
        # Let's continue generating.
        # We need close < close[3] for next 3 steps.
        # Since our sequence is strictly decreasing (step -1), close[0] < close[3] is always true (p < p+3).
        
        for _ in range(3):
            prices.append(current_price)
            current_price -= 1.0
            
        # Total 13 + 3 = 16 candles? No. 4 + 9 = 13. Index 0..12.
        # Added 3 -> Index 13, 14, 15.
        # Index 15 should be Bullish=12 (Level 2).
        
        signal = detector.detect_signal(prices)
        self.assertTrue(signal['bull_l2'], "Level 2 Bullish should be True after 12 counts")
        self.assertEqual(signal['bull_count'], 12)
        
        # Now Level 3 (14 counts). Need 2 more.
        # Condition: close < close[2].
        # Since step is -1, close < close[2] is true (p < p+2).
        
        for _ in range(2):
            prices.append(current_price)
            current_price -= 1.0
            
        # Index 16, 17.
        # Index 17 should be Bullish=14 (Level 3).
        
        signal = detector.detect_signal(prices)
        self.assertTrue(signal['bull_l3'], "Level 3 Bullish should be True after 14 counts")
        self.assertEqual(signal['bull_count'], 14)
        
        # Next candle should reset and start new cycle (Count 1)
        prices.append(current_price)
        signal = detector.detect_signal(prices)
        self.assertEqual(signal['bull_count'], 1, "Should restart count to 1 after L3 reset")

if __name__ == '__main__':
    unittest.main()
