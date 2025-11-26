import unittest
from unittest.mock import MagicMock, patch
from profit_manager import ProfitManager

class TestProfitManager(unittest.TestCase):
    def setUp(self):
        # Mock wallet manager
        self.mock_wallet = MagicMock()
        self.mock_wallet.get_balance.return_value = 1000.0 # 1000 ADA
        self.mock_wallet.send_transaction.return_value = "tx_hash_123"
        
        self.manager = ProfitManager(
            wallet_manager=self.mock_wallet,
            profit_target_ada=100.0, # Withdraw if profit > 100
            reserve_ada=500.0,       # Keep 500 ADA in bot
            user_address="addr_user_mainnet_123"
        )
        
    def test_no_withdraw_if_below_threshold(self):
        """Test that no withdrawal happens if balance is low."""
        self.mock_wallet.get_balance.return_value = 550.0 # 50 profit (reserve 500)
        # Threshold is 100 profit, so need 600 total.
        
        result = self.manager.check_and_withdraw()
        self.assertIsNone(result)
        self.mock_wallet.send_transaction.assert_not_called()
        
    def test_withdraw_if_above_threshold(self):
        """Test withdrawal when profit target is met."""
        self.mock_wallet.get_balance.return_value = 650.0 # 150 profit
        # Should withdraw 150 ADA (keeping 500 reserve)
        
        result = self.manager.check_and_withdraw()
        self.assertEqual(result, "tx_hash_123")
        self.mock_wallet.send_transaction.assert_called_with(
            to_address="addr_user_mainnet_123",
            amount_ada=150.0
        )

if __name__ == '__main__':
    unittest.main()
