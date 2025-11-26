from pycardano import HDWallet, Network, Address
from mnemonic import Mnemonic
import os
import logging
import sqlite3
import qrcode
from crypto_utils import CryptoUtils

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DB_FILE = "bot_data.db"

class WalletManager:
    def __init__(self, network: Network = Network.TESTNET):
        self.mnemo = Mnemonic("english")
        self.network = network
        self.init_db()
        
        # Security: Load Master Password
        password = os.getenv("BOT_MASTER_PASSWORD", "default_insecure_password")
        if password == "default_insecure_password":
            logger.warning("USING INSECURE DEFAULT PASSWORD. SET 'BOT_MASTER_PASSWORD' ENV VAR.")
        
        fixed_salt = b'cardano_bot_salt' 
        self.crypto = CryptoUtils(password, fixed_salt)

    def init_db(self):
        """Initialize SQLite database."""
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS wallets
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      wallet_name TEXT,
                      mnemonic_encrypted TEXT,
                      address TEXT,
                      network TEXT,
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        conn.commit()
        conn.close()
        logger.info("Database initialized.")

    def generate_wallet(self, name: str = "Main Wallet") -> dict:
        """Generates a new BIP39 mnemonic and derives a Shelley address via PyCardano."""
        from pycardano import PaymentVerificationKey, StakeVerificationKey
        
        words = self.mnemo.generate(strength=256) # 24 words
        
        # Derive Address using PyCardano
        hdwallet = HDWallet.from_mnemonic(words)
        
        # Derive account 0, chain 0 (external), address 0
        hdwallet_spend = hdwallet.derive_from_path("m/1852'/1815'/0'/0/0")
        hdwallet_stake = hdwallet.derive_from_path("m/1852'/1815'/0'/2/0")
        
        # Convert raw bytes to VerificationKeys
        spend_vk = PaymentVerificationKey.from_primitive(hdwallet_spend.public_key)
        stake_vk = StakeVerificationKey.from_primitive(hdwallet_stake.public_key)
        
        address = Address(spend_vk.hash(), stake_vk.hash(), network=self.network)
        address_str = str(address)
        
        # Encrypt mnemonic
        encrypted_mnemonic = self.crypto.encrypt(words)
        
        self.save_wallet(name, encrypted_mnemonic, address_str)
        self.generate_qr(address_str, name)
        
        return {
            "name": name,
            "mnemonic": words, # Return plain for display ONCE
            "address": address_str,
            "network": self.network.name
        }

    def get_balance(self, address: str) -> float:
        """
        Mock balance for now. In production, use BlockFrost or PyCardano.
        """
        # TODO: Implement real balance check
        return 0.0

    def send_transaction(self, to_address: str, amount_ada: float) -> str:
        """
        Mock transaction.
        """
        # TODO: Implement real transaction building
        return "tx_mock_hash_12345"

    def backup_wallet(self, wallet_name: str, backup_file: str = "agent_x_private_seed.key"):
        """
        Exports the encrypted mnemonic to a file with restricted permissions (600).
        """
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT mnemonic_encrypted FROM wallets WHERE wallet_name=?", (wallet_name,))
        row = c.fetchone()
        conn.close()
        
        if not row:
            raise ValueError(f"Wallet '{wallet_name}' not found.")
            
        encrypted_data = row[0]
        
        # Write to file
        with open(backup_file, "wb") as f:
            f.write(encrypted_data)
            
        # Set permissions to 600 (Read/Write by owner only)
        os.chmod(backup_file, 0o600)
        logger.info(f"Wallet '{wallet_name}' backed up to {backup_file} with permissions 600.")
        return backup_file

    def restore_wallet(self, backup_file: str, new_name: str) -> dict:
        """
        Restores a wallet from an encrypted backup file.
        """
        if not os.path.exists(backup_file):
            raise FileNotFoundError(f"Backup file {backup_file} not found.")
            
        with open(backup_file, "rb") as f:
            encrypted_data = f.read()
            
        # Verify we can decrypt it (password check)
        try:
            mnemonic = self.crypto.decrypt(encrypted_data)
        except Exception:
            raise ValueError("Failed to decrypt backup. Wrong password or corrupted file.")
            
        # Re-derive address (PyCardano logic duplicated from generate_wallet)
        # Ideally refactor address derivation into a helper method
        from pycardano import HDWallet, PaymentVerificationKey, StakeVerificationKey, Address
        
        hdwallet = HDWallet.from_mnemonic(mnemonic)
        hdwallet_spend = hdwallet.derive_from_path("m/1852'/1815'/0'/0/0")
        hdwallet_stake = hdwallet.derive_from_path("m/1852'/1815'/0'/2/0")
        
        spend_vk = PaymentVerificationKey.from_primitive(hdwallet_spend.public_key)
        stake_vk = StakeVerificationKey.from_primitive(hdwallet_stake.public_key)
        
        address = Address(spend_vk.hash(), stake_vk.hash(), network=self.network)
        address_str = str(address)
        
        # Save to DB
        self.save_wallet(new_name, encrypted_data, address_str)
        self.generate_qr(address_str, new_name)
        
        return {
            "name": new_name,
            "address": address_str,
            "network": self.network.name
        }

    def save_wallet(self, name, encrypted_mnemonic, address):
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        # Check if column exists (migration for existing DB)
        # For MVP we just try insert, if fails we might need to recreate DB or alter table
        # Let's assume fresh start or handle migration simply
        try:
            c.execute("INSERT INTO wallets (wallet_name, mnemonic_encrypted, address, network) VALUES (?, ?, ?, ?)",
                      (name, encrypted_mnemonic, address, self.network.name))
        except sqlite3.OperationalError:
            # Likely missing columns if DB existed from previous step
            logger.warning("Database schema mismatch. Recreating table...")
            c.execute("DROP TABLE wallets")
            self.init_db()
            c.execute("INSERT INTO wallets (wallet_name, mnemonic_encrypted, address, network) VALUES (?, ?, ?, ?)",
                      (name, encrypted_mnemonic, address, self.network.name))
            
        conn.commit()
        conn.close()
        logger.info(f"Wallet '{name}' saved to DB (Encrypted).")

    def generate_qr(self, data: str, name: str):
        """Generates a QR code for the address."""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        filename = f"wallet_{name.replace(' ', '_')}.png"
        img.save(filename)
        logger.info(f"QR code saved to {filename}")

    def list_wallets(self):
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        try:
            c.execute("SELECT id, wallet_name, address, network FROM wallets")
            rows = c.fetchall()
        except sqlite3.Error:
            rows = []
        conn.close()
        return rows

if __name__ == "__main__":
    # Default to TESTNET for safety
    wm = WalletManager(Network.TESTNET)
    
    logger.info("Generating new PyCardano wallet...")
    wallet = wm.generate_wallet("PyCardano Wallet")
    
    print("\n--- New Wallet Generated ---")
    print(f"Name: {wallet['name']}")
    print(f"Network: {wallet['network']}")
    print(f"Mnemonic: {wallet['mnemonic']}")
    print(f"Address: {wallet['address']}")
    print("----------------------------\n")
