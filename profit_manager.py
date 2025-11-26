import logging
from typing import Optional

logger = logging.getLogger(__name__)

class ProfitManager:
    def __init__(self, wallet_manager, profit_target_ada: float, reserve_ada: float, user_address: str):
        """
        :param wallet_manager: Instance of WalletManager (must have get_balance and send_transaction)
        :param profit_target_ada: Minimum profit amount to trigger withdrawal
        :param reserve_ada: Amount of ADA to keep in the bot (base capital)
        :param user_address: Destination address for profits
        """
        self.wallet = wallet_manager
        self.profit_target_ada = profit_target_ada
        self.reserve_ada = reserve_ada
        self.user_address = user_address

    def check_and_withdraw(self) -> Optional[str]:
        """
        Checks balance. If (Balance - Reserve) >= Profit Target, withdraws the excess.
        Returns tx_hash if withdrawal occurred, else None.
        """
        try:
            current_balance = self.wallet.get_balance()
            profit = current_balance - self.reserve_ada
            
            if profit >= self.profit_target_ada:
                logger.info(f"Profit Target Met! Balance: {current_balance}, Reserve: {self.reserve_ada}, Profit: {profit}")
                logger.info(f"Initiating withdrawal of {profit} ADA to {self.user_address}...")
                
                tx_hash = self.wallet.send_transaction(
                    to_address=self.user_address,
                    amount_ada=profit
                )
                logger.info(f"Withdrawal Successful! Tx Hash: {tx_hash}")
                return tx_hash
            
            return None
            
        except Exception as e:
            logger.error(f"Error in ProfitManager: {e}")
            return None
