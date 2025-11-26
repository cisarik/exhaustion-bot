import unittest
from exhaustion_detector import ExhaustionDetector

class TestExhaustionDetector(unittest.TestCase):
    def setUp(self):
        self.detector = ExhaustionDetector()

    def test_bullish_level_1(self):
        """Test detection of Level 1 (9 counts)."""
        # We need a sequence where close < close[4] for 9 bars.
        # History needs to be at least 9 + 4 = 13 bars long.
        
        # Construct a sequence
        # Bars 0-3: Init
        prices = [10.0, 10.0, 10.0, 10.0] 
        
        # Bars 4-12 (9 bars): Each lower than 4 bars ago
        # To ensure close[i] < close[i-4], we can just decrease price monotonically
        for i in range(9):
            prices.append(9.0 - i * 0.1)
            
        # Run detector
        # We need to feed it bar by bar or full list. 
        # The new detector will likely be stateful or re-process.
        # Let's assume we pass the full list and it returns the signal for the LAST bar.
        
        signal = self.detector.detect_signal(prices)
        
        self.assertTrue(signal['bull_l1'])
        self.assertEqual(signal['bull_count'], 9)
        
    def test_bullish_level_3(self):
        """Test detection of Level 3 (14 counts) with variable lookback."""
        # Level 1 (9): close < close[4]
        # Level 2 (12): close < close[3] (for counts 10, 11, 12)
        # Level 3 (14): close < close[2] (for counts 13, 14)
        
        prices = [100.0] * 50 # Init buffer
        
        # Start the sequence at index 10
        start_idx = 10
        
        # Count 1-9 (close < close[4])
        for i in range(9):
            # We need prices[current] < prices[current-4]
            # Let's just make a steep drop
            prices[start_idx + i] = 90.0 - i
            
        # Count 10-12 (close < close[3])
        # current is start_idx + 9, +10, +11
        for i in range(9, 12):
            prices[start_idx + i] = prices[start_idx + i - 3] - 1.0
            
        # Count 13-14 (close < close[2])
        for i in range(12, 14):
            prices[start_idx + i] = prices[start_idx + i - 2] - 1.0
            
        # Slice up to the 14th bar
        test_slice = prices[:start_idx + 14]
        
        signal = self.detector.detect_signal(test_slice)
        
        self.assertTrue(signal['bull_l3'])
        self.assertEqual(signal['bull_count'], 14)

if __name__ == '__main__':
    unittest.main()
