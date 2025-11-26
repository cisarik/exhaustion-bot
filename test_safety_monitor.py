import unittest
from safety_monitor import SafetyMonitor

class TestSafetyMonitor(unittest.TestCase):
    def setUp(self):
        self.monitor = SafetyMonitor(
            max_daily_loss_pct=0.05, # 5%
            max_trade_size_usdc=1000.0,
            max_consecutive_losses=3
        )
        
    def test_trade_size_check(self):
        """Test that large trades are rejected."""
        self.assertTrue(self.monitor.check_trade_size(500.0))
        self.assertFalse(self.monitor.check_trade_size(1500.0))
        
    def test_daily_loss_limit(self):
        """Test that trading stops after max daily loss."""
        # Initial capital 1000
        # Loss limit 5% = $50
        
        self.monitor.record_trade_pnl(-20.0) # -2%
        self.assertTrue(self.monitor.can_trade())
        
        self.monitor.record_trade_pnl(-31.0) # Total -51 (-5.1%)
        self.assertFalse(self.monitor.can_trade())
        
    def test_consecutive_losses(self):
        """Test stopping after N consecutive losses."""
        self.monitor.record_trade_pnl(-10.0)
        self.monitor.record_trade_pnl(-10.0)
        self.assertTrue(self.monitor.can_trade())
        
        self.monitor.record_trade_pnl(-10.0) # 3rd loss
        self.assertFalse(self.monitor.can_trade())
        
        # A win should reset
        self.monitor.reset_consecutive() # Manually reset or logic reset?
        # Usually a win resets the counter.
        
    def test_win_resets_consecutive(self):
        self.monitor.record_trade_pnl(-10.0)
        self.monitor.record_trade_pnl(-10.0)
        self.monitor.record_trade_pnl(50.0) # Win
        self.monitor.record_trade_pnl(-10.0) # 1st loss again
        
        self.assertTrue(self.monitor.can_trade())

if __name__ == '__main__':
    unittest.main()
